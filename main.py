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

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Document Assistant")

# Ensure static directory exists
os.makedirs("static", exist_ok=True)

# Mount static files for frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

# Models
class UserCreate(BaseModel):
    username: str
    password: str

class ChatRequest(BaseModel):
    question: str

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
    current_user: models.User = Depends(auth.get_current_user)
):
    pdf_contents = []
    file_names = []
    
    for file in files:
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail=f"Only PDF files are allowed. ({file.filename} is invalid)")
        
        contents = await file.read()
        pdf_contents.append(contents)
        file_names.append(file.filename)
    
    try:
        rag_pipeline.process_pdfs(pdf_contents, current_user.id)
        return {"message": f"Successfully processed {len(files)} document(s). You can now ask questions."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDFs: {str(e)}")

@app.get("/api/history")
def get_chat_history(
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(auth.get_current_user)
):
    chats = db.query(models.ChatHistory).filter(models.ChatHistory.user_id == current_user.id).order_by(models.ChatHistory.timestamp.asc()).all()
    return [{"sender": chat.sender, "message": chat.message} for chat in chats]

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
