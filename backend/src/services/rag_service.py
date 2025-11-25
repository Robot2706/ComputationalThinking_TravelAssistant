import os
import re
import glob
import time
import functools
import json
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# LangChain Imports
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI
from langchain_classic.memory import ConversationBufferWindowMemory
from langchain_classic.chains import ConversationalRetrievalChain

# Tool Imports (cho Pushover, nếu muốn tái sử dụng logic ghi lại câu hỏi)
import requests

# Load environment variables (để lấy OPENAI_API_KEY)
load_dotenv()
os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')

# =========================================================================
# I. CẤU HÌNH VÀ HẰNG SỐ
# =========================================================================

MODEL = "gpt-4o-mini"
DB_NAME = "vector_db_hotel_rag" # Đặt tên khác để tránh xung đột
# Cập nhật đường dẫn này cho môi trường của bạn
KNOWLEDGE_BASE_DIR = "D:/HCMUS/Year 2/TDTT/ComputationalThinking_TravelAssistant/backend/data/raw" 
HOTELS_PATH = os.path.join(KNOWLEDGE_BASE_DIR, "hotels_list.md")

# System Message
SYSTEM_MESSAGE = (
    "Bạn là một Trợ lý Thông tin Khách sạn AI (Hotel Info Assistant) chuyên nghiệp của website du lịch. "
    "Nhiệm vụ của bạn là cung cấp thông tin chi tiết và chính xác về các khách sạn/chỗ ở mà người dùng quan tâm. "
    "Bạn sẽ trả lời các câu hỏi về tiện nghi, dịch vụ, quy tắc của khách sạn. "
    "Các câu trả lời phải **ngắn gọn, tập trung vào dữ liệu đã được cung cấp**. "
    "**QUAN TRỌNG:** Nếu thông tin cụ thể không có sẵn trong dữ liệu của bạn, hãy nói rõ ràng: 'Tôi xin lỗi, thông tin này không có sẵn trong cơ sở dữ liệu hiện tại của tôi. Vui lòng liên hệ trực tiếp với khách sạn để biết chi tiết chính xác nhất.' "
    "Tuyệt đối không bịa ra thông tin không có cơ sở."
)

# Pushover Configuration (cho Tool Use)
PUSHOVER_USER = os.getenv("PUSHOVER_USER")
PUSHOVER_TOKEN = os.getenv("PUSHOVER_TOKEN")
PUSHOVER_URL = "https://api.pushover.net/1/messages.json"

# =========================================================================
# II. CÁC HÀM XỬ LÝ (TOOLS)
# =========================================================================

def push(message: str):
    """Gửi thông báo qua Pushover (Mocked if credentials not available)"""
    if not PUSHOVER_USER or not PUSHOVER_TOKEN:
        print(f"[MOCK PUSH] Recording question: {message}")
        return {"status": "mocked_ok"}
        
    payload = {"user": PUSHOVER_USER, "token": PUSHOVER_TOKEN, "message": message}
    try:
        requests.post(PUSHOVER_URL, data=payload)
        return {"status": "ok"}
    except Exception as e:
        print(f"[PUSH ERROR] Failed to send notification: {e}")
        return {"status": "error"}

def record_unknown_question(question: str):
    """Ghi lại câu hỏi mà RAG không trả lời được."""
    push(f"Recording unknown question asked: '{question}'")
    return {"recorded": "ok"}

# =========================================================================
# III. RAG SERVICE CLASS
# =========================================================================

class RAGService:
    _instance = None # Singleton pattern
    
    def __new__(cls):
        """Đảm bảo chỉ có một thể hiện (instance) của RAGService"""
        if cls._instance is None:
            cls._instance = super(RAGService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        print("Initializing RAG Service...")
        self.context_dict = self._load_context_from_md() # Dùng hàm load context từ notebook
        self.embeddings = self._init_embeddings()
        self.vectorstore = self._init_vectorstore()
        self.llm = self._init_llm()
        self.memory = ConversationBufferWindowMemory(memory_key='chat_history', return_messages=True)
        self.conversation_chain = self._init_conversation_chain()
        self._initialized = True
        print("RAG Service initialized successfully.")

    @functools.lru_cache(maxsize=None)
    def _load_context_from_md(self):
        """Tải và phân đoạn context từ hotels_list.md theo tiêu đề."""
        context = {}
        try:
            with open(HOTELS_PATH, "r", encoding="utf-8") as f:
                text = f.read()
        except Exception as e:
            print(f"Error reading {HOTELS_PATH}: {e}")
            return context

        # Logic phân đoạn bằng Regex dựa trên tiêu đề (1. Hotel Name)
        matches = list(re.finditer(r'^\s*\d+\.\s+(.*)$', text, flags=re.MULTILINE))
        
        if not matches:
            context[os.path.basename(HOTELS_PATH)] = text.strip()
            return context

        for i, m in enumerate(matches):
            title = m.group(1).strip()
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            body = text[start:end].strip()

            key = title
            context[key] = f"{title}\n\n{body}" # Chứa Title + Body

        return context
        
    def _init_embeddings(self):
        """Khởi tạo Embedding Function (HuggingFace Embeddings như trong Notebook)"""
        # Đây là dòng bạn đã sử dụng trong notebook
        return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    def _init_vectorstore(self):
        """Khởi tạo và lưu/tải Vector Store (Chroma)"""
        
        # 1. Khởi tạo Embedding Function
        embeddings = self._init_embeddings() # Gọi lại hàm init_embeddings
        
        # 2. KIỂM TRA NẾU DATABASE ĐÃ TỒN TẠI (Tối ưu hóa)
        if os.path.exists(DB_NAME) and os.listdir(DB_NAME):
            print(f"Loading existing vectorstore from {DB_NAME}...")
            try:
                # Tải Vector Store đã tồn tại
                vectorstore = Chroma(
                    persist_directory=DB_NAME,
                    embedding_function=embeddings
                )
                if vectorstore._collection.count() > 0:
                    print(f"Vectorstore loaded successfully with {vectorstore._collection.count()} documents.")
                    return vectorstore
                else:
                    # Nếu thư mục tồn tại nhưng không có document nào (lỗi)
                    print("Existing vectorstore is empty. Rebuilding...")
            except Exception as e:
                print(f"Error loading existing vectorstore: {e}. Rebuilding...")

        # 3. NẾU KHÔNG TỒN TẠI HOẶC TẢI THẤT BẠI, CHẠY LẠI LOGIC TẠO DB
        print("Vectorstore not found or empty. Running build process...")
        
        # Tải Documents và chia Chunks (Lấy toàn bộ file .md trong thư mục knowledge-base)
        loader = DirectoryLoader(KNOWLEDGE_BASE_DIR, 
                                 glob="*.md", 
                                 loader_cls=TextLoader, 
                                 loader_kwargs={'autodetect_encoding': True})
        documents = loader.load()
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=100,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        chunks = text_splitter.split_documents(documents)
        print(f"Total chunks created: {len(chunks)}")

        # Tạo Vector Store mới
        vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=DB_NAME
        )
        print(f"New vectorstore created with {vectorstore._collection.count()} documents.")
        return vectorstore

    def _init_llm(self):
        """Khởi tạo LLM"""
        return ChatOpenAI(
            temperature=0.7, 
            model_name=MODEL,
            openai_api_key=os.environ.get('OPENAI_API_KEY')
        )

    def _init_conversation_chain(self):
        """Tạo chuỗi RAG (ConversationalRetrievalChain)"""
        
        # Sử dụng Vector Retriever với k=30 (như trong cell 46 của notebook)
        retriever = self.vectorstore.as_retriever(search_kwargs={"k": 30})
        
        # NOTE: Bạn có thể thêm system_message vào prompt template nếu cần tùy chỉnh
        # Nhưng với ConversationalRetrievalChain, ta chỉ cần truyền retriever và memory
        
        chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=retriever,
            memory=self.memory
        )
        return chain

    def get_rag_response(self, query: str) -> str:
        """Giao diện gọi RAG Chain để xử lý câu hỏi"""
        
        # Bắt đầu với System Message để định hướng LLM
        # Do ConversationalRetrievalChain tự quản lý prompt, ta thêm query trực tiếp
        
        result = self.conversation_chain.invoke({"question": query})
        response_text = result["answer"]
        
        # Logic kiểm tra "I don't know" và gọi Tool (Tùy chọn)
        # Sử dụng Python string check để mô phỏng việc gọi tool
        if "tôi không biết" in response_text.lower() or "không có sẵn" in response_text.lower():
            record_unknown_question(query)
            
        return response_text

# =========================================================================
# IV. KHỞI TẠO DỊCH VỤ TOÀN CỤC
# =========================================================================

# Khởi tạo RAG Service Singleton khi module được import
try:
    RAG_SERVICE = RAGService()
except Exception as e:
    print(f"FATAL: Failed to initialize RAG Service: {e}")
    RAG_SERVICE = None