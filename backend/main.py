from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
try:
    import PyPDF2
except ImportError:
    print("PyPDF2 is not installed. Please run: pip install PyPDF2")
    exit()
from collections import Counter
import io
import httpx
import re

# --- IMPORTANT: ADD YOUR GEMINI API KEY HERE ---
# Get your key from https://aistudio.google.com/app/apikey
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE"
# ---

app = FastAPI()

# --- CORS Configuration ---
origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:5500",
    "null", 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)
# --- End of CORS Configuration ---

db = {}
id_counter = 0


# ----------- UTILITIES --------------

def build_summary_prompt(text: str) -> str:
    """Builds a dynamic prompt for Gemini based on PDF length"""
    word_count = len(text.split())
    if word_count < 500:
        target_range = "50–100 words"
    elif word_count < 1500:
        target_range = "100–150 words"
    else:
        target_range = "150–200 words"

    return f"""
    Act as a professional recruiter analyzing a resume.
    Provide a clear and professional summary of the candidate’s profile.
    The summary should be {target_range}, highlighting key skills, significant experiences, and overall qualifications.

    Resume Text:
    ---
    {text}
    """


async def get_gemini_summary(text: str) -> str:
    """
    Calls the Google Gemini API asynchronously.
    Returns the summary on success, or raises an error string on failure.
    """
    if not text.strip():
        return "ERROR: Could not summarize empty document."

    max_chars = 15000
    truncated_text = text[:max_chars]

    API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}

    prompt = build_summary_prompt(truncated_text)

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.5,
            "maxOutputTokens": 512,   # allow longer summaries
        }
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(API_URL, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
        
        data = response.json()
        summary = data["candidates"][0]["content"]["parts"][0]["text"]
        return summary.strip()

    except httpx.HTTPStatusError as e:
        error_details = e.response.text
        if "API key not valid" in error_details:
            return "ERROR: Your Gemini API Key is invalid or expired."
        return f"ERROR: Gemini API returned status {e.response.status_code}."
    except httpx.RequestError:
        return "ERROR: Could not connect to Gemini AI service."


def extract_text_from_pdf(file_content: bytes) -> str:
    """Extracts text from the content of a PDF file."""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        print(f"Error extracting PDF text: {e}")
        raise HTTPException(status_code=400, detail="Could not extract text from PDF.")


def local_fallback_summary(text: str) -> str:
    """
    Simple fallback summarizer if Gemini API fails.
    Extracts first few sentences until ~120 words.
    """
    sentences = re.split(r'(?<=[.!?])\s+', text)
    summary = []
    word_count = 0
    for sent in sentences:
        words = sent.split()
        if not words:
            continue
        summary.append(sent)
        word_count += len(words)
        if word_count > 120:
            break
    return " ".join(summary).strip() or "Summary could not be generated locally."


# ----------- ROUTES --------------

@app.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    """
    Receives a PDF, attempts to get a Gemini AI summary, 
    and uses a local fallback summarizer on failure.
    """
    global id_counter
    
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a PDF.")

    contents = await file.read()
    
    try:
        text = extract_text_from_pdf(contents)
        insights = ""

        if GEMINI_API_KEY and GEMINI_API_KEY != "YOUR_GEMINI_API_KEY_HERE":
            summary_or_error = await get_gemini_summary(text)
            if summary_or_error.startswith("ERROR:"):
                # Gemini failed → use local fallback
                print("Gemini failed. Using local summarizer...")
                insights = local_fallback_summary(text)
            else:
                insights = summary_or_error
        else:
            insights = local_fallback_summary(text)

        db[str(id_counter)] = {"filename": file.filename, "insights": insights}
        id_counter += 1
        
        return {"filename": file.filename, "insights": insights}
    except Exception as e:
        print(f"An unexpected error occurred in upload_resume: {e}")
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {e}")


@app.get("/history")
async def get_history():
    """Returns the history of uploaded documents."""
    return db
