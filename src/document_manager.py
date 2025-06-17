import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Union
from fuzzywuzzy import fuzz
from config import CONFIG

class DocumentManager:
    def __init__(self, documents_file: str, 
                 log_file: str = CONFIG["document_logs_file"], categories_file: str = CONFIG["document_categories_file"]):
        self.documents_file = documents_file
        self.log_file = log_file
        self.categories_file = categories_file
        self.documents = self._load_documents()
        self.logs = self._load_logs()
        self.categories = self._load_categories()

    def _load_documents(self) -> List[Dict]:
        try:
            with open(self.documents_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    def _load_logs(self) -> List[Dict]:
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    def _load_categories(self) -> List[Dict]:
        try:
            with open(self.categories_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # Danh mục mặc định nếu file không tồn tại
            default_categories = []
            self._save_categories(default_categories)
            return default_categories

    def _save_documents(self):
        with open(CONFIG["documents_file"], 'w', encoding='utf-8') as f:
            json.dump(self.documents, f, ensure_ascii=False, indent=4)

    def _save_logs(self):
        with open(CONFIG["document_logs_file"], 'w', encoding='utf-8') as f:
            json.dump(self.logs, f, ensure_ascii=False, indent=4)

    def _save_categories(self, categories: List[Dict]):
        with open(CONFIG["document_categories_file"], 'w', encoding='utf-8') as f:
            json.dump(categories, f, ensure_ascii=False, indent=4)

    def _log_action(self, action: str, doc_id: str, details: str):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "doc_id": doc_id,
            "details": details
        }
        self.logs.append(log_entry)
        self._save_logs()

    def _generate_doc_id(self) -> str:
        return f"TL{str(len(self.documents) + 1).zfill(3)}"

    def _generate_category_id(self) -> str:
        return f"DM{str(len(self.categories) + 1).zfill(3)}"

    def _check_duplicate_doc_id(self, doc_id: str) -> bool:
        return any(doc['doc_id'] == doc_id for doc in self.documents)

    def _check_duplicate_category_name(self, name: str) -> bool:
        return any(cat['name'].upper() == name.upper() for cat in self.categories)

    def _update_status(self, document: Dict):
        """Cập nhật trạng thái tài liệu dựa trên AvailableQuantity."""
        if document['AvailableQuantity'] > 0:
            document['status'] = "available"
        else:
            document['status'] = "unavailable"
            
    def get_all_documents(self) -> List[Dict]:
        """Trả về danh sách tất cả tài liệu chưa bị xóa, có thêm số thứ tự (STT)."""
        active_documents = [doc for doc in self.documents if not doc.get("deleted", False)]
        for idx, doc in enumerate(active_documents, 1):
            doc["stt"] = idx
        return active_documents

    def add_document(self, title: str, category: str, SoLuong: int, DacBiet: bool = False) -> Dict:
        if not title or not category:
            raise ValueError("Tên tài liệu và lĩnh vực không được để trống")
        if SoLuong < 0:
            raise ValueError("Số lượng không được âm")

        doc_id = self._generate_doc_id()
        if self._check_duplicate_doc_id(doc_id):
            raise ValueError("Mã tài liệu đã tồn tại")

        document = {
            "doc_id": doc_id,
            "title": title.upper(),
            "category": category.upper(),
            "SoLuong": SoLuong,
            "DacBiet": DacBiet,
            "status": "available" if SoLuong > 0 else "unavailable",
            "AvailableQuantity": SoLuong
        }
        self.documents.append(document)
        self._save_documents()
        self._log_action("add", doc_id, f"Thêm tài liệu: {title}")
        return document

    def search_documents(self, doc_id: Optional[str] = None, title: Optional[str] = None, 
                        category: Optional[str] = None, min_similarity: int = 80) -> List[Dict]:
        results = []
        for doc in self.documents:
            match = True
            if doc_id and doc_id.lower() not in doc['doc_id'].lower():
                match = False
            if title:
                similarity = fuzz.partial_ratio(title.lower(), doc['title'].lower())
                if similarity < min_similarity:
                    match = False
            if category and category.lower() not in doc['category'].lower():
                match = False
            if match:
                results.append({
                    "stt": len(results) + 1,
                    "doc_id": doc['doc_id'],
                    "title": doc['title'],
                    "category": doc['category'],
                    "SoLuong": doc['SoLuong'],
                    "DacBiet": doc['DacBiet'],
                    "status": doc['status'],
                    "AvailableQuantity": doc['AvailableQuantity']
                })
        return results

    def update_document(self, doc_id: str, updates: Dict) -> bool:
        document = self.get_document_details(doc_id)
        if not document:
            self._log_action("update_document", doc_id, f"Không tìm thấy tài liệu để cập nhật: {doc_id}")
            return False

        if 'doc_id' in updates:
            raise ValueError("Không thể chỉnh sửa mã tài liệu")

        # Kiểm tra nếu tài liệu đang được mượn và có thay đổi số lượng
        if ('SoLuong' in updates or 'AvailableQuantity' in updates) and hasattr(self, 'borrowing_manager'):
            if self.borrowing_manager.is_document_borrowed(doc_id):
                raise ValueError("Tài liệu đang được mượn, không thể cập nhật số lượng!")

        valid_fields = ['title', 'category', 'SoLuong', 'DacBiet', 'AvailableQuantity']
        for key, value in updates.items():
            if key not in valid_fields:
                raise ValueError(f"Trường {key} không hợp lệ")
            if key in ['title', 'category']:
                # Kiểm tra giá trị không chỉ chứa khoảng trắng
                if not value or value.isspace():
                    raise ValueError(f"Trường {key} không được để trống hoặc chỉ chứa khoảng trắng")
                # Kiểm tra độ dài tối đa cho title (ví dụ: 200 ký tự)
                if key == 'title' and len(value) > 200:
                    raise ValueError("Tiêu đề không được dài quá 200 ký tự")
            if key in ['SoLuong', 'AvailableQuantity'] and value < 0:
                raise ValueError("Số lượng không được âm")

            if key == 'SoLuong':
                document[key] = value
                if 'AvailableQuantity' not in updates:
                    document['AvailableQuantity'] = value
            elif key == 'AvailableQuantity':
                document[key] = value
            elif key == 'title':
                # Giữ nguyên định dạng tự nhiên của tiêu đề
                document[key] = value.strip()
            elif key == 'category':
                # Chuẩn hóa category thành chữ hoa
                document[key] = value.upper().strip()
            else:
                document[key] = value

        # Cập nhật trạng thái dựa trên AvailableQuantity
        self._update_status(document)

        # Ghi log chi tiết các thay đổi
        changes = ", ".join(f"{key}: {value}" for key, value in updates.items())
        self._log_action("update", doc_id, f"Cập nhật tài liệu: {document['title']} - Thay đổi: {changes}")

        self._save_documents()
        return True

    def delete_document(self, doc_id: str) -> bool:
        document = self.get_document_details(doc_id)
        if not document:
            return False

        if document['AvailableQuantity'] < document['SoLuong']:
            raise ValueError("Tài liệu đang được mượn, không thể xóa")

        # Đánh dấu tài liệu là đã xóa
        document['deleted'] = True
        self._save_documents()
        self._log_action("delete", doc_id, f"Xóa tài liệu: {document['title']}")
        return True

    def get_document_stats(self) -> Dict:
        stats = {
            "by_title": {},
            "by_category": {},
            "by_status": {},
            "by_DacBiet": {}
        }
        for doc in self.documents:
            title = doc['title']
            category = doc['category']
            status = doc['status']
            DacBiet = doc['DacBiet']
            stats['by_title'][title] = stats['by_title'].get(title, 0) + doc['SoLuong']
            stats['by_category'][category] = stats['by_category'].get(category, 0) + doc['SoLuong']
            stats['by_status'][status] = stats['by_status'].get(status, 0) + doc['SoLuong']
            stats['by_DacBiet'][str(DacBiet)] = stats['by_DacBiet'].get(str(DacBiet), 0) + doc['SoLuong']
        return stats

    def get_borrowed_documents_stats(self, readers: List[Dict]) -> Dict:
        stats = {
            "by_title": {},
            "by_category": {}
        }
        doc_dict = {doc['doc_id']: doc for doc in self.documents}
        for reader in readers:
            for record in reader.get('borrow_history', []):
                if record['status'] == 'borrowed':
                    doc_id = record['book_id']
                    doc = doc_dict.get(doc_id)
                    if doc:
                        title = doc['title']
                        category = doc['category']
                        stats['by_title'][title] = stats['by_title'].get(title, 0) + 1
                        stats['by_category'][category] = stats['by_category'].get(category, 0) + 1
        return stats

    def borrow_document(self, doc_id: str) -> bool:
        document = self.get_document_details(doc_id)
        if not document:
            return False
        if document['status'] != "available":
            raise ValueError(f"Tài liệu {doc_id} hiện không có sẵn để mượn")
        if document['AvailableQuantity'] <= 0:
            raise ValueError(f"Tài liệu {doc_id} không còn bản sao nào để mượn")

        document['AvailableQuantity'] -= 1
        self._update_status(document)
        self._save_documents()
        return True

    def return_document(self, doc_id: str) -> bool:
        document = self.get_document_details(doc_id)
        if not document:
            return False
        if document['AvailableQuantity'] >= document['SoLuong']:
            raise ValueError(f"Tài liệu {doc_id} đã đạt số lượng tối đa")

        document['AvailableQuantity'] += 1
        self._update_status(document)
        self._save_documents()
        return True
    
    def import_documents_from_json(self, file_path: str) -> Dict[str, Union[int, List[str]]]:
        """
        Nhập tài liệu hàng loạt từ file JSON
        Trả về dict với số lượng thành công, thất bại và danh sách lỗi
        """
        result = {
            "success": 0,
            "failed": 0,
            "errors": []
        }

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                documents_to_import = json.load(f)
        except Exception as e:
            result["failed"] += 1
            result["errors"].append(f"Lỗi đọc file: {str(e)}")
            return result

        if not isinstance(documents_to_import, list):
            result["failed"] += 1
            result["errors"].append("Dữ liệu không hợp lệ: phải là mảng các tài liệu")
            return result

        for doc in documents_to_import:
            try:
                # Kiểm tra các trường bắt buộc
                required_fields = ['title', 'category', 'SoLuong']
                for field in required_fields:
                    if field not in doc:
                        raise ValueError(f"Thiếu trường bắt buộc: {field}")

                # Kiểm tra trùng doc_id nếu có
                if 'doc_id' in doc and self._check_duplicate_doc_id(doc['doc_id']):
                    raise ValueError(f"doc_id '{doc['doc_id']}' đã tồn tại")

                # Tạo doc_id mới nếu không có
                if 'doc_id' not in doc:
                    doc['doc_id'] = self._generate_doc_id()

                # Chuẩn hóa dữ liệu
                doc['title'] = doc['title'].upper()
                doc['category'] = doc['category'].upper()
                doc['DacBiet'] = doc.get('DacBiet', False)
                doc['AvailableQuantity'] = doc['SoLuong']
                doc['status'] = "available" if doc['SoLuong'] > 0 else "unavailable"

                self.documents.append(doc)
                result["success"] += 1
                self._log_action("import", doc['doc_id'], f"Nhập tài liệu từ file: {doc['title']}")

            except Exception as e:
                result["failed"] += 1
                result["errors"].append(f"Lỗi với tài liệu {doc.get('title', 'Không rõ')}: {str(e)}")

        if result["success"] > 0:
            self._save_documents()

        return result

    def add_category(self, name: str, description: str = "") -> Dict:
        """
        Thêm danh mục mới
        """
        if not name:
            raise ValueError("Tên danh mục không được để trống")

        if self._check_duplicate_category_name(name):
            raise ValueError(f"Danh mục '{name}' đã tồn tại")

        category = {
            "category_id": self._generate_category_id(),
            "name": name.upper(),
            "description": description
        }

        self.categories.append(category)
        self._save_categories(self.categories)
        self._log_action("add_category", "", f"Thêm danh mục: {name}")
        return category

    def update_category(self, category_id: str, updates: Dict) -> bool:
        """
        Cập nhật thông tin danh mục
        """
        category = next((cat for cat in self.categories if cat['category_id'] == category_id), None)
        if not category:
            return False

        if 'name' in updates:
            new_name = updates['name'].upper()
            if new_name != category['name'] and self._check_duplicate_category_name(new_name):
                raise ValueError(f"Danh mục '{new_name}' đã tồn tại")
            category['name'] = new_name

        if 'description' in updates:
            category['description'] = updates['description']

        self._save_categories(self.categories)
        self._log_action("update_category", "", f"Cập nhật danh mục: {category['name']}")
        return True

    def delete_category(self, category_id: str) -> bool:
        """
        Xóa danh mục
        """
        category = next((cat for cat in self.categories if cat['category_id'] == category_id), None)
        if not category:
            return False

        # Kiểm tra xem danh mục có đang được sử dụng không
        if any(doc['category'] == category['name'] for doc in self.documents):
            raise ValueError("Không thể xóa danh mục đang có tài liệu")

        self.categories = [cat for cat in self.categories if cat['category_id'] != category_id]
        self._save_categories(self.categories)
        self._log_action("delete_category", "", f"Xóa danh mục: {category['name']}")
        return True

    def get_all_categories(self) -> List[Dict]:
        """
        Lấy danh sách tất cả danh mục
        """
        return self.categories

    def restore_document(self, doc_id: str) -> bool:
        document = self.get_document_details(doc_id, include_deleted=True)
        if not document:
            raise ValueError("Tài liệu không tồn tại!")
    
        if not document.get('deleted', False):
            raise ValueError("Tài liệu chưa bị xóa, không cần khôi phục!")
    
        document['deleted'] = False
        self._update_status(document)  # Cập nhật trạng thái tài liệu
        self._save_documents()
        self._log_action("restore", doc_id, f"Khôi phục tài liệu: {document['title']}")
        return True
    def get_document_details(self, doc_id: str, include_deleted: bool = False) -> Optional[Dict]:
        doc = next((doc for doc in self.documents if doc['doc_id'] == doc_id), None)
        if not doc:
            self._log_action("get_document_details", doc_id, f"Không tìm thấy tài liệu với doc_id: {doc_id}")
            return None
        if doc.get('deleted', False) and not include_deleted:
            self._log_action("get_document_details", doc_id, f"Tài liệu {doc_id} đã bị xóa, không thể truy cập")
            return None
        return doc
