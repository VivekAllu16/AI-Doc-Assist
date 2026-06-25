from datetime import datetime
from uuid import uuid4
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List
from sqlalchemy.orm import Session
import uvicorn
import os

from database import engine, Base, get_db
import models
import auth
from rag import rag_pipeline

UPLOAD_DIR = "uploads"

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Document Assistant")

# Ensure static and upload directories exist
os.makedirs("static", exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Mount static files for frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

# Models
class UserCreate(BaseModel):
    username: str
    password: str

class ChatRequest(BaseModel):
    question: str

class DocumentInfo(BaseModel):
    id: int
    filename: str
    uploaded_at: datetime

    class Config:
        orm_mode = True

@app.post("/api/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = auth.get_password_hash(user.password)
    new_user = models.User(username=user.username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Generate token
    access_token = auth.create_access_token(data={"sub": new_user.username})
    return {"access_token": access_token, "token_type": "bearer", "username": new_user.username}

@app.post("/api/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer", "username": user.username}

@app.post("/api/upload")
async def upload_pdf(
    files: List[UploadFile] = File(...), 
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    pdf_contents = []
    saved_paths = []
    document_records = []
    user_dir = os.path.join(UPLOAD_DIR, str(current_user.id))
    os.makedirs(user_dir, exist_ok=True)

    for file in files:
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail=f"Only PDF files are allowed. ({file.filename} is invalid)")
        
        contents = await file.read()
        pdf_contents.append(contents)

        sanitized_name = os.path.basename(file.filename)
        saved_name = f"{uuid4().hex}_{sanitized_name}"
        save_path = os.path.join(user_dir, saved_name)
        with open(save_path, "wb") as f:
            f.write(contents)
        saved_paths.append(save_path)

        document = models.Document(
            user_id=current_user.id,
            filename=sanitized_name,
            file_path=save_path,
        )
        db.add(document)
        document_records.append(document)

    try:
        # Process PDFs before committing document records so failures do not leave stale DB entries.
        rag_pipeline.process_pdfs(pdf_contents, current_user.id)
        db.commit()
        for doc in document_records:
            db.refresh(doc)

        return {"message": f"Successfully processed {len(files)} document(s). You can now ask questions."}
    except Exception as e:
        db.rollback()
        for saved_path in saved_paths:
            if os.path.exists(saved_path):
                os.remove(saved_path)
        raise HTTPException(status_code=500, detail=f"Error processing PDFs: {str(e)}")

@app.get("/api/history")
def get_chat_history(
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(auth.get_current_user)
):
    chats = db.query(models.ChatHistory).filter(models.ChatHistory.user_id == current_user.id).order_by(models.ChatHistory.timestamp.asc()).all()
    return [{"sender": chat.sender, "message": chat.message} for chat in chats]

@app.get("/api/documents", response_model=List[DocumentInfo])
def list_documents(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    documents = db.query(models.Document).filter(models.Document.user_id == current_user.id).order_by(models.Document.uploaded_at.desc()).all()
    return documents

@app.delete("/api/documents/{document_id}")
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    document = db.query(models.Document).filter(models.Document.id == document_id, models.Document.user_id == current_user.id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if os.path.exists(document.file_path):
        os.remove(document.file_path)

    db.delete(document)
    db.commit()

    remaining_docs = db.query(models.Document).filter(models.Document.user_id == current_user.id).all()
    if remaining_docs:
        pdf_files = []
        for doc in remaining_docs:
            try:
                with open(doc.file_path, "rb") as f:
                    pdf_files.append(f.read())
            except FileNotFoundError:
                continue
        rag_pipeline.rebuild_user_store(current_user.id, pdf_files)
    else:
        rag_pipeline.remove_user_store(current_user.id)

    return {"message": "Document deleted successfully"}

@app.get("/api/me")
def get_current_user_info(
    current_user: models.User = Depends(auth.get_current_user)
):
    return {"username": current_user.username}

@app.post("/api/chat")
async def chat(
    request: ChatRequest, 
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    if not rag_pipeline.has_documents(current_user.id):
        raise HTTPException(status_code=400, detail="No documents uploaded. Please upload PDFs first.")
    
    try:
        # Save user message
        user_msg = models.ChatHistory(user_id=current_user.id, message=request.question, sender="user")
        db.add(user_msg)
        db.commit()

        # Get answer
        answer = rag_pipeline.ask_question(request.question, current_user.id)
        
        # Save bot message
        bot_msg = models.ChatHistory(user_id=current_user.id, message=answer, sender="bot")
        db.add(bot_msg)
        db.commit()

        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating answer: {str(e)}")

@app.get("/")
async def root():
    return FileResponse("static/index.html")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
