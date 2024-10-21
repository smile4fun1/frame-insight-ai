import os
import subprocess
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
import tempfile
import base64
import requests
from dotenv import load_dotenv
import hashlib
import json
from pathlib import Path
import asyncio
from typing import List
from fpdf import FPDF
import markdown
import shutil
from openai import OpenAI
import time
import io
import textwrap
import logging

# Add this near the top of the file, after the imports
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()  # Load environment variables from .env file

app = FastAPI()

# Update the CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://frame-insight-ai.vercel.app", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

# Initialize the OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Updated and enhanced Analysis Types
ANALYSIS_TYPES = {
    "general": "Provide a detailed general analysis of the video content, including key elements, actions, and overall context.",
    "ui_interaction": "Analyze the user interface interactions in detail, focusing on button clicks, menu navigation, cursor movements, and any changes in the UI state.",
    "emotion_recognition": "Detect and analyze emotions of people in the video, including facial expressions, body language, and any changes in emotional state over time.",
    "object_detection": "Identify and describe key objects in the video, their positions, movements, and any interactions between objects.",
    "text_recognition": "Recognize and transcribe any text visible in the video, including on-screen displays, subtitles, or text within the scene.",
    "action_recognition": "Identify and describe specific actions or activities occurring in the video, including human actions, object movements, or scene changes.",
    "scene_understanding": "Analyze the overall scene composition, including setting, lighting, camera angles, and how these elements contribute to the video's message or mood.",
    "color_analysis": "Examine the color palette used in the video, including dominant colors, color transitions, and how colors are used to convey mood or emphasis.",
    "audio_visual_sync": "Analyze the synchronization between visual elements and any audio cues (if present), including lip-sync, sound effects matching visuals, or music beats aligning with scene changes.",
    "temporal_analysis": "Examine how the video content changes over time, including scene transitions, narrative progression, or changes in visual elements.",
    "accessibility_assessment": "Evaluate the video for accessibility features, such as closed captions, visual clarity, color contrast, and ease of understanding without audio.",
    "brand_presence": "Identify and analyze any brand elements present in the video, including logos, product placements, or brand-specific color schemes and designs.",
    "custom": "Analyze the video based on a custom prompt provided by the user."
}

class RateLimiter:
    def __init__(self, tokens_per_minute):
        self.tokens = tokens_per_minute
        self.max_tokens = tokens_per_minute
        self.updated_at = time.monotonic()

    def consume(self, tokens):
        now = time.monotonic()
        time_passed = now - self.updated_at
        self.tokens = min(self.max_tokens, self.tokens + time_passed * (self.max_tokens / 60))
        self.updated_at = now

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

rate_limiter = RateLimiter(30)  # 30 requests per minute, adjust as needed

def get_cache_key(file_content, prompt):
    file_hash = hashlib.md5(file_content).hexdigest()
    prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
    return f"{file_hash}_{prompt_hash}"

def get_cached_result(cache_key):
    cache_file = CACHE_DIR / f"{cache_key}.json"
    if cache_file.exists():
        with cache_file.open("r") as f:
            return json.load(f)
    return None

def save_to_cache(cache_key, result):
    cache_file = CACHE_DIR / f"{cache_key}.json"
    with cache_file.open("w") as f:
        json.dump(result, f)

def extract_frames(video_path, output_folder, frame_interval=1):
    os.makedirs(output_folder, exist_ok=True)
    ffmpeg_command = shutil.which('ffmpeg') or 'ffmpeg'  # This will find FFmpeg in the system PATH
    command = [
        ffmpeg_command,
        '-i', video_path,
        '-vf', f'fps=1/{frame_interval}',
        f'{output_folder}/frame_%04d.jpg'
    ]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        raise Exception(f"FFmpeg error: {e.stderr}")
    except FileNotFoundError:
        raise Exception("FFmpeg not found. Please make sure FFmpeg is installed and available in the system PATH.")
    
    return [os.path.join(output_folder, f) for f in os.listdir(output_folder) if f.endswith('.jpg')]

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_frames_with_gpt4(frames, analysis_type, custom_prompt=""):
    system_message = "You are an AI assistant that analyzes video frames and provides insights based on the given prompt. Provide a detailed analysis."
    
    if analysis_type in ANALYSIS_TYPES:
        prompt = ANALYSIS_TYPES[analysis_type]
    else:
        prompt = custom_prompt if custom_prompt else "Provide a general analysis of the video content."

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": [{"type": "text", "text": f"Analyze the following video frames based on this instruction: {prompt}. Provide a comprehensive analysis with as much detail as possible."}]}
    ]

    for frame in frames[:5]:  # Limit to 5 frames for this example
        with open(frame, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        messages.append({
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                }
            ]
        })

    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # Using the correct model name
            messages=messages,
            max_tokens=1000  # Increase the token limit for a longer response
        )
        return response.choices[0].message.content
    except Exception as e:
        return {"error": str(e)}

async def process_chunk(chunk: bytes, chunk_number: int, total_chunks: int, analysis_type: str, custom_prompt: str = ""):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
        temp_file.write(chunk)
        temp_file_path = temp_file.name

    frames_folder = tempfile.mkdtemp()
    try:
        extracted_frames = extract_frames(temp_file_path, frames_folder)
        gpt4_analysis = analyze_frames_with_gpt4(extracted_frames, analysis_type, custom_prompt)
        
        result = {
            "chunk_number": chunk_number,
            "total_chunks": total_chunks,
            "frames_extracted": len(extracted_frames),
            "analysis": gpt4_analysis
        }
    except Exception as e:
        result = {
            "error": str(e)
        }
    finally:
        # Clean up temporary files
        os.unlink(temp_file_path)
        shutil.rmtree(frames_folder)
    
    return result

def generate_pdf(result):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Video Analysis Result", ln=1, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt=f"Filename: {result.get('filename', 'N/A')}", ln=1)
    pdf.cell(200, 10, txt=f"Analysis Type: {result.get('analysis_type', 'N/A')}", ln=1)
    
    if 'custom_prompt' in result and result['custom_prompt']:
        pdf.cell(200, 10, txt=f"Custom Prompt: {result['custom_prompt']}", ln=1)
    
    pdf.ln(10)
    
    if 'chunks' in result:
        for chunk in result['chunks']:
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(200, 10, txt=f"Chunk {chunk['chunk_number']} of {chunk['total_chunks']}", ln=1)
            pdf.set_font("Arial", '', 12)
            pdf.cell(200, 10, txt=f"Frames extracted: {chunk['frames_extracted']}", ln=1)
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(200, 10, txt="GPT-4 Analysis:", ln=1)
            pdf.set_font("Arial", '', 12)
            text = chunk['analysis']
            wrapped_text = textwrap.wrap(text, width=90)
            for line in wrapped_text:
                pdf.cell(0, 10, txt=line, ln=1)
            pdf.ln(10)
    else:
        pdf.set_font("Arial", '', 12)
        pdf.cell(200, 10, txt=f"Frames extracted: {result.get('frames_extracted', 'N/A')}", ln=1)
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt="GPT-4 Analysis:", ln=1)
        pdf.set_font("Arial", '', 12)
        text = result.get('analysis', 'N/A')
        wrapped_text = textwrap.wrap(text, width=90)
        for line in wrapped_text:
            pdf.cell(0, 10, txt=line, ln=1)
    
    return pdf.output(dest='S').encode('latin-1')

def generate_markdown(result):
    md = f"# Video Analysis Result\n\n"
    md += f"**Filename:** {result['filename']}\n"
    md += f"**Analysis Type:** {result['analysis_type']}\n"
    
    if 'custom_prompt' in result and result['custom_prompt']:
        md += f"**Custom Prompt:** {result['custom_prompt']}\n"
    
    if 'chunks' in result:
        for chunk in result['chunks']:
            md += f"\n## Chunk {chunk['chunk_number']} of {chunk['total_chunks']}\n"
            md += f"**Frames extracted:** {chunk['frames_extracted']}\n"
            md += f"### GPT-4 Analysis:\n```json\n{json.dumps(chunk['analysis'], indent=2)}\n```\n"
    else:
        md += f"\n**Frames extracted:** {result['frames_extracted']}\n"
        md += f"## GPT-4 Analysis:\n```json\n{json.dumps(result['analysis'], indent=2)}\n```\n"
    
    return md

@app.post("/upload_chunk")
async def upload_chunk(
    chunk: UploadFile = File(...),
    chunk_number: int = Form(...),
    total_chunks: int = Form(...),
    analysis_type: str = Form(...),
    custom_prompt: str = Form("")
):
    chunk_content = await chunk.read()
    result = await process_chunk(chunk_content, chunk_number, total_chunks, analysis_type, custom_prompt)
    return JSONResponse(result)

@app.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    analysis_type: str = Form(...),
    custom_prompt: str = Form("")
):
    if not rate_limiter.consume(1):
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Please try again later.")

    file_content = await file.read()
    cache_key = get_cache_key(file_content, f"{analysis_type}_{custom_prompt}")
    
    cached_result = get_cached_result(cache_key)
    if cached_result:
        return JSONResponse(cached_result)

    # Process the entire video if it's small enough
    if len(file_content) < 10 * 1024 * 1024:  # 10 MB threshold
        result = await process_chunk(file_content, 1, 1, analysis_type, custom_prompt)
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        save_to_cache(cache_key, result)
        return JSONResponse(result)
    else:
        raise HTTPException(status_code=413, detail="File too large. Please use chunked upload.")

@app.get("/analysis_types")
async def get_analysis_types():
    logger.info("Received request for analysis types")
    logger.debug(f"Returning analysis types: {ANALYSIS_TYPES}")
    return ANALYSIS_TYPES

@app.get("/download/{format}/{cache_key}")
async def download_result(format: str, cache_key: str):
    result = get_cached_result(cache_key)
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    
    if format == "json":
        return JSONResponse(result)
    elif format == "pdf":
        pdf_content = generate_pdf(result)
        return FileResponse(
            io.BytesIO(pdf_content),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=analysis_result.pdf"}
        )
    elif format == "markdown":
        md_content = generate_markdown(result)
        return FileResponse(
            io.BytesIO(md_content.encode()),
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename=analysis_result.md"}
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid format")

# Add a new endpoint to clear the cache
@app.post("/clear_cache")
async def clear_cache():
    try:
        shutil.rmtree(CACHE_DIR)
        CACHE_DIR.mkdir(exist_ok=True)
        return JSONResponse({"message": "Cache cleared successfully"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")

@app.get("/health")
async def health_check():
    logger.info("Health check endpoint accessed")
    return {"status": "ok"}

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "Welcome to FrameInsight AI API"}

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting the FastAPI application")
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
