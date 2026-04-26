import os
from io import BytesIO
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

# Check for API Key
if not os.getenv("GOOGLE_API_KEY"):
    print("WARNING: GOOGLE_API_KEY not found in environment variables. Set it in the .env file.")

class RAGPipeline:
    def __init__(self):
        # We use a fast, local embedding model
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.vector_store = None
        self.llm = ChatGoogleGenerativeAI(model="gemini-flash-latest", temperature=0)

        # Create the prompt template for the RAG chain
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

        self.retrieval_chain = None

    def format_docs(self, docs):
        return "\n\n".join(doc.page_content for doc in docs)

    def process_pdf(self, pdf_file: bytes):
        """Extracts text from PDF, chunks it, and updates the vector store."""
        reader = PdfReader(BytesIO(pdf_file))
        text = ""
        for page in reader.pages:
            if page.extract_text():
                text += page.extract_text() + "\n"
        
        if not text.strip():
            raise ValueError("Could not extract any text from the provided PDF.")

        # Chunk the text
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_text(text)

        # Create or update vector store
        if self.vector_store is None:
            self.vector_store = FAISS.from_texts(chunks, self.embeddings)
        else:
            self.vector_store.add_texts(chunks)

        # Recreate the retrieval chain with the updated vector store
        retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})
        
        self.retrieval_chain = (
            {"context": retriever | self.format_docs, "input": RunnablePassthrough()}
            | self.prompt
            | self.llm
            | StrOutputParser()
        )

    def ask_question(self, question: str) -> str:
        """Answers a question based on the ingested document."""
        if self.retrieval_chain is None:
            return "Please upload a document first before asking questions."
        
        # Invoke the LCEL chain directly with the input string
        response = self.retrieval_chain.invoke(question)
        return response

# Global instance
rag_pipeline = RAGPipeline()