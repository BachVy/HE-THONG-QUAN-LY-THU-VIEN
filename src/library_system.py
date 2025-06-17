from datetime import datetime, timedelta
from reader_manager import ReaderManager
from document_manager import DocumentManager
from borrowing_manager import BorrowingManager
import os
import tkinter as tk
from tkinter import messagebox, ttk
from login_register import LoginRegisterWindow
from collections import defaultdict
import os
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import json
import time
from config import CONFIG


class LibrarySystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Quản lý thư viện - Reader")
        self.root.geometry("800x600")
        self.root.configure(bg="#87CEEB")

        self.reader_manager = ReaderManager(
            readers_file=CONFIG["readers_file"],
            reader_types_file=CONFIG["reader_types_file"],
            log_file=CONFIG["reader_logs_file"]
        )
        self.doc_manager = DocumentManager(CONFIG["documents_file"])
        self.borrowing_manager = BorrowingManager(self.reader_manager, self.doc_manager)
        self.current_user = None
        self.rules_file = CONFIG["library_rules_file"]
        self.login_window = LoginRegisterWindow(self.root, self.handle_login)

    def show_main_menu(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        self.main_frame = tk.Frame(self.root, bg="#fffaf0")
        self.main_frame.pack(fill="both", expand=True)

        sidebar = tk.Frame(self.main_frame, bg="#87CEEB", width=250)
        sidebar.pack(side="left", fill="y")
        self.content_frame = tk.Frame(self.main_frame, bg="#fffaf0")
        self.content_frame.pack(side="right", fill="both", expand=True)

        tk.Label(sidebar, text="HỆ THỐNG QUẢN LÝ THƯ VIỆN", font=("Arial", 15, "bold"), fg="#000000", bg="#87CEEB", wraplength=300, pady=20).pack(fill="x")
        ttk.Separator(sidebar, orient="horizontal").pack(fill="x", pady=10)

        buttons = [
            ("👤 Quản lý độc giả", self.manage_readers),
            ("📚 Quản lý tài liệu", self.manage_documents),
            ("📋 Quản lý mượn trả", self.manage_borrowing),
            ("📊 Thống kê", self.display_statistics),
            ("🔓 Đăng xuất", self.logout),
            ("🚪 Thoát", self.root.quit)
        ] if self.current_user['role'] == 'admin' else [
            ("👤 Thông tin cá nhân", self.show_reader_info),
            ("🔍 Tìm kiếm tài liệu", self.search_documents),
            ("📚 Danh sách tài liệu", self.show_all_documents),
            ("📜 Phiếu mượn", self.show_borrow_records),
            ("📋 Phiếu trả", self.show_return_records),
            ("💰 Phí phạt", self.show_fine),
            ("💳 Thanh toán phí", self.manage_payments),
            ("📖 Mượn tài liệu", self.borrow_document),
            ("🔙 Trả tài liệu", self.return_document),
            ("🔓 Đăng xuất", self.logout),
            ("🚪 Thoát", self.root.quit)
        ]

        def on_enter(btn): btn.config(bg="#fffaf0")
        def on_leave(btn): btn.config(bg="#87CEEB")

        for text, cmd in buttons:
            btn = tk.Button(sidebar, text=text, command=cmd, font=("Arial", 15), fg="#023020", bg="#87CEEB", relief="flat", anchor="w", padx=10, pady=3)
            btn.pack(fill="x", pady=2)
            btn.bind("<Enter>", lambda e, b=btn: on_enter(b))
            btn.bind("<Leave>", lambda e, b=btn: on_leave(b))

        # Thêm canvas và thanh cuộn cho content_frame
        canvas = tk.Canvas(self.content_frame, bg="#FFFAF0", highlightthickness=0)# Đây 
        scrollbar_y = ttk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#FFFAF0")
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.configure(yscrollcommand=scrollbar_y.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar_y.pack(side="right", fill="y")
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        # Nội dung chào mừng
        tk.Label(scrollable_frame, text="CHÀO MỪNG ĐẾN VỚI THƯ VIỆN", font=("Arial", 18, "bold"), fg="#023020", bg="#FFFAF0").pack(pady=10)
        tk.Label(scrollable_frame, text=f"XIN CHÀO, {self.current_user['full_name']}", font=("Arial", 15), fg="#7F8C8D", bg="#FFFAF0").pack(pady=10)
        ttk.Separator(scrollable_frame, orient="horizontal").pack(fill="x", pady=10)

        # Khung nội quy với viền
        rules_frame = tk.Frame(scrollable_frame, bg="#F5E6E8", bd=2, relief="groove", padx=20, pady=15)
        rules_frame.pack(padx=10, pady=10, fill="both", expand=True)
        # Tiêu đề nội quy
        tk.Label(rules_frame, text="NỘI QUY THƯ VIỆN", font=("Arial", 15, "bold"), fg="#023020", bg="#F5E6E8").pack(anchor="center", pady=5)

        # Định dạng nội quy thành danh sách với ngắt dòng
        summary, _ = self.crawl_library_rules()
        if not summary or "Không thể tải" in summary:
            summary = "Không thể tải nội quy. Vui lòng kiểm tra kết nối hoặc thử lại sau."
        rules_text = summary.split('\n')  # Chia nhỏ dựa trên xuống dòng
        if len(rules_text) > 1:
            for i, rule in enumerate(rules_text, 1):
                if rule.strip():
                    tk.Label(rules_frame, text=f"{i}. {rule.strip()}", font=("Arial", 12), fg="#34495E", bg="#F5E6E8", justify="left", wraplength=910).pack(anchor="w", pady=2, padx=10)
        else:
            # Nếu không có xuống dòng, chia dựa trên dấu chấm
            rules_text = [r.strip() for r in summary.split('.') if r.strip()]
            for i, rule in enumerate(rules_text, 1):
                tk.Label(rules_frame, text=f"{i}. {rule}", font=("Arial", 12), fg="#34495E", bg="#F5E6E8", justify="left", wraplength=910).pack(anchor="w", pady=2, padx=10)

    def crawl_library_rules(self):
        """Crawl nội quy từ https://thuvien.huit.edu.vn/Page/quy-dinh-su-dung-thu-vien"""
        url = "https://thuvien.huit.edu.vn/Page/quy-dinh-su-dung-thu-vien"
        summary = ""
        detailed = ""
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, timeout=20)  # Tăng timeout
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # Thử các thẻ có thể chứa nội quy
                content = soup.find('div', class_='main-content') or soup.find('section', class_='content') or soup.find_all('p')
                if content:
                    if isinstance(content, list):
                        text = "\n".join(p.get_text(strip=True) for p in content if p.get_text(strip=True))
                    else:
                        text = content.get_text(strip=True)
                    detailed = text[:2000]
                    summary = text[:20000] + "..." if len(text) > 20000 else text
                else:
                    raise ValueError("Không tìm thấy nội dung nội quy")
            else:
                chrome_options = Options()
                chrome_options.add_argument("--headless")
                driver = webdriver.Chrome(options=chrome_options)
                driver.get(url)
                time.sleep(3)
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                driver.quit()
                content = soup.find('div', class_='main-content') or soup.find('section', class_='content') or soup.find_all('p')
                if content:
                    if isinstance(content, list):
                        text = "\n".join(p.get_text(strip=True) for p in content if p.get_text(strip=True))
                    else:
                        text = content.get_text(strip=True)
                    detailed = text[:2000]
                    summary = text[:200] + "..." if len(text) > 200 else text
                else:
                    raise ValueError("Không tìm thấy nội dung nội quy")
        except Exception as e:
            print(f"Lỗi crawl: {e}")  # Log lỗi để debug
            if os.path.exists(self.rules_file):
                with open(self.rules_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    summary = data.get('summary', "Không thể tải nội quy. Vui lòng kiểm tra kết nối.")
                    detailed = data.get('detailed', "")
            else:
                summary = "Không thể tải nội quy. Vui lòng kiểm tra kết nối."
                detailed = ""

        if summary and detailed and "Không thể tải" not in summary:
            with open(self.rules_file, 'w', encoding='utf-8') as f:
                json.dump({"summary": summary, "detailed": detailed}, f, ensure_ascii=False, indent=2)

        return summary, detailed

    def show_library_rules_gui(self):
        self.clear_content()
        self.content_frame = tk.Frame(self.root, bg="#FFFAF0")
        self.content_frame.pack(fill="both", expand=True)

        tk.Label(self.content_frame, text="Nội quy thư viện", font=("Arial", 20, "bold"), fg="#023020", bg="#FFFAF0").pack(pady=20)

        canvas = tk.Canvas(self.content_frame, bg="#FFFAF0", highlightthickness=0)
        scrollbar_y = ttk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#FFFAF0")
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.configure(yscrollcommand=scrollbar_y.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar_y.pack(side="right", fill="y")
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        result_frame = tk.Frame(scrollable_frame, bg="#FFFAF0")
        result_frame.pack(fill="x", pady=10)

        summary, detailed = self.crawl_library_rules()
        tk.Label(result_frame, text=summary, font=("Arial", 12), fg="#34495E", bg="#FFFAF0", justify="left").pack(anchor="w", padx=10, pady=5)
        tk.Label(result_frame, text=detailed, font=("Arial", 10), fg="#34495E", bg="#FFFAF0", justify="left").pack(anchor="w", padx=10, pady=5)

        btn = tk.Button(self.content_frame, text="⬅ Quay lại", command=self.show_main_menu, font=("Arial", 12, "bold"), fg="#023020", bg="#708090", relief="flat", padx=15, pady=5)
        btn.pack(anchor="e", pady=10)
        btn.bind("<Enter>", lambda e: btn.config(bg="#34495E", relief="raised"))
        btn.bind("<Leave>", lambda e: btn.config(bg="#708090", relief="flat"))

        ttk.Separator(self.content_frame, orient="horizontal").pack(fill="x", pady=20)

    def handle_login(self, username, password):
        user = self.reader_manager.login(username, password)
        if user :
            self.current_user = user
            messagebox.showinfo("Thành công", f"Đăng nhập thành công! Chào {user['full_name']} ({user['role']})")
            self.root.geometry("600x700")
            self.show_main_menu()
        else:
            messagebox.showerror("Lỗi", "Tên đăng nhập, mật khẩu không đúng hoặc bạn không có quyền reader!")

    def logout(self):
        # Ghi log đăng xuất (nếu cần)
        if self.current_user and hasattr(self.reader_manager, 'log_action'):
            self.reader_manager.log_action(self.current_user['username'], 'logout')
        # Xóa thông tin người dùng hiện tại
        self.current_user = None
        # Xóa giao diện hiện tại
        for widget in self.root.winfo_children():
            widget.destroy()
        # Đặt lại cấu hình cửa sổ
        self.root.title("Quản lý thư viện - Reader")
        self.root.geometry("800x600")
        self.root.configure(bg="#87CEEB")
        # Tạo lại màn hình đăng nhập
        self.login_window = LoginRegisterWindow(self.root, self.handle_login)
        # Thông báo đăng xuất (tùy chọn)
        messagebox.showinfo("Thông báo", "Đăng xuất thành công!")
         
    def clear_content(self):
        if hasattr(self, 'content_frame'):
            for widget in self.content_frame.winfo_children():
                widget.destroy()
        else:
            self.content_frame = tk.Frame(self.main_frame, bg="#FFFAF0")
        self.content_frame.pack(side="right", fill="both", expand=True)

    def manage_payments(self):
        self.clear_content()
        main_frame = tk.Frame(self.content_frame, bg="#FFFFFF")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(main_frame, text="Thanh toán phí phạt", font=("Arial", 20, "bold"), fg="#000000", bg="#FFFFFF").pack(fill="x", pady=20)

        reader = self.reader_manager.get_reader_details(self.current_user['username'])
        if not reader:
            tk.Label(main_frame, text="Không tìm thấy thông tin độc giả!", font=("Arial", 12), fg="#E74C3C", bg="#FFFFFF").pack(fill="x", pady=10)
            return

        info_frame = tk.Frame(main_frame, bg="#FFFFFF")
        info_frame.pack(fill="x", pady=10)
        stats = [
            ("Mã độc giả", reader.get('reader_id', 'N/A')),
            ("Tên độc giả", reader.get('full_name', 'N/A')),
            ("Phí phạt", f"{reader.get('fine_amount', 0.0):.2f} VND")
        ]
        for idx, (label, value) in enumerate(stats):
            tk.Label(info_frame, text=f"{label}:", font=("Arial", 12, "bold"), fg="#000000", bg="#FFFFFF").grid(row=idx, column=0, sticky="w", padx=5, pady=5)
            tk.Label(info_frame, text=value, font=("Arial", 12), fg="#34495E", bg="#FFFFFF").grid(row=idx, column=1, sticky="w", padx=5, pady=5)

        payment_frame = tk.Frame(main_frame, bg="#FFFFFF")
        payment_frame.pack(fill="x", pady=10)
        tk.Label(payment_frame, text="Số tiền thanh toán (VND):", font=("Arial", 12, "bold"), fg="#000000", bg="#FFFFFF").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        payment_amount_var = tk.StringVar()
        tk.Entry(payment_frame, textvariable=payment_amount_var, font=("Arial", 12), width=20).grid(row=0, column=1, sticky="w", padx=5, pady=5)


        def process_payment():
            try:
                amount = float(payment_amount_var.get())
                if amount <= 0:
                    raise ValueError("Số tiền phải lớn hơn 0!")
                if amount > reader['fine_amount']:
                    messagebox.showwarning("Cảnh báo", "Số tiền vượt quá phí phạt!")
                    return
                reader['fine_amount'] -= amount
                self.reader_manager.update_reader(reader['reader_id'], reader)
                messagebox.showinfo("Thành công", f"Thanh toán {amount:.2f} VND thành công!\nCòn lại: {reader['fine_amount']:.2f} VND")
                self.manage_payments()
            except ValueError as e:
                messagebox.showerror("Lỗi", str(e) if str(e) == "Số tiền phải lớn hơn 0!" else "Vui lòng nhập số hợp lệ!")

        def on_enter(btn): btn.config(bg="#34495E", relief="raised")
        def on_leave(btn): btn.config(bg="#708090", relief="flat")

        tk.Button(payment_frame, text="Thanh toán", command=process_payment, font=("Arial", 12, "bold"), fg="#023020", bg="#708090", relief="flat", padx=15, pady=5).grid(row=1, column=0, columnspan=2, pady=10).bind("<Enter>", lambda e: on_enter(e.widget)).bind("<Leave>", lambda e: on_leave(e.widget))

        button_frame = tk.Frame(main_frame, bg="#FFFFFF")
        button_frame.pack(fill="x", pady=10)
        ttk.Separator(main_frame, orient="horizontal").pack(fill="x", pady=20)

    def show_reader_info(self):
        self.clear_content()
        reader = self.reader_manager.get_reader_details(self.current_user['reader_id'])
        tk.Label(self.content_frame, text="Thông tin cá nhân", font=("Arial", 18, "bold"), fg="#023020", bg="#FFFAF0").pack(pady=20)#k đổi 

        info_frame = tk.Frame(self.content_frame, bg="#FFFAF0")# NỀN
        info_frame.pack(fill="both", padx=20, pady=10)
        expiry_date = datetime.fromisoformat(reader['expiry_date']).strftime("%Y-%m-%d")
        info_items = [
            ("👤 Mã độc giả", reader['reader_id']),
            ("🧑 Họ tên", reader['full_name']),
            ("📋 Loại độc giả", reader['reader_type']),
            ("📚 Số sách đang mượn", str(reader['borrowed_books'])),
            ("💰 Phí phạt", f"{reader['fine_amount']:.2f} VND"),
            ("💳 Phí thường niên", "Đã thanh toán" if reader['annual_fee_paid'] else "Chưa thanh toán"),
            ("🔄 Trạng thái", reader['status'].capitalize()),
            ("📅 Ngày hết hạn", expiry_date)
        ]
        for row, (label, value) in enumerate(info_items): #
            tk.Label(info_frame, text=label, font=("Arial", 12, "bold"), fg="#34495E", bg="#FFFAF0").grid(row=row, column=0, sticky="w", padx=10, pady=5)
            tk.Label(info_frame, text=value, font=("Arial", 12), fg="#7F8C8D", bg="#FFFAF0").grid(row=row, column=1, sticky="w", padx=10, pady=5)

        ttk.Separator(self.content_frame, orient="horizontal").pack(fill="x", pady=20)
    def search_documents(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Tìm kiếm tài liệu", font=("Arial", 18, "bold"), fg="#023020", bg="#FFFAF0").pack(pady=20)

        input_frame = tk.Frame(self.content_frame, bg="#FFFAF0")
        input_frame.pack(fill="x", padx=20, pady=10)
        labels = ["👤 Mã tài liệu:", "📝 Tiêu đề:", "📋 Thể loại:"]
        entries = [tk.StringVar() for _ in range(3)]
        for i, label in enumerate(labels):
            tk.Label(input_frame, text=label, font=("Arial", 12, "bold"), fg="#34495E", bg="#FFFAF0").grid(row=i, column=0, sticky="w", pady=5)
            tk.Entry(input_frame, textvariable=entries[i], font=("Arial", 12), width=40).grid(row=i, column=1, sticky="w", pady=5, padx=10)

        result_frame = tk.Frame(self.content_frame, bg="#FFFAF0")
        result_frame.pack(fill="both", expand=True, padx=20, pady=10)
        columns = ("STT", "Mã tài liệu", "Tiêu đề", "Thể loại", "Số lượng", "Đặc biệt", "Trạng thái", "Số lượng có sẵn")
        tree = ttk.Treeview(result_frame, columns=columns, show="headings", height=10)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100, anchor="center" if col != "Tiêu đề" else "w")
        tree.column("Tiêu đề", width=200)
        scrollbar = ttk.Scrollbar(result_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def on_search():
            doc_id, title, category = [e.get() or None for e in entries]
            try:
                documents = self.doc_manager.search_documents(doc_id=doc_id, title=title, category=category)
                for item in tree.get_children():
                    tree.delete(item)
                if documents:
                    for doc in documents:
                        tree.insert("", "end", values=(doc['stt'], doc['doc_id'], doc['title'], doc['category'], doc['SoLuong'], doc['DacBiet'], doc['status'], doc['AvailableQuantity']))
                else:
                    tree.insert("", "end", values=("Không tìm thấy tài liệu.", "", "", "", "", "", "", ""))
            except Exception as e:
                for item in tree.get_children():
                    tree.delete(item)
                tree.insert("", "end", values=(f"Lỗi: {e}", "", "", "", "", "", "", ""))

        def on_enter(btn): btn.config(bg="#34495E")
        def on_leave(btn): btn.config(bg="#708090")

        tk.Button(self.content_frame, text="Tìm kiếm", command=on_search, font=("Arial", 12, "bold"), fg="#023020", bg="#708090", relief="flat", padx=20, pady=5).pack(pady=10).bind("<Enter>", lambda e: on_enter(e.widget)).bind("<Leave>", lambda e: on_leave(e.widget))

        btn = tk.Button(self.content_frame, text="Đóng", command=self.clear_content, font=("Arial", 12, "bold"), fg="#023020", bg="#708090", relief="flat", padx=20, pady=5)
        btn.pack(pady=10)
        btn.bind("<Enter>", lambda e: on_enter(e.widget))
        btn.bind("<Leave>", lambda e: on_leave(e.widget))

        ttk.Separator(self.content_frame, orient="horizontal").pack(fill="x", pady=20)

    def show_all_documents(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Danh sách tài liệu", font=("Arial", 18, "bold"), fg="#023020", bg="#FFFAF0").pack(pady=20)# đây 

        result_frame = tk.Frame(self.content_frame, bg="#FFFAF0")
        result_frame.pack(fill="both", expand=True, padx=20, pady=10)
        columns = ("Mã tài liệu", "Tiêu đề", "Thể loại", "Số lượng", "Đặc biệt", "Trạng thái", "Số lượng có sẵn")
        tree = ttk.Treeview(result_frame, columns=columns, show="headings", height=10)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100, anchor="center" if col != "Tiêu đề" else "w")
        tree.column("Tiêu đề", width=200)
        scrollbar = ttk.Scrollbar(result_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        documents = self.doc_manager.get_all_documents()
        if documents:
            for doc in documents:
                tree.insert("", "end", values=(doc['doc_id'], doc['title'], doc['category'], doc['SoLuong'], str(doc['DacBiet']), doc['status'], doc['AvailableQuantity']))
        else:
            messagebox.showinfo("Thông báo", "Không có tài liệu nào.")

        ttk.Separator(self.content_frame, orient="horizontal").pack(fill="x", pady=20)

    def show_borrow_records(self):
        self.clear_content()
        reader = self.reader_manager.get_reader_details(self.current_user['reader_id'])
        borrowed = [r for r in reader['borrow_history'] if r['status'] == 'borrowed']
        tk.Label(self.content_frame, text="Phiếu mượn", font=("Arial", 18, "bold"), fg="#023020", bg="#FFFAF0").pack(pady=20)

        result_frame = tk.Frame(self.content_frame, bg="#FFFAF0")
        result_frame.pack(fill="both", expand=True, padx=20, pady=10)
        columns = ("Mã tài liệu", "Ngày mượn", "Ngày phải trả")
        tree = ttk.Treeview(result_frame, columns=columns, show="headings", height=10)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150, anchor="center")
        scrollbar = ttk.Scrollbar(result_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        if borrowed:
            for r in borrowed:
                borrow_date = datetime.fromisoformat(r['borrow_date']).strftime("%Y-%m-%d")
                due_date = datetime.fromisoformat(r['due_date']).strftime("%Y-%m-%d")
                tree.insert("", "end", values=(r['book_id'], borrow_date, due_date))
        else:
            messagebox.showinfo("Thông báo", "Bạn chưa mượn tài liệu nào.")

        def on_enter(btn): btn.config(bg="#34495E")
        def on_leave(btn): btn.config(bg="#708090")

        btn = tk.Button(self.content_frame,text="Đóng",command=self.clear_content,font=("Arial", 12, "bold"),
            fg="#023020",
            bg="#708090",
            relief="flat",
            padx=20,
            pady=5)
        btn.pack(pady=10)
        btn.bind("<Enter>", lambda e: on_enter(e.widget))
        btn.bind("<Leave>", lambda e: on_leave(e.widget))

        ttk.Separator(self.content_frame, orient="horizontal").pack(fill="x", pady=20)

    def show_return_records(self):
        self.clear_content()
        reader = self.reader_manager.get_reader_details(self.current_user['reader_id'])
        returned = [r for r in reader['borrow_history'] if r['status'] == 'returned']
        tk.Label(self.content_frame, text="Phiếu trả", font=("Arial", 18, "bold"), fg="#023020", bg="#FFFAF0").pack(pady=20)

        result_frame = tk.Frame(self.content_frame, bg="#FFFAF0")
        result_frame.pack(fill="both", expand=True, padx=20, pady=10)
        columns = ("Mã tài liệu", "Ngày trả", "Phí phạt (VND)")
        tree = ttk.Treeview(result_frame, columns=columns, show="headings", height=10)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150, anchor="center")
        scrollbar = ttk.Scrollbar(result_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        if returned:
            for r in returned:
                return_date = datetime.fromisoformat(r['return_date']).strftime("%Y-%m-%d") if r['return_date'] else "Chưa trả"
                tree.insert("", "end", values=(r['book_id'], return_date, r['fine'] if r['fine'] is not None else "0"))
        else:
            messagebox.showinfo("Thông báo", "Bạn chưa trả tài liệu nào.")

        ttk.Separator(self.content_frame, orient="horizontal").pack(fill="x", pady=20)

    def show_fine(self):
        self.clear_content()
        reader = self.reader_manager.get_reader_details(self.current_user['reader_id'])
        tk.Label(self.content_frame, text="Phí phạt", font=("Arial", 18, "bold"), fg="#023020", bg="#FFFAF0").pack(pady=20)

        info_frame = tk.Frame(self.content_frame, bg="#FFFAF0")
        info_frame.pack(pady=20, padx=20)
        tk.Label(info_frame, text=f"Phí phạt hiện tại: {reader['fine_amount']:.2f} VND" if reader['fine_amount'] > 0 else "Bạn không có phí phạt.", font=("Arial", 14), fg="#34495E" if reader['fine_amount'] > 0 else "#7F8C8D", bg="#FFFAF0").pack()

        ttk.Separator(self.content_frame, orient="horizontal").pack(fill="x", pady=20)

    def borrow_document(self):
        self.clear_content()
        reader = self.reader_manager.get_reader_details(self.current_user['reader_id'])
        if reader['status'] != 'active':
            messagebox.showerror("Lỗi", "Tài khoản không active, không thể mượn!")
            return
        if reader['borrowed_books'] >= reader['max_books']:
            messagebox.showerror("Lỗi", f"Đã mượn tối đa {reader['max_books']} tài liệu!")
            return

        tk.Label(self.content_frame, text="Mượn tài liệu", font=("Arial", 18, "bold"), fg="#023020", bg="#FFFAF0").pack(pady=20)
        input_frame = tk.Frame(self.content_frame, bg="#FFFAF0")
        input_frame.pack(pady=10, padx=20)
        tk.Label(input_frame, text="Mã tài liệu:", font=("Arial", 12, "bold"), fg="#34495E", bg="#FFFAF0").pack()
        doc_id_var = tk.StringVar()
        tk.Entry(input_frame, textvariable=doc_id_var, font=("Arial", 12), width=40).pack(pady=5)

        def on_borrow():
            doc_id = doc_id_var.get()
            if doc_id and messagebox.askyesno("Xác nhận", f"Mượn tài liệu {doc_id}?"):
                try:
                    borrow_date = datetime.now().strftime("%Y-%m-%d")
                    due_date = (datetime.now() + timedelta(days=reader['max_days'])).strftime("%Y-%m-%d")
                    self.borrowing_manager.create_borrow_record(self.current_user['reader_id'], [doc_id], borrow_date, due_date)
                    messagebox.showinfo("Thành công", "Mượn tài liệu thành công!")
                    self.show_main_menu()
                except ValueError as e:
                    messagebox.showerror("Lỗi", f"Lỗi: {e}")

        def on_enter(btn): btn.config(bg="#34495E")
        def on_leave(btn): btn.config(bg="#708090")

        tk.Button(self.content_frame, text="Mượn", command=on_borrow, font=("Arial", 12, "bold"), fg="#023020", bg="#708090", relief="flat", padx=20, pady=5).pack(pady=10).bind("<Enter>", lambda e: on_enter(e.widget)).bind("<Leave>", lambda e: on_leave(e.widget))
        ttk.Separator(self.content_frame, orient="horizontal").pack(fill="x", pady=20)

    def return_document(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Trả tài liệu", font=("Arial", 18, "bold"), fg="#023020", bg="#FFFAF0").pack(pady=20)
        input_frame = tk.Frame(self.content_frame, bg="#FFFAF0")
        input_frame.pack(pady=10, padx=20)
        tk.Label(input_frame, text="Mã tài liệu:", font=("Arial", 12, "bold"), fg="#34495E", bg="#FFFAF0").pack()
        doc_id_var = tk.StringVar()
        tk.Entry(input_frame, textvariable=doc_id_var, font=("Arial", 12), width=40).pack(pady=5)

        def on_return():
            doc_id = doc_id_var.get()
            if doc_id and messagebox.askyesno("Xác nhận", f"Trả tài liệu {doc_id}?"):
                try:
                    return_date = datetime.now().strftime("%Y-%m-%d")
                    self.borrowing_manager.create_return_record(self.current_user['reader_id'], doc_id, return_date)
                    messagebox.showinfo("Thành công", "Trả tài liệu thành công!")
                    self.show_main_menu()
                except ValueError as e:
                    messagebox.showerror("Lỗi", f"Lỗi: {e}")

        def on_enter(btn): btn.config(bg="#34495E")
        def on_leave(btn): btn.config(bg="#708090")

        tk.Button(self.content_frame, text="Trả", command=on_return, font=("Arial", 12, "bold"), fg="#023020", bg="#708090", relief="flat", padx=20, pady=5).pack(pady=10).bind("<Enter>", lambda e: on_enter(e.widget)).bind("<Leave>", lambda e: on_leave(e.widget))
        ttk.Separator(self.content_frame, orient="horizontal").pack(fill="x", pady=20)

    def search_reader_common(self, search_var, result_frame, callback=None):
        query = search_var.get().strip()
        if not query:
            messagebox.showwarning("Cảnh báo!", "Vui lòng nhập mã độc giả!")
            return None

        for widget in result_frame.winfo_children():
            widget.destroy()

        reader = self.reader_manager.get_reader_details(query)
        if reader:
            info_frame = tk.Frame(result_frame, bg="#FFFAF0")
            info_frame.pack(fill="x", pady=5)
            fields = [
                ("Mã độc giả", reader.get("reader_id", "N/A")),
                ("Họ tên", reader.get("full_name", "N/A")),
                ("Ngày sinh", reader.get("dob", "N/A")),
                ("Địa chỉ", reader.get("address", "N/A")),
                ("Số điện thoại", reader.get("phone", "N/A")),
                ("Email", reader.get("email", "N/A")),
                ("CMND/CCCD", reader.get("id_card", "N/A")),
                ("Mã sinh viên" if reader.get("reader_type") == "Sinh viên" else "Mã cán bộ", reader.get("student_id" if reader.get("reader_type") == "Sinh viên" else "employee_id", "N/A")),
                ("Loại độc giả", reader.get("reader_type", "N/A")),
                ("Số ngày mượn tối đa", reader.get("max_days", "N/A")),
                ("Số sách mượn tối đa", reader.get("max_books", "N/A")),
                ("Tài liệu đặc biệt", "Có" if reader.get("special_document", False) else "Không"),
                ("Trạng thái", reader.get("status", "N/A")),
                ("Số sách đang mượn", reader.get("borrowed_books", 0)),
                ("Số sách quá hạn", reader.get("overdue_books", 0)),
                ("Tiền phạt", f"{reader.get('fine_amount', 0):,.0f} VNĐ")
            ]
            for idx, (label, value) in enumerate(fields):
                tk.Label(info_frame, text=f"{label}:", font=("Arial", 11, "bold"), fg="#023020", bg="#FFFAF0").grid(row=idx, column=0, sticky="w", padx=5, pady=2)
                tk.Label(info_frame, text=value, font=("Arial", 11), fg="#34495E", bg="#FFFAF0").grid(row=idx, column=1, sticky="w", padx=5, pady=2)

            if callback:
                callback(reader, query, result_frame)
        else:
            tk.Label(result_frame, text="Không tìm thấy thông tin độc giả!", font=("Arial", 12), fg="#E74C3C", bg="#FFFAF0").pack(fill="x", pady=20)
        return reader
            
# #///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////-mốc
    def manage_readers(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Quản lý độc giả", font=("Arial", 20, "bold"), fg="#023020", bg="#FFFAF0").pack(pady=20)

        button_frame = tk.Frame(self.content_frame, bg="#FFFAF0")
        button_frame.pack(pady=10, padx=20, fill="both", expand=True)

        buttons = [
            ("🔍 Tìm kiếm độc giả", self.search_readers_gui),
            ("📅 Gia hạn tài khoản", self.renew_account_gui),
            ("🚫 Tạm khóa độc giả", self.suspend_reader_gui),
            ("🗑️ Xóa độc giả", self.delete_reader_gui),
            ("✏️ Cập nhật thông tin độc giả", self.update_reader_info_gui),
            ("🔄 Khôi phục tài khoản", self.restore_account_gui),
            ("⬅ Quay lại", self.clear_content)
        ]

        def on_enter(btn): btn.config(bg="#87CAFA", relief="raised")
        def on_leave(btn): btn.config(bg="#FFC0CB", relief="flat")

        for idx, (text, cmd) in enumerate(buttons):
            btn = tk.Button(button_frame, text=text, command=cmd, font=("Arial", 14, "bold"), fg="#023020", bg="#708090", relief="flat", anchor="w", padx=20, pady=10, width=30)
            btn.grid(row=idx, column=0, padx=10, pady=8, sticky="ew")
            btn.bind("<Enter>", lambda e, b=btn: on_enter(b))
            btn.bind("<Leave>", lambda e, b=btn: on_leave(b))

        button_frame.columnconfigure(0, weight=1)
        ttk.Separator(self.content_frame, orient="horizontal").pack(fill="x", pady=20)
        
    def search_readers_gui(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Tìm kiếm độc giả", font=("Arial", 20, "bold"), fg="#023020", bg="#FFFAF0").pack(pady=20)

        input_frame = tk.Frame(self.content_frame, bg="#FFFAF0")
        input_frame.pack(fill="x", pady=10)
        tk.Label(input_frame, text="Mã độc giả:", font=("Arial", 12), fg="#000000", bg="#FFFAF0").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        search_var = tk.StringVar()
        tk.Entry(input_frame, textvariable=search_var, font=("Arial", 12), width=30).grid(row=0, column=1, padx=5, pady=5, sticky="w")

        canvas = tk.Canvas(self.content_frame, bg="#FFFAF0", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
        result_frame = tk.Frame(canvas, bg="#FFFAF0")
        result_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.create_window((0, 0), window=result_frame, anchor="nw")

        def search_callback(reader, query, result_frame):
            tk.Label(result_frame, text="Lịch sử mượn", font=("Arial", 14, "bold"), fg="#023020", bg="#FFFAF0").pack(fill="x", pady=10)
            columns = ("STT", "Mã tài liệu", "Ngày mượn", "Hạn trả", "Ngày trả", "Trạng thái", "Phí phạt")
            tree = ttk.Treeview(result_frame, columns=columns, show="headings", height=5)
            column_widths = [50, 100, 120, 120, 120, 100, 100]
            for col, width in zip(columns, column_widths):
                tree.heading(col, text=col)
                tree.column(col, width=width, anchor="w")
            tree.pack(fill="both", expand=True)

            style = ttk.Style()
            style.configure("Treeview", background="#FFFAF0", foreground="#708090", fieldbackground="#FFFAF0")
            style.map('Treeview', background=[('selected', '#34495E')], foreground=[('selected', '#FFFFFF')])

            for idx, record in enumerate(reader.get("borrow_history", []), 1):
                tree.insert("", "end", values=(
                    idx,
                    record.get("book_id", "N/A"),
                    record.get("borrow_date", "N/A").split("T")[0] if record.get("borrow_date") else "N/A",
                    record.get("due_date", "N/A").split("T")[0] if record.get("due_date") else "N/A",
                    record.get("return_date", "N/A").split("T")[0] if record.get("return_date") else "N/A",
                    record.get("status", "N/A"),
                    f"{record.get('fine', 0):,.0f} VNĐ"
                ))

        def on_enter(btn): btn.config(bg="#87CAFA", relief="raised")
        def on_leave(btn): btn.config(bg="#FFC0CB", relief="flat")

        btn = tk.Button(
            input_frame,
            text="🔍 Tìm kiếm",
            command=lambda: self.search_reader_common(search_var, result_frame, search_callback),
            font=("Arial", 12, "bold"),
            fg="#023020",
            bg="#708090",
            relief="flat",
            padx=15,
            pady=5
        )
        btn.grid(row=0, column=2, padx=5, pady=5, sticky="w")
        btn.bind("<Enter>", lambda e: on_enter(e.widget))
        btn.bind("<Leave>", lambda e: on_leave(e.widget))

        ttk.Separator(self.content_frame, orient="horizontal").pack(fill="x", pady=20)
        
    def renew_account_gui(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Gia hạn tài khoản", font=("Arial", 20, "bold"), fg="#023020", bg="#FFFAF0").pack(pady=20)

        input_frame = tk.Frame(self.content_frame, bg="#FFFAF0")
        input_frame.pack(fill="x", pady=10)
        tk.Label(input_frame, text="Mã độc giả:", font=("Arial", 12), fg="#000000", bg="#FFFAF0").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        search_var = tk.StringVar()
        tk.Entry(input_frame, textvariable=search_var, font=("Arial", 12), width=30).grid(row=0, column=1, padx=5, pady=5, sticky="w")

        canvas = tk.Canvas(self.content_frame, bg="#FFFAF0", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
        result_frame = tk.Frame(canvas, bg="#FFFAF0")
        result_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.create_window((0, 0), window=result_frame, anchor="nw")

        def renew_callback(reader, query, result_frame):
            status = reader.get("status", "")
            if status == "active":
                tk.Label(result_frame, text="Tài khoản đang hoạt động, không cần gia hạn!", font=("Arial", 12), fg="#2ECC71", bg="#FFFAF0").pack(fill="x", pady=10)
            elif status == "suspended":
                tk.Label(result_frame, text="Tài khoản đã bị tạm khóa, có thể gia hạn.", font=("Arial", 12), fg="#E74C3C", bg="#FFFAF0").pack(fill="x", pady=10)
                def renew():
                    try:
                        self.reader_manager.renew_account(query)
                        messagebox.showinfo("Thành công", "Tài khoản đã được gia hạn!")
                        self.search_reader_common(search_var, result_frame, renew_callback)
                    except ValueError as e:
                        messagebox.showerror("Lỗi", f"Không thể gia hạn: {e}")
                tk.Button(result_frame, text="📅 Gia hạn tài khoản", command=renew, font=("Arial", 12, "bold"), fg="#023020", bg="#708090", relief="flat", padx=15, pady=5).pack(anchor="w", pady=5).bind("<Enter>", lambda e: on_enter(e.widget)).bind("<Leave>", lambda e: on_leave(e.widget))
            else:
                tk.Label(result_frame, text="Trạng thái tài khoản không hợp lệ!", font=("Arial", 12), fg="#E74C3C", bg="#FFFAF0").pack(fill="x", pady=10)

        def on_enter(btn): btn.config(bg="#87CAFA", relief="raised")
        def on_leave(btn): btn.config(bg="#FFC0CB", relief="flat")

        btn = tk.Button(
            input_frame,
            text="🔍 Tìm kiếm",
            command=lambda: self.search_reader_common(search_var, result_frame, renew_callback),
            font=("Arial", 12, "bold"),
            fg="#023020",
            bg="#708090",
            relief="flat",
            padx=15,
            pady=5
        )
        btn.grid(row=0, column=2, padx=5, pady=5, sticky="w")
        btn.bind("<Enter>", lambda e: on_enter(e.widget))
        btn.bind("<Leave>", lambda e: on_leave(e.widget))

        ttk.Separator(self.content_frame, orient="horizontal").pack(fill="x", pady=20)
        
    def suspend_reader_gui(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Tạm khóa tài khoản", font=("Arial", 20, "bold"), fg="#023020", bg="#FFFAF0").pack(pady=20)

        input_frame = tk.Frame(self.content_frame, bg="#FFFAF0")
        input_frame.pack(fill="x", pady=10)
        tk.Label(input_frame, text="Mã độc giả:", font=("Arial", 12), fg="#000000", bg="#FFFAF0").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        search_var = tk.StringVar()
        tk.Entry(input_frame, textvariable=search_var, font=("Arial", 12), width=30).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        tk.Label(input_frame, text="Lý do tạm khóa:", font=("Arial", 12), fg="#000000", bg="#FFFAF0").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        reason_var = tk.StringVar()
        tk.Entry(input_frame, textvariable=reason_var, font=("Arial", 12), width=30).grid(row=1, column=1, padx=5, pady=5, sticky="w")

        canvas = tk.Canvas(self.content_frame, bg="#FFFAF0", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
        result_frame = tk.Frame(canvas, bg="#FFFAF0")
        result_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.create_window((0, 0), window=result_frame, anchor="nw")

        def suspend_callback(reader, query, result_frame):
            status = reader.get("status", "")
            if status == "suspended":
                tk.Label(result_frame, text="Tài khoản đã bị tạm khóa!", font=("Arial", 12), fg="#E74C3C", bg="#FFFAF0").pack(fill="x", pady=10)
            elif status == "active":
                tk.Label(result_frame, text="Tài khoản đang hoạt động, có thể tạm khóa.", font=("Arial", 12), fg="#E67E22", bg="#FFFAF0").pack(fill="x", pady=10)
                def suspend():
                    reason = reason_var.get().strip()
                    if not reason:
                        messagebox.showwarning("Cảnh báo", "Vui lòng nhập lý do tạm khóa!")
                        return
                    try:
                        self.reader_manager.suspend_reader(query, reason)
                        messagebox.showinfo("Thành công", "Tài khoản đã bị tạm khóa!")
                        self.search_reader_common(search_var, result_frame, suspend_callback)
                    except ValueError as e:
                        messagebox.showerror("Lỗi", f"Không thể tạm khóa: {e}")
                tk.Button(result_frame, text="🚫 Tạm khóa tài khoản", command=suspend, font=("Arial", 12, "bold"), fg="#023020", bg="#708090", relief="flat", padx=15, pady=5).pack(anchor="w", pady=5).bind("<Enter>", lambda e: on_enter(e.widget)).bind("<Leave>", lambda e: on_leave(e.widget))
            else:
                tk.Label(result_frame, text="Trạng thái tài khoản không hợp lệ!", font=("Arial", 12), fg="#E74C3C", bg="#FFFAF0").pack(fill="x", pady=10)

        def on_enter(btn): btn.config(bg="#87CAFA", relief="raised")
        def on_leave(btn): btn.config(bg="#FFC0CB", relief="flat")

        btn = tk.Button(
            input_frame,
            text="🔍 Tìm kiếm",
            command=lambda: self.search_reader_common(search_var, result_frame, suspend_callback),
            font=("Arial", 12, "bold"),
            fg="#023020",
            bg="#708090",
            relief="flat",
            padx=15,
            pady=5
        )
        btn.grid(row=0, column=2, padx=5, pady=5, sticky="w")
        btn.bind("<Enter>", lambda e: on_enter(e.widget))
        btn.bind("<Leave>", lambda e: on_leave(e.widget))

        ttk.Separator(self.content_frame, orient="horizontal").pack(fill="x", pady=20)
 
    def delete_reader_gui(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Xóa độc giả", font=("Arial", 20, "bold"), fg="#023020", bg="#FFFAF0").pack(pady=20)

        input_frame = tk.Frame(self.content_frame, bg="#FFFAF0")
        input_frame.pack(fill="x", pady=10)
        tk.Label(input_frame, text="Mã độc giả:", font=("Arial", 12), fg="#000000", bg="#FFFAF0").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        search_var = tk.StringVar()
        tk.Entry(input_frame, textvariable=search_var, font=("Arial", 12), width=30).grid(row=0, column=1, padx=5, pady=5, sticky="w")

        canvas = tk.Canvas(self.content_frame, bg="#FFFAF0", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
        result_frame = tk.Frame(canvas, bg="#FFFAF0")
        result_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.create_window((0, 0), window=result_frame, anchor="nw")

        def delete_callback(reader, query, result_frame):
            borrowed_books = reader.get("borrowed_books", 0)
            if borrowed_books > 0:
                tk.Label(result_frame, text=f"Không thể xóa! Độc giả đang mượn {borrowed_books} sách.", font=("Arial", 12), fg="#E74C3C", bg="#FFFAF0").pack(fill="x", pady=10)
            else:
                tk.Label(result_frame, text="Cảnh báo: Hành động này sẽ xóa vĩnh viễn thông tin độc giả!", font=("Arial", 12), fg="#E74C3C", bg="#FFFAF0").pack(fill="x", pady=10)

                def delete():
                    if messagebox.askyesno("Xác nhận xóa", "Bạn có chắc chắn muốn xóa độc giả này?"):
                        try:
                            self.reader_manager.delete_reader(query)
                            messagebox.showinfo("Thành công", "Độc giả đã được xóa!")
                            for widget in result_frame.winfo_children():
                                widget.destroy()
                            tk.Label(result_frame, text="Độc giả đã được xóa!", font=("Arial", 12), fg="#2ECC71", bg="#FFFAF0").pack(fill="x", pady=20)
                        except ValueError as e:
                            messagebox.showerror("Lỗi", f"Không thể xóa: {e}")

                tk.Button(result_frame, text="🗑️ Xóa độc giả", command=delete, font=("Arial", 12, "bold"), fg="#023020", bg="#708090", relief="flat", padx=15, pady=5).pack(anchor="w", pady=5).bind("<Enter>", lambda e: on_enter(e.widget)).bind("<Leave>", lambda e: on_leave(e.widget))

        def on_enter(btn): btn.config(bg="#87CAFA", relief="raised")
        def on_leave(btn): btn.config(bg="#FFC0CB", relief="flat")

        tk.Button(input_frame, text="🔍 Tìm kiếm", command=lambda: self.search_reader_common(search_var, result_frame, delete_callback), font=("Arial", 12, "bold"), fg="#023020", bg="#708090", relief="flat", padx=15, pady=5).grid(row=0, column=2, padx=5, pady=5, sticky="w").bind("<Enter>", lambda e: on_enter(e.widget)).bind("<Leave>", lambda e: on_leave(e.widget))
        ttk.Separator(self.content_frame, orient="horizontal").pack(fill="x", pady=20)   
  
    def update_reader_info_gui(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Cập nhật thông tin độc giả", font=("Arial", 20, "bold"), fg="#023020", bg="#FFFAF0").pack(pady=20)

        input_frame = tk.Frame(self.content_frame, bg="#FFFAF0")
        input_frame.pack(fill="x", pady=10)
        tk.Label(input_frame, text="Mã độc giả:", font=("Arial", 12), fg="#000000", bg="#FFFAF0").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        search_var = tk.StringVar()
        tk.Entry(input_frame, textvariable=search_var, font=("Arial", 12), width=30).grid(row=0, column=1, padx=5, pady=5, sticky="w")

        canvas = tk.Canvas(self.content_frame, bg="#FFFAF0", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
        result_frame = tk.Frame(canvas, bg="#FFFAF0")
        result_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.create_window((0, 0), window=result_frame, anchor="nw")

        def search():
            query = search_var.get().strip()
            if not query:
                messagebox.showwarning("Cảnh báo", "Vui lòng nhập mã độc giả!")
                return

            for widget in result_frame.winfo_children():
                widget.destroy()

            reader = self.reader_manager.get_reader_details(query)
            if reader:
                edit_frame = tk.Frame(result_frame, bg="#FFFAF0")
                edit_frame.pack(fill="x", pady=5)

                full_name_var = tk.StringVar(value=reader.get("full_name", ""))
                email_var = tk.StringVar(value=reader.get("email", ""))
                phone_var = tk.StringVar(value=reader.get("phone", ""))
                id_card_var = tk.StringVar(value=reader.get("id_card", ""))
                dob_var = tk.StringVar(value=reader.get("dob", ""))
                student_id_var = tk.StringVar(value=reader.get("student_id", ""))
                employee_id_var = tk.StringVar(value=reader.get("employee_id", ""))
                reader_type_var = tk.StringVar(value=reader.get("reader_type", ""))

                fields = [
                    ("Họ tên", full_name_var),
                    ("Email", email_var),
                    ("Số điện thoại", phone_var),
                    ("CMND/CCCD", id_card_var),
                    ("Ngày sinh", dob_var),
                ]

                code_frame = tk.Frame(edit_frame, bg="#FFFAF0")
                code_frame.grid(row=len(fields), column=0, columnspan=2, sticky="w", padx=5, pady=2)

                def update_code_field():
                    for widget in code_frame.winfo_children():
                        widget.destroy()
                    reader_type = reader_type_var.get()
                    label = "Mã sinh viên" if reader_type == "Sinh viên" else "Mã Giảng viên/Cán bộ"
                    var = student_id_var if reader_type == "Sinh viên" else employee_id_var
                    tk.Label(code_frame, text=f"{label}:", font=("Arial", 11, "bold"), fg="#023020", bg="#FFFAF0").grid(row=0, column=0, sticky="w", padx=5, pady=2)
                    tk.Entry(code_frame, textvariable=var, font=("Arial", 11), width=30).grid(row=0, column=1, sticky="w", padx=5, pady=2)

                for idx, (label, var) in enumerate(fields):
                    tk.Label(edit_frame, text=f"{label}:", font=("Arial", 11, "bold"), fg="#023020", bg="#FFFAF0").grid(row=idx, column=0, sticky="w", padx=5, pady=2)
                    tk.Entry(edit_frame, textvariable=var, font=("Arial", 11), width=30).grid(row=idx, column=1, sticky="w", padx=5, pady=2)

                tk.Label(edit_frame, text="Loại độc giả:", font=("Arial", 11, "bold"), fg="#023020", bg="#FFFAF0").grid(row=len(fields) + 1, column=0, sticky="w", padx=5, pady=2)
                reader_types = [rt["type"] for rt in getattr(self.reader_manager, "reader_types", [])] or ["Sinh viên", "Giảng viên/Cán bộ"]
                reader_type_combobox = ttk.Combobox(edit_frame, textvariable=reader_type_var, values=reader_types, state="readonly", font=("Arial", 11), width=27)
                reader_type_combobox.grid(row=len(fields) + 1, column=1, sticky="w", padx=5, pady=2)
                reader_type_combobox.bind("<<ComboboxSelected>>", lambda e: update_code_field())

                update_code_field()

                def update():
                    updates = {}
                    if full_name_var.get().strip() != reader.get("full_name", ""):
                        updates["full_name"] = full_name_var.get().strip()
                    if email_var.get().strip() != reader.get("email", ""):
                        updates["email"] = email_var.get().strip()
                    if phone_var.get().strip() != reader.get("phone", ""):
                        updates["phone"] = phone_var.get().strip()
                    if id_card_var.get().strip() != reader.get("id_card", ""):
                        updates["id_card"] = id_card_var.get().strip()
                    if dob_var.get().strip() != reader.get("dob", ""):
                        updates["dob"] = dob_var.get().strip()
                    if reader_type_var.get() == "Sinh viên" and student_id_var.get().strip() != reader.get("student_id", ""):
                        updates["student_id"] = student_id_var.get().strip()
                    if reader_type_var.get() == "Giảng viên/Cán bộ" and employee_id_var.get().strip() != reader.get("employee_id", ""):
                        updates["employee_id"] = employee_id_var.get().strip()
                    if reader_type_var.get().strip() != reader.get("reader_type", ""):
                        updates["reader_type"] = reader_type_var.get().strip()

                    if not updates:
                        messagebox.showinfo("Thông báo", "Không có thông tin nào được cập nhật!")
                        return

                    try:
                        self.reader_manager.update_reader(query, updates)
                        messagebox.showinfo("Thành công", "Thông tin độc giả đã được cập nhật!")
                        search()
                    except ValueError as e:
                        messagebox.showerror("Lỗi", f"Không thể cập nhật: {e}")

                update_button = tk.Button(result_frame, text="💾 Cập nhật thông tin", command=update, font=("Arial", 12, "bold"), fg="#023020", bg="#708090", relief="flat", padx=15, pady=5)
                update_button.pack(anchor="w", pady=10)
                update_button.bind("<Enter>", lambda e: on_enter(update_button))
                update_button.bind("<Leave>", lambda e: on_leave(update_button))
            else:
                tk.Label(result_frame, text="Không tìm thấy độc giả!", font=("Arial", 12), fg="#E74C3C", bg="#FFFAF0").pack(fill="x", pady=20)

        def on_enter(btn): btn.config(bg="#87CAFA", relief="raised")
        def on_leave(btn): btn.config(bg="#FFC0CB", relief="flat")

        tk.Button(input_frame, text="🔍 Tìm kiếm", command=search, font=("Arial", 12, "bold"), fg="#023020", bg="#708090", relief="flat", padx=15, pady=5).grid(row=0, column=2, padx=5, pady=5, sticky="w").bind("<Enter>", lambda e: on_enter(e.widget)).bind("<Leave>", lambda e: on_leave(e.widget))
        ttk.Separator(self.content_frame, orient="horizontal").pack(fill="x", pady=20)
    
    def restore_account_gui(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Khôi phục tài khoản", font=("Arial", 20, "bold"), fg="#023020", bg="#FFFAF0").pack(pady=20)

        input_frame = tk.Frame(self.content_frame, bg="#FFFAF0")
        input_frame.pack(fill="x", pady=10)
        tk.Label(input_frame, text="Mã độc giả:", font=("Arial", 12), fg="#000000", bg="#FFFAF0").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        search_var = tk.StringVar()
        tk.Entry(input_frame, textvariable=search_var, font=("Arial", 12), width=30).grid(row=0, column=1, padx=5, pady=5, sticky="w")

        canvas = tk.Canvas(self.content_frame, bg="#FFFAF0", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
        result_frame = tk.Frame(canvas, bg="#FFFAF0")
        result_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.create_window((0, 0), window=result_frame, anchor="nw")

        def restore_callback(reader, query, result_frame):
            status = reader.get("status", "")
            if status not in ["suspended", "expired"]:
                tk.Label(result_frame, text="Tài khoản không ở trạng thái cần khôi phục!", font=("Arial", 12), fg="#E74C3C", bg="#FFFAF0").pack(fill="x", pady=10)
            else:
                fine_amount = reader.get("fine_amount", 0)
                annual_fee_paid = reader.get("annual_fee_paid", False)

                payment_frame = tk.Frame(result_frame, bg="#FFFAF0")
                payment_frame.pack(fill="x", pady=5)

                paid_fine_var = tk.BooleanVar(value=False)
                paid_annual_fee_var = tk.BooleanVar(value=False)

                if fine_amount > 0:
                    tk.Checkbutton(payment_frame, text=f"Đã thanh toán phí phạt ({fine_amount:,.0f} VNĐ)", variable=paid_fine_var, font=("Arial", 11), fg="#023020", bg="#FFFAF0").pack(fill="x", padx=5, pady=2)
                if not annual_fee_paid:
                    tk.Checkbutton(payment_frame, text="Đã thanh toán phí thường niên", variable=paid_annual_fee_var, font=("Arial", 11), fg="#023020", bg="#FFFAF0").pack(fill="x", padx=5, pady=2)

                def restore():
                    try:
                        self.reader_manager.restore_account(query, paid_fine=paid_fine_var.get(), paid_annual_fee=paid_annual_fee_var.get())
                        messagebox.showinfo("Thành công", "Tài khoản đã được khôi phục!")
                        self.search_reader_common(search_var, result_frame, restore_callback)
                    except ValueError as e:
                        messagebox.showerror("Lỗi", f"Không thể khôi phục: {e}")

                tk.Button(result_frame, text="🔄 Khôi phục tài khoản", command=restore, font=("Arial", 12, "bold"), fg="#023020", bg="#708090", relief="flat", padx=15, pady=5).pack(anchor="w", pady=5).bind("<Enter>", lambda e: on_enter(e.widget)).bind("<Leave>", lambda e: on_leave(e.widget))

        def on_enter(btn): btn.config(bg="#87CAFA", relief="raised")
        def on_leave(btn): btn.config(bg="#FFC0CB", relief="flat")

        tk.Button(input_frame, text="🔍 Tìm kiếm", command=lambda: self.search_reader_common(search_var, result_frame, restore_callback), font=("Arial", 12, "bold"), fg="#023020", bg="#708090", relief="flat", padx=15, pady=5).grid(row=0, column=2, padx=5, pady=5, sticky="w").bind("<Enter>", lambda e: on_enter(e.widget)).bind("<Leave>", lambda e: on_leave(e.widget))
        ttk.Separator(self.content_frame, orient="horizontal").pack(fill="x", pady=20)

#////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
    def manage_documents(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Quản lý tài liệu", font=("Arial", 20, "bold"), fg="#023020", bg="#FFFAF0").pack(pady=20)

        button_frame = tk.Frame(self.content_frame, bg="#FFFAF0")
        button_frame.pack(pady=10, padx=20, fill="both", expand=True)

        buttons = [
            ("📖 Thêm tài liệu mới", self.add_document_gui),
            ("🗑️ Xóa tài liệu", self.delete_document_gui),
            ("💾 Cập nhật thông tin", self.update_document_gui),
            ("🔄 Khôi phục tài liệu", self.restore_document_gui),
            ("⬅ Quay lại", self.clear_content)
        ]

        def on_enter(btn): btn.config(bg="#87CAFA", relief="raised")
        def on_leave(btn): btn.config(bg="#FFC0CB", relief="flat")

        for idx, (text, cmd) in enumerate(buttons):
            btn = tk.Button(button_frame, text=text, command=cmd, font=("Arial", 14, "bold"), fg="#023020", bg="#708090", relief="flat", anchor="w", padx=20, pady=10, width=30)
            btn.grid(row=idx, column=0, padx=10, pady=8, sticky="ew")
            btn.bind("<Enter>", lambda e, b=btn: on_enter(b))
            btn.bind("<Leave>", lambda e, b=btn: on_leave(b))

        button_frame.columnconfigure(0, weight=1)
        ttk.Separator(self.content_frame, orient="horizontal").pack(fill="x", pady=20)
 
    def add_document_gui(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Thêm tài liệu mới", font=("Arial", 20, "bold"), fg="#023020", bg="#FFFAF0").pack(pady=20)

        input_frame = tk.Frame(self.content_frame, bg="#FFFAF0")
        input_frame.pack(fill="x", pady=10)

        title_var = tk.StringVar()
        category_var = tk.StringVar()
        quantity_var = tk.StringVar(value="0")
        special_var = tk.BooleanVar(value=False)

        tk.Label(input_frame, text="Tên tài liệu:", font=("Arial", 12), fg="#000000", bg="#FFFAF0").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        tk.Entry(input_frame, textvariable=title_var, font=("Arial", 12), width=30).grid(row=0, column=1, padx=5, pady=5, sticky="w")

        tk.Label(input_frame, text="Lĩnh vực:", font=("Arial", 12), fg="#000000", bg="#FFFAF0").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        categories = getattr(self.doc_manager, "categories")  # Giả định danh sách lĩnh vực
        category_names = [cat['name'] for cat in categories]  # Lấy chỉ các giá trị 'name'
        ttk.Combobox(input_frame, textvariable=category_var, values=category_names, font=("Arial", 12), width=27).grid(row=1, column=1, padx=5, pady=5, sticky="w")

        tk.Label(input_frame, text="Số lượng:", font=("Arial", 12), fg="#000000", bg="#FFFAF0").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        tk.Entry(input_frame, textvariable=quantity_var, font=("Arial", 12), width=30).grid(row=2, column=1, padx=5, pady=5, sticky="w")

        tk.Checkbutton(input_frame, text="Tài liệu đặc biệt", variable=special_var, font=("Arial", 12), fg="#023020", bg="#FFFAF0").grid(row=3, column=1, padx=5, pady=5, sticky="w")

        result_frame = tk.Frame(self.content_frame, bg="#FFFAF0")
        result_frame.pack(fill="x", pady=10)

        def add_document():
            title = title_var.get().strip()
            category = category_var.get().strip()
            try:
                quantity = int(quantity_var.get().strip())
            except ValueError:
                messagebox.showerror("Lỗi", "Số lượng phải là số nguyên!")
                return

            for widget in result_frame.winfo_children():
                widget.destroy()

            try:
                document = self.doc_manager.add_document(title, category, quantity, special_var.get())
                tk.Label(result_frame, text=f"Thêm tài liệu thành công! Mã tài liệu: {document['doc_id']}", font=("Arial", 12), fg="#27AE60", bg="#FFFAF0").pack(fill="x", pady=10)
                title_var.set("")
                category_var.set("")
                quantity_var.set("0")
                special_var.set(False)
            except ValueError as e:
                tk.Label(result_frame, text=f"Lỗi: {str(e)}", font=("Arial", 12), fg="#E74C3C", bg="#FFFAF0").pack(fill="x", pady=10)

        def on_enter(btn): btn.config(bg="#87CAFA", relief="raised")
        def on_leave(btn): btn.config(bg="#FFC0CB", relief="flat")

        btn = tk.Button(
            input_frame,
            text="📖 Thêm tài liệu",
            command=add_document,
            font=("Arial", 12, "bold"),
            fg="#023020",
            bg="#708090",
            relief="flat",
            padx=15,
            pady=5
        )
        btn.grid(row=4, column=1, padx=5, pady=5, sticky="w")
        btn.bind("<Enter>", lambda e: on_enter(e.widget))
        btn.bind("<Leave>", lambda e: on_leave(e.widget))

        ttk.Separator(self.content_frame, orient="horizontal").pack(fill="x", pady=20) 
    
    def search_document_common(self, search_var, result_frame, callback, include_deleted=False):
        query = search_var.get().strip()
        if not query:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập mã tài liệu!")
            return

        for widget in result_frame.winfo_children():
            widget.destroy()

        document = self.doc_manager.get_document_details(query, include_deleted=include_deleted)
        if document:
            info_frame = tk.Frame(result_frame, bg="#FFFAF0")
            info_frame.pack(fill="x", pady=5)

            fields = [
                ("Mã tài liệu", document.get("doc_id", "N/A")),
                ("Tên tài liệu", document.get("title", "N/A")),
                ("Lĩnh vực", document.get("category", "N/A")),
                ("Số lượng", document.get("SoLuong", 0)),
                ("Tài liệu đặc biệt", "Có" if document.get("DacBiet", False) else "Không"),
                ("Trạng thái", document.get("status", "N/A")),
                ("Số lượng sẵn có", document.get("AvailableQuantity", 0)),
                ("Đã xóa", "Có" if document.get("deleted", False) else "Không"),
            ]

            for idx, (label, value) in enumerate(fields):
                tk.Label(info_frame, text=f"{label}:", font=("Arial", 11, "bold"), fg="#023020", bg="#FFFAF0").grid(row=idx, column=0, sticky="w", padx=5, pady=2)
                tk.Label(info_frame, text=value, font=("Arial", 11), fg="#34495E", bg="#FFFAF0").grid(row=idx, column=1, sticky="w", padx=5, pady=2)

            callback(document, query, result_frame)
        else:
            tk.Label(result_frame, text="Không tìm thấy tài liệu!", font=("Arial", 12), fg="#E74C3C", bg="#FFFAF0").pack(fill="x", pady=20)

    def delete_document_gui(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Xóa tài liệu", font=("Arial", 20, "bold"), fg="#023020", bg="#FFFAF0").pack(pady=20)

        input_frame = tk.Frame(self.content_frame, bg="#FFFAF0")
        input_frame.pack(fill="x", pady=10)
        tk.Label(input_frame, text="Mã tài liệu:", font=("Arial", 12), fg="#000000", bg="#FFFAF0").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        search_var = tk.StringVar()
        tk.Entry(input_frame, textvariable=search_var, font=("Arial", 12), width=30).grid(row=0, column=1, padx=5, pady=5, sticky="w")

        canvas = tk.Canvas(self.content_frame, bg="#FFFAF0", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
        result_frame = tk.Frame(canvas, bg="#FFFAF0")
        result_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.create_window((0, 0), window=result_frame, anchor="nw")

        def delete_callback(document, query, result_frame):
            if document.get('status') == "unavailable" and document.get('AvailableQuantity', 0) > 0:
                tk.Label(result_frame, text="Không thể xóa! Tài liệu đang được mượn.", font=("Arial", 12), fg="#E74C3C", bg="#FFFAF0").pack(fill="x", pady=10)
            else:
                tk.Label(result_frame, text="Cảnh báo: Hành động này sẽ xóa vĩnh viễn tài liệu!", font=("Arial", 12), fg="#E74C3C", bg="#FFFAF0").pack(fill="x", pady=10)

                def delete():
                    confirm = messagebox.askyesno("Xác nhận xóa", "Bạn có chắc chắn muốn xóa tài liệu này?")
                    if confirm:
                        try:
                            self.doc_manager.delete_document(query)
                            messagebox.showinfo("Thành công", "Tài liệu đã được xóa!")
                            self.search_document_common(search_var, result_frame, delete_callback)
                        except ValueError as e:
                            messagebox.showerror("Lỗi", f"Không thể xóa: {str(e)}")

                tk.Button(result_frame, text="🗑️ Xóa tài liệu", command=delete, font=("Arial", 12, "bold"), fg="#023020", bg="#708090", relief="flat", padx=15, pady=5).pack(anchor="w", pady=5).bind("<Enter>", lambda e: on_enter(e.widget)).bind("<Leave>", lambda e: on_leave(e.widget))

        def on_enter(btn): btn.config(bg="#87CAFA", relief="raised")
        def on_leave(btn): btn.config(bg="#FFC0CB", relief="flat")

        tk.Button(input_frame, text="🔍 Tìm kiếm", command=lambda: self.search_document_common(search_var, result_frame, delete_callback), font=("Arial", 12, "bold"), fg="#023020", bg="#708090", relief="flat", padx=15, pady=5).grid(row=0, column=2, padx=5, pady=5, sticky="w").bind("<Enter>", lambda e: on_enter(e.widget)).bind("<Leave>", lambda e: on_leave(e.widget))
        ttk.Separator(self.content_frame, orient="horizontal").pack(fill="x", pady=20)

    def restore_document_gui(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Khôi phục tài liệu", font=("Arial", 20, "bold"), fg="#023020", bg="#FFFAF0").pack(pady=20)

        input_frame = tk.Frame(self.content_frame, bg="#FFFAF0")
        input_frame.pack(fill="x", pady=10)
        tk.Label(input_frame, text="Mã tài liệu:", font=("Arial", 12), fg="#000000", bg="#FFFAF0").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        search_var = tk.StringVar()
        tk.Entry(input_frame, textvariable=search_var, font=("Arial", 12), width=30).grid(row=0, column=1, padx=5, pady=5, sticky="w")

        canvas = tk.Canvas(self.content_frame, bg="#FFFAF0", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
        result_frame = tk.Frame(canvas, bg="#FFFAF0")
        result_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.create_window((0, 0), window=result_frame, anchor="nw")

        def restore_callback(document, query, result_frame):
            if not document.get('deleted', False):
                tk.Label(result_frame, text="Tài liệu chưa bị xóa, không cần khôi phục!", font=("Arial", 12), fg="#E74C3C", bg="#FFFAF0").pack(fill="x", pady=10)
            else:
                def restore():
                    try:
                        self.doc_manager.restore_document(query)
                        messagebox.showinfo("Thành công", "Tài liệu đã được khôi phục!")
                        self.search_document_common(search_var, result_frame, restore_callback, include_deleted=True)
                    except ValueError as e:
                        messagebox.showerror("Lỗi", f"Không thể khôi phục: {str(e)}")

                tk.Button(result_frame, text="🔄 Khôi phục tài liệu", command=restore, font=("Arial", 12, "bold"), fg="#023020", bg="#708090", relief="flat", padx=15, pady=5).pack(anchor="w", pady=5).bind("<Enter>", lambda e: on_enter(e.widget)).bind("<Leave>", lambda e: on_leave(e.widget))

        def on_enter(btn): btn.config(bg="#87CAFA", relief="raised")
        def on_leave(btn): btn.config(bg="#FFC0CB", relief="flat")

        tk.Button(input_frame, text="🔍 Tìm kiếm", command=lambda: self.search_document_common(search_var, result_frame, restore_callback, include_deleted=True), font=("Arial", 12, "bold"), fg="#023020", bg="#708090", relief="flat", padx=15, pady=5).grid(row=0, column=2, padx=5, pady=5, sticky="w").bind("<Enter>", lambda e: on_enter(e.widget)).bind("<Leave>", lambda e: on_leave(e.widget))
        ttk.Separator(self.content_frame, orient="horizontal").pack(fill="x", pady=20)
  
    def update_document_gui(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Cập nhật thông tin tài liệu", font=("Arial", 20, "bold"), fg="#023020", bg="#FFFAF0").pack(pady=20)

        input_frame = tk.Frame(self.content_frame, bg="#FFFAF0")
        input_frame.pack(fill="x", pady=10)
        tk.Label(input_frame, text="Mã tài liệu:", font=("Arial", 12), fg="#000000", bg="#FFFAF0").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        search_var = tk.StringVar()
        tk.Entry(input_frame, textvariable=search_var, font=("Arial", 12), width=30).grid(row=0, column=1, padx=5, pady=5, sticky="w")

        canvas = tk.Canvas(self.content_frame, bg="#FFFAF0", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
        result_frame = tk.Frame(canvas, bg="#FFFAF0")
        result_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.create_window((0, 0), window=result_frame, anchor="nw")

        def search():
            query = search_var.get().strip()
            if not query:
                messagebox.showwarning("Cảnh báo", "Vui lòng nhập mã tài liệu!")
                return

            for widget in result_frame.winfo_children():
                widget.destroy()

            document = self.doc_manager.get_document_details(query)
            if document:
                edit_frame = tk.Frame(result_frame, bg="#FFFAF0")
                edit_frame.pack(fill="x", pady=5)

                title_var = tk.StringVar(value=document.get("title", ""))
                category_var = tk.StringVar(value=document.get("category", ""))
                so_luong_var = tk.StringVar(value=str(document.get("SoLuong", 0)))
                dac_biet_var = tk.BooleanVar(value=document.get("DacBiet", False))

                fields = [
                    ("Mã tài liệu", document.get("doc_id", "N/A"), None),
                    ("Tên tài liệu", title_var, tk.Entry),
                    ("Lĩnh vực", category_var, ttk.Combobox),
                    ("Số lượng", so_luong_var, tk.Entry),
                    ("Tài liệu đặc biệt", dac_biet_var, tk.Checkbutton),
                    ("Trạng thái", document.get("status", "N/A"), None),
                ]

                categories = getattr(self.doc_manager, "categories", ["Khoa học", "Công nghệ", "Văn học", "Lịch sử"])

                for idx, (label, var, widget_type) in enumerate(fields):
                    tk.Label(edit_frame, text=f"{label}:", font=("Arial", 11, "bold"), fg="#023020", bg="#FFFAF0").grid(row=idx, column=0, sticky="w", padx=5, pady=2)
                    if widget_type == tk.Entry:
                        tk.Entry(edit_frame, textvariable=var, font=("Arial", 11), width=30).grid(row=idx, column=1, sticky="w", padx=5, pady=2)
                    elif widget_type == ttk.Combobox:
                        combobox = ttk.Combobox(edit_frame, textvariable=var, values=categories, font=("Arial", 11), width=27)
                        combobox.grid(row=idx, column=1, sticky="w", padx=5, pady=2)
                    elif widget_type == tk.Checkbutton:
                        tk.Checkbutton(edit_frame, variable=var, font=("Arial", 11), fg="#023020", bg="#FFFAF0").grid(row=idx, column=1, sticky="w", padx=5, pady=2)
                    else:
                        tk.Label(edit_frame, text=var, font=("Arial", 11), fg="#34495E", bg="#FFFAF0").grid(row=idx, column=1, sticky="w", padx=5, pady=2)

                def update():
                    updates = {}
                    if title_var.get().strip() != document.get("title", ""):
                        updates["title"] = title_var.get().strip()
                    if category_var.get().strip() != document.get("category", ""):
                        updates["category"] = category_var.get().strip()
                    if so_luong_var.get().strip() != str(document.get("SoLuong", 0)):
                        try:
                            updates["SoLuong"] = int(so_luong_var.get().strip())
                        except ValueError:
                            messagebox.showerror("Lỗi", "Số lượng phải là số nguyên!")
                            return
                    if dac_biet_var.get() != document.get("DacBiet", False):
                        updates["DacBiet"] = dac_biet_var.get()

                    if not updates:
                        messagebox.showinfo("Thông báo", "Không có thông tin nào được cập nhật!")
                        return

                    try:
                        self.doc_manager.update_document(query, updates)
                        messagebox.showinfo("Thành công", "Thông tin tài liệu đã được cập nhật!")
                        search()
                    except ValueError as e:
                        messagebox.showerror("Lỗi", f"Không thể cập nhật: {e}")

                tk.Button(result_frame, text="💾 Cập nhật", command=update, font=("Arial", 12, "bold"), fg="#023020", bg="#708090", relief="flat", padx=15, pady=5).pack(anchor="w", pady=5).bind("<Enter>", lambda e: on_enter(e.widget)).bind("<Leave>", lambda e: on_leave(e.widget))
            else:
                tk.Label(result_frame, text="Không tìm thấy tài liệu!", font=("Arial", 12), fg="#E74C3C", bg="#FFFAF0").pack(fill="x", pady=20)

        def on_enter(btn): btn.config(bg="#87CAFA", relief="raised")
        def on_leave(btn): btn.config(bg="#FFC0CB", relief="flat")

        btn_search = tk.Button(
            input_frame,
            text="🔍 Tìm kiếm",
            command=search,
            font=("Arial", 12, "bold"),
            fg="#023020",
            bg="#708090",
            relief="flat",
            padx=15,
            pady=5
        )
        btn_search.grid(row=0, column=2, padx=5, pady=5, sticky="w")
        btn_search.bind("<Enter>", lambda e: on_enter(e.widget))
        btn_search.bind("<Leave>", lambda e: on_leave(e.widget))

        ttk.Separator(self.content_frame, orient="horizontal").pack(fill="x", pady=20)

#////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
    def manage_borrowing(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Quản lý mượn trả", font=("Arial", 20, "bold"), fg="#023020", bg="#FFFAF0").pack(pady=20)

        button_frame = tk.Frame(self.content_frame, bg="#FFFAF0")
        button_frame.pack(pady=10, padx=20, fill="both", expand=True)

        buttons = [
            ("🔍 Tìm kiếm phiếu mượn", self.search_borrow_records_gui),
            ("🔍 Tìm kiếm phiếu trả", self.search_return_records_gui),
            ("📋 Xem tất cả phiếu trả", self.show_all_return_records_gui),
            ("⏰ Xem phiếu mượn quá hạn", self.show_overdue_records_gui),
            ("📌 Xem phiếu mượn chưa trả", self.show_unreturned_records_gui),
            ("📅 Gia hạn thời gian mượn", self.extend_borrow_period_gui),
            ("⬅ Quay lại", self.clear_content)
        ]

        def on_enter(btn): btn.config(bg="#87CAFA", relief="raised")
        def on_leave(btn): btn.config(bg="#FFC0CB", relief="flat")

        for idx, (text, cmd) in enumerate(buttons):
            btn = tk.Button(button_frame, text=text, command=cmd, font=("Arial", 14, "bold"), fg="#023020", bg="#708090", relief="flat", anchor="w", padx=20, pady=10, width=30)
            btn.grid(row=idx, column=0, padx=10, pady=8, sticky="ew")
            btn.bind("<Enter>", lambda e, b=btn: on_enter(b))
            btn.bind("<Leave>", lambda e, b=btn: on_leave(b))

        button_frame.columnconfigure(0, weight=1)
        ttk.Separator(self.content_frame, orient="horizontal").pack(fill="x", pady=20)

    def display_borrow_records(self, result_frame, records, empty_message="Không có phiếu mượn!"):
        for widget in result_frame.winfo_children():
            widget.destroy()

        if records:
            columns = ["STT", "Mã phiếu mượn", "Mã độc giả", "Ngày mượn", "Hạn trả", "Số lượng", "Trạng thái"]
            tree = ttk.Treeview(result_frame, columns=columns, show="headings", height=10)

            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, anchor="w", width=120)

            for record in records:
                try:
                    borrow_date = datetime.fromisoformat(record["borrow_date"]).strftime("%Y-%m-%d")
                    due_date = datetime.fromisoformat(record["due_date"]).strftime("%Y-%m-%d")
                except (ValueError, TypeError):
                    borrow_date = record["borrow_date"]
                    due_date = record["due_date"]

                tree.insert("", "end", values=(
                    record["stt"],
                    record["borrow_id"],
                    record["reader_id"],
                    borrow_date,
                    due_date,
                    record["quantity"],
                    record["status"]
                ))

            tree_scroll_y = ttk.Scrollbar(result_frame, orient="vertical", command=tree.yview)
            tree_scroll_x = ttk.Scrollbar(result_frame, orient="horizontal", command=tree.xview)
            tree.configure(yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)
            tree_scroll_y.pack(side="right", fill="y")
            tree_scroll_x.pack(side="bottom", fill="x")
            tree.pack(fill="both", expand=True, pady=10)
        else:
            tk.Label(result_frame, text=empty_message, font=("Arial", 12), fg="#E74C3C", bg="#FFFAF0").pack(fill="x", pady=20)

    def search_borrow_common(self, borrow_id_var, reader_id_var, result_frame, callback=None):
        borrow_id = borrow_id_var.get().strip() or None
        reader_id = reader_id_var.get().strip() or None

        if not borrow_id and not reader_id:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập ít nhất một tiêu chí tìm kiếm!")
            return

        records = self.borrowing_manager.search_borrow_records(borrow_id, reader_id)
        self.display_borrow_records(result_frame, records)
        if callback and records:
            callback(records, result_frame)

    def search_borrow_records_gui(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Tìm kiếm phiếu mượn", font=("Arial", 20, "bold"), fg="#023020", bg="#FFFAF0").pack(pady=20)

        input_frame = tk.Frame(self.content_frame, bg="#FFFAF0")
        input_frame.pack(fill="x", pady=10)
        tk.Label(input_frame, text="Mã phiếu mượn:", font=("Arial", 12), fg="#000000", bg="#FFFAF0").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        borrow_id_var = tk.StringVar()
        tk.Entry(input_frame, textvariable=borrow_id_var, font=("Arial", 12), width=20).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        tk.Label(input_frame, text="Mã độc giả:", font=("Arial", 12), fg="#000000", bg="#FFFAF0").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        reader_id_var = tk.StringVar()
        tk.Entry(input_frame, textvariable=reader_id_var, font=("Arial", 12), width=20).grid(row=1, column=1, padx=5, pady=5, sticky="w")

        canvas = tk.Canvas(self.content_frame, bg="#FFFAF0", highlightthickness=0)
        scrollbar_y = ttk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
        scrollbar_x = ttk.Scrollbar(self.content_frame, orient="horizontal", command=canvas.xview)
        result_frame = tk.Frame(canvas, bg="#FFFAF0")
        result_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar_y.pack(side="right", fill="y")
        scrollbar_x.pack(side="bottom", fill="x")
        canvas.create_window((0, 0), window=result_frame, anchor="nw")

        def on_enter(btn): btn.config(bg="#34495E", relief="raised")
        def on_leave(btn): btn.config(bg="#708090", relief="flat")

        tk.Button(input_frame, text="🔍 Tìm kiếm", command=lambda: self.search_borrow_common(borrow_id_var, reader_id_var, result_frame), font=("Arial", 12, "bold"), fg="#023020", bg="#708090", relief="flat", padx=15, pady=5).grid(row=0, column=2, padx=5, pady=5, sticky="w").bind("<Enter>", lambda e: on_enter(e.widget)).bind("<Leave>", lambda e: on_leave(e.widget))
        ttk.Separator(self.content_frame, orient="horizontal").pack(fill="x", pady=20)
 
    def show_overdue_records_gui(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Danh sách phiếu mượn quá hạn", font=("Arial", 20, "bold"), fg="#023020", bg="#FFFAF0").pack(pady=20)

        canvas = tk.Canvas(self.content_frame, bg="#FFFAF0", highlightthickness=0)
        scrollbar_y = ttk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
        scrollbar_x = ttk.Scrollbar(self.content_frame, orient="horizontal", command=canvas.xview)
        result_frame = tk.Frame(canvas, bg="#FFFAF0")
        result_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar_y.pack(side="right", fill="y")
        scrollbar_x.pack(side="bottom", fill="x")
        canvas.create_window((0, 0), window=result_frame, anchor="nw")

        records = self.borrowing_manager.get_overdue_borrow_records()
        self.display_borrow_records(result_frame, records)

        def on_enter(btn): btn.config(bg="#34495E", relief="raised")
        def on_leave(btn): btn.config(bg="#708090", relief="flat")
        ttk.Separator(self.content_frame, orient="horizontal").pack(fill="x", pady=20)
  
    def show_unreturned_records_gui(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Danh sách phiếu mượn chưa trả", font=("Arial", 20, "bold"), fg="#023020", bg="#FFFAF0").pack(pady=20)

        canvas = tk.Canvas(self.content_frame, bg="#FFFAF0", highlightthickness=0)
        scrollbar_y = ttk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
        scrollbar_x = ttk.Scrollbar(self.content_frame, orient="horizontal", command=canvas.xview)
        result_frame = tk.Frame(canvas, bg="#FFFAF0")
        result_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar_y.pack(side="right", fill="y")
        scrollbar_x.pack(side="bottom", fill="x")
        canvas.create_window((0, 0), window=result_frame, anchor="nw")

        records = self.borrowing_manager.get_unreturned_borrow_records()
        self.display_borrow_records(result_frame, records, empty_message="Không có phiếu mượn chưa trả!")

        def on_enter(btn): btn.config(bg="#34495E", relief="raised")
        def on_leave(btn): btn.config(bg="#708090", relief="flat")
        ttk.Separator(self.content_frame, orient="horizontal").pack(fill="x", pady=20)

    def extend_borrow_period_gui(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Gia hạn thời gian mượn", font=("Arial", 20, "bold"), fg="#023020", bg="#FFFAF0").pack(pady=20)

        input_frame = tk.Frame(self.content_frame, bg="#FFFAF0")
        input_frame.pack(fill="x", pady=10)
        tk.Label(input_frame, text="Mã phiếu mượn:", font=("Arial", 12), fg="#000000", bg="#FFFAF0").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        borrow_id_var = tk.StringVar()
        tk.Entry(input_frame, textvariable=borrow_id_var, font=("Arial", 12), width=30).grid(row=0, column=1, padx=5, pady=5, sticky="w")

        canvas = tk.Canvas(self.content_frame, bg="#FFFAF0", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
        result_frame = tk.Frame(canvas, bg="#FFFAF0")
        result_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.create_window((0, 0), window=result_frame, anchor="nw")

        def on_enter(btn): btn.config(bg="#34495E", relief="raised")
        def on_leave(btn): btn.config(bg="#708090", relief="flat")

        def search():
            query = borrow_id_var.get().strip()
            if not query:
                messagebox.showwarning("Cảnh báo", "Vui lòng nhập mã phiếu mượn!")
                return

            for widget in result_frame.winfo_children():
                widget.destroy()

            record = self.borrowing_manager.get_borrow_record_details(query)
            if record:
                info_frame = tk.Frame(result_frame, bg="#FFFAF0")
                info_frame.pack(fill="x", pady=5)

                # Định dạng ngày
                try:
                    borrow_date = datetime.fromisoformat(record["borrow_date"]).strftime("%Y-%m-%d")
                    due_date = datetime.fromisoformat(record["due_date"]).strftime("%Y-%m-%d")
                except (ValueError, TypeError):
                    borrow_date = record["borrow_date"]
                    due_date = record["due_date"]

                fields = [
                    ("Mã phiếu mượn", record.get("borrow_id", "N/A")),
                    ("Mã độc giả", record.get("reader_id", "N/A")),
                    ("Ngày mượn", borrow_date),
                    ("Hạn trả", due_date),
                    ("Số lượng", record.get("quantity", 0)),
                    ("Trạng thái", record.get("status", "N/A")),
                    ("Danh sách tài liệu", ", ".join(record.get("documents", []))),
                ]

                for idx, (label, value) in enumerate(fields):
                    tk.Label(info_frame, text=f"{label}:", font=("Arial", 11, "bold"), fg="#023020", bg="#FFFAF0").grid(row=idx, column=0, sticky="w", padx=5, pady=2)
                    tk.Label(info_frame, text=value, font=("Arial", 11), fg="#34495E", bg="#FFFAF0").grid(row=idx, column=1, sticky="w", padx=5, pady=2)

                can_extend = True
                error_message = ""

                if record['status'] != 'borrowed':
                    can_extend = False
                    error_message = "Chỉ có thể gia hạn phiếu mượn đang hoạt động!"
                else:
                    for doc_id in record['documents']:
                        if any(res['doc_id'] == doc_id and res['status'] == 'pending' for res in self.borrowing_manager.reservation_records):
                            can_extend = False
                            error_message = f"Không thể gia hạn vì tài liệu {doc_id} có người đặt trước!"
                            break

                    if can_extend:
                        reader = self.reader_manager.get_reader_details(record['reader_id'])
                        if reader:
                            for history in reader['borrow_history']:
                                if history['book_id'] in record['documents'] and history.get('extended', False):
                                    can_extend = False
                                    error_message = "Đã gia hạn mượn tài liệu này trước đó!"
                                    break

                if not can_extend:
                    tk.Label(result_frame, text=error_message, font=("Arial", 12), fg="#E74C3C", bg="#FFFAF0").pack(fill="x", pady=10)
                else:
                    try:
                        current_due_date = datetime.fromisoformat(record['due_date'])
                        new_due_date = (current_due_date + timedelta(days=7)).strftime("%Y-%m-%d")
                    except (ValueError, TypeError):
                        new_due_date = record['due_date']

                    tk.Label(result_frame, text=f"Gia hạn thêm 7 ngày: Hạn trả mới sẽ là {new_due_date}", font=("Arial", 12), fg="#023020", bg="#FFFAF0").pack(fill="x", pady=10)

                    def extend():
                        try:
                            success = self.borrowing_manager.extend_borrow_period(query)
                            if success:
                                messagebox.showinfo("Thành công", "Gia hạn thời gian mượn thành công!")
                                search()
                            else:
                                messagebox.showerror("Lỗi", "Không thể gia hạn thời gian mượn!")
                        except ValueError as e:
                            messagebox.showerror("Lỗi", str(e))

                    tk.Button(result_frame, text="📅 Gia hạn", command=extend, font=("Arial", 12, "bold"), fg="#023020", bg="#708090", relief="flat", padx=15, pady=5).pack(anchor="w", pady=5).bind("<Enter>", lambda e: on_enter(e.widget)).bind("<Leave>", lambda e: on_leave(e.widget))
            else:
                tk.Label(result_frame, text="Không tìm thấy phiếu mượn!", font=("Arial", 12), fg="#E74C3C", bg="#FFFAF0").pack(fill="x", pady=20)

        tk.Button(input_frame, text="🔍 Tìm kiếm", command=search, font=("Arial", 12, "bold"), fg="#023020", bg="#708090", relief="flat", padx=15, pady=5).grid(row=0, column=2, padx=5, pady=5, sticky="w").bind("<Enter>", lambda e: on_enter(e.widget)).bind("<Leave>", lambda e: on_leave(e.widget))
        ttk.Separator(self.content_frame, orient="horizontal").pack(fill="x", pady=20)

    def display_return_records(self, result_frame, records, empty_message="Không có phiếu trả!"):
        for widget in result_frame.winfo_children():
            widget.destroy()

        if records:
            columns = ["STT", "Mã phiếu trả", "Mã phiếu mượn", "Mã độc giả", "Ngày trả", "Tổng tiền phạt"]
            tree = ttk.Treeview(result_frame, columns=columns, show="headings", height=10)

            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, anchor="w", width=120)

            for record in records:
                try:
                    return_date = datetime.fromisoformat(record["return_date"]).strftime("%Y-%m-%d")
                except (ValueError, TypeError):
                    return_date = record["return_date"]

                tree.insert("", "end", values=(
                    record["stt"],
                    record["return_id"],
                    record["borrow_id"],
                    record["reader_id"],
                    return_date,
                    record["total_fine"]
                ))

            tree_scroll_y = ttk.Scrollbar(result_frame, orient="vertical", command=tree.yview)
            tree_scroll_x = ttk.Scrollbar(result_frame, orient="horizontal", command=tree.xview)
            tree.configure(yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)
            tree_scroll_y.pack(side="right", fill="y")
            tree_scroll_x.pack(side="bottom", fill="x")
            tree.pack(fill="both", expand=True, pady=10)
        else:
            tk.Label(result_frame, text=empty_message, font=("Arial", 12), fg="#E74C3C", bg="#FFFAF0").pack(fill="x", pady=20)

    def search_return_common(self, return_id_var, borrow_id_var, reader_id_var, result_frame, callback=None):
        return_id = return_id_var.get().strip() or None
        borrow_id = borrow_id_var.get().strip() or None
        reader_id = reader_id_var.get().strip() or None

        if not return_id and not borrow_id and not reader_id:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập ít nhất một tiêu chí tìm kiếm!")
            return

        try:
            records = self.borrowing_manager.search_return_records(return_id, borrow_id, reader_id)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi khi tìm kiếm phiếu trả: {str(e)}")
            return

        if not records:
            self.display_return_records(result_frame, records, empty_message="Không tìm thấy phiếu trả!")
        else:
            self.display_return_records(result_frame, records)
            if callback:
                callback(records, result_frame)

    def search_return_records_gui(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Tìm kiếm phiếu trả", font=("Arial", 20, "bold"), fg="#023020", bg="#FFFAF0").pack(pady=20)

        input_frame = tk.Frame(self.content_frame, bg="#FFFAF0")
        input_frame.pack(fill="x", pady=10)
        tk.Label(input_frame, text="Mã phiếu trả:", font=("Arial", 12), fg="#000000", bg="#FFFAF0").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        return_id_var = tk.StringVar()
        tk.Entry(input_frame, textvariable=return_id_var, font=("Arial", 12), width=20).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        tk.Label(input_frame, text="Mã phiếu mượn:", font=("Arial", 12), fg="#000000", bg="#FFFAF0").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        borrow_id_var = tk.StringVar()
        tk.Entry(input_frame, textvariable=borrow_id_var, font=("Arial", 12), width=20).grid(row=1, column=1, padx=5, pady=5, sticky="w")
        tk.Label(input_frame, text="Mã độc giả:", font=("Arial", 12), fg="#000000", bg="#FFFAF0").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        reader_id_var = tk.StringVar()
        tk.Entry(input_frame, textvariable=reader_id_var, font=("Arial", 12), width=20).grid(row=2, column=1, padx=5, pady=5, sticky="w")

        canvas = tk.Canvas(self.content_frame, bg="#FFFAF0", highlightthickness=0)
        scrollbar_y = ttk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
        scrollbar_x = ttk.Scrollbar(self.content_frame, orient="horizontal", command=canvas.xview)
        result_frame = tk.Frame(canvas, bg="#FFFAF0")
        result_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar_y.pack(side="right", fill="y")
        scrollbar_x.pack(side="bottom", fill="x")
        canvas.create_window((0, 0), window=result_frame, anchor="nw")

        def on_enter(btn): btn.config(bg="#34495E", relief="raised")
        def on_leave(btn): btn.config(bg="#708090", relief="flat")

        tk.Button(input_frame, text="🔍 Tìm kiếm", command=lambda: self.search_return_common(return_id_var, borrow_id_var, reader_id_var, result_frame), font=("Arial", 12, "bold"), fg="#023020", bg="#708090", relief="flat", padx=15, pady=5).grid(row=0, column=2, padx=5, pady=5, sticky="w").bind("<Enter>", lambda e: on_enter(e.widget)).bind("<Leave>", lambda e: on_leave(e.widget))
        ttk.Separator(self.content_frame, orient="horizontal").pack(fill="x", pady=20)

    def display_return_records(self, result_frame, records, empty_message="Không có phiếu trả!"):
        for widget in result_frame.winfo_children():
            widget.destroy()

        if records:
            columns = ["STT", "Mã phiếu trả", "Mã phiếu mượn", "Mã độc giả", "Ngày trả", "Tổng tiền phạt"]
            tree = ttk.Treeview(result_frame, columns=columns, show="headings", height=10)

            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, anchor="w", width=120)

            for record in records:
                try:
                    return_date = datetime.fromisoformat(record["return_date"]).strftime("%Y-%m-%d")
                except (ValueError, TypeError):
                    return_date = record["return_date"]

                tree.insert("", "end", values=(
                    record["stt"],
                    record["return_id"],
                    record["borrow_id"],
                    record["reader_id"],
                    return_date,
                    record["total_fine"]
                ))

            tree_scroll_y = ttk.Scrollbar(result_frame, orient="vertical", command=tree.yview)
            tree_scroll_x = ttk.Scrollbar(result_frame, orient="horizontal", command=tree.xview)
            tree.configure(yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)
            tree_scroll_y.pack(side="right", fill="y")
            tree_scroll_x.pack(side="bottom", fill="x")
            tree.pack(fill="both", expand=True, pady=10)
        else:
            tk.Label(result_frame, text=empty_message, font=("Arial", 12), fg="#E74C3C", bg="#FFFAF0").pack(fill="x", pady=20)

    def show_all_return_records_gui(self):
        self.clear_content()
        tk.Label(self.content_frame, text="Danh sách toàn bộ phiếu trả", font=("Arial", 20, "bold"), fg="#023020", bg="#FFFAF0").pack(pady=20)

        canvas = tk.Canvas(self.content_frame, bg="#FFFAF0", highlightthickness=0)
        scrollbar_y = ttk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
        scrollbar_x = ttk.Scrollbar(self.content_frame, orient="horizontal", command=canvas.xview)
        result_frame = tk.Frame(canvas, bg="#FFFAF0")
        result_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar_y.pack(side="right", fill="y")
        scrollbar_x.pack(side="bottom", fill="x")
        canvas.create_window((0, 0), window=result_frame, anchor="nw")

        try:
            records = self.borrowing_manager.get_all_return_records()
        except Exception as e:
            tk.Label(result_frame, text=f"Lỗi khi lấy dữ liệu: {str(e)}", font=("Arial", 12), fg="#E74C3C", bg="#FFFAF0").pack(fill="x", pady=20)
            return

        self.display_return_records(result_frame, records, empty_message="Không có phiếu trả nào!")

        def on_enter(btn): btn.config(bg="#87CAFA", relief="raised")
        def on_leave(btn): btn.config(bg="#FFC0CB", relief="flat")

        ttk.Separator(self.content_frame, orient="horizontal").pack(fill="x", pady=20)

#////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
    def display_statistics(self):
        self.clear_content()
        # Tạo Canvas làm nền
        canvas = tk.Canvas(self.content_frame, bg="#FFFAF0", highlightthickness=0)
        canvas.pack(fill="both", expand=True)
        # Frame chứa nội dung
        content_frame = tk.Frame(canvas, bg="#FFFAF0")
        content_frame.place(relx=0.05, rely=0.05, relwidth=0.9, relheight=0.9)
        # Tiêu đề
        tk.Label(content_frame,text="Thống kê",font=("Arial", 20, "bold"),fg="#023020", bg="#FFFAF0").pack(pady=20)
        # Frame chứa các nút
        button_frame = tk.Frame(content_frame, bg="#FFFAF0")
        button_frame.pack(pady=10, padx=20, fill="both", expand=True)
        # Danh sách các nút
        buttons = [
            ("📊 Thống kê tổng số tài liệu", self.show_document_stats_gui),
            ("🏆 Thống kê tổng số độc giả mượn", self.show_top_borrowers_gui),
            ("📋 Thống kê tỷ lệ mượn theo loại", self.show_reader_type_ratio_gui),
            ("💰 Thống kê phí phạt", self.show_fines_stats_gui),
            ("⬅ Quay lại", self.clear_content)
        ]
        # Tạo và sắp xếp các nút với hiệu ứng hover
        def on_enter(btn):
            btn.config(bg="#87CAFA", relief="raised")
        def on_leave(btn):
            btn.config(bg="#FFC0CB", relief="flat")
        for idx, (text, cmd) in enumerate(buttons):
            button = tk.Button(button_frame,text=text,command=cmd,font=("Arial", 14, "bold"),fg="#023020",bg="#708090", relief="flat",anchor="w",padx=20,pady=10,width=30)
            button.grid(row=idx, column=0, padx=10, pady=8, sticky="ew")
            button.bind("<Enter>", lambda e, b=button: on_enter(b))
            button.bind("<Leave>", lambda e, b=button: on_leave(b))
        # Căn chỉnh cột
        button_frame.columnconfigure(0, weight=1)
        # Separator
        ttk.Separator(content_frame, orient="horizontal").pack(fill="x", pady=20)

    def update_stats_display(self, frame, show_details, total_docs, total_bor, checkbox):
        # Xóa nội dung cũ, giữ checkbox
        for widget in frame.winfo_children():
            if widget != checkbox: widget.destroy()

        # Hiển thị thống kê tổng quát
        stats_frame = tk.Frame(frame, bg="#FFFAF0")
        stats_frame.pack(fill="x", pady=5)

        total_docs = total_docs if total_docs is not None else 0
        total_bor = total_bor if total_bor is not None else 0

        stats = [("Tổng số tài liệu hiện có", total_docs), ("Tổng số tài liệu đang được mượn", total_bor)]

        for idx, (label, value) in enumerate(stats):
            tk.Label(stats_frame, text=f"{label}:", font=("Arial", 12, "bold"), fg="#023020", bg="#FFFAF0").grid(row=idx, column=0, sticky="w", padx=5, pady=5)
            tk.Label(stats_frame, text=value, font=("Arial", 12), fg="#34495E", bg="#FFFAF0").grid(row=idx, column=1, sticky="w", padx=5, pady=5)

        # Thêm biểu đồ cột
        try:
            fig, ax = plt.subplots(figsize=(4, 2))
            labels, values, colors = ["Tổng tài liệu", "Đang mượn"], [total_docs, total_bor], ["#708090", "#E74C3C"]
            ax.bar(labels, values, color=colors)
            ax.set_ylabel("Số lượng", fontsize=10, color="#FFFFFF")
            ax.set_facecolor("#FFFAF0"); fig.patch.set_facecolor("#FFFAF0")
            ax.tick_params(colors="#FFFFFF", labelsize=8)
            for spine in ax.spines.values(): spine.set_edgecolor("#FFFFFF")
            canvas = FigureCanvasTkAgg(fig, master=stats_frame)
            canvas.draw()
            canvas.get_tk_widget().grid(row=len(stats), column=0, columnspan=2, pady=10, sticky="ew")
            plt.close(fig)
        except Exception as e:
            tk.Label(stats_frame, text=f"Lỗi vẽ biểu đồ: {str(e)}", font=("Arial", 10), fg="#E74C3C", bg="#FFFAF0").grid(row=len(stats), column=0, columnspan=2, pady=10)

        # Hiển thị chi tiết nếu được chọn
        if show_details:
            try:
                borrowed_records = [record for record in self.borrowing_manager.borrow_records if record.get('status') == 'borrowed']
            except AttributeError:
                tk.Label(frame, text="Lỗi: Không thể truy cập dữ liệu phiếu mượn!", font=("Arial", 12), fg="#E74C3C", bg="#FFFAF0").pack(fill="x", pady=10)
                return

            if borrowed_records:
                details_frame = tk.Frame(frame, bg="#FFFAF0")
                details_frame.pack(fill="x", pady=10)
                columns = ["STT", "Mã phiếu mượn", "Mã độc giả", "Ngày mượn", "Danh sách tài liệu", "Số lượng"]
                tree = ttk.Treeview(details_frame, columns=columns, show="headings", height=5)

                for col in columns: 
                    tree.heading(col, text=col)
                    tree.column(col, anchor="w", width=120)

                for idx, record in enumerate(borrowed_records, start=1):
                    try: 
                        borrow_date = datetime.fromisoformat(record.get("borrow_date", "")).strftime("%Y-%m-%d")
                    except (ValueError, TypeError): 
                        borrow_date = record.get("borrow_date", "N/A")
                    tree.insert("", "end", values=(
                        idx, 
                        record.get("borrow_id", "N/A"), 
                        record.get("reader_id", "N/A"), 
                        borrow_date, 
                        ", ".join(record.get("documents", [])), 
                        record.get("quantity", 0)
                    ))

                tree_scroll_y = ttk.Scrollbar(details_frame, orient="vertical", command=tree.yview)
                tree_scroll_x = ttk.Scrollbar(details_frame, orient="horizontal", command=tree.xview)
                tree.configure(yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)
                tree_scroll_y.pack(side="right", fill="y")
                tree_scroll_x.pack(side="bottom", fill="x")
                tree.pack(fill="both", expand=True)
            else:
                tk.Label(frame, text="Không có tài liệu nào đang được mượn!", font=("Arial", 12), fg="#E74C3C", bg="#FFFAF0").pack(fill="x", pady=10)

    def update_top_borrowers_display(self, frame, show_details, total_readers, total_borrowing_readers, checkbox):
        # Xóa nội dung cũ, giữ checkbox
        for widget in frame.winfo_children():
            if widget != checkbox: widget.destroy()

        # Hiển thị thống kê tổng quát
        stats_frame = tk.Frame(frame, bg="#FFFAF0")
        stats_frame.pack(fill="x", pady=5)

        total_readers = total_readers if total_readers is not None else 0
        total_borrowing_readers = total_borrowing_readers if total_borrowing_readers is not None else 0

        stats = [("Tổng số độc giả hiện có", total_readers), ("Tổng số độc giả đang mượn", total_borrowing_readers)]

        for idx, (label, value) in enumerate(stats):
            tk.Label(stats_frame, text=f"{label}:", font=("Arial", 12, "bold"), fg="#023020", bg="#FFFAF0").grid(row=idx, column=0, sticky="w", padx=5, pady=5)
            tk.Label(stats_frame, text=value, font=("Arial", 12), fg="#34495E", bg="#FFFAF0").grid(row=idx, column=1, sticky="w", padx=5, pady=5)

        # Thêm biểu đồ cột
        try:
            fig, ax = plt.subplots(figsize=(4, 2))
            labels, values, colors = ["Tổng độc giả", "Đang mượn"], [total_readers, total_borrowing_readers], ["#708090", "#E74C3C"]
            ax.bar(labels, values, color=colors)
            ax.set_ylabel("Số lượng", fontsize=10, color="#FFFFFF")
            ax.set_facecolor("#FFFAF0"); fig.patch.set_facecolor("#FFFAF0")
            ax.tick_params(colors="#FFFFFF", labelsize=8)
            for spine in ax.spines.values(): spine.set_edgecolor("#FFFFFF")
            canvas = FigureCanvasTkAgg(fig, master=stats_frame)
            canvas.draw()
            canvas.get_tk_widget().grid(row=len(stats), column=0, columnspan=2, pady=10, sticky="ew")
            plt.close(fig)
        except Exception as e:
            tk.Label(stats_frame, text=f"Lỗi vẽ biểu đồ: {str(e)}", font=("Arial", 10), fg="#E74C3C", bg="#FFFAF0").grid(row=len(stats), column=0, columnspan=2, pady=10)

        # Hiển thị chi tiết nếu được chọn
        if show_details:
            try:
                reader_quantities = defaultdict(int)
                for record in self.borrowing_manager.borrow_records or []:
                    if record.get('status') == 'borrowed':
                        reader_id = record.get('reader_id')
                        reader_quantities[reader_id] += record.get('quantity', 0)

                borrowing_readers = []
                for reader_id, quantity in reader_quantities.items():
                    reader = self.reader_manager.get_reader_details(reader_id) or {}
                    borrowing_readers.append({"reader_id": reader_id, "full_name": reader.get("full_name", "N/A"), "quantity": quantity})

                borrowing_readers.sort(key=lambda x: x["quantity"], reverse=True)

                if borrowing_readers:
                    details_frame = tk.Frame(frame, bg="#FFFAF0")
                    details_frame.pack(fill="x", pady=10)
                    columns = ["STT", "Mã độc giả", "Tên độc giả", "Số lượng tài liệu đang mượn"]
                    tree = ttk.Treeview(details_frame, columns=columns, show="headings", height=5)

                    for col in columns: 
                        tree.heading(col, text=col)
                        tree.column(col, anchor="w", width=150)

                    for idx, reader in enumerate(borrowing_readers, start=1):
                        tree.insert("", "end", values=(idx, reader["reader_id"], reader["full_name"], reader["quantity"]))

                    tree_scroll_y = ttk.Scrollbar(details_frame, orient="vertical", command=tree.yview)
                    tree_scroll_x = ttk.Scrollbar(details_frame, orient="horizontal", command=tree.xview)
                    tree.configure(yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)
                    tree_scroll_y.pack(side="right", fill="y")
                    tree_scroll_x.pack(side="bottom", fill="x")
                    tree.pack(fill="both", expand=True)
                else:
                    tk.Label(frame, text="Không có độc giả nào đang mượn tài liệu!", font=("Arial", 12), fg="#E74C3C", bg="#FFFAF0").pack(fill="x", pady=10)
            except AttributeError:
                tk.Label(frame, text="Lỗi: Không thể truy cập dữ liệu độc giả hoặc phiếu mượn!", font=("Arial", 12), fg="#E74C3C", bg="#FFFAF0").pack(fill="x", pady=10)
 
    def show_document_stats_gui(self):
        # Xóa toàn bộ widget con trong content_frame hiện tại
        if hasattr(self, 'content_frame'):
            for widget in self.content_frame.winfo_children():
                widget.destroy()

        # Đảm bảo content_frame luôn tồn tại và được gói bên phải
        if not hasattr(self, 'content_frame'):
            self.content_frame = tk.Frame(self.main_frame, bg="#FFFAF0")
        self.content_frame.pack(side="right", fill="both", expand=True)

        # Frame chính với màu nền đơn giản
        main_frame = tk.Frame(self.content_frame, bg="#FFFAF0")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Tiêu đề
        tk.Label(
            main_frame,
            text="Thống kê tài liệu",
            font=("Arial", 20, "bold"),
            fg="#023020",
            bg="#FFFAF0",
            anchor="w",
            justify="left"
        ).pack(fill="x", pady=20)

        # Canvas và Scrollbar để cuộn thông tin
        canvas = tk.Canvas(main_frame, bg="#FFFAF0", highlightthickness=0)
        scrollbar_y = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#FFFAF0")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.configure(yscrollcommand=scrollbar_y.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar_y.pack(side="right", fill="y")
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        # Frame để hiển thị kết quả
        result_frame = tk.Frame(scrollable_frame, bg="#FFFAF0")
        result_frame.pack(fill="x", pady=10)

        # Tính toán thống kê
        # Tổng số tài liệu hiện có (chưa bị xóa)
        total_documents = sum(1 for doc in self.doc_manager.documents if not doc.get('deleted', False))

        # Tổng số tài liệu đang được mượn
        total_borrowed = sum(
            record['quantity']
            for record in self.borrowing_manager.borrow_records
            if record['status'] == 'borrowed'
        )

        # Checkbox để chọn xem chi tiết
        show_details_var = tk.BooleanVar(value=False)  # Giá trị mặc định là False
        checkbox = tk.Checkbutton(
            result_frame,
            text="Xem chi tiết tài liệu đang được mượn",
            variable=show_details_var,
            font=("Arial", 12),
            fg="#023020",
            bg="#FFFAF0",
            activebackground="#FFFAF0",
            command=lambda: self.update_stats_display(result_frame, show_details_var.get(), total_documents, total_borrowed, checkbox)
        )
        checkbox.pack(anchor="w", pady=5)

        # Gọi hàm cập nhật ban đầu với show_details=False
        self.update_stats_display(result_frame, show_details_var.get(), total_documents, total_borrowed, checkbox)

        # Separator
        ttk.Separator(main_frame, orient="horizontal").pack(fill="x", pady=20)
  
    def update_top_borrowers_display(self, frame, show_details, total_readers, total_borrowing_readers, checkbox):
        # Xóa nội dung cũ, giữ checkbox
        for widget in frame.winfo_children():
            if widget != checkbox: widget.destroy()

        # Hiển thị thống kê tổng quát
        stats_frame = tk.Frame(frame, bg="#FFFAF0")
        stats_frame.pack(fill="x", pady=5)

        total_readers = total_readers if total_readers is not None else 0
        total_borrowing_readers = total_borrowing_readers if total_borrowing_readers is not None else 0

        stats = [
            ("Tổng số độc giả hiện có", total_readers),
            ("Tổng số độc giả đang mượn", total_borrowing_readers),
        ]

        for idx, (label, value) in enumerate(stats):
            tk.Label(stats_frame, text=f"{label}:", font=("Arial", 12, "bold"), fg="#023020", bg="#FFFAF0").grid(row=idx, column=0, sticky="w", padx=5, pady=5)
            tk.Label(stats_frame, text=value, font=("Arial", 12), fg="#34495E", bg="#FFFAF0").grid(row=idx, column=1, sticky="w", padx=5, pady=5)

        # Thêm biểu đồ cột
        try:
            fig, ax = plt.subplots(figsize=(4, 2))
            labels, values, colors = ["Tổng độc giả", "Đang mượn"], [total_readers, total_borrowing_readers], ["#708090", "#E74C3C"]
            ax.bar(labels, values, color=colors)
            ax.set_ylabel("Số lượng", fontsize=10, color="#FFFFFF")
            ax.set_facecolor("#FFFAF0"); fig.patch.set_facecolor("#FFFAF0")
            ax.tick_params(colors="#FFFFFF", labelsize=8)
            for spine in ax.spines.values(): spine.set_edgecolor("#FFFFFF")
            canvas = FigureCanvasTkAgg(fig, master=stats_frame)
            canvas.draw()
            canvas.get_tk_widget().grid(row=len(stats), column=0, columnspan=2, pady=10, sticky="ew")
            plt.close(fig)
        except Exception as e:
            tk.Label(stats_frame, text=f"Lỗi vẽ biểu đồ: {str(e)}", font=("Arial", 10), fg="#E74C3C", bg="#FFFAF0").grid(row=len(stats), column=0, columnspan=2, pady=10)

        # Hiển thị chi tiết nếu được chọn
        if show_details:
            try:
                reader_quantities = defaultdict(int)
                for record in self.borrowing_manager.borrow_records or []:
                    if record.get('status') == 'borrowed':
                        reader_id = record.get('reader_id')
                        reader_quantities[reader_id] += record.get('quantity', 0)

                borrowing_readers = []
                for reader_id, quantity in reader_quantities.items():
                    reader = self.reader_manager.get_reader_details(reader_id) or {}
                    borrowing_readers.append({
                        "reader_id": reader_id,
                        "full_name": reader.get("full_name", "N/A"),
                        "quantity": quantity
                    })

                borrowing_readers.sort(key=lambda x: x["quantity"], reverse=True)

                if borrowing_readers:
                    details_frame = tk.Frame(frame, bg="#FFFAF0")
                    details_frame.pack(fill="x", pady=10)
                    columns = ["STT", "Mã độc giả", "Tên độc giả", "Số lượng tài liệu đang mượn"]
                    tree = ttk.Treeview(details_frame, columns=columns, show="headings", height=5)

                    for col in columns:
                        tree.heading(col, text=col)
                        tree.column(col, anchor="w", width=150)

                    for idx, reader in enumerate(borrowing_readers, start=1):
                        tree.insert("", "end", values=(
                            idx,
                            reader["reader_id"],
                            reader["full_name"],
                            reader["quantity"]
                        ))

                    tree_scroll_y = ttk.Scrollbar(details_frame, orient="vertical", command=tree.yview)
                    tree_scroll_x = ttk.Scrollbar(details_frame, orient="horizontal", command=tree.xview)
                    tree.configure(yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)
                    tree_scroll_y.pack(side="right", fill="y")
                    tree_scroll_x.pack(side="bottom", fill="x")
                    tree.pack(fill="both", expand=True)
                else:
                    tk.Label(frame, text="Không có độc giả nào đang mượn tài liệu!", font=("Arial", 12), fg="#E74C3C", bg="#FFFAF0").pack(fill="x", pady=10)
            except AttributeError:
                tk.Label(frame, text="Lỗi: Không thể truy cập dữ liệu độc giả hoặc phiếu mượn!", font=("Arial", 12), fg="#E74C3C", bg="#FFFAF0").pack(fill="x", pady=10)
 
    def show_top_borrowers_gui(self):
        # Xóa nội dung cũ
        self.clear_content()

        # Tiêu đề
        tk.Label(self.content_frame, text="Thống kê độc giả", font=("Arial", 20, "bold"), fg="#023020", bg="#FFFAF0").pack(pady=20)

        # Canvas và Scrollbar để cuộn
        canvas = tk.Canvas(self.content_frame, bg="#FFFAF0", highlightthickness=0)
        scrollbar_y = ttk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#FFFAF0")
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.configure(yscrollcommand=scrollbar_y.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar_y.pack(side="right", fill="y")
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        # Frame hiển thị kết quả
        result_frame = tk.Frame(scrollable_frame, bg="#FFFAF0")
        result_frame.pack(fill="x", pady=10)

        # Tính toán thống kê
        try:
            total_readers = sum(1 for reader in self.reader_manager.readers if not reader.get('deleted', False))
            borrowing_readers = set(record.get('reader_id') for record in self.borrowing_manager.borrow_records or [] if record.get('status') == 'borrowed')
            total_borrowing_readers = len(borrowing_readers)
        except AttributeError:
            tk.Label(result_frame, text="Lỗi: Không thể truy cập dữ liệu độc giả hoặc phiếu mượn!", font=("Arial", 12), fg="#E74C3C", bg="#FFFAF0").pack(fill="x", pady=10)
            return

        # Checkbox để xem danh sách
        show_details_var = tk.BooleanVar(value=False)
        checkbox = tk.Checkbutton(
            result_frame,
            text="Xem danh sách độc giả đang mượn",
            variable=show_details_var,
            font=("Arial", 12),
            fg="#023020",
            bg="#FFFAF0",
            command=lambda: self.update_top_borrowers_display(result_frame, show_details_var.get(), total_readers, total_borrowing_readers, checkbox)
        )
        checkbox.pack(anchor="w", pady=5)

        # Cập nhật ban đầu
        self.update_top_borrowers_display(result_frame, show_details_var.get(), total_readers, total_borrowing_readers, checkbox)
       # Separator
        ttk.Separator(self.content_frame, orient="horizontal").pack(fill="x", pady=20)
 
    def update_reader_type_ratio_display(self, frame):
        # Xóa nội dung cũ
        for widget in frame.winfo_children():
            widget.destroy()

        # Tính toán thống kê
        try:
            # Tỉ lệ loại sách mượn
            doc_type_counts = defaultdict(int)
            total_borrowed_docs = 0
            for record in self.borrowing_manager.borrow_records or []:
                if record.get('status') == 'borrowed':
                    quantity = record.get('quantity', 0)
                    for doc_id in record.get('documents', []):
                        doc = self.doc_manager.get_document_details(doc_id) or {}
                        if not doc.get('deleted', False):
                            doc_type = doc.get('category', 'Unknown')
                            doc_type_counts[doc_type] += quantity
                            total_borrowed_docs += quantity

            doc_ratios = [
                {"type": doc_type, "count": count, "ratio": (count / total_borrowed_docs * 100) if total_borrowed_docs > 0 else 0}
                for doc_type, count in doc_type_counts.items()
            ]
            doc_ratios.sort(key=lambda x: x["ratio"], reverse=True)

            # Tỉ lệ loại độc giả
            reader_type_counts = defaultdict(int)
            total_borrowing_readers = 0
            borrowing_reader_ids = set()
            for record in self.borrowing_manager.borrow_records or []:
                if record.get('status') == 'borrowed' and record.get('reader_id') not in borrowing_reader_ids:
                    reader = self.reader_manager.get_reader_details(record.get('reader_id')) or {}
                    if not reader.get('deleted', False):
                        reader_type = reader.get('reader_type', 'Unknown')
                        reader_type_counts[reader_type] += 1
                        borrowing_reader_ids.add(record.get('reader_id'))
                        total_borrowing_readers += 1

            reader_ratios = [
                {"type": reader_type, "count": count, "ratio": (count / total_borrowing_readers * 100) if total_borrowing_readers > 0 else 0}
                for reader_type, count in reader_type_counts.items()
            ]
            reader_ratios.sort(key=lambda x: x["ratio"], reverse=True)
        except AttributeError:
            tk.Label(frame, text="Lỗi: Không thể truy cập dữ liệu!", font=("Arial", 12), fg="#E74C3C", bg="#FFFAF0").pack(fill="x", pady=10)
            return

        # Hiển thị nội dung
        if doc_ratios or reader_ratios:
            # Tỉ lệ loại sách mượn
            tk.Label(frame, text="Tỉ lệ loại sách mượn", font=("Arial", 14, "bold"), fg="#023020", bg="#FFFAF0").pack(fill="x", pady=5)
            
            # Frame chứa bảng và biểu đồ
            doc_container = tk.Frame(frame, bg="#FFFAF0")
            doc_container.pack(fill="x", pady=5)
            
            # Bảng
            doc_frame = tk.Frame(doc_container, bg="#FFFAF0")
            doc_frame.pack(side="left", fill="both", expand=True)
            columns_doc = ["Loại", "Số lượng", "Tỉ lệ (%)"]
            tree_doc = ttk.Treeview(doc_frame, columns=columns_doc, show="headings", height=5)
            for col in columns_doc: 
                tree_doc.heading(col, text=col)
                tree_doc.column(col, anchor="w", width=100)
            for ratio in doc_ratios:
                tree_doc.insert("", "end", values=(ratio["type"], ratio["count"], f"{ratio['ratio']:.2f}"))
            tree_doc_scroll_y = ttk.Scrollbar(doc_frame, orient="vertical", command=tree_doc.yview)
            tree_doc_scroll_x = ttk.Scrollbar(doc_frame, orient="horizontal", command=tree_doc.xview)
            tree_doc.configure(yscrollcommand=tree_doc_scroll_y.set, xscrollcommand=tree_doc_scroll_x.set)
            tree_doc_scroll_y.pack(side="right", fill="y")
            tree_doc_scroll_x.pack(side="bottom", fill="x")
            tree_doc.pack(fill="both", expand=True)

            # Biểu đồ
            try:
                fig, ax = plt.subplots(figsize=(3, 2))
                labels = [ratio["type"] for ratio in doc_ratios]
                values = [ratio["ratio"] for ratio in doc_ratios]
                colors = ["#708090", "#E74C3C", "#1ABC9C", "#F1C40F", "#9B59B6"][:len(doc_ratios)]
                ax.bar(labels, values, color=colors)
                ax.set_ylabel("Tỉ lệ (%)", fontsize=8, color="#FFFFFF")
                ax.set_facecolor("#FFFAF0")
                fig.patch.set_facecolor("#FFFAF0")
                ax.tick_params(colors="#FFFFFF", labelsize=6, rotation=45)
                for spine in ax.spines.values(): 
                    spine.set_edgecolor("#FFFFFF")
                canvas = FigureCanvasTkAgg(fig, master=doc_container)
                canvas.draw()
                canvas.get_tk_widget().pack(side="right", padx=10)
                plt.close(fig)
            except Exception as e:
                tk.Label(doc_container, text=f"Lỗi vẽ biểu đồ sách: {str(e)}", font=("Arial", 10), fg="#E74C3C", bg="#FFFAF0").pack(side="right", padx=10)

            # Tỉ lệ loại độc giả
            tk.Label(frame, text="Tỉ lệ loại độc giả", font=("Arial", 14, "bold"), fg="#023020", bg="#FFFAF0").pack(fill="x", pady=10)
            
            # Frame chứa bảng và biểu đồ
            reader_container = tk.Frame(frame, bg="#FFFAF0")
            reader_container.pack(fill="x", pady=5)
            
            # Bảng
            reader_frame = tk.Frame(reader_container, bg="#FFFAF0")
            reader_frame.pack(side="left", fill="both", expand=True)
            columns_reader = ["Loại", "Số lượng", "Tỉ lệ (%)"]
            tree_reader = ttk.Treeview(reader_frame, columns=columns_reader, show="headings", height=5)
            for col in columns_reader: 
                tree_reader.heading(col, text=col)
                tree_reader.column(col, anchor="w", width=100)
            for ratio in reader_ratios:
                tree_reader.insert("", "end", values=(ratio["type"], ratio["count"], f"{ratio['ratio']:.2f}"))
            tree_reader_scroll_y = ttk.Scrollbar(reader_frame, orient="vertical", command=tree_reader.yview)
            tree_reader_scroll_x = ttk.Scrollbar(reader_frame, orient="horizontal", command=tree_reader.xview)
            tree_reader.configure(yscrollcommand=tree_reader_scroll_y.set, xscrollcommand=tree_reader_scroll_x.set)
            tree_reader_scroll_y.pack(side="right", fill="y")
            tree_reader_scroll_x.pack(side="bottom", fill="x")
            tree_reader.pack(fill="both", expand=True)

            # Biểu đồ
            try:
                fig, ax = plt.subplots(figsize=(3, 2))
                labels = [ratio["type"] for ratio in reader_ratios]
                values = [ratio["ratio"] for ratio in reader_ratios]
                colors = ["#708090", "#E74C3C", "#1ABC9C", "#F1C40F", "#9B59B6"][:len(reader_ratios)]
                ax.bar(labels, values, color=colors)
                ax.set_ylabel("Tỉ lệ (%)", fontsize=8, color="#FFFFFF")
                ax.set_facecolor("#FFFAF0")
                fig.patch.set_facecolor("#FFFAF0")
                ax.tick_params(colors="#FFFFFF", labelsize=6, rotation=45)
                for spine in ax.spines.values(): 
                    spine.set_edgecolor("#FFFFFF")
                canvas = FigureCanvasTkAgg(fig, master=reader_container)
                canvas.draw()
                canvas.get_tk_widget().pack(side="right", padx=10)
                plt.close(fig)
            except Exception as e:
                tk.Label(reader_container, text=f"Lỗi vẽ biểu đồ độc giả: {str(e)}", font=("Arial", 10), fg="#E74C3C", bg="#FFFAF0").pack(side="right", padx=10)
        else:
            tk.Label(frame, text="Không có dữ liệu để thống kê!", font=("Arial", 12), fg="#E74C3C", bg="#FFFAF0").pack(fill="x", pady=10)
    def show_reader_type_ratio_gui(self):
        # Xóa nội dung cũ
        self.clear_content()

        # Tiêu đề
        tk.Label(self.content_frame, text="Thống kê tỉ lệ loại sách và độc giả", font=("Arial", 20, "bold"), fg="#023020", bg="#FFFAF0").pack(pady=20)

        # Canvas và Scrollbar
        canvas = tk.Canvas(self.content_frame, bg="#FFFAF0", highlightthickness=0)
        scrollbar_y = ttk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#FFFAF0")
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.configure(yscrollcommand=scrollbar_y.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar_y.pack(side="right", fill="y")
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        # Frame kết quả
        result_frame = tk.Frame(scrollable_frame, bg="#FFFAF0")
        result_frame.pack(fill="x", pady=10)

        # Cập nhật hiển thị
        self.update_reader_type_ratio_display(result_frame)
        # Separator
        ttk.Separator(self.content_frame, orient="horizontal").pack(fill="x", pady=20)

    def update_fines_stats_display(self, frame, show_details, total_fines, checkbox):
        # Xóa nội dung cũ, giữ checkbox
        for widget in frame.winfo_children():
            if widget != checkbox:
                widget.destroy()

        # Hiển thị thống kê tổng phí phạt
        stats_frame = tk.Frame(frame, bg="#FFFAF0")
        stats_frame.pack(fill="x", pady=5)

        tk.Label(stats_frame, text="Tổng phí phạt hiện có:", font=("Arial", 12, "bold"), fg="#023020", bg="#FFFAF0").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        tk.Label(stats_frame, text=f"{total_fines:.2f} VND", font=("Arial", 12), fg="#34495E", bg="#FFFAF0").grid(row=0, column=1, sticky="w", padx=5, pady=5)

        # Hiển thị danh sách độc giả có phí phạt nếu được chọn
        if show_details:
            try:
                fined_readers = [
                    {
                        "reader_id": reader['reader_id'],
                        "name": reader.get("full_name", "Tên không xác định"),
                        "total_fine": reader.get('fine_amount', 0.0)
                    }
                    for reader in self.reader_manager.readers or []
                    if not reader.get('deleted', False) and reader.get('fine_amount', 0.0) > 0
                ]
                fined_readers.sort(key=lambda x: x["total_fine"], reverse=True)
            except AttributeError:
                tk.Label(frame, text="Lỗi: Không thể truy cập dữ liệu độc giả!", font=("Arial", 12), fg="#E74C3C", bg="#FFFAF0").pack(fill="x", pady=10)
                return

            if fined_readers:
                # Bảng
                details_frame = tk.Frame(frame, bg="#FFFAF0")
                details_frame.pack(fill="x", pady=10)
                columns = ["STT", "Mã độc giả", "Tên độc giả", "Tổng phí phạt (VND)"]
                tree = ttk.Treeview(details_frame, columns=columns, show="headings", height=8)
                for col in columns:
                    tree.heading(col, text=col)
                    tree.column(col, anchor="w", width=200)
                for idx, reader in enumerate(fined_readers, start=1):
                    tree.insert("", "end", values=(idx, reader["reader_id"], reader["name"], f"{reader['total_fine']:.2f}"))
                tree_scroll_y = ttk.Scrollbar(details_frame, orient="vertical", command=tree.yview)
                tree_scroll_x = ttk.Scrollbar(details_frame, orient="horizontal", command=tree.xview)
                tree.configure(yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)
                tree_scroll_y.pack(side="right", fill="y")
                tree_scroll_x.pack(side="bottom", fill="x")
                tree.pack(fill="both", expand=True)

                # Biểu đồ phí phạt theo độc giả
                try:
                    fig, ax = plt.subplots(figsize=(5, 3))
                    labels = [reader["reader_id"] for reader in fined_readers]
                    values = [reader["total_fine"] for reader in fined_readers]
                    colors = ["#708090", "#E74C3C", "#1ABC9C", "#F1C40F", "#9B59B6"][:len(fined_readers)]
                    ax.bar(labels, values, color=colors)
                    ax.set_ylabel("Phí phạt (VND)", fontsize=10, color="#FFFFFF")
                    ax.set_facecolor("#FFFAF0")
                    fig.patch.set_facecolor("#FFFAF0")
                    ax.tick_params(colors="#FFFFFF", labelsize=8, rotation=45)
                    for spine in ax.spines.values():
                        spine.set_edgecolor("#FFFFFF")
                    canvas = FigureCanvasTkAgg(fig, master=frame)
                    canvas.draw()
                    canvas.get_tk_widget().pack(fill="x", pady=10)
                    plt.close(fig)
                except Exception as e:
                    tk.Label(frame, text=f"Lỗi vẽ biểu đồ: {str(e)}", font=("Arial", 10), fg="#E74C3C", bg="#FFFAF0").pack(fill="x", pady=10)
            else:
                tk.Label(frame, text="Không có độc giả nào có phí phạt!", font=("Arial", 12), fg="#E74C3C", bg="#FFFAF0").pack(fill="x", pady=10)
  
    def show_fines_stats_gui(self):
        # Xóa nội dung cũ
        self.clear_content()

        # Tiêu đề
        tk.Label(self.content_frame, text="Thống kê phí phạt", font=("Arial", 20, "bold"), fg="#023020", bg="#FFFAF0").pack(pady=20)

        # Canvas và Scrollbar
        canvas = tk.Canvas(self.content_frame, bg="#FFFAF0", highlightthickness=0)
        scrollbar_y = ttk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#FFFAF0")
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.configure(yscrollcommand=scrollbar_y.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar_y.pack(side="right", fill="y")
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        # Frame kết quả
        result_frame = tk.Frame(scrollable_frame, bg="#FFFAF0")
        result_frame.pack(fill="x", pady=10)

        # Tính tổng phí phạt
        try:
            total_fines = sum(reader.get('fine_amount', 0.0) for reader in self.reader_manager.readers or [] if not reader.get('deleted', False))
        except AttributeError:
            tk.Label(result_frame, text="Lỗi: Không thể truy cập dữ liệu độc giả!", font=("Arial", 12), fg="#E74C3C", bg="#FFFAF0").pack(fill="x", pady=10)
            return
        # Checkbox
        show_details_var = tk.BooleanVar(value=False)
        checkbox = tk.Checkbutton(
            result_frame,
            text="Xem danh sách độc giả có phí phạt",
            variable=show_details_var,
            font=("Arial", 12),
            fg="#023020",
            bg="#FFFAF0",
            command=lambda: self.update_fines_stats_display(result_frame, show_details_var.get(), total_fines, checkbox)
        )
        checkbox.pack(anchor="w", pady=5)
        # Cập nhật ban đầu
        self.update_fines_stats_display(result_frame, show_details_var.get(), total_fines, checkbox)
        # Separator
        ttk.Separator(self.content_frame, orient="horizontal").pack(fill="x", pady=20)
