import os
import json
import re
from dotenv import load_dotenv

load_dotenv()

ALLOWED_CATEGORIES = ["Academics", "Infrastructure", "Hostel", "Transport", "Canteen", "IT", "Other"]
ALLOWED_PRIORITIES = ["Low", "Medium", "High"]

def get_gemini_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None
    try:
        from google import genai
        return genai.Client(api_key=api_key)
    except Exception as e:
        print(f"Error initializing google-genai client: {e}")
        return None

def fallback_classifier(title, description):
    """Fallback rule-based classifier if Gemini API key is missing or fails."""
    text = (title + " " + description).lower()
    
    # Category rule matching
    category = "Other"
    department = "Administration"
    
    if any(k in text for k in ["projector", "fan", "light", "bench", "door", "window", "ac", "air conditioner", "building", "water", "pipe", "toilet", "washroom"]):
        category = "Infrastructure"
        department = "Estate & Maintenance"
    elif any(k in text for k in ["wifi", "internet", "lab", "computer", "portal", "login", "server", "software", "network", "printer"]):
        category = "IT"
        department = "IT Support Cell"
    elif any(k in text for k in ["exam", "marks", "grade", "professor", "teacher", "lecture", "attendance", "syllabus", "assignment"]):
        category = "Academics"
        department = "Academic Affairs"
    elif any(k in text for k in ["hostel", "room", "mess", "bed", "warden", "roommate"]):
        category = "Hostel"
        department = "Hostel Administration"
    elif any(k in text for k in ["bus", "transport", "driver", "route", "parking"]):
        category = "Transport"
        department = "Transport Department"
    elif any(k in text for k in ["canteen", "food", "hygiene", "snack", "cafeteria"]):
        category = "Canteen"
        department = "Canteen Committee"

    # Priority rule matching
    priority = "Medium"
    if any(k in text for k in ["urgent", "tomorrow", "exam", "fire", "leak", "broken", "danger", "emergency", "immediately", "today"]):
        priority = "High"
    elif any(k in text for k in ["minor", "request", "suggestion", "slow", "feedback"]):
        priority = "Low"

    summary = f"{title[:60]}... Needs attention from {department}." if len(title) > 60 else f"{title}. Needs attention from {department}."

    return {
        "category": category,
        "priority": priority,
        "department": department,
        "summary": summary,
        "is_fallback": True,
        "notice": "Generated via Local Rule Engine (Set GEMINI_API_KEY to enable live Gemini AI)."
    }

def analyze_complaint_with_gemini(title, description):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key or api_key.strip() == "" or api_key == "your_gemini_api_key_here":
        print("GEMINI_API_KEY not found or default. Using fallback classifier.")
        return fallback_classifier(title, description)

    prompt = f"""
You are an AI assistant for a college administration portal.
Analyze the following student complaint and classify it into standard categories.

Complaint Title: {title}
Complaint Description: {description}

Requirements:
1. Return ONLY a valid JSON object with key names: "category", "priority", "department", "summary".
2. "category" MUST be one of: {json.dumps(ALLOWED_CATEGORIES)}
3. "priority" MUST be one of: {json.dumps(ALLOWED_PRIORITIES)}
4. "department" should be the most relevant college department (e.g., "Maintenance", "IT Support", "Academic Cell", "Hostel Warden", "Transport Office", "Canteen Operations").
5. "summary" should be a clear, concise 1-2 sentence summary of the issue.

Example JSON output:
{{
  "category": "Infrastructure",
  "priority": "High",
  "department": "Maintenance",
  "summary": "Projector in Room 204 is non-functional, requiring urgent repair ahead of scheduled exam."
}}
"""

    try:
        # Attempt standard google.genai SDK
        client = get_gemini_client()
        if client:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            raw_text = response.text.strip()
        else:
            # Try google.generativeai if google-genai fails
            import google.generativeai as genai_legacy
            genai_legacy.configure(api_key=api_key)
            model = genai_legacy.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            raw_text = response.text.strip()

        # Parse JSON from response
        # Clean markdown codeblocks if present
        json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(0))
        else:
            data = json.loads(raw_text)

        # Validate fields
        category = data.get("category", "Other")
        if category not in ALLOWED_CATEGORIES:
            category = "Other"

        priority = data.get("priority", "Medium")
        if priority not in ALLOWED_PRIORITIES:
            priority = "Medium"

        department = data.get("department", "General Administration")
        summary = data.get("summary", title)

        return {
            "category": category,
            "priority": priority,
            "department": department,
            "summary": summary,
            "is_fallback": False
        }

    except Exception as e:
        print(f"Gemini API call error: {e}. Falling back to rule engine.")
        res = fallback_classifier(title, description)
        res["notice"] = f"Gemini API Error: {str(e)}. Used local rule fallback."
        return res
