# AI Document Assistant

A FastAPI-based document assistant application that uses Retrieval Augmented Generation (RAG) to answer questions about uploaded documents.

## Features

- **User Authentication**: Secure JWT-based registration and login
- **Document Upload**: Upload PDF documents for processing
- **RAG Pipeline**: AI-powered Q&A using your uploaded documents
- **Vector Storage**: FAISS-based vector store for efficient document retrieval
- **RESTful API**: FastAPI backend with clean API endpoints

## Tech Stack

- **Backend**: FastAPI
- **Database**: SQLite with SQLAlchemy
- **Authentication**: JWT (Python JOSE + bcrypt)
- **AI/ML**: 
  - LangChain for RAG pipeline
  - HuggingFace Embeddings (all-MiniLM-L6-v2)
  - Google Gemini API for LLM
- **Frontend**: HTML/CSS/JavaScript (static files)

## Project Structure

```
├── auth.py          # Authentication utilities (JWT, password hashing)
├── database.py      # Database configuration and session management
├── main.py          # FastAPI application and API endpoints
├── models.py        # SQLAlchemy database models
├── rag.py           # RAG pipeline implementation
├── static/
│   ├── app.js      # Frontend JavaScript
│   ├── index.html  # Frontend HTML
│   └── styles.css # Frontend styles
└── README.md       # This file
```

## Prerequisites

- Python 3.8+
- Google API Key (for Gemini LLM)

## Installation

1. **Clone the repository**

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   
   Create a `.env` file in the project root:
   ```env
   GOOGLE_API_KEY=your_google_api_key_here
   JWT_SECRET_KEY=your_secret_key_here
   ```

5. **Run the application**
   ```bash
   python main.py
   ```

6. **Access the app**
   
   Open your browser and navigate to: `http://localhost:8000`

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/register` | Register a new user |
| POST | `/api/login` | Login and get JWT token |
| POST | `/api/upload` | Upload a PDF document |
| POST | `/api/chat` | Ask questions about documents |
| GET | `/api/documents` | List user's uploaded documents |
| DELETE | `/api/documents/{id}` | Delete a document |

## Usage

1. **Register**: Create an account via the web interface or API
2. **Login**: Authenticate to get access to document features
3. **Upload**: Upload PDF documents you want to query
4. **Chat**: Ask questions about your uploaded documents

## License

MIT License