from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from rag import rag_pipeline
import uvicorn
import os

app = FastAPI(title="AI Document Assistant")

# Ensure static directory exists
os.makedirs("static", exist_ok=True)

# Mount static files for frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

class ChatRequest(BaseModel):
    question: str

@app.post("/api/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")
    
    try:
        contents = await file.read()
        rag_pipeline.process_pdf(contents)
        return {"message": f"Successfully processed {file.filename}. You can now ask questions."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

@app.post("/api/chat")
async def chat(request: ChatRequest):
    if not rag_pipeline.vector_store:
        raise HTTPException(status_code=400, detail="No document uploaded. Please upload a PDF first.")
    
    try:
        answer = rag_pipeline.ask_question(request.question)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating answer: {str(e)}")

@app.get("/")
async def root():
    # Return the index.html directly
    return FileResponse("static/index.html")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
