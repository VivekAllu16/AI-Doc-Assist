import os
from io import BytesIO
from typing import List
from PyPDF2 import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

load_dotenv()

if not os.getenv("GOOGLE_API_KEY"):
    print("WARNING: GOOGLE_API_KEY not found in environment variables. Set it in the .env file.")

class RAGPipeline:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.llm = ChatGoogleGenerativeAI(model="gemini-flash-latest", temperature=0)
        
        # Maps user_id -> vector_store and user_id -> retrieval_chain
        self.user_vector_stores = {}
        self.user_retrieval_chains = {}

        system_prompt = (
            "You are an AI document assistant. Use the following pieces of retrieved context to answer the question. "
            "If you don't know the answer based on the context, say that you don't know. "
            "Do NOT use external knowledge. Only use the provided context.\n\n"
            "{context}"
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
        ])

    def format_docs(self, docs):
        return "\n\n".join(doc.page_content for doc in docs)

    def process_pdfs(self, pdf_files: List[bytes], user_id: int):
        all_text = ""
        for pdf_bytes in pdf_files:
            reader = PdfReader(BytesIO(pdf_bytes))
            for page in reader.pages:
                if page.extract_text():
                    all_text += page.extract_text() + "\n"
        
        if not all_text.strip():
            raise ValueError("Could not extract any text from the provided PDFs.")

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_text(all_text)

        if user_id not in self.user_vector_stores:
            self.user_vector_stores[user_id] = FAISS.from_texts(chunks, self.embeddings)
        else:
            self.user_vector_stores[user_id].add_texts(chunks)

        retriever = self.user_vector_stores[user_id].as_retriever(search_kwargs={"k": 5})
        
        self.user_retrieval_chains[user_id] = (
            {"context": retriever | self.format_docs, "input": RunnablePassthrough()}
            | self.prompt
            | self.llm
            | StrOutputParser()
        )

    def has_documents(self, user_id: int) -> bool:
        return user_id in self.user_retrieval_chains

    def ask_question(self, question: str, user_id: int) -> str:
        if user_id not in self.user_retrieval_chains:
            return "Please upload a document first before asking questions."
        
        response = self.user_retrieval_chains[user_id].invoke(question)
        return response

rag_pipeline = RAGPipeline()