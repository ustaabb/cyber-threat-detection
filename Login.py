import tkinter as tk
from tkinter import messagebox
import csv
import os
import hashlib
import subprocess
from PIL import Image, ImageTk, ImageFilter
import random
import time
import requests

class LoginApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Cyber Security - Login")
        self.root.geometry("900x600")
        self.root.minsize(750, 520)
        self.root.config(bg="#000000")
        self.root.resizable(True, True)

                # ---------- OTP Variables ----------
        self.generated_otp = None
        self.otp_expiry = None
        self.api_key = # 🔑 Replace with your actual key

        # ---------- Load Your Uploaded Background ----------
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            bg_path = os.path.join(base_dir, "cyber_bg.jpg")

            # Copy your uploaded image into the same folder if not already there
            if not os.path.exists(bg_path):
                # If you have the file path, replace below path with actual one
                from shutil import copyfile
                # This assumes you have a file named 'background.jpg' in working dir.
                # If not, remove these two lines or provide the correct source path.
                copyfile("background.jpg", bg_path)

            self.bg_original = Image.open(bg_path).convert("RGBA")
            self.bg_photo = None
            self.bg_label = tk.Label(self.root)
            self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
            self._update_background()
            self.root.bind("<Configure>", self._update_background)
        except Exception as e:
            print(f"Error loading background image: {e}")
            self.root.configure(bg="#0a0a0a")

        # ---------- Colors ----------
        self.BTN_COLOR = "#1E90FF"
        self.TEXT_COLOR = "#FFFFFF"
        self.show_password = False

        # ---------- UI ----------
        self.create_glass_frame()

    # ---------- BACKGROUND RESIZE ----------
    def _update_background(self, event=None):
        try:
            if not hasattr(self, "bg_original"):
                return
            w, h = max(1, self.root.winfo_width()), max(1, self.root.winfo_height())
            img = self.bg_original.resize((w, h), Image.LANCZOS)
            self.bg_photo = ImageTk.PhotoImage(img)
            self.bg_label.config(image=self.bg_photo)
        except Exception as e:
            print(f"Error updating background: {e}")

    # ---------- CREATE GLASS FRAME ----------
    def create_glass_frame(self):
        overlay = tk.Canvas(self.root, width=380, height=360, highlightthickness=0, bg="#000000")
        overlay.place(relx=0.5, rely=0.5, anchor="center")

        try:
            glass_img = self.bg_original.copy().filter(ImageFilter.GaussianBlur(10)).resize((380, 360))
            blurred = ImageTk.PhotoImage(glass_img)
            overlay.image = blurred
            overlay.create_image(0, 0, anchor="nw", image=blurred)
        except Exception:
            overlay.create_rectangle(0, 0, 380, 360, fill="#0A0A0A", outline="")

        # Neon border glow effect
        overlay.create_rectangle(0, 0, 380, 360, outline="#00BFFF", width=2)

        # Login frame
        self.frame = tk.Frame(self.root, bg="#ffffff", highlightbackground="#00BFFF",
                              highlightthickness=1)
        self.frame.place(relx=0.5, rely=0.5, anchor="center", width=360, height=340)

        # ---------- Icon ----------
        icon = tk.Label(self.frame, text="🔐", font=("Segoe UI", 35), bg="#ffffff", fg="#0078D7")
        icon.pack(pady=(25, 10))

        # ---------- Username Entry ----------
        # Use a single placeholder string and bind with the same text
        self.username_placeholder = "Enter Gmail or Phone Number"
        self.username_entry = tk.Entry(self.frame, font=("Segoe UI", 11), relief="flat", justify="center")
        self.username_entry.insert(0, self.username_placeholder)
        self.username_entry.config(fg="gray")
        # Bind focus in/out to the matching placeholder
        self.username_entry.bind("<FocusIn>", lambda e: self._clear_placeholder(self.username_entry, self.username_placeholder))
        self.username_entry.bind("<FocusOut>", lambda e: self._restore_placeholder(self.username_entry, self.username_placeholder))
        self.username_entry.pack(pady=10, ipady=6, ipadx=10)

        # ---------- Password Entry ----------
        self.password_placeholder = "Enter password"
        self.password_var = tk.StringVar()
        self.password_entry = tk.Entry(
            self.frame, textvariable=self.password_var, font=("Segoe UI", 11),
            relief="flat", show="", justify="center"  # show empty while placeholder visible
        )
        self.password_entry.insert(0, self.password_placeholder)
        self.password_entry.config(fg="gray", show="")
        # Bind focus in/out with is_password flag to handle show="*"
        self.password_entry.bind(
            "<FocusIn>",
            lambda e: self._clear_placeholder(self.password_entry, self.password_placeholder, is_password=True)
        )
        self.password_entry.bind(
            "<FocusOut>",
            lambda e: self._restore_placeholder(self.password_entry, self.password_placeholder, is_password=True)
        )
        self.password_entry.pack(pady=10, ipady=6, ipadx=10)

        # ---------- Show/Hide Password ----------
        self.toggle_btn = tk.Button(
            self.frame, text="👁", bd=0, bg="#ffffff", font=("Segoe UI", 10),
            command=self.toggle_password, cursor="hand2"
        )
        self.toggle_btn.place(relx=0.88, rely=0.465, anchor="center")

        # ---------- Login Button ----------
        self.login_btn = tk.Button(
            self.frame, text="Login", bg="#0078D7", fg="white",
            font=("Segoe UI", 11, "bold"), relief="flat", cursor="hand2",
            command=self.submit, activebackground="#005BB5"
        )
        self.login_btn.pack(pady=(20, 5), ipadx=40, ipady=5)

        # Hover glow effect
        self.login_btn.bind("<Enter>", lambda e: self.login_btn.config(bg="#005BB5"))
        self.login_btn.bind("<Leave>", lambda e: self.login_btn.config(bg="#0078D7"))

        # ---------- Register Text ----------
        tk.Label(self.frame, text="Don't have an account?", bg="#ffffff",
                 fg="#333333", font=("Segoe UI", 9)).pack()
        register = tk.Label(self.frame, text="Register Now", bg="#ffffff",
                            fg="#0078D7", font=("Segoe UI", 9, "underline"), cursor="hand2")
        register.pack()
        register.bind("<Button-1>", lambda e: self.open_register_window())

    # ---------- PLACEHOLDER HELPERS ----------
    def _clear_placeholder(self, entry, placeholder, is_password=False):
        # Remove placeholder when field clicked
        try:
            if entry.get() == placeholder:
                entry.delete(0, tk.END)
                entry.config(fg="black")
                if is_password:
                    entry.config(show="*")
                # place cursor at start
                entry.icursor(0)
        except Exception:
            pass

    def _restore_placeholder(self, entry, placeholder, is_password=False):
        # Restore placeholder if field left empty
        try:
            if not entry.get():
                entry.insert(0, placeholder)
                entry.config(fg="gray")
                if is_password:
                    entry.config(show="")
        except Exception:
            pass

    # ---------- PASSWORD TOGGLE ----------
    def toggle_password(self):
        # Only toggle if the password entry currently holds a real password (not placeholder)
        current = self.password_entry.get()
        if current == self.password_placeholder:
            return  # don't toggle when placeholder is showing
        if self.show_password:
            self.password_entry.config(show="*")
            self.toggle_btn.config(text="👁")
            self.show_password = False
        else:
            self.password_entry.config(show="")
            self.toggle_btn.config(text="🙈")
            self.show_password = True

    # ---------- OPEN REGISTER ----------
    def open_register_window(self):
        try:
            subprocess.Popen(["python", "Registration.py"])
        except FileNotFoundError:
            messagebox.showerror("Error", "Registration file 'Registration.py' not found!")

    # ---------- SEND OTP ----------
    def send_otp(self, phone):
        otp = str(random.randint(100000, 999999))
        url = "https://www.fast2sms.com/dev/bulkV2"
        payload = {
            "sender_id": "TXTIND",
            "message": f"Your OTP for Cyber Security login is {otp}. It will expire in 2 minutes.",
            "route": "v3",
            "numbers": phone
        }
        headers = {
            "authorization": self.api_key,
            "Content-Type": "application/x-www-form-urlencoded"
        }

        try:
            response = requests.post(url, data=payload, headers=headers)
            if response.status_code == 200:
                self.generated_otp = otp
                self.otp_expiry = time.time() + 120  # 2 minutes
                messagebox.showinfo("OTP Sent", f"OTP sent successfully to {phone}")
            else:
                messagebox.showerror("Error", f"Failed to send OTP: {response.text}")
        except Exception as e:
            messagebox.showerror("Error", f"OTP sending failed: {e}")

    # ---------- VERIFY OTP ----------
    def verify_otp(self):
        user_otp = self.otp_entry.get().strip()
        if not self.generated_otp:
            messagebox.showerror("Error", "No OTP generated. Please try again.")
            return
        if time.time() > self.otp_expiry:
            messagebox.showwarning("Expired", "Your OTP has expired. Please login again.")
            self.generated_otp = None
            return
        if user_otp == self.generated_otp:
            messagebox.showinfo("Login Successful", f"Welcome, {self.logged_in_user['Username']}!")
            try:
                subprocess.Popen(["python", "Dashboard.py",
                                  self.logged_in_user.get("Username", ""),
                                  self.logged_in_user.get("Gmail", ""),
                                  self.logged_in_user.get("Phone", "")])
                self.root.destroy()
            except FileNotFoundError:
                messagebox.showerror("Error", "Dashboard file 'Dashboard.py' not found!")
        else:
            messagebox.showerror("Error", "Invalid OTP. Please try again.")

    # ---------- LOGIN FUNCTION ----------
    def submit(self):
        user_input = self.username_entry.get().strip()
        password = self.password_var.get().strip()

        # Make sure placeholders are not treated as real input
        if user_input == self.username_placeholder:
            user_input = ""
        if password == self.password_placeholder:
            password = ""

        if not user_input or not password:
            messagebox.showwarning("Warning", "Please enter username and password")
            return

        if not os.path.exists("users.csv"):
            messagebox.showerror("Error", "No registered users found. Please register first.")
            return

        hashed_pw = hashlib.sha256(password.encode()).hexdigest()
        found = False
        user_data = None

        with open("users.csv", "r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if (
                    user_input == row.get("Username")
                    or user_input == row.get("Gmail")
                    or user_input == row.get("Phone")
                ) and hashed_pw == row.get("Password (SHA-256 Hash)"):
                    found = True
                    user_data = row
                    break

        if found:
            messagebox.showinfo("Login Successful", f"Welcome, {user_data['Username']}!")
            try:
                subprocess.Popen(
                    ["python", "Dashboard.py", user_data.get("Username", ""), user_data.get("Gmail", ""), user_data.get("Phone", "")]
                )
                self.root.destroy()
            except FileNotFoundError:
                messagebox.showerror("Error", "Dashboard file 'Dashboard.py' not found!")
        else:
            messagebox.showerror("Error", "Invalid username or password!")


# ---------- RUN APP ----------
if __name__ == "__main__":
    root = tk.Tk()
    app = LoginApp(root)
    root.mainloop()
