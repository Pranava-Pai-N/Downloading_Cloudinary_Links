from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import requests
import base64
from io import BytesIO
from PyPDF2 import PdfReader
from urllib.parse import quote_plus, urlparse
import os

app = FastAPI()

class URLRequest(BaseModel):
    url: str

def file_to_base64(file_bytes: bytes) -> str:
    return base64.b64encode(file_bytes).decode("utf-8")

def extract_text_from_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(file_bytes))
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text.strip()

def get_filename_from_url(url: str) -> str:
    parsed_url = urlparse(url)
    filename = os.path.basename(parsed_url.path)

    if not filename:
        filename = f"temp_file{os.path.splitext(url)[1]}"  

    return filename

@app.get("/")
async def root():
    return {"message": "Welcome to the File Processing API."}

@app.post("/download_files")
async def process_url(request: URLRequest):
    file_url = request.url

    try:
        response = requests.get(file_url)
        file_bytes = response.content
        filename = get_filename_from_url(file_url)
        ext = filename.split(".")[-1].lower()

        result = {}
        if ext in ["jpg", "jpeg", "png", "mp4", "mov", "avi"]:
            base64_str = file_to_base64(file_bytes)
            result["Output"] = base64_str
            result["download_link"] = f"data:image/{ext};base64,{base64_str}"  
        elif ext == "pdf":
            result["content"] = extract_text_from_pdf(file_bytes)  
        else:
            result["error"] = f"Unsupported file type: {ext}"

        return JSONResponse(content=result)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
