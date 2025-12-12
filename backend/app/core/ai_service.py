"""
AI Service for Job Description Classification

Uses Google Gemini API to extract structured data from raw job description text.
"""

import json
import logging
from typing import Dict, Optional, List
from datetime import datetime
import google.generativeai as genai
from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize Gemini API
if settings.GEMINI_API_KEY:
    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        logger.info(f"Gemini API configured with model: {settings.GEMINI_MODEL}")
    except Exception as e:
        logger.error(f"Failed to configure Gemini API: {str(e)}")
else:
    logger.warning("GEMINI_API_KEY not set - AI classification will not work")


def classify_job_description(jd_text: str) -> Dict:
    """
    Classify job description text using Google Gemini API.
    
    Extracts structured fields from raw JD text:
    - Job Title
    - Client/Company Name
    - Required Experience (Years)
    - Required Tech Stack/Skills
    - Location
    - Visa Requirements
    - Start Date/Availability
    - Job Type (Contract/Full-time/C2C/W2)
    - JD Summary/Description
    - Additional Notes
    
    Args:
        jd_text: Raw job description text
        
    Returns:
        Dictionary with classified fields
        
    Raises:
        ValueError: If API key is not configured or API call fails
    """
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not configured. Please set it in environment variables.")
    
    try:
        # Create the model
        model = genai.GenerativeModel(settings.GEMINI_MODEL)
        
        # Create a detailed prompt for classification
        prompt = f"""Extract structured information from the following job description text. 
Return a JSON object with the following fields:
- title: Job title (string)
- client_name: Client/Company name (string, or null if not mentioned)
- experience_required: Required years of experience (float number, default to 0 if not mentioned)
- tech_required: List of required technologies/skills (array of strings, empty array if none)
- location: Job location (string, or null if not mentioned)
- visa_required: Visa requirements (string, or null if not mentioned)
- start_date: Start date or availability date in ISO format YYYY-MM-DD (string, or null if not mentioned)
- job_type: Job type - one of: "Contract", "Full-time", "C2C", "W2" (string, default to null if not clear)
- jd_summary: Brief summary of the job description (string, or null)
- additional_notes: Any additional notes or requirements (string, or null)

Job Description Text:
{jd_text}

Return ONLY valid JSON, no additional text or explanation."""

        logger.debug(f"Calling Gemini API with model: {settings.GEMINI_MODEL}")
        
        # Generate response
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.3,  # Lower temperature for more consistent extraction
                "max_output_tokens": 2000,
            }
        )
        
        # Extract JSON from response
        response_text = response.text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        # Parse JSON
        try:
            classified_data = json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {response_text[:200]}")
            raise ValueError(f"AI returned invalid JSON: {str(e)}")
        
        # Validate and normalize the response
        result = {
            "title": classified_data.get("title", "").strip(),
            "client_name": classified_data.get("client_name") or None,
            "experience_required": float(classified_data.get("experience_required", 0)),
            "tech_required": classified_data.get("tech_required", []),
            "location": classified_data.get("location") or None,
            "visa_required": classified_data.get("visa_required") or None,
            "start_date": classified_data.get("start_date") or None,
            "job_type": classified_data.get("job_type") or None,
            "jd_summary": classified_data.get("jd_summary") or None,
            "additional_notes": classified_data.get("additional_notes") or None,
            "description": jd_text,  # Keep original text as description
        }
        
        # Validate required fields
        if not result["title"]:
            result["title"] = "Untitled Position"
        
        # Ensure tech_required is a list
        if not isinstance(result["tech_required"], list):
            result["tech_required"] = []
        
        # Parse start_date if provided
        if result["start_date"]:
            try:
                # Try to parse ISO format date
                datetime.fromisoformat(result["start_date"].replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                # If parsing fails, set to None
                logger.warning(f"Invalid date format: {result['start_date']}")
                result["start_date"] = None
        
        logger.info(f"Successfully classified JD: {result['title']}")
        return result
        
    except Exception as e:
        logger.error(f"Error classifying job description: {str(e)}", exc_info=True)
        raise ValueError(f"Failed to classify job description: {str(e)}")


def is_ai_service_available() -> bool:
    """
    Check if AI service is available and configured.
    
    Returns:
        True if API key is configured, False otherwise
    """
    return bool(settings.GEMINI_API_KEY)

