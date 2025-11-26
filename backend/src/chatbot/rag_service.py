import os

from dotenv import load_dotenv

# LangChain Imports
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_classic.memory import ConversationBufferWindowMemory
from langchain_classic.chains import ConversationalRetrievalChain

# Tool Imports (cho Pushover, nếu muốn tái sử dụng logic ghi lại câu hỏi)
import requests

# --- XỬ LÝ ĐƯỜNG DẪN (QUAN TRỌNG) ---
# Lấy đường dẫn của file rag_service.py hiện tại
current_dir = os.path.dirname(os.path.abspath(__file__))

# Trỏ đến file .env nằm cùng thư mục với rag_service.py
env_path = os.path.join(current_dir, ".env")
load_dotenv(env_path)

# Trỏ đến thư mục data và vector_db nằm trong thư mục chatbot
DATA_PATH = os.path.join(current_dir, "data")
DB_PATH = os.path.join(current_dir, "vector_db")

class HotelChatbot:
    def __init__(self):
        print(f"--- Đang khởi tạo Chatbot ---")
        print(f"--- Đọc dữ liệu từ: {DATA_PATH}")
        
        self.model_name = "gpt-4o-mini"
        
        # 1. Embeddings (Giống notebook của bạn)
        self.embeddings = OpenAIEmbeddings()
        #self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        
        # 2. LLM
        self.llm = ChatOpenAI(temperature=0.7, model_name=self.model_name)
        
        # 3. Vector DB
        self.vector_db = self._initialize_vector_db()
        
        # 4. Memory & Chain
        self.memory = ConversationBufferWindowMemory(
            memory_key='chat_history', 
            return_messages=True, 
            k=5
        )
        
        self.qa_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.vector_db.as_retriever(search_kwargs={"k": 5}),
            memory=self.memory
        )

    def _initialize_vector_db(self):
        # Kiểm tra xem folder vector_db đã có dữ liệu chưa
        if os.path.exists(DB_PATH) and os.listdir(DB_PATH):
            print("--- Tìm thấy Vector DB cũ, đang tải lên... ---")
            return Chroma(persist_directory=DB_PATH, embedding_function=self.embeddings)
        else:
            print("--- Chưa có Vector DB, đang tạo mới từ file .md... ---")
            return self._create_new_db()

    def _create_new_db(self):
        if not os.path.exists(DATA_PATH):
            raise FileNotFoundError(f"Không tìm thấy thư mục data tại: {DATA_PATH}")

        # Load file .md
        loader = DirectoryLoader(DATA_PATH, glob="*.md", loader_cls=TextLoader, loader_kwargs={'autodetect_encoding': True})
        documents = loader.load()
        
        if not documents:
            raise ValueError("Không tìm thấy file .md nào trong thư mục data!")

        # Cắt nhỏ văn bản
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
        chunks = text_splitter.split_documents(documents)
        
        # Tạo và lưu Vector Store
        vector_db = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=DB_PATH
        )
        print(f"--- Đã tạo DB thành công với {len(chunks)} chunks ---")
        return vector_db

    def chat(self, question: str):
        try:
            result = self.qa_chain.invoke({"question": question})
            return result["answer"]
        except Exception as e:
            return f"Lỗi xử lý AI: {str(e)}"