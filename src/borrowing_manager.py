import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from reader_manager import ReaderManager
from document_manager import DocumentManager
from config import CONFIG

class BorrowingManager:
    def __init__(self, reader_manager: ReaderManager, doc_manager: DocumentManager, 
                 borrow_file: str = CONFIG["borrow_file"], 
                 return_file: str = CONFIG["return_file"], 
                 log_file: str = CONFIG["borrowing_logs_file"]):
                #  reservation_file: str = "reservation_records.json"):
        self.reader_manager = reader_manager
        self.doc_manager = doc_manager
        self.borrow_file = borrow_file
        self.return_file = return_file
        self.log_file = log_file
        # self.reservation_file = reservation_file
        self.borrow_records = self._load_borrow_records()
        self.return_records = self._load_return_records()
        self.logs = self._load_logs()
        # self.reservation_records = self._load_reservation_records()

    def _load_borrow_records(self) -> List[Dict]:
        try:
            with open(self.borrow_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    def _load_return_records(self) -> List[Dict]:
        try:
            with open(self.return_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    def _load_logs(self) -> List[Dict]:
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    def _save_borrow_records(self):
        with open(CONFIG["borrow_file"], 'w', encoding='utf-8') as f:
            json.dump(self.borrow_records, f, ensure_ascii=False, indent=4)

    def _save_return_records(self):
        with open(CONFIG["return_file"], 'w', encoding='utf-8') as f:
            json.dump(self.return_records, f, ensure_ascii=False, indent=4)

    def _save_logs(self):
        with open(CONFIG["borrowing_logs_file"], 'w', encoding='utf-8') as f:
            json.dump(self.logs, f, ensure_ascii=False, indent=4)

    def _log_action(self, action: str, record_id: str, details: str):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "record_id": record_id,
            "details": details
        }
        self.logs.append(log_entry)
        self._save_logs()

    def _generate_borrow_id(self) -> str:
        return f"BR{str(len(self.borrow_records) + 1).zfill(5)}"

    def _generate_return_id(self) -> str:
        return f"RT{str(len(self.return_records) + 1).zfill(5)}"

    def create_borrow_record(self, reader_id: str, doc_ids: List[str], borrow_date: str, due_date: str) -> Dict:
        reader = self.reader_manager.get_reader_details(reader_id)
        if not reader:
            raise ValueError("Không tìm thấy độc giả")

        if reader['status'] != 'active':
            raise ValueError("Tài khoản không ở trạng thái hoạt động")

        expiry_date = datetime.fromisoformat(reader['expiry_date'])
        if expiry_date < datetime.now():
            raise ValueError("Tài khoản đã hết hạn")

        if not reader['annual_fee_paid']:
            raise ValueError("Phí thường niên chưa được thanh toán")

        max_books = reader.get('max_books', 5)
        if reader['borrowed_books'] + len(doc_ids) > max_books:
            raise ValueError(f"Số lượng tài liệu mượn vượt quá giới hạn ({max_books})")

        documents = []
        for doc_id in doc_ids:
            doc = self.doc_manager.get_document_details(doc_id)
            if not doc:
                raise ValueError(f"Không tìm thấy tài liệu {doc_id}")
            if doc['status'] != 'available':
                raise ValueError(f"Tài liệu {doc_id} hiện không có sẵn để mượn")
            if doc['DacBiet'] and not reader['special_document']:
                raise ValueError(f"Độc giả không có quyền truy cập tài liệu đặc biệt {doc_id}")
            documents.append(doc)

        borrow_id = self._generate_borrow_id()

        for doc_id in doc_ids:
            self.reader_manager.add_borrow_record(reader_id, doc_id, borrow_date, due_date)
            self.doc_manager.borrow_document(doc_id)  # Cập nhật AvailableQuantity và status

        borrow_record = {
            "borrow_id": borrow_id,
            "reader_id": reader_id,
            "borrow_date": borrow_date,
            "due_date": due_date,
            "documents": doc_ids,
            "quantity": len(doc_ids),
            "status": "borrowed"
        }
        self.borrow_records.append(borrow_record)
        self._save_borrow_records()
        self._log_action("create_borrow", borrow_id, f"Lập phiếu mượn cho độc giả {reader_id}")
        return borrow_record

    def search_borrow_records(self, borrow_id: Optional[str] = None, 
                             reader_id: Optional[str] = None) -> List[Dict]:
        results = []
        for record in self.borrow_records:
            match = True
            if borrow_id and borrow_id.lower() not in record['borrow_id'].lower():
                match = False
            if reader_id and reader_id.lower() not in record['reader_id'].lower():
                match = False
            if match:
                results.append({
                    "stt": len(results) + 1,
                    "borrow_id": record['borrow_id'],
                    "reader_id": record['reader_id'],
                    "borrow_date": record['borrow_date'],
                    "due_date": record['due_date'],
                    "quantity": record['quantity'],
                    "status": record['status']
                })
        return results

    def get_overdue_borrow_records(self) -> List[Dict]:
        overdue_records = []
        for record in self.borrow_records:
            if record['status'] == 'borrowed':
                due_date = datetime.fromisoformat(record['due_date'])
                if due_date < datetime.now():
                    overdue_records.append({
                        "stt": len(overdue_records) + 1,
                        "borrow_id": record['borrow_id'],
                        "reader_id": record['reader_id'],
                        "borrow_date": record['borrow_date'],
                        "due_date": record['due_date'],
                        "quantity": record['quantity'],
                        "status": record['status']
                    })
        return overdue_records

    def get_unreturned_borrow_records(self) -> List[Dict]:
        return [{
            "stt": idx + 1,
            "borrow_id": record['borrow_id'],
            "reader_id": record['reader_id'],
            "borrow_date": record['borrow_date'],
            "due_date": record['due_date'],
            "quantity": record['quantity'],
            "status": record['status']
        } for idx, record in enumerate(self.borrow_records) if record['status'] == 'borrowed']

    def get_borrow_record_details(self, borrow_id: str) -> Optional[Dict]:
        return next((record for record in self.borrow_records if record['borrow_id'] == borrow_id), None)

    def delete_borrow_record(self, borrow_id: str) -> bool:
        record = self.get_borrow_record_details(borrow_id)
        if not record:
            return False

        if record['status'] != 'borrowed':
            raise ValueError("Không thể xóa phiếu mượn đã hoàn tất")

        reader = self.reader_manager.get_reader_details(record['reader_id'])
        if not reader:
            raise ValueError("Không tìm thấy độc giả")

        for doc_id in record['documents']:
            for borrow_record in reader['borrow_history']:
                if borrow_record['book_id'] == doc_id and borrow_record['status'] == 'borrowed':
                    borrow_record['status'] = 'cancelled'
                    reader['borrowed_books'] -= 1
                    break
            self.doc_manager.return_document(doc_id)  # Cập nhật AvailableQuantity và status

        self.borrow_records = [r for r in self.borrow_records if r['borrow_id'] != borrow_id]
        self.reader_manager._save_readers()
        self.doc_manager._save_documents()
        self._save_borrow_records()
        self._log_action("delete_borrow", borrow_id, f"Xóa phiếu mượn cho độc giả {record['reader_id']}")
        return True

    def create_return_record(self, reader_id: str, doc_id: str, return_date: str) -> Dict:
        # Tìm phiếu mượn chứa tài liệu này
        borrow_record = None
        for record in self.borrow_records:
            if record['reader_id'] == reader_id and doc_id in record['documents'] and record['status'] == 'borrowed':
                borrow_record = record
                break

        if not borrow_record:
            raise ValueError("Không tìm thấy phiếu mượn hợp lệ cho tài liệu này")

        reader = self.reader_manager.get_reader_details(reader_id)
        if not reader:
            raise ValueError("Không tìm thấy độc giả")

        return_id = self._generate_return_id()
        total_fine = 0

        # Trả từng tài liệu
        result = self.reader_manager.return_book(borrow_record['reader_id'], doc_id, return_date)
        if result['success']:
            self.doc_manager.return_document(doc_id)  # Cập nhật AvailableQuantity và status
            total_fine += result['fine']

        # Cập nhật trạng thái phiếu mượn
        remaining_docs = [d for d in borrow_record['documents'] if d != doc_id]
        if not remaining_docs:
            borrow_record['status'] = 'returned'
        borrow_record['documents'] = remaining_docs
        borrow_record['quantity'] = len(remaining_docs)

        return_record = {
            "return_id": return_id,
            "borrow_id": borrow_record['borrow_id'],
            "reader_id": reader_id,
            "return_date": return_date,
            "documents": [doc_id],
            "total_fine": total_fine
        }
        self.return_records.append(return_record)
        self.reader_manager._save_readers()
        self.doc_manager._save_documents()
        self._save_borrow_records()
        self._save_return_records()
        self._log_action("create_return", return_id, f"Lập phiếu trả cho phiếu mượn {borrow_record['borrow_id']}, Phí phạt: {total_fine} VNĐ")
        return return_record

    def search_return_records(self, return_id: Optional[str] = None, 
                             borrow_id: Optional[str] = None, 
                             reader_id: Optional[str] = None) -> List[Dict]:
        results = []
        for record in self.return_records:
            match = True
            if return_id and return_id.lower() not in record['return_id'].lower():
                match = False
            if borrow_id and borrow_id.lower() not in record['borrow_id'].lower():
                match = False
            if reader_id and reader_id.lower() not in record['reader_id'].lower():
                match = False
            if match:
                results.append({
                    "stt": len(results) + 1,
                    "return_id": record['return_id'],
                    "borrow_id": record['borrow_id'],
                    "reader_id": record['reader_id'],
                    "return_date": record['return_date'],
                    "total_fine": record['total_fine']
                })
        return results

    def get_all_return_records(self) -> List[Dict]:
        return [{
            "stt": idx + 1,
            "return_id": record['return_id'],
            "borrow_id": record['borrow_id'],
            "reader_id": record['reader_id'],
            "return_date": record['return_date'],
            "total_fine": record['total_fine']
        } for idx, record in enumerate(self.return_records)]

    def get_return_record_details(self, return_id: str) -> Optional[Dict]:
        return next((record for record in self.return_records if record['return_id'] == return_id), None)

    def update_return_record(self, return_id: str, new_doc_ids: List[str]) -> bool:
        return_record = self.get_return_record_details(return_id)
        if not return_record:
            return False

        borrow_record = self.get_borrow_record_details(return_record['borrow_id'])
        if not borrow_record:
            raise ValueError("Không tìm thấy phiếu mượn liên quan")

        reader = self.reader_manager.get_reader_details(return_record['reader_id'])
        if not reader:
            raise ValueError("Không tìm thấy độc giả")

        old_doc_ids = return_record['documents']
        for doc_id in old_doc_ids:
            for history in reader['borrow_history']:
                if history['book_id'] == doc_id and history['status'] == 'returned':
                    history['status'] = 'borrowed'
                    reader['borrowed_books'] += 1
                    reader['fine_amount'] -= history['fine']
                    break
            self.doc_manager.borrow_document(doc_id)  # Cập nhật AvailableQuantity và status

        invalid_docs = [doc_id for doc_id in new_doc_ids if doc_id not in borrow_record['documents']]
        if invalid_docs:
            raise ValueError(f"Các tài liệu {invalid_docs} không thuộc phiếu mượn này")

        total_fine = 0
        for doc_id in new_doc_ids:
            result = self.reader_manager.return_book(return_record['reader_id'], doc_id, return_record['return_date'])
            if result['success']:
                self.doc_manager.return_document(doc_id)  # Cập nhật AvailableQuantity và status
                total_fine += result['fine']

        remaining_docs = [doc_id for doc_id in borrow_record['documents'] if doc_id not in new_doc_ids]
        if not remaining_docs:
            borrow_record['status'] = 'returned'
        else:
            borrow_record['status'] = 'borrowed'

        return_record['documents'] = new_doc_ids
        return_record['total_fine'] = total_fine
        self.reader_manager._save_readers()
        self.doc_manager._save_documents()
        self._save_borrow_records()
        self._save_return_records()
        self._log_action("update_return", return_id, f"Cập nhật phiếu trả cho phiếu mượn {return_record['borrow_id']}")
        return True

    def delete_return_record(self, return_id: str) -> bool:
        return_record = self.get_return_record_details(return_id)
        if not return_record:
            return False

        borrow_record = self.get_borrow_record_details(return_record['borrow_id'])
        if not borrow_record:
            raise ValueError("Không tìm thấy phiếu mượn liên quan")

        reader = self.reader_manager.get_reader_details(return_record['reader_id'])
        if not reader:
            raise ValueError("Không tìm thấy độc giả")

        for doc_id in return_record['documents']:
            for history in reader['borrow_history']:
                if history['book_id'] == doc_id and history['status'] == 'returned':
                    history['status'] = 'borrowed'
                    reader['borrowed_books'] += 1
                    reader['fine_amount'] -= history['fine']
                    break
            self.doc_manager.borrow_document(doc_id)  # Cập nhật AvailableQuantity và status

        borrow_record['status'] = 'borrowed'
        self.return_records = [r for r in self.return_records if r['return_id'] != return_id]
        self.reader_manager._save_readers()
        self.doc_manager._save_documents()
        self._save_borrow_records()
        self._save_return_records()
        self._log_action("delete_return", return_id, f"Xóa phiếu trả cho phiếu mượn {return_record['borrow_id']}")
        return True

    def extend_borrow_period(self, borrow_id: str) -> bool:
        """
        Gia hạn thời gian mượn thêm 7 ngày (tối đa 1 lần) nếu không có đặt trước
        """
        borrow_record = self.get_borrow_record_details(borrow_id)
        if not borrow_record:
            raise ValueError("Không tìm thấy phiếu mượn")

        if borrow_record['status'] != 'borrowed':
            raise ValueError("Chỉ có thể gia hạn phiếu mượn đang hoạt động")

        # Kiểm tra xem đã gia hạn chưa
        reader = self.reader_manager.get_reader_details(borrow_record['reader_id'])
        if not reader:
            raise ValueError("Không tìm thấy độc giả")

        for history in reader['borrow_history']:
            if history['book_id'] in borrow_record['documents'] and history.get('extended', False):
                raise ValueError("Đã gia hạn mượn tài liệu này trước đó")

        # Gia hạn thêm 7 ngày
        new_due_date = (datetime.fromisoformat(borrow_record['due_date']) + timedelta(days=7)).isoformat()
        borrow_record['due_date'] = new_due_date

        # Cập nhật lịch sử mượn của độc giả
        for doc_id in borrow_record['documents']:
            for history in reader['borrow_history']:
                if history['book_id'] == doc_id and history['status'] == 'borrowed':
                    history['due_date'] = new_due_date
                    history['extended'] = True
                    break

        self._save_borrow_records()
        self.reader_manager._save_readers()
        self._log_action("extend_borrow", borrow_id, f"Gia hạn mượn đến {new_due_date}")
        return True
