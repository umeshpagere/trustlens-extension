from flask import Blueprint, request, jsonify
from app.services.video_analysis import extract_transcript, analyze_video_with_llm
import asyncio

video_bp = Blueprint('video_bp', __name__)

@video_bp.route('/extract', methods=['POST'])
async def api_extract_video():
    """Extracts speech/transcript from a video URL without analyzing."""
    data = request.json
    if not data or not data.get('videoUrl'):
        return jsonify({"success": False, "error": "Missing videoUrl"}), 400
        
    url = data['videoUrl']
    
    try:
        # Run synchronous extraction in thread to avoid blocking Event Loop
        result = await asyncio.to_thread(extract_transcript, url)
        
        if result.get("success"):
            return jsonify({
                "success": True,
                "platform": result.get("platform_name"),
                "tier": result.get("tier"),
                "transcript": result.get("transcript"),
                "message": "Transcript extracted successfully"
            })
        else:
            return jsonify({
                "success": False,
                "error": result.get("error", "Failed to extract transcript")
            }), 400
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@video_bp.route('/analyze', methods=['POST'])
async def api_analyze_video():
    """Runs LLM analysis on a previously extracted transcript."""
    data = request.json
    if not data or not data.get('transcript') or not data.get('videoUrl'):
        return jsonify({"success": False, "error": "Missing transcript or videoUrl"}), 400
        
    try:
        # Run synchronous LLM analysis in thread to avoid blocking Event Loop
        analysis_result = await asyncio.to_thread(
            analyze_video_with_llm, 
            data['transcript'], 
            data['videoUrl']
        )
        
        return jsonify({
            "success": True,
            "analysis": analysis_result
        })
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
