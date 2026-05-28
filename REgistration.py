from tkinter import *
from tkinter import messagebox
import csv
import os
import hashlib
import re  

class CyberSecurityRegistration:
    def __init__(self, root):
        self.root = root
        self.root.title("Cyber Security - Registration Form")
        self.root.geometry("520x750")
        self.root.config(bg="#e9eff6")
        self.root.resizable(True, True)

        # Title
        Label(
            root, text="Cyber Security",
            font=("Helvetica", 34, "bold"),
            fg="#1565c0", bg="#e9eff6"
        ).pack(pady=(30, 5))

        Label(
            root, text="Create a Secure Account",
            font=("Arial", 13), bg="#e9eff6", fg="#555"
        ).pack(pady=(0, 15))

        # Main Card
        self.card = Frame(root, bg="white", bd=0, relief="ridge")
        self.card.pack(pady=10)
        self.card.configure(width=450, height=620)
        self.card.pack_propagate(False)

        Label(
            self.card, text="Registration Form",
            font=("Arial", 18, "bold"), bg="white", fg="#333"
        ).pack(pady=(25, 5))

        Label(
            self.card, text="Please fill in all the fields below",
            font=("Arial", 10), bg="white", fg="gray"
        ).pack(pady=(0, 15))

        # Form Frame
        form = Frame(self.card, bg="white")
        form.pack(pady=5, padx=10)

        # Helper function for placeholders
        def add_placeholder(entry, placeholder):
            entry.insert(0, placeholder)
            entry.config(fg="gray")
            def on_focus_in(e):
                if entry.get() == placeholder:
                    entry.delete(0, END)
                    entry.config(fg="black")
            def on_focus_out(e):
                if entry.get() == "":
                    entry.insert(0, placeholder)
                    entry.config(fg="gray")
            entry.bind("<FocusIn>", on_focus_in)
            entry.bind("<FocusOut>", on_focus_out)

        # USERNAME 
        self.username = Entry(form, font=("Arial", 12), width=40, bd=1, relief="solid")
        self.username.grid(row=0, column=0, columnspan=2, padx=5, pady=(10, 0))
        add_placeholder(self.username, "Enter Username")
        self.username_error = Label(form, text="", bg="white", fg="red", font=("Arial", 9))
        self.username_error.grid(row=1, column=0, columnspan=2, sticky=W, padx=8)

        # DOB
        Label(form, text="Date of Birth ?", font=("Arial", 10, "bold"), bg="white", fg="#555").grid(row=2, column=0, sticky=W, pady=(10, 0))
        dob_frame = Frame(form, bg="white")
        dob_frame.grid(row=3, column=0, columnspan=2, pady=5)

        self.day = Entry(dob_frame, font=("Arial", 12), width=6, bd=1, relief="solid", justify='center')
        self.day.pack(side=LEFT, padx=6)
        add_placeholder(self.day, "DD")

        self.month = Entry(dob_frame, font=("Arial", 12), width=8, bd=1, relief="solid", justify='center')
        self.month.pack(side=LEFT, padx=6)
        add_placeholder(self.month, "MM")

        self.year = Entry(dob_frame, font=("Arial", 12), width=10, bd=1, relief="solid", justify='center')
        self.year.pack(side=LEFT, padx=6)
        add_placeholder(self.year, "YYYY")

        self.dob_error = Label(form, text="", bg="white", fg="red", font=("Arial", 9))
        self.dob_error.grid(row=4, column=0, columnspan=2, sticky=W, padx=8)

        # GENDER
        Label(form, text="Gender ?", font=("Arial", 10, "bold"), bg="white", fg="#555").grid(row=5, column=0, sticky=W, pady=(10, 0))
        gender_frame = Frame(form, bg="white")
        gender_frame.grid(row=6, column=0, columnspan=2, pady=5)

        self.gender = StringVar()
        self.gender.set(None)

        Radiobutton(gender_frame, text="Female", variable=self.gender, value="Female", bg="white", font=("Arial", 10)).pack(side=LEFT, padx=10)
        Radiobutton(gender_frame, text="Male", variable=self.gender, value="Male", bg="white", font=("Arial", 10)).pack(side=LEFT, padx=10)
        Radiobutton(gender_frame, text="Other", variable=self.gender, value="Other", bg="white", font=("Arial", 10)).pack(side=LEFT, padx=10)

        self.gender_error = Label(form, text="", bg="white", fg="red", font=("Arial", 9))
        self.gender_error.grid(row=7, column=0, columnspan=2, sticky=W, padx=8)

        # GMAIL
        self.gmail = Entry(form, font=("Arial", 12), width=40, bd=1, relief="solid")
        self.gmail.grid(row=8, column=0, columnspan=2, padx=5, pady=(10, 0))
        add_placeholder(self.gmail, "Enter Gmail")
        self.gmail_error = Label(form, text="", bg="white", fg="red", font=("Arial", 9))
        self.gmail_error.grid(row=9, column=0, columnspan=2, sticky=W, padx=8)

        # PHONE 
        self.phone = Entry(form, font=("Arial", 12), width=40, bd=1, relief="solid")
        self.phone.grid(row=10, column=0, columnspan=2, padx=5, pady=(10, 0))
        add_placeholder(self.phone, "Enter Phone Number")
        self.phone_error = Label(form, text="", bg="white", fg="red", font=("Arial", 9))
        self.phone_error.grid(row=11, column=0, columnspan=2, sticky=W, padx=8)

        # ----- PASSWORD -----
        self.password = Entry(form, font=("Arial", 12), width=40, bd=1, relief="solid", show="*")
        self.password.grid(row=12, column=0, columnspan=2, padx=5, pady=(10, 0))
        add_placeholder(self.password, "Enter Password")
        self.password_error = Label(form, text="", bg="white", fg="red", font=("Arial", 9))
        self.password_error.grid(row=13, column=0, columnspan=2, sticky=W, padx=8)

        # ----- Password Strength Hint -----
        self.password_hint = Label(form, text="", bg="white", fg="red", font=("Arial", 9))
        self.password_hint.grid(row=14, column=0, columnspan=2, sticky=W, padx=8)

        # Bind key event to password field
        self.password.bind("<KeyRelease>", self.check_password_strength)

        # REGISTER BUTTON
        Button(
            self.card, text="Register",
            font=("Arial", 14, "bold"),
            bg="#1565c0", fg="white",
            width=22, height=1,
            relief="flat",
            command=self.register_user,
            cursor="hand2",
            activebackground="#0d47a1"
        ).pack(pady=25)

        Label(
            self.card,
            text="Your data is protected under Cyber Security standards.",
            font=("Arial", 9), bg="white", fg="gray"
        ).pack(pady=(0, 5))

    # Password Strength Checker
    def check_password_strength(self, event=None):
        password = self.password.get()
        if password == "" or password == "Enter Password":
            self.password_hint.config(text="")
            return

        # Weak: only letters
        if password.isalpha():
            self.password_hint.config(text="Weak Password", fg="red")

        # Medium: letters + numbers
        elif re.match(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]+$', password):
            self.password_hint.config(text="Medium Password", fg="orange")

        # Strong: includes special characters
        elif re.match(r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*?&#])[A-Za-z\d@$!%*?&#]+$', password):
            self.password_hint.config(text="Strong Password", fg="green")

        else:
            self.password_hint.config(text="Weak Password", fg="red")

    # Registration Function
    def register_user(self):
        username = self.username.get()
        gmail = self.gmail.get()
        phone = self.phone.get()
        day = self.day.get()
        month = self.month.get()
        year = self.year.get()
        gender = self.gender.get()
        password = self.password.get()

        # Reset error labels
        self.username_error.config(text="")
        self.gmail_error.config(text="")
        self.phone_error.config(text="")
        self.password_error.config(text="")
        self.dob_error.config(text="")
        self.gender_error.config(text="")

        # Validation
        valid = True
        if username in ["", "Enter Username"]:
            self.username_error.config(text="Please enter a valid username.")
            valid = False
        if day in ["", "DD"] or month in ["", "MM"] or year in ["", "YYYY"]:
            self.dob_error.config(text="Please enter a valid date of birth.")
            valid = False
        if gender == "" or gender is None:
            self.gender_error.config(text="Please select your gender.")
            valid = False
        if gmail in ["", "Enter Gmail"]:
            self.gmail_error.config(text="Please enter your email.")
            valid = False
        if phone in ["", "Enter Phone Number"]:
            self.phone_error.config(text="Please enter your phone number.")
            valid = False
        if password in ["", "Enter Password"]:
            self.password_error.config(text="Please enter a password.")
            valid = False

        if not valid:
            return

        # Check if username already exists
        if os.path.isfile("users.csv"):
            with open("users.csv", "r", newline="", encoding="utf-8") as file:
                reader = csv.reader(file)
                next(reader, None)  # Skip header
                for row in reader:
                    if len(row) > 0 and row[0] == username:
                        messagebox.showerror(
                            "User Exists",
                            "This user already exists. Try registering using another username."
                        )
                        return

        # Hash the password 
        hashed_pw = hashlib.sha256(password.encode()).hexdigest()

        #  SAVE TO CSV 
        file_exists = os.path.isfile("users.csv")
        with open("users.csv", "a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(["Username", "Gmail", "Phone", "Day", "Month", "Year", "Gender", "Password","Image_path"])
            writer.writerow([username, gmail, phone, day, month, year, gender, hashed_pw])

        # SUCCESS MESSAGE 
        messagebox.showinfo(
            "✅ Registration Successful",
            f"Registration saved successfully!\n\n"
            f"Username: {username}\nEmail: {gmail}\nPhone: {phone}\n"
            f"DOB: {day}-{month}-{year}\nGender: {gender}"
        )

        # Close the registration frame after success
        self.root.destroy()

# Run the App
if __name__ == "__main__":
    root = Tk()
    app = CyberSecurityRegistration(root)
    root.mainloop()
