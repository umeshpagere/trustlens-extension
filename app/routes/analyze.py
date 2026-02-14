from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from app.models.schemas import AnalyzeRequest
from app.services.llm_analysis import analyze_text_with_llm, analyze_image_with_llm
from app.services.scoring import calculate_final_score
from app.services.image_metadata import analyze_image_metadata
from app.services.image_tracing import trace_image
from app.services.image_scoring import calculate_image_credibility
from app.services.analysis_storage_service import store_analysis, get_analysis_by_hash
from app.utils.fetch_image import download_image
from app.utils.hashing import hash_image, hash_text

analyze_bp = Blueprint('analyze', __name__)

VALID_VERDICTS = ["Reliable", "Questionable", "High Risk"]

def normalize_verdict(verdict: str) -> str:
    if isinstance(verdict, str) and verdict in VALID_VERDICTS:
        return verdict
    return "High Risk"


@analyze_bp.route('', methods=['GET'])
def get_analyze_info():
    return jsonify({
        "success": True,
        "message": "TrustLens Analyze API",
        "endpoint": "/api/analyze",
        "method": "POST",
        "description": "Analyze text and images for misinformation risk assessment",
        "requestBody": {
            "text": {
                "type": "string",
                "required": False,
                "minLength": 5,
                "description": "Optional text content to analyze"
            },
            "imageUrl": {
                "type": "string",
                "required": False,
                "format": "url",
                "description": "Optional image URL to analyze"
            }
        },
        "example": {
            "text": "This is a sample text to analyze for misinformation",
            "imageUrl": "https://example.com/image.jpg"
        }
    })


@analyze_bp.route('', methods=['POST'])
def analyze():
    try:
        print("📥 /api/analyze route hit")
        
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "message": "Invalid JSON in request body"
            }), 400
        
        try:
            validated_data = AnalyzeRequest(**data)
        except ValidationError as e:
            return jsonify({
                "success": False,
                "message": e.errors()[0]['msg']
            }), 400
        
        text_analysis = None
        text_hash = None
        text_reused = False
        
        if validated_data.text:
            text_hash = hash_text(validated_data.text)
            existing_text = get_analysis_by_hash(text_hash)
            
            if existing_text:
                print(f"♻️ Reusing cached text analysis for hash: {text_hash[:16]}...")
                text_analysis = existing_text.get("analysis", {})
                text_reused = True
            else:
                try:
                    print(f"✍️ Starting LLM Text Analysis...")
                    llm_result = analyze_text_with_llm(validated_data.text)
                    print(f"✅ LLM Text Analysis Result: {llm_result}")
                    
                    text_analysis = {
                        "riskLevel": llm_result.get("riskLevel", "medium"),
                        "riskKeywordsFound": llm_result.get("riskKeywordsFound", []),
                        "credibilityScore": llm_result.get("credibilityScore", 50),
                        "verdict": normalize_verdict(llm_result.get("verdict")),
                        "explanation": llm_result.get("explanation", "")
                    }
                    
                    store_analysis(text_hash, "text", text_analysis)
                except Exception as e:
                    print(f"❌ Azure OpenAI LLM text analysis failed: {str(e)}")
                    return jsonify({
                        "success": False,
                        "message": f"LLM text analysis failed: {str(e)}"
                    }), 503
        else:
            print("📝 No text provided, skipping LLM text analysis")
            text_analysis = {"status": "skipped"}
        
        image_analysis = {"status": "skipped"}
        image_hash = None
        image_reused = False
        
        if validated_data.imageUrl:
            try:
                print(f"🖼️ Fetching image: {validated_data.imageUrl}")
                download_result = download_image(validated_data.imageUrl)
                
                if download_result.get("success") and download_result.get("buffer"):
                    image_buffer = download_result["buffer"]
                    
                    image_hash = hash_image(image_buffer)
                    existing_image = get_analysis_by_hash(image_hash)
                    
                    if existing_image:
                        print(f"♻️ Reusing cached image analysis for hash: {image_hash[:16]}...")
                        image_analysis = existing_image.get("analysis", {})
                        image_analysis["reused"] = True
                        image_reused = True
                    else:
                        metadata = {}
                        tracing = {}
                        try:
                            metadata = analyze_image_metadata(image_buffer)
                            tracing = trace_image(image_buffer)
                        except Exception as tech_err:
                            print(f"⚠️ Technical analysis error: {str(tech_err)}")

                        llm_image_result = {}
                        try:
                            print("🎨 Starting LLM Image Analysis...")
                            llm_image_result = analyze_image_with_llm(image_buffer)
                            print(f"✅ LLM Image Analysis Result: {llm_image_result}")
                        except Exception as llm_err:
                            print(f"❌ LLM image analysis failed: {str(llm_err)}")

                        ai_prob = llm_image_result.get("aiGeneratedProbability", 0)
                        credibility_result = calculate_image_credibility(metadata, tracing, ai_prob)
                        
                        llm_score = llm_image_result.get("credibilityScore", 100)
                        tech_score = credibility_result["score"]
                        final_image_score = min(llm_score, tech_score)
                        
                        final_image_verdict = normalize_verdict(llm_image_result.get("verdict", credibility_result.get("verdict", "High Risk")))
                        
                        if final_image_score < 40:
                            final_image_verdict = "High Risk"
                        elif final_image_score < 75:
                            final_image_verdict = "Questionable"

                        image_analysis = {
                            "status": "processed",
                            "metadata": metadata,
                            "tracing": tracing,
                            "llmAnalysis": {
                                "riskLevel": llm_image_result.get("riskLevel", "medium"),
                                "verdict": normalize_verdict(llm_image_result.get("verdict")),
                                "credibilityScore": llm_image_result.get("credibilityScore", 50),
                                "extractedText": llm_image_result.get("extractedText", ""),
                                "textVerification": llm_image_result.get("textVerification", ""),
                                "imageContent": llm_image_result.get("imageContent", ""),
                                "conveyedMessage": llm_image_result.get("conveyedMessage", ""),
                                "veracityCheck": llm_image_result.get("veracityCheck", ""),
                                "explanation": llm_image_result.get("explanation", "Image analysis complete."),
                                "visualRedFlags": llm_image_result.get("visualRedFlags", []),
                                "aiGeneratedProbability": llm_image_result.get("aiGeneratedProbability", 0)
                            } if llm_image_result else None,
                            "credibilityScore": final_image_score,
                            "verdict": final_image_verdict
                        }
                        
                        store_analysis(image_hash, "image", image_analysis)
                else:
                    print(f"⚠️ [Image Analysis] Skipped due to download failure: {download_result.get('error')}")
                    image_analysis = {"status": "skipped", "error": download_result.get("error")}
            except Exception as e:
                print(f"❌ [Image Analysis] Unexpected error: {str(e)}")
                image_analysis = {"status": "skipped", "error": str(e)}
        
        final_result = calculate_final_score(text_analysis, image_analysis)
        
        response_data = {
            "success": True,
            "textAnalysis": text_analysis,
            "imageAnalysis": image_analysis,
            "finalResult": final_result
        }
        
        if text_hash:
            response_data["hash"] = text_hash
            response_data["reused"] = text_reused
        if image_hash:
            # If both exist, image hash takes precedence for the top-level 'hash' 
            # or we could keep them separate. The prompt implies a single result structure.
            response_data["hash"] = image_hash
            response_data["reused"] = image_reused
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500
