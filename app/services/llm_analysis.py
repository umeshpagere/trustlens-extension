import json
import re
import base64
from app.config.azure import get_azure_client
from app.config.settings import Config

def analyze_text_with_llm(text: str) -> dict:
    if not text or not isinstance(text, str) or len(text.strip()) == 0:
        raise ValueError("Text input is required")
    
    try:
        client = get_azure_client()
        response = client.chat.completions.create(
            model=Config.AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert AI fact-checker that analyzes text for misinformation, fake news, and credibility risks. 
Your analysis should consider:
- Sensational or clickbait language
- Unverified claims or lack of credible sources
- Emotional manipulation tactics
- Conspiracy theories or false narratives
- Patterns typical of misinformation campaigns
- Factual accuracy indicators

Respond ONLY in valid JSON format. No markdown, no code blocks, no extra text."""
                },
                {
                    "role": "user",
                    "content": f"""Analyze this text for misinformation risk and return JSON only in this exact format:
{{
  "riskLevel": "low" | "medium" | "high",
  "credibilityScore": number (0-100, where 0 is completely unreliable and 100 is highly credible),
  "verdict": "Reliable" | "Questionable" | "High Risk",
  "riskKeywordsFound": string[],
  "explanation": string (detailed explanation of why this verdict was given)
}}

Scoring guidelines:
- 75-100: Reliable - Well-sourced, factual, credible content
- 40-74: Questionable - Some red flags, unverified claims, or suspicious patterns
- 0-39: High Risk - Strong indicators of misinformation, fake news, or manipulation

Text to analyze: {text}"""
                }
            ],
            temperature=0.2,
            max_tokens=500,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        
        if not content:
            raise ValueError("No response content from Azure OpenAI")
        
        parsed_content = content.strip()
        
        if parsed_content.startswith("```json"):
            parsed_content = re.sub(r'^```json\s*', '', parsed_content)
            parsed_content = re.sub(r'\s*```$', '', parsed_content)
        elif parsed_content.startswith("```"):
            parsed_content = re.sub(r'^```\s*', '', parsed_content)
            parsed_content = re.sub(r'\s*```$', '', parsed_content)
        
        result = json.loads(parsed_content)
        
        if not all(key in result for key in ["riskLevel", "credibilityScore", "verdict", "explanation"]):
            raise ValueError("Invalid response format from Azure OpenAI")
        
        if not isinstance(result.get("riskKeywordsFound"), list):
            result["riskKeywordsFound"] = []
        
        return result
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse LLM response: {str(e)}")
    except Exception as e:
        print(f"Azure OpenAI text analysis failed: {str(e)}")
        raise ValueError(f"LLM text analysis failed: {str(e)}")

def detect_image_mime_type(image_bytes: bytes) -> str:
    if image_bytes[:8] == b'\x89PNG\r\n\x1a\n':
        return "image/png"
    elif image_bytes[:2] == b'\xff\xd8':
        return "image/jpeg"
    elif image_bytes[:6] in (b'GIF87a', b'GIF89a'):
        return "image/gif"
    elif image_bytes[:4] == b'RIFF' and image_bytes[8:12] == b'WEBP':
        return "image/webp"
    else:
        return "image/jpeg"

def analyze_image_with_llm(image_bytes: bytes) -> dict:
    if not image_bytes:
        raise ValueError("Image bytes are required")
    
    try:
        mime_type = detect_image_mime_type(image_bytes)
        print(f"🔍 Detected image MIME type: {mime_type}")
        
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        client = get_azure_client()
        response = client.chat.completions.create(
            model=Config.AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert AI multi-layered image analyst, forensic investigator, and fact-checker. Your mission is to perform a deep-dive extraction and verification of every detail in an image to identify misinformation, AI-generation, or manipulation.

Your analysis MUST cover these layers:
1. FULL TEXT EXTRACTION & VERIFICATION:
   - Extract ALL visible text, including small print, signs, and background text.
   - Verify every claim found in the text against factual knowledge. Identify if it's true, false, or a known conspiracy/misinformation narrative.

2. VISUAL CONTENT & CONVEYED MESSAGE:
   - Provide a granular description of all subjects, objects, settings, and actions.
   - Decode the underlying narrative: What emotional response is it trying to trigger? What message is it pushing?

3. AI GENERATION & MANIPULATION FORENSICS:
   - Look for "AI Artifacts": Distorted hands/fingers, inconsistent lighting, unnatural textures, blurred background blending, logical impossibilities (e.g., objects merging), or overly smooth "plastic" skin.
   - Analyze if the image represents a real-world event or is a synthetic creation meant to deceive.

4. VERACITY & TRUST VERDICT:
   - Is it really true? Provide a definitive assessment based on visual evidence and factual verification.

Respond ONLY in valid JSON format. No markdown, no code blocks, no extra text."""
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """Perform a rigorous multi-layered analysis of this image. Provide detailed evidence for your findings.

Return JSON in this exact format:
{
  "riskLevel": "low" | "medium" | "high",
  "credibilityScore": number (0-100),
  "verdict": "Reliable" | "Questionable" | "High Risk",
  "extractedText": "all text extracted from the image",
  "textVerification": "detailed factual verification of the extracted text claims",
  "imageContent": "granular description of what the image is about/depicts",
  "conveyedMessage": "deep analysis of what the image is trying to convey/its intent",
  "veracityCheck": "comprehensive explanation of whether the image and its message are true or not, with evidence",
  "visualRedFlags": ["list of specific visual anomalies or red flags found"],
  "explanation": "concise summary of why this specific verdict was reached",
  "aiGeneratedProbability": number (0-100, where 100 means definitely AI-generated)
}

Critical AI Detection Note: Even if an image looks 'good', look for subtle inconsistencies in shadows, reflections, and fine details like jewelry or text characters that might be slightly warped."""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            temperature=0.1,
            max_tokens=1500,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        
        if not content:
            raise ValueError("No response content from Azure OpenAI")
        
        result = json.loads(content.strip())
        
        if not all(key in result for key in ["riskLevel", "credibilityScore", "verdict", "explanation"]):
            raise ValueError("Invalid response format from Azure OpenAI")
        
        if not isinstance(result.get("visualRedFlags"), list):
            result["visualRedFlags"] = []
            
        return result
        
    except Exception as e:
        print(f"Azure OpenAI image analysis failed: {str(e)}")
        raise ValueError(f"LLM image analysis failed: {str(e)}")
