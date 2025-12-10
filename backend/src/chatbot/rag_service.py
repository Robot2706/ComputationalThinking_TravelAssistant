# import os

# from dotenv import load_dotenv

# # LangChain Imports
# from langchain_community.document_loaders import DirectoryLoader, TextLoader
# from langchain_text_splitters import RecursiveCharacterTextSplitter
# from langchain_community.embeddings import HuggingFaceEmbeddings
# from langchain_chroma import Chroma
# from langchain_openai import ChatOpenAI, OpenAIEmbeddings
# from langchain_classic.memory import ConversationBufferWindowMemory
# from langchain_classic.chains import ConversationalRetrievalChain

# # Tool Imports (cho Pushover, nếu muốn tái sử dụng logic ghi lại câu hỏi)
# import requests

# # --- XỬ LÝ ĐƯỜNG DẪN (QUAN TRỌNG) ---
# # Lấy đường dẫn của file rag_service.py hiện tại
# current_dir = os.path.dirname(os.path.abspath(__file__))

# # Trỏ đến file .env nằm cùng thư mục với rag_service.py
# env_path = os.path.join(current_dir, ".env")
# load_dotenv(env_path)

# # Trỏ đến thư mục data và vector_db nằm trong thư mục chatbot
# DATA_PATH = os.path.join(current_dir, "data")
# DB_PATH = os.path.join(current_dir, "vector_db")

# class HotelChatbot:
#     def __init__(self):
#         print(f"--- Đang khởi tạo Chatbot ---")
#         print(f"--- Đọc dữ liệu từ: {DATA_PATH}")
        
#         self.model_name = "gpt-4o-mini"
        
#         # 1. Embeddings (Giống notebook của bạn)
#         self.embeddings = OpenAIEmbeddings()
#         #self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        
#         # 2. LLM
#         self.llm = ChatOpenAI(temperature=0.7, model_name=self.model_name)
        
#         # 3. Vector DB
#         self.vector_db = self._initialize_vector_db()
        
#         # 4. Memory & Chain
#         self.memory = ConversationBufferWindowMemory(
#             memory_key='chat_history', 
#             return_messages=True, 
#             k=5
#         )
        
#         self.qa_chain = ConversationalRetrievalChain.from_llm(
#             llm=self.llm,
#             retriever=self.vector_db.as_retriever(search_kwargs={"k": 5}),
#             memory=self.memory
#         )

#     def _initialize_vector_db(self):
#         # Kiểm tra xem folder vector_db đã có dữ liệu chưa
#         if os.path.exists(DB_PATH) and os.listdir(DB_PATH):
#             print("--- Tìm thấy Vector DB cũ, đang tải lên... ---")
#             return Chroma(persist_directory=DB_PATH, embedding_function=self.embeddings)
#         else:
#             print("--- Chưa có Vector DB, đang tạo mới từ file .md... ---")
#             return self._create_new_db()

#     def _create_new_db(self):
#         if not os.path.exists(DATA_PATH):
#             raise FileNotFoundError(f"Không tìm thấy thư mục data tại: {DATA_PATH}")

#         # Load file .md
#         loader = DirectoryLoader(DATA_PATH, glob="*.md", loader_cls=TextLoader, loader_kwargs={'autodetect_encoding': True})
#         documents = loader.load()
        
#         if not documents:
#             raise ValueError("Không tìm thấy file .md nào trong thư mục data!")

#         # Cắt nhỏ văn bản
#         text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
#         chunks = text_splitter.split_documents(documents)
        
#         # Tạo và lưu Vector Store
#         vector_db = Chroma.from_documents(
#             documents=chunks,
#             embedding=self.embeddings,
#             persist_directory=DB_PATH
#         )
#         print(f"--- Đã tạo DB thành công với {len(chunks)} chunks ---")
#         return vector_db

#     def chat(self, question: str):
#         try:
#             result = self.qa_chain.invoke({"question": question})
#             return result["answer"]
#         except Exception as e:
#             return f"Lỗi xử lý AI: {str(e)}"

import os
import json

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_classic.memory import ConversationBufferWindowMemory
from langchain_classic.chains import ConversationalRetrievalChain
from langchain_classic.prompts import PromptTemplate

# --- ĐƯỜNG DẪN ---
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, ".env")
load_dotenv(env_path)

DATA_PATH = os.path.join(current_dir, "data")
DB_PATH = os.path.join(current_dir, "vector_db")

# ✅ 2 NGUỒN DATA
HOTELS_JSON_PATH = os.path.join(current_dir, "..", "..", "data", "processed", "hotels_parsed.json")
TRAINING_MD_PATH = os.path.join(current_dir, "data", "hotels_enhanced.md")


class HotelChatbot:
    def __init__(self):
        print(f"--- Đang khởi tạo Chatbot ---")
        
        self.model_name = "gpt-4o-mini"
        self.embeddings = OpenAIEmbeddings()
        
        self.llm = ChatOpenAI(
            temperature=0.8,
            model_name=self.model_name,
            max_tokens=1500
        )
        
        self.vector_db = self._initialize_vector_db()
        
        self.memory = ConversationBufferWindowMemory(
            memory_key='chat_history', 
            return_messages=True, 
            k=10,
            output_key='answer'
        )
        
        self.qa_prompt = self._create_qa_prompt()
        
        self.qa_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.vector_db.as_retriever(
                search_type="mmr",
                search_kwargs={"k": 10, "fetch_k": 30}
            ),
            memory=self.memory,
            return_source_documents=True,
            combine_docs_chain_kwargs={"prompt": self.qa_prompt}
        )

    def _create_qa_prompt(self):
        template = """Bạn là Trợ lý AI thông minh tên Touriri của 2rism.

🧠 **QUY TRÌNH SUY NGHĨ (THỰC HIỆN BƯỚC NÀY TRONG ĐẦU):**
Trước khi trả lời, hãy xác định **Ý ĐỊNH (INTENT)** của người dùng:

1.  **TRƯỜNG HỢP 1: CHÀO HỎI / XÃ GIAO (Greetings/Chit-chat)**
    - Keywords: "Chào", "Hi", "Hello", "Alo", "Bạn tên gì", "Cảm ơn".
    - HÀNH ĐỘNG: Trả lời thân thiện, ngắn gọn và gợi ý ngay khả năng của bạn.
    - *Ví dụ:* "Chào bạn! Mình là Touriri - trợ lý ảo của 2rism. Bạn đang cần tìm khách sạn ở khu vực nào (VD: Quận 1, Quận 3...)?"

2.  **TRƯỜNG HỢP 2: CÓ NHU CẦU TÌM PHÒNG (Booking Intent)**
    - Keywords: "Tìm phòng", "Khách sạn", "Du lịch", "Ở đâu rẻ", hoặc người dùng đưa ra tiêu chí cụ thể.
    - HÀNH ĐỘNG: Áp dụng quy tắc "GỢI Ý NGAY" bên dưới.

---

⚠️ **QUY TẮC CHO TRƯỜNG HỢP 2 (KHI ĐÃ XÁC ĐỊNH LÀ TÌM PHÒNG):**
1.  **TỰ ĐỘNG ĐIỀN THÔNG TIN THIẾU:**
    - Thiếu khu vực? -> Ưu tiên **Quận 1, Quận 3**.
    - Thiếu ngân sách? -> Đề xuất mix (1 Rẻ + 1 Sang).
2.  **KHÔNG HỎI LẠI:** Trừ khi context hoàn toàn rỗng.

---
DỮ LIỆU TỪ HỆ THỐNG (CONTEXT):
{context}

LỊCH SỬ CHAT:
{chat_history}

CÂU HỎI CỦA KHÁCH:
{question}
---

HÃY TRẢ LỜI:
- Nếu là chào hỏi: Chào lại thân thiện + Gợi ý khách nhập địa điểm/nhu cầu.
- Nếu là tìm phòng: Trả lời theo format gợi ý khách sạn (Icon 🎯).
"""
        return PromptTemplate(
        template=template,
        input_variables=["context", "chat_history", "question"]
        )
    def _initialize_vector_db(self):
        if os.path.exists(DB_PATH) and os.listdir(DB_PATH):
            print("--- Tìm thấy Vector DB ---")
            return Chroma(persist_directory=DB_PATH, embedding_function=self.embeddings)
        else:
            print("--- Tạo Vector DB mới ---")
            return self._create_new_db()

    def _create_new_db(self):
        """
        ✅ QUAN TRỌNG: Load CẢ HAI nguồn data
        1. Training/Instructions từ .md
        2. Actual hotels data từ JSON
        """
        all_documents = []
        
        # ✅ PART 1: Load training instructions từ .md
        if os.path.exists(TRAINING_MD_PATH):
            print(f"--- Đang load training data từ: {TRAINING_MD_PATH} ---")
            try:
                loader = TextLoader(TRAINING_MD_PATH, encoding='utf-8')
                training_docs = loader.load()
                
                # Add metadata để phân biệt
                for doc in training_docs:
                    doc.metadata['source_type'] = 'training_instructions'
                    doc.metadata['priority'] = 'high'  # ✅ Đánh dấu ưu tiên cao
                
                all_documents.extend(training_docs)
                print(f"--- ✅ Đã load {len(training_docs)} training documents ---")
            except Exception as e:
                print(f"--- ⚠️ Không load được training file: {e} ---")
        else:
            print(f"--- ⚠️ Không tìm thấy training file: {TRAINING_MD_PATH} ---")
        
        # ✅ PART 2: Load actual hotels data từ JSON
        if os.path.exists(HOTELS_JSON_PATH):
            print(f"--- Đang load hotels data từ: {HOTELS_JSON_PATH} ---")
            
            with open(HOTELS_JSON_PATH, 'r', encoding='utf-8') as f:
                hotels_data = json.load(f)
            
            print(f"--- Đã load {len(hotels_data)} khách sạn từ JSON ---")
            
            # Convert JSON to documents
            hotels_docs = self._convert_json_to_documents(hotels_data)
            all_documents.extend(hotels_docs)
        else:
            raise FileNotFoundError(f"Không tìm thấy: {HOTELS_JSON_PATH}")
        
        print(f"--- Tổng cộng: {len(all_documents)} documents ---")
        
        # ✅ Chunking
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=250,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        chunks = text_splitter.split_documents(all_documents)
        
        print(f"--- Đã tạo {len(chunks)} chunks ---")
        
        # ✅ Create Vector DB
        vector_db = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=DB_PATH
        )
        
        print("--- ✅ Vector DB hoàn tất ---")
        return vector_db

    def _convert_json_to_documents(self, hotels_data):
        """Convert JSON hotels to Documents"""
        documents = []
        
        for hotel in hotels_data:
            if not hotel or not isinstance(hotel, dict):
                continue
            
            hotel_id = hotel.get('id', 'N/A')
            name = hotel.get('name', 'Unknown')
            district = hotel.get('district', 'N/A')
            address = hotel.get('address', 'N/A')
            price = hotel.get('price', 0)
            rating = hotel.get('rating', 0)
            stars = hotel.get('stars', 0)
            reviews_count = hotel.get('reviews_count', 0)
            details = hotel.get('details', '')
            amenities = hotel.get('amenities', [])
            
            # Format content
            page_content = f"""
=== KHÁCH SẠN: {name} ===

📌 THÔNG TIN CƠ BẢN:
- Mã số: {hotel_id}
- Phân loại: {stars} sao
- Địa chỉ: {address}
- Khu vực: {district}

💰 GIÁ & ĐÁNH GIÁ:
- Giá: {price:,.0f} VND/đêm
- Rating: {rating}/10 ({reviews_count} reviews)

🏨 MÔ TẢ:
{details}

✨ TIỆN NGHI:
{', '.join(amenities) if amenities else 'Không có thông tin'}
"""
            
            # Metadata
            metadata = {
                'hotel_id': str(hotel_id),
                'name': name,
                'district': district,
                'price': float(price),
                'rating': float(rating),
                'stars': int(stars),
                'reviews_count': int(reviews_count),
                'source_type': 'hotel_data',  # ✅ Phân biệt với training
                'priority': 'normal'  # ✅ Priority thấp hơn training
            }
            
            documents.append(Document(
                page_content=page_content.strip(),
                metadata=metadata
            ))
        
        print(f"--- ✅ Đã convert {len(documents)} hotels ---")
        return documents

    def chat(self, question: str):
        try:
            result = self.qa_chain.invoke({"question": question})
            answer = result["answer"]
            
            # ✅ Kiểm tra nếu bot hỏi quá nhiều
            if answer.count("?") > 3:  # Nếu có > 3 dấu hỏi
                return ("Để gợi ý nhanh hơn, bạn chỉ cần cho tôi biết:\n"
                    "1️⃣ Ngân sách (VD: dưới 1 triệu, 2-3 triệu...)\n"
                    "2️⃣ Khu vực ưa thích (VD: Quận 1, Quận 7...)\n\n"
                    "Hoặc tôi có thể gợi ý ngay các khách sạn phổ biến nhất!")
            
            return answer
        except Exception as e:
            return f"❌ Lỗi: {str(e)}"


    def rebuild_vector_db():
        """Force rebuild Vector DB"""
        import shutil
        
        if os.path.exists(DB_PATH):
            print(f"--- Xóa Vector DB cũ ---")
            shutil.rmtree(DB_PATH)
        
        chatbot = HotelChatbot()
        print("--- ✅ Rebuild hoàn tất ---")
        return chatbot


    if __name__ == "__main__":
        print("=== Testing Chatbot với câu hỏi thiếu thông tin ===\n")
        
        # Rebuild để apply prompt mới
        chatbot = rebuild_vector_db()
        
        # Test cases
        tests = [
            "Tôi muốn tìm khách sạn rẻ nhất ở TP HCM",
            "Khách sạn nào tốt?",
            "Tôi có 2 triệu, gợi ý khách sạn",
            "Tìm khách sạn ở Quận 1",
        ]
        
        for i, question in enumerate(tests, 1):
            print(f"\n{'='*70}")
            print(f"Test {i}: {question}")
            print(f"{'='*70}")
            response = chatbot.chat(question)
            print(f"\n{response}\n")