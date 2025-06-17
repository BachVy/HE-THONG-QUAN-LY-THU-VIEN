import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from fuzzywuzzy import fuzz
from config import CONFIG

class ReaderManager:
    def __init__(self, readers_file: str, reader_types_file: str, log_file: str = CONFIG["reader_logs_file"]):
        self.readers_file = readers_file
        self.reader_types_file = reader_types_file
        self.log_file = log_file
        self.readers = self._load_readers()
        self.reader_types = self._load_reader_types()
        self.logs = self._load_logs()

    def _load_readers(self) -> List[Dict]:
        try:
            with open(self.readers_file, 'r', encoding='utf-8') as f:
                readers = json.load(f)
            for reader in readers:
                if reader.get('borrowed_books', 0) < 0:
                    print(f"Invalid borrowed_books for {reader['reader_id']}")
                if reader.get('role') not in ['admin', 'reader']:
                    print(f"Invalid role for {reader['reader_id']}")
                if not reader.get('username'):
                    print(f"Missing username for {reader['reader_id']}")
            return readers
        except FileNotFoundError:
            return []

    def _load_reader_types(self) -> List[Dict]:
        try:
            with open(self.reader_types_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    def _load_logs(self) -> List[Dict]:
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    def _save_readers(self):
        with open(CONFIG["readers_file"], 'w', encoding='utf-8') as f:
            json.dump(self.readers, f, ensure_ascii=False, indent=4)

    def _save_logs(self):
        with open(CONFIG["reader_logs_file"], 'w', encoding='utf-8') as f:
            json.dump(self.logs, f, ensure_ascii=False, indent=4)
    
    def login(self, username: str, password: str) -> Optional[Dict]:
        # self._load_readers()
        for reader in self.readers:
            if reader.get('username') == username and reader.get('password') == password:
                return reader
        return None

    def _log_action(self, action: str, reader_id: str, details: str):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "reader_id": reader_id,
            "details": details
        }
        self.logs.append(log_entry)
        self._save_logs()

    def _generate_reader_id(self) -> str:
        return f"DG{str(len(self.readers) + 1).zfill(5)}"

    def _validate_email(self, email: str) -> bool:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def _validate_phone(self, phone: str) -> bool:
        pattern = r'^(0|\+84)(\d{9})$'
        return bool(re.match(pattern, phone))

    def _validate_id_card(self, id_card: str) -> bool:
        pattern = r'^\d{9}|\d{12}$'
        return bool(re.match(pattern, id_card))

    def _validate_student_id(self, student_id: str) -> bool:
        pattern = r'^[A-Z0-9]{6,10}$'
        return bool(re.match(pattern, student_id))

    def _validate_employee_id(self, employee_id: str) -> bool:
        pattern = r'^CB[A-Z0-9]{6,10}$'
        return bool(re.match(pattern, employee_id))

    def _validate_dob(self, dob: str) -> bool:
        try:
            datetime.strptime(dob, '%Y-%m-%d')
            return True
        except ValueError:
            return False

    def _check_duplicate(self, id_card: str, student_id: Optional[str] = None, employee_id: Optional[str] = None) -> bool:
        for reader in self.readers:
            if reader['id_card'] == id_card:
                return True
            if student_id and reader.get('student_id') == student_id:
                return True
            if employee_id and reader.get('employee_id') == employee_id:
                return True
        return False

    def register_reader(self, full_name: str, id_card: str, dob: Optional[str], 
                       phone: str, email: str, address: str, reader_type: str,
                       student_id: Optional[str] = None, employee_id: Optional[str] = None,
                       role: str = "reader") -> Dict:
        if not full_name or not id_card or not phone or not email or not address or not reader_type:
            raise ValueError("Tất cả các trường bắt buộc phải được cung cấp")

        if not self._validate_email(email):
            raise ValueError("Định dạng email không hợp lệ")
        
        if not self._validate_phone(phone):
            raise ValueError("Định dạng số điện thoại không hợp lệ")

        if not self._validate_id_card(id_card):
            raise ValueError("Định dạng CMND/CCCD không hợp lệ")

        if dob and not self._validate_dob(dob):
            raise ValueError("Định dạng ngày sinh không hợp lệ (YYYY-MM-DD)")

        if reader_type not in [rt['type'] for rt in self.reader_types]:
            raise ValueError("Loại độc giả không hợp lệ")

        if reader_type == "Sinh viên":
            if not student_id or not self._validate_student_id(student_id):
                raise ValueError("Mã số sinh viên không hợp lệ")
        elif reader_type == "Giảng viên/Cán bộ":
            if not employee_id or not self._validate_employee_id(employee_id):
                raise ValueError("Mã số cán bộ không hợp lệ")

        if self._check_duplicate(id_card, student_id, employee_id):
            raise ValueError("CMND, MSSV hoặc MSCB đã tồn tại")

        reader_id = self._generate_reader_id()
        reader_type_info = next(rt for rt in self.reader_types if rt['type'] == reader_type)
        expiry_date = (datetime.now() + timedelta(days=365)).isoformat()

        reader = {
            "reader_id": reader_id,
            "full_name": full_name.upper(),
            "dob": dob,
            "address": address,
            "phone": phone,
            "email": email,
            "id_card": id_card,
            "student_id": student_id,
            "employee_id": employee_id,
            "reader_type": reader_type.lower(),
            "max_days": reader_type_info['max_days'],
            "max_books": reader_type_info['max_books'],
            "special_document": reader_type_info['special_document'],
            "password": f"{reader_id}123",
            "status": "active",
            "borrowed_books": 0,
            "overdue_books": 0,
            "borrow_history": [],
            "annual_fee_paid": True,
            "expiry_date": expiry_date,
            "fine_amount": 0,
            "update_history": [],
            "role": role,  # Thêm role
            "username": reader_id  # Thêm username
    }
        self.readers.append(reader)
        self._save_readers()
        self._log_action("register", reader_id, f"Đăng ký độc giả mới: {full_name}")
        return reader

    def search_readers(self, reader_id: Optional[str] = None, 
                     id_number: Optional[str] = None, 
                     full_name: Optional[str] = None, 
                     email: Optional[str] = None,
                     min_similarity: int = 80) -> List[Dict]:
        results = []
        
        for reader in self.readers:
            match = True
            if reader_id and reader_id.lower() not in reader['reader_id'].lower():
                match = False
            if id_number and id_number not in (reader['id_card'], 
                                            reader.get('student_id', ''), 
                                            reader.get('employee_id', '')):
                match = False
            if email and email.lower() not in reader['email'].lower():
                match = False
            if full_name:
                similarity = fuzz.partial_ratio(full_name.lower(), reader['full_name'].lower())
                if similarity < min_similarity:
                    match = False
            
            if match:
                results.append({
                    "stt": len(results) + 1,
                    "reader_id": reader['reader_id'],
                    "full_name": reader['full_name'],
                    "id_card": reader['id_card'],
                    "reader_type": reader['reader_type'],
                    "status": reader['status'],
                    "borrowed_books": reader.get('borrowed_books', 0),
                    "overdue_books": reader.get('overdue_books', 0),
                    "fine_amount": reader.get('fine_amount', 0)
                })
        
        return results

    def get_reader_details(self, reader_id: str) -> Optional[Dict]:
        return next((reader for reader in self.readers if reader['reader_id'] == reader_id), None)

    def update_reader_info(self, reader_id: str, full_name: Optional[str] = None, 
                         phone: Optional[str] = None, email: Optional[str] = None, 
                         address: Optional[str] = None) -> bool:
        reader = self.get_reader_details(reader_id)
        if not reader:
            return False

        updates = {}
        old_values = {}
        
        if full_name:
            updates['full_name'] = full_name.upper()
            old_values['full_name'] = reader['full_name']
        if phone:
            if not self._validate_phone(phone):
                raise ValueError("Định dạng số điện thoại không hợp lệ")
            updates['phone'] = phone
            old_values['phone'] = reader['phone']
        if email:
            if not self._validate_email(email):
                raise ValueError("Định dạng email không hợp lệ")
            updates['email'] = email
            old_values['email'] = reader['email']
        if address:
            updates['address'] = address
            old_values['address'] = reader['address']

        if not updates:
            return False

        update_record = {
            "timestamp": datetime.now().isoformat(),
            "old_values": old_values,
            "new_values": updates
        }
        
        reader['update_history'].append(update_record)
        reader.update(updates)
        
        self._save_readers()
        self._log_action("update_info", reader_id, f"Cập nhật thông tin cá nhân: {updates}")
        self.send_notification(reader_id, "update_info", f"Thông tin cá nhân của bạn đã được cập nhật: {updates}")
        return True

    def send_notification(self, reader_id: str, notification_type: str, message: str) -> bool:
        reader = self.get_reader_details(reader_id)
        if not reader:
            return False

        notification = {
            "timestamp": datetime.now().isoformat(),
            "type": notification_type,
            "message": message,
            "recipient_email": reader['email'],
            "status": "sent"
        }
        
        # Simulate sending notification (in real implementation, this would integrate with email/SMS service)
        self._log_action("notification", reader_id, f"Gửi thông báo: {notification_type} - {message}")
        
        # Store notification in reader's record
        if 'notifications' not in reader:
            reader['notifications'] = []
        reader['notifications'].append(notification)
        
        self._save_readers()
        return True

    def restore_account(self, reader_id: str, paid_fine: bool = False, paid_annual_fee: bool = False) -> bool:
        reader = self.get_reader_details(reader_id)
        if not reader:
            return False

        if reader['status'] not in ['suspended', 'expired']:
            raise ValueError("Tài khoản không ở trạng thái cần khôi phục")

        # Check conditions for restoration
        if reader['fine_amount'] > 0 and not paid_fine:
            raise ValueError("Vui lòng thanh toán phí phạt trước khi khôi phục tài khoản")
        
        if not reader['annual_fee_paid'] and not paid_annual_fee:
            raise ValueError("Vui lòng thanh toán phí thường niên trước khi khôi phục tài khoản")

        # Update reader status
        if paid_fine:
            reader['fine_amount'] = 0
        if paid_annual_fee:
            reader['annual_fee_paid'] = True
            reader['expiry_date'] = (datetime.now() + timedelta(days=365)).isoformat()

        reader['status'] = 'active'
        
        self._save_readers()
        self._log_action("restore", reader_id, f"Khôi phục tài khoản: {reader['full_name']}")
        self.send_notification(reader_id, "account_restored", 
                             "Tài khoản của bạn đã được khôi phục thành công!")
        return True

    def update_reader(self, reader_id: str, updates: Dict) -> bool:
        reader = self.get_reader_details(reader_id)
        if not reader:
            return False

        if 'email' in updates and not self._validate_email(updates['email']):
            raise ValueError("Định dạng email không hợp lệ")
        
        if 'phone' in updates and not self._validate_phone(updates['phone']):
            raise ValueError("Định dạng số điện thoại không hợp lệ")

        if 'id_card' in updates and not self._validate_id_card(updates['id_card']):
            raise ValueError("Định dạng CMND/CCCD không hợp lệ")

        if 'dob' in updates and updates['dob'] and not self._validate_dob(updates['dob']):
            raise ValueError("Định dạng ngày sinh không hợp lệ")

        if 'student_id' in updates and updates['student_id'] and not self._validate_student_id(updates['student_id']):
            raise ValueError("Mã số sinh viên không hợp lệ")

        if 'employee_id' in updates and updates['employee_id'] and not self._validate_employee_id(updates['employee_id']):
            raise ValueError("Mã số cán bộ không hợp lệ")

        if 'reader_type' in updates:
            if updates['reader_type'] not in [rt['type'] for rt in self.reader_types]:
                raise ValueError("Loại độc giả không hợp lệ")
            reader_type_info = next(rt for rt in self.reader_types if rt['type'] == updates['reader_type'])
            updates['max_days'] = reader_type_info['max_days']
            updates['max_books'] = reader_type_info['max_books']
            updates['special_document'] = reader_type_info['special_document']

        for key, value in updates.items():
            if key in reader:
                reader[key] = value.upper() if key == 'full_name' else value

        self._save_readers()
        self._log_action("update", reader_id, f"Cập nhật thông tin độc giả: {reader['full_name']}")
        self.send_notification(reader_id, "update", f"Thông tin độc giả của bạn đã được cập nhật")
        return True

    def delete_reader(self, reader_id: str) -> bool:
        reader = self.get_reader_details(reader_id)
        if not reader:
            return False
        
        if reader.get('borrowed_books', 0) > 0:
            raise ValueError("Không thể xóa độc giả đang có sách mượn")
        
        self.readers = [r for r in self.readers if r['reader_id'] != reader_id]
        self._save_readers()
        self._log_action("delete", reader_id, f"Xóa độc giả: {reader['full_name']}")
        self.send_notification(reader_id, "account_deleted", 
                             "Tài khoản của bạn đã bị xóa khỏi hệ thống")
        return True

    def renew_account(self, reader_id: str) -> bool:
        reader = self.get_reader_details(reader_id)
        if not reader:
            return False
        
        reader['annual_fee_paid'] = True
        reader['expiry_date'] = (datetime.now() + timedelta(days=365)).isoformat()
        reader['status'] = 'active'
        self._save_readers()
        self._log_action("renew", reader_id, f"Gia hạn tài khoản: {reader['full_name']}")
        self.send_notification(reader_id, "account_renewed", 
                             "Tài khoản của bạn đã được gia hạn thành công!")
        return True

    def suspend_reader(self, reader_id: str, reason: str) -> bool:
        reader = self.get_reader_details(reader_id)
        if not reader:
            return False
        
        reader['status'] = 'suspended'
        self._save_readers()
        self._log_action("suspend", reader_id, f"Tạm khóa độc giả: {reader['full_name']}, lý do: {reason}")
        self.send_notification(reader_id, "account_suspended", 
                             f"Tài khoản của bạn đã bị tạm khóa. Lý do: {reason}")
        return True

    def add_borrow_record(self, reader_id: str, book_id: str, borrow_date: str, due_date: str) -> bool:
        reader = self.get_reader_details(reader_id)
        if not reader:
            return False
        
        if reader['status'] != 'active':
            raise ValueError("Tài khoản không ở trạng thái hoạt động")
        
        if not reader['annual_fee_paid']:
            raise ValueError("Phí thường niên chưa được thanh toán")
        
        max_books = reader.get('max_books', 5)
        if reader['borrowed_books'] >= max_books:
            raise ValueError(f"Đã đạt số lượng sách mượn tối đa ({max_books})")

        reader['borrowed_books'] += 1
        reader['borrow_history'].append({
            "book_id": book_id,
            "borrow_date": borrow_date,
            "due_date": due_date,
            "return_date": None,
            "status": "borrowed",
            "fine": 0
        })
        
        self._save_readers()
        self._log_action("borrow", reader_id, f"Mượn sách {book_id}")
        self.send_notification(reader_id, "book_borrowed", 
                             f"Bạn đã mượn sách {book_id}. Ngày trả: {due_date}")
        return True

    def return_book(self, reader_id: str, book_id: str, return_date: str, fine_per_day: int = 5000) -> Dict:
        reader = self.get_reader_details(reader_id)
        if not reader:
            return {"success": False, "fine": 0}

        for record in reader['borrow_history']:
            if record['book_id'] == book_id and record['status'] == 'borrowed':
                record['return_date'] = return_date
                record['status'] = 'returned'
                reader['borrowed_books'] -= 1

                due_date = datetime.fromisoformat(record['due_date'])
                return_date_dt = datetime.fromisoformat(return_date)
                if return_date_dt > due_date:
                    days_late = (return_date_dt - due_date).days
                    fine = days_late * fine_per_day
                    record['fine'] = fine
                    reader['fine_amount'] = reader.get('fine_amount', 0) + fine
                    reader['overdue_books'] = reader.get('overdue_books', 0) + 1

                self._save_readers()
                self._log_action("return", reader_id, f"Trả sách {book_id}, Phí phạt: {record.get('fine', 0)} VNĐ")
                self.send_notification(reader_id, "book_returned", 
                                     f"Bạn đã trả sách {book_id}. Phí phạt: {record.get('fine', 0)} VNĐ")
                return {"success": True, "fine": record.get('fine', 0)}
        
        raise ValueError("Không tìm thấy bản ghi mượn sách")

    def get_borrowing_stats(self) -> Dict:
        stats = {
            "total_readers": len(self.readers),
            "active_readers": 0,
            "borrowing_readers": 0,
            "returned_readers": 0,
            "suspended_readers": 0,
            "expired_readers": 0
        }
        
        for reader in self.readers:
            expiry_date = datetime.fromisoformat(reader['expiry_date'])
            if expiry_date < datetime.now():
                reader['status'] = 'expired'
            
            if reader['status'] == 'active':
                stats['active_readers'] += 1
            elif reader['status'] == 'suspended':
                stats['suspended_readers'] += 1
            elif reader['status'] == 'expired':
                stats['expired_readers'] += 1
            
            borrowed = reader.get('borrowed_books', 0)
            if borrowed > 0:
                stats['borrowing_readers'] += 1
            else:
                stats['returned_readers'] += 1
                
        self._save_readers()
        return stats

    def get_top_borrowers(self, limit: int = 5) -> List[Dict]:
        sorted_readers = sorted(self.readers, 
                              key=lambda x: x.get('borrowed_books', 0), 
                              reverse=True)
        return [{
            "reader_id": r['reader_id'],
            "full_name": r['full_name'],
            "borrowed_books": r.get('borrowed_books', 0),
            "overdue_books": r.get('overdue_books', 0),
            "fine_amount": r.get('fine_amount', 0)
        } for r in sorted_readers[:limit]]

    def get_reader_type_borrowing_ratio(self) -> Dict:
        ratios = {}
        total_books = sum(r.get('borrowed_books', 0) for r in self.readers)
        for rt in self.reader_types:
            type_name = rt['type'].lower()
            type_books = sum(r.get('borrowed_books', 0) 
                           for r in self.readers 
                           if r['reader_type'].lower() == type_name)
            ratios[type_name] = {
                "books": type_books,
                "percentage": (type_books / total_books * 100) if total_books > 0 else 0
            }
        return ratios

    def get_overdue_readers(self) -> List[Dict]:
        overdue_readers = []
        for reader in self.readers:
            for record in reader['borrow_history']:
                if record['status'] == 'borrowed':
                    due_date = datetime.fromisoformat(record['due_date'])
                    if due_date < datetime.now():
                        overdue_readers.append({
                            "reader_id": reader['reader_id'],
                            "full_name": reader['full_name'],
                            "book_id": record['book_id'],
                            "due_date": record['due_date']
                        })
                        break
        return overdue_readers

    def get_readers_with_fines(self) -> List[Dict]:
        return [{
            "reader_id": reader['reader_id'],
            "full_name": reader['full_name'],
            "fine_amount": reader.get('fine_amount', 0)
        } for reader in self.readers if reader.get('fine_amount', 0) > 0]