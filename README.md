# AI Document Assistant

AI Document Assistant is a FastAPI-based document question-answering application that uses retrieval-augmented generation (RAG) to answer questions from uploaded PDF documents.

## Features

- User authentication with JWT-based registration and login
- PDF upload and document management
- Document-aware Q&A with an AI-powered RAG pipeline
- FAISS vector store for fast retrieval
- Static HTML/CSS/JS frontend with a chat interface
- User-specific document and chat history handling

## Tech Stack

- Backend: FastAPI
- Database: SQLite with SQLAlchemy
- Authentication: JWT using `python-jose` and `bcrypt`
- AI/RAG: LangChain, HuggingFace embeddings, Google Gemini LLM
- Vector store: FAISS
- Frontend: Static HTML, CSS, JavaScript

## Project Structure

```
├── auth.py          # Authentication utilities (JWT, password hashing)
├── database.py      # Database configuration and session management
├── main.py          # FastAPI application and API endpoints
├── models.py        # SQLAlchemy models for users, documents, and chat history
├── rag.py           # RAG pipeline and document embedding logic
├── requirements.txt # Python dependency list
├── README.md        # Project documentation
├── .env.example     # Example environment variables
└── static/          # Frontend assets
    ├── app.js       # Frontend JavaScript
    ├── index.html  # Frontend HTML
    └── styles.css  # Frontend styles
```

## Prerequisites

- Python 3.8 or newer
- Google API key for Gemini

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/VivekAllu16/AI-Doc-Assist.git
   cd AI-Doc-Assist
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root:
   ```env
   GOOGLE_API_KEY=your_google_api_key_here
   JWT_SECRET_KEY=your_secret_key_here
   ```

5. Run the application:
   ```bash
   python main.py
   ```

6. Open the app in your browser:
   ```text
   http://localhost:8000
   ```

## Environment Variables

- `GOOGLE_API_KEY` — required for Google Gemini API access
- `JWT_SECRET_KEY` — secret used to sign authentication tokens

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/register` | Register a new user |
| POST | `/api/login` | Login and receive a JWT token |
| POST | `/api/upload` | Upload PDF documents |
| POST | `/api/chat` | Ask a question about uploaded documents |
| GET | `/api/documents` | List uploaded documents for the current user |
| DELETE | `/api/documents/{id}` | Delete a document by ID |
| GET | `/api/history` | Retrieve chat history for the current user |
| GET | `/api/me` | Get current authenticated user info |

## Usage

1. Register a user from the web UI
2. Log in to obtain a session
3. Upload one or more PDF documents
4. Ask document-based questions in the chat interface
5. Delete documents as needed to refresh the knowledge base

## Notes

- Uploaded PDFs are stored in `uploads/<user_id>/`
- Documents are processed into embeddings and stored in-memory via FAISS
- The app includes retry handling for temporary Gemini service unavailability

## License

MIT License
