import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from reader_manager import ReaderManager
import os
from config import CONFIG

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class LoginRegisterWindow:
    def __init__(self, root, on_login_success):
        self.root = root
        self.root.title("Quản lý thư viện")
        self.root.geometry("500x400")
        self.root.configure(bg="#87cefa")
        self.on_login_success = on_login_success

        self.reader_manager = ReaderManager(
            readers_file=CONFIG["readers_file"],
            reader_types_file=CONFIG["reader_types_file"],
            log_file=CONFIG["reader_logs_file"]
        )

        # Khởi tạo giao diện đăng nhập
        self.show_login_screen()

    def show_login_screen(self):
        # Xóa các widget hiện tại (nếu có)
        for widget in self.root.winfo_children():
            widget.destroy()

        # Xử lý logo 600x600 và resize xuống kích thước phù hợp
        try:
            original_logo = Image.open(CONFIG["logo_file"])
            resized_logo = original_logo.resize((150, 250), Image.Resampling.LANCZOS)
            self.logo = ImageTk.PhotoImage(resized_logo)
            tk.Label(self.root, image=self.logo, bg="#87cefa").place(x=50, y=50)
        except:
            tk.Label(self.root, text="[Logo]", bg="#87cefa").place(x=50, y=50)

        tk.Label(self.root, text="Đăng nhập", font=("Arial", 20, "bold"), fg="#dc143c", bg="#87cefa").place(x=250, y=50)

        # Nhãn và ô nhập liệu
        tk.Label(self.root, text="Tên đăng nhập", font=("Arial", 11, "bold"), fg="#000000", bg="#87cefa").place(x=250, y=120)
        self.username = tk.Entry(self.root)
        self.username.place(x=250, y=150)

        tk.Label(self.root, text="Mật khẩu", font=("Arial", 11, "bold"), fg="#000000", bg="#87cefa").place(x=250, y=180)
        self.password = tk.Entry(self.root, show="*")
        self.password.place(x=250, y=210)

        # Nút đăng nhập và đăng ký
        tk.Button(self.root, text="Đăng nhập", bg="#2e8b57", font=("Arial", 13, "bold"), fg="white", command=self.login).place(x=250, y=250, width=100)
        tk.Button(self.root, text="Đăng ký", bg="#2e8b57", font=("Arial", 13, "bold"), fg="white", command=self.show_register_screen).place(x=360, y=250, width=80)

    def show_register_screen(self):
    # Xóa các widget hiện tại để hiển thị màn hình đăng ký
        for widget in self.root.winfo_children():
            widget.destroy()

        # Thiết lập kích thước cửa sổ
        self.root.geometry("500x600")

        # Tiêu đề màn hình đăng ký
        tk.Label(self.root, text="Đăng ký", font=("Arial", 20, "bold"), fg="#dc143c", bg="#87cefa").place(x=200, y=30)

        # Các trường nhập liệu
        y_start = 100
        spacing = 40

        # Họ tên
        y_position = y_start
        tk.Label(self.root, text="Họ tên", font=("Arial", 13, "bold"), fg="#000000", bg="#87cefa").place(x=50, y=y_position)
        self.reg_full_name = tk.Entry(self.root)
        self.reg_full_name.place(x=300, y=y_position)

        # Email
        y_position += spacing
        tk.Label(self.root, text="Email", font=("Arial", 13, "bold"), fg="#000000", bg="#87cefa").place(x=50, y=y_position)
        self.reg_email = tk.Entry(self.root)
        self.reg_email.place(x=300, y=y_position)

        # Số điện thoại
        y_position += spacing
        tk.Label(self.root, text="Số điện thoại", font=("Arial", 13, "bold"), fg="#000000", bg="#87cefa").place(x=50, y=y_position)
        self.reg_phone = tk.Entry(self.root)
        self.reg_phone.place(x=300, y=y_position)

        # CMND/CCCD
        y_position += spacing
        tk.Label(self.root, text="CMND/CCCD", font=("Arial", 13, "bold"), fg="#000000", bg="#87cefa").place(x=50, y=y_position)
        self.reg_id_card = tk.Entry(self.root)
        self.reg_id_card.place(x=300, y=y_position)

        # Địa chỉ
        y_position += spacing
        tk.Label(self.root, text="Địa chỉ", font=("Arial", 13, "bold"), fg="#000000", bg="#87cefa").place(x=50, y=y_position)
        self.reg_address = tk.Entry(self.root)
        self.reg_address.place(x=300, y=y_position)

        # Ngày sinh (tùy chọn)
        y_position += spacing
        tk.Label(self.root, text="Ngày sinh (YYYY-MM-DD)", font=("Arial", 13, "bold"), fg="#000000", bg="#87cefa").place(x=50, y=y_position)
        self.reg_dob = tk.Entry(self.root)
        self.reg_dob.place(x=300, y=y_position)

        # Loại độc giả
        y_position += spacing
        tk.Label(self.root, text="Loại độc giả", font=("Arial", 11, "bold"), fg="#000000", bg="#87cefa").place(x=50, y=y_position)
        self.reg_reader_type = tk.StringVar(value="Sinh viên")
        self.reader_type_menu = tk.OptionMenu(self.root, self.reg_reader_type, "Sinh viên", "Giảng viên/Cán bộ", "Khách vãng lai")
        self.reader_type_menu.place(x=50, y=y_position + 30)
        self.reg_reader_type.trace("w", self.update_reader_type_fields)

        # Role (mặc định là "reader")
        tk.Label(self.root, text="Role", font=("Arial", 11, "bold"), fg="#000000", bg="#87cefa").place(x=350, y=y_position)
        self.reg_role = tk.StringVar(value="reader")
        tk.OptionMenu(self.root, self.reg_role, "reader").place(x=350, y=y_position + 30)

        # Khung động cho mã số sinh viên hoặc mã số cán bộ
        y_position += 2*spacing
        self.dynamic_frame = tk.Frame(self.root, bg="#87cefa")
        self.dynamic_frame.place(x=50, y=y_position)
        self.update_reader_type_fields()

        # Nút đăng ký và quay lại
        button_y = y_position + spacing + 40
        tk.Button(self.root, text="Đăng ký", bg="#2e8b57", font=("Arial", 14, "bold"), fg="white", command=self.register).place(x=150, y=button_y, width=120)
        tk.Button(self.root, text="Quay lại", bg="#2e8b57", font=("Arial", 14, "bold"), fg="white", command=self.show_login_screen).place(x=300, y=button_y, width=100)

        # Nhãn thương hiệu
        tk.Label(self.root, text="Quản lý thư viện", fg="white", bg="#000000").place(x=50, y=700)

    def update_reader_type_fields(self, *args):
        # Xóa các widget hiện tại trong dynamic_frame
        for widget in self.dynamic_frame.winfo_children():
            widget.destroy()

        # Cập nhật trường động dựa trên loại độc giả
        reader_type = self.reg_reader_type.get()
        if reader_type == "Sinh viên":
            tk.Label(self.dynamic_frame, text="Mã số sinh viên", font=("Arial", 13, "bold"), fg="#000000", bg="#87cefa").pack()
            self.reg_student_id = tk.Entry(self.dynamic_frame)
            self.reg_student_id.pack()
            self.reg_employee_id = None
        elif reader_type == "Giảng viên/Cán bộ":
            tk.Label(self.dynamic_frame, text="Mã số cán bộ", font=("Arial", 13, "bold"), fg="#000000", bg="#87cefa").pack()
            self.reg_employee_id = tk.Entry(self.dynamic_frame)
            self.reg_employee_id.pack()
            self.reg_student_id = None
        else:
            self.reg_student_id = None
            self.reg_employee_id = None

    def login(self):
        username = self.username.get()
        password = self.password.get()
        self.on_login_success(username, password)

    def register(self):
        full_name = self.reg_full_name.get()
        id_card = self.reg_id_card.get()
        dob = self.reg_dob.get() if self.reg_dob.get() else None
        phone = self.reg_phone.get()
        email = self.reg_email.get()
        address = self.reg_address.get()
        reader_type = self.reg_reader_type.get()
        role = self.reg_role.get()
        student_id = self.reg_student_id.get() if hasattr(self, 'reg_student_id') and self.reg_student_id else None
        employee_id = self.reg_employee_id.get() if hasattr(self, 'reg_employee_id') and self.reg_employee_id else None

        try:
            new_reader = self.reader_manager.register_reader(
                full_name=full_name,
                id_card=id_card,
                dob=dob,
                phone=phone,
                email=email,
                address=address,
                reader_type=reader_type,
                student_id=student_id,
                employee_id=employee_id,
                role=role 
            )
            # Gán username giống reader_id
            new_reader["username"] = new_reader["reader_id"]
            messagebox.showinfo("Thành công", f"Đăng ký thành công! Mã độc giả: {new_reader['reader_id']}, Username: {new_reader['username']}, Mật khẩu: {new_reader['password']}")
            
            self.show_login_screen()
        except ValueError as e:
            messagebox.showerror("Lỗi", f"Đăng ký thất bại: {str(e)}")