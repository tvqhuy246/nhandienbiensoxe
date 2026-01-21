import tkinter as tk
from tkinter import filedialog, Label, Button, Scale, HORIZONTAL, messagebox
from PIL import Image, ImageTk, ImageEnhance
import os
import cv2
import re
import matplotlib.pyplot as plt
from paddleocr import PaddleOCR
import pyrebase
#import firebase_admin7kj
from firebase_admin import credentials, db

# ==================== Firebase Setup ====================

firebaseConfig = {

    "authDomain": "nhandienbiensoxe-938c7.firebaseapp.com",
    "databaseURL": "https://nhandienbiensoxe-938c7-default-rtdb.firebaseio.com",
    "storageBucket": "nhandienbiensoxe-938c7.firebasestorage.app"
}

firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()

cred = credentials.Certificate("nhandienbiensoxe-938c7-firebase-adminsdk-fbsvc-866cc65b64.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://nhandienbiensoxe-938c7-default-rtdb.firebaseio.com'
})

# ==================== PaddleOCR Setup ====================
ocr = PaddleOCR(use_angle_cls=True, lang='en')

# ==================== Global Variables ====================
original_img = None
processed_img = None
last_detected_plate = ""
brightness_scale = None
current_user = None

# ==================== Functions ====================

def classify_plate(text):
    plate_raw = re.sub(r'[^A-Z0-9.-]', '', text.upper().replace(" ", ""))
    if re.match(r'^\d{2}[A-Z]{1}-\d{3}\.\d{2}$', text):
        return "Car"
    if re.match(r'^\d{2}[A-Z]{1}-\d{5}$', text):
        return "Car"
    if re.match(r'^\d{2}[-*][A-Z0-9]{1,2}\d{4,5}$', plate_raw):
        return "Motorbike"
    if re.match(r'^\d{2}[-*][A-Z0-9]{1,2}\d{3}\.\d{2}$', plate_raw):
        return "Motorbike"
    return "Undefined"

def detect_plate(image_path):
    img = cv2.imread(image_path)
    results = ocr.ocr(image_path, cls=True)

    best_plate = ""
    best_confidence = 0
    lines = []

    for result in results[0]:
        text = result[1][0]
        prob = result[1][1]
        if prob > 0.5:
            lines.append((text.strip(), prob))

            top_left = tuple(map(int, result[0][0]))
            bottom_right = tuple(map(int, result[0][2]))
            cv2.rectangle(img, top_left, bottom_right, (0, 255, 0), 2)
            cv2.putText(img, text, (top_left[0], top_left[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    if len(lines) == 2:
        sorted_lines = sorted(lines, key=lambda x: results[0][lines.index(x)][0][0][1])
        line1, _ = sorted_lines[0]
        line2, _ = sorted_lines[1]
        combined = f"{line1}{line2}".strip().upper().replace(" ", "")
        best_plate = combined
        vehicle_type = classify_plate(combined)
    else:
        for text, prob in lines:
            fixed = text.strip().upper().replace(" ", "")
            if prob > best_confidence:
                best_plate = fixed
                best_confidence = prob
        vehicle_type = classify_plate(best_plate)

    return img, best_plate, vehicle_type

# ==================== App GUI ====================

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Ứng dụng nhận diện biển số xe")
        self.geometry("800x650")
        self.frames = {}
        for F in (LoginPage, RegisterPage, HomePage, DetectPlatePage, RegisteredPlatesPage):
            page_name = F.__name__
            frame = F(parent=self, controller=self)
            self.frames[page_name] = frame
            frame.place(x=0, y=0, relwidth=1, relheight=1)

        self.show_frame("LoginPage")

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()

class LoginPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        tk.Label(self, text="Đăng nhập", font=("Arial", 20)).pack(pady=20)
        tk.Label(self, text="Email").pack()
        self.username_entry = tk.Entry(self)
        self.username_entry.pack(pady=5)

        tk.Label(self, text="Mật khẩu").pack()
        self.password_entry = tk.Entry(self, show="*")
        self.password_entry.pack(pady=5)

        tk.Button(self, text="Đăng nhập", command=self.login).pack(pady=10)
        tk.Button(self, text="Chưa có tài khoản? Đăng ký", 
                  command=lambda: controller.show_frame("RegisterPage")).pack()

    def login(self):
        global current_user
        email = self.username_entry.get()
        password = self.password_entry.get()

        try:
            user = auth.sign_in_with_email_and_password(email, password)
            current_user = user
            messagebox.showinfo("Thành công", "Đăng nhập thành công!")
            self.controller.show_frame("HomePage")
        except:
            messagebox.showerror("Lỗi", "Sai email hoặc mật khẩu!")

class RegisterPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        tk.Label(self, text="Đăng ký", font=("Arial", 20)).pack(pady=20)
        tk.Label(self, text="Email").pack()
        self.username_entry = tk.Entry(self)
        self.username_entry.pack(pady=5)

        tk.Label(self, text="Mật khẩu").pack()
        self.password_entry = tk.Entry(self, show="*")
        self.password_entry.pack(pady=5)

        tk.Button(self, text="Đăng ký", command=self.register).pack(pady=10)
        tk.Button(self, text="Quay lại đăng nhập",  
                  command=lambda: controller.show_frame("LoginPage")).pack()

    def register(self):
        email = self.username_entry.get()
        password = self.password_entry.get()

        try:
            auth.create_user_with_email_and_password(email, password)
            messagebox.showinfo("Thành công", "Đăng ký thành công!")
            self.controller.show_frame("LoginPage")
        except:
            messagebox.showerror("Lỗi", "Email đã tồn tại hoặc định dạng sai!")

class HomePage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        tk.Label(self, text="Trang chủ", font=("Arial", 20)).pack(pady=20)
        tk.Button(self, text="📷 Nhận diện biển số", 
                  command=lambda: controller.show_frame("DetectPlatePage"),
                  width=30, height=2, bg="#4CAF50", fg="white").pack(pady=10)
        tk.Button(self, text="📋 Xem thông tin biển số đã đăng ký",
                  command=lambda: controller.show_frame("RegisteredPlatesPage"),
                  width=30, height=2, bg="#2196F3", fg="white").pack(pady=10)
        tk.Button(self, text="🚪 Đăng xuất", 
                  command=lambda: controller.show_frame("LoginPage"),
                  width=30, height=2, bg="#f44336", fg="white").pack(pady=10)

class DetectPlatePage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        global brightness_scale
        tk.Button(self, text="🔙 Về Home", command=lambda: controller.show_frame("HomePage")).pack(pady=5)

        self.choose_btn = Button(self, text="📂 Chọn ảnh để nhận diện", command=self.choose_image,
                                 font=('Arial', 12), bg="#4CAF50", fg="white")
        self.choose_btn.pack(pady=10)

        self.image_label = Label(self)
        self.image_label.pack()

        brightness_scale = Scale(self, from_=0.5, to=2.0, resolution=0.1,
                                 orient=HORIZONTAL, label="🔆 Độ sáng",
                                 command=self.adjust_brightness, length=300)
        brightness_scale.set(1.0)
        brightness_scale.pack(pady=10)

        self.result_label = Label(self, text="", font=("Arial", 13))
        self.result_label.pack(pady=5)

        Button(self, text="🔍 Phóng to ảnh", command=self.zoom_image, font=("Arial", 11)).pack(pady=3)
        Button(self, text="📝 Đăng ký thông tin biển số", command=self.open_registration_window, font=("Arial", 11)).pack(pady=5)

    def choose_image(self):
        global original_img, processed_img, last_detected_plate
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg;*.jpeg;*.png")])
        if file_path:
            img, plate, vehicle_type = detect_plate(file_path)
            original_img = img.copy()
            processed_img = img
            last_detected_plate = plate
            self.update_display_image(img)

            if plate:
                self.result_label.config(
                    text=f"📍 Biển số: {plate}\n🚗 Loại xe: {vehicle_type}",
                    fg="green", font=("Arial", 14, "bold"))
            else:
                self.result_label.config(text="Không phát hiện biển số!", fg="red", font=("Arial", 13, "bold"))

    def update_display_image(self, img):
        img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        enhancer = ImageEnhance.Brightness(img_pil)
        img_pil = enhancer.enhance(brightness_scale.get())
        img_pil.thumbnail((600, 400))
        img_tk = ImageTk.PhotoImage(img_pil)
        self.image_label.config(image=img_tk)
        self.image_label.image = img_tk

    def adjust_brightness(self, val):
        if original_img is not None:
            self.update_display_image(original_img)

    def zoom_image(self):
        if processed_img is not None:
            plt.figure("Phóng to ảnh")
            plt.imshow(cv2.cvtColor(processed_img, cv2.COLOR_BGR2RGB))
            plt.axis('off')
            plt.show()

    def open_registration_window(self):
        reg_window = tk.Toplevel(self)
        reg_window.title("Đăng ký biển số")
        reg_window.geometry("400x400")

        tk.Label(reg_window, text="Họ tên:", font=("Arial", 12)).pack(pady=5)
        name_entry = tk.Entry(reg_window, font=("Arial", 12))
        name_entry.pack(pady=5)

        tk.Label(reg_window, text="Số điện thoại:", font=("Arial", 12)).pack(pady=5)
        phone_entry = tk.Entry(reg_window, font=("Arial", 12))
        phone_entry.pack(pady=5)
        tk.Label(reg_window, text="Tuổi:", font=("Arial", 12)).pack(pady=5)
        age_entry = tk.Entry(reg_window, font=("Arial", 12))
        age_entry.pack(pady=5)
        tk.Label(reg_window, text="Email:", font=("Arial", 12)).pack(pady=5)
        email_entry = tk.Entry(reg_window, font=("Arial", 12))
        email_entry.pack(pady=5)

        tk.Label(reg_window, text="Biển số xe:", font=("Arial", 12)).pack(pady=5)
        plate_entry = tk.Entry(reg_window, font=("Arial", 12))
        plate_entry.pack(pady=5)

        if last_detected_plate:
            plate_entry.insert(0, last_detected_plate)

        def submit_registration():
            name = name_entry.get()
            phone = phone_entry.get()
            age = age_entry.get()
            email = email_entry.get()
            plate = plate_entry.get()

            if not name or not phone or not plate:
                messagebox.showwarning("Thiếu thông tin", "Vui lòng điền đầy đủ.")
                return

            data = {
                "name": name,
                "phone": phone,
                "age": age,
                "email": email,
                "plate": plate
            }

            db.reference(f"nguoi_dung/{current_user['localId']}/plates").push(data)
            messagebox.showinfo("Thành công", "Đăng ký biển số thành công!")
            reg_window.destroy()

        Button(reg_window, text="✅ Đăng ký", command=submit_registration, bg="#4CAF50", fg="white", font=("Arial", 12)).pack(pady=20)

class RegisteredPlatesPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        tk.Button(self, text="🔙 Về Home", command=lambda: controller.show_frame("HomePage")).pack(pady=5)
        tk.Label(self, text="Danh sách biển số đã đăng ký", font=("Arial", 18)).pack(pady=10)

        self.text_area = tk.Text(self, width=80, height=30)
        self.text_area.pack(pady=10)
        tk.Button(self, text="🔄 Làm mới", command=self.refresh_data).pack(pady=5)

    def refresh_data(self):
        self.text_area.delete(1.0, tk.END)
        if current_user:
            plates_ref = db.reference(f"users/{current_user['localId']}/plates")
            plates = plates_ref.get()
            if plates:
                for plate_id, plate_info in plates.items():
                    self.text_area.insert(tk.END, f"{plate_info}\n{'-'*40}\n")
            else:
                self.text_area.insert(tk.END, "Chưa có thông tin nào.")
        else:
            self.text_area.insert(tk.END, "Vui lòng đăng nhập lại.")

# ==================== Start App ====================

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
