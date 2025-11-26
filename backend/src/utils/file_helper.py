import json
import os
from pathlib import Path

def get_project_root() -> Path:
    """Trả về đường dẫn gốc của dự án (thư mục backend)"""
    # Lấy đường dẫn file này, đi ngược ra 3 cấp: utils -> src -> backend
    return Path(__file__).parent.parent.parent

def load_json(file_path: str):
    """Đọc file JSON an toàn với encoding utf-8"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: File not found at {file_path}")
        return []
    except json.JSONDecodeError:
        print(f"❌ Error: Failed to decode JSON from {file_path}")
        return []

def save_json(data, file_path: str):
    """Lưu data xuống file JSON"""
    try:
        # Tạo folder nếu chưa tồn tại
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"✅ Saved data to {file_path}")
    except Exception as e:
        print(f"❌ Error saving file: {e}")