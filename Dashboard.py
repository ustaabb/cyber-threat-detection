import tkinter as tk
from tkinter import filedialog, messagebox, Toplevel, scrolledtext
from PIL import Image, ImageTk, ImageDraw
import sys
import os
import csv
import random
import subprocess
import threading
import time
import ipaddress
import socket
import platform
import shutil

TOOLS_CONFIG = {
    "vboxmanage_path": r"C:\Program Files\Oracle\VirtualBox\VBoxManage.exe",
    "kali_vm_name": "kali-linux-2025.2-virtualbox-amd64",
    "wireshark_path": r"C:\Program Files\Wireshark\wireshark.exe",
    "nmap_path": r"C:\Users\azadb\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Nmap\Nmap - Zenmap GUI.lnk"
}


# ProfileWindow (almost unchanged logic; integrated as Toplevel)
class ProfileWindow:
    def __init__(self, parent, username, gmail, phone, on_save=None):
        """
        parent: the parent tk window (UserDashboard.root)
        this class will create a Toplevel window attached to parent and keep
        the CSV & image update logic as before.
        """
        # create Toplevel instead of using root directly so we don't change your logic
        self.root = Toplevel(parent)
        self.root.transient(parent)
        self.root.grab_set()
        self.username = username
        self.gmail = gmail
        self.phone = phone
        self.on_save = on_save  # callback from dashboard

        self.root.title("User Profile")
        self.root.geometry("450x420")
        self.root.configure(bg="#f7f9fc")

        self.users_csv = "users.csv"
        self.default_icon = "icon.png"
        self.profile_img_path = self.load_user_image()

        tk.Label(self.root, text="👤 User Profile", font=("Arial", 16, "bold"),
                 fg="#1565c0", bg="#f7f9fc").pack(pady=(12, 6))
        tk.Label(self.root, text=self.gmail, font=("Arial", 10, "italic"),
                 bg="#f7f9fc").pack()

        self.image_label = tk.Label(self.root, bg="#f7f9fc")
        self.image_label.pack(pady=15)
        self.update_profile_icon(self.profile_img_path)

        edit_btn = tk.Button(self.root, text="📁 Change Image", bg="#1565c0", fg="white",
                             command=self.browse_file)
        edit_btn.pack()

        info_frame = tk.Frame(self.root, bg="#f7f9fc")
        info_frame.pack(pady=15, fill="x", padx=12)

        tk.Label(info_frame, text="Username:", bg="#f7f9fc").grid(row=0, column=0, sticky="w", padx=8, pady=5)
        self.entry_username = tk.Entry(info_frame, width=30)
        self.entry_username.insert(0, self.username)
        self.entry_username.grid(row=0, column=1, padx=8, pady=5, sticky="w")

        tk.Label(info_frame, text="Phone:", bg="#f7f9fc").grid(row=1, column=0, sticky="w", padx=8, pady=5)
        tk.Label(info_frame, text=self.phone, bg="#f7f9fc").grid(row=1, column=1, sticky="w", padx=8, pady=5)

        tk.Button(self.root, text="💾 Save", bg="#2e7d32", fg="white", width=10,
                  command=self.save_profile).pack(pady=10)

    # IMAGE HANDLING
    def make_circle_image(self, path, size=(120, 120)):
        try:
            img = Image.open(path).convert("RGBA").resize(size, Image.LANCZOS)
            mask = Image.new("L", size, 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, size[0], size[1]), fill=255)
            img.putalpha(mask)
            return ImageTk.PhotoImage(img)
        except Exception as e:
            print("Image load error:", e)
            return None

    def update_profile_icon(self, path):
        photo = self.make_circle_image(path)
        if photo:
            self.image_label.config(image=photo)
            self.image_label.image = photo
        else:
            self.image_label.config(text="👤", font=("Arial", 60), fg="gray")

    # LOAD USER IMAGE 
    def load_user_image(self):
        if not os.path.exists(self.users_csv):
            return self.default_icon
        try:
            with open(self.users_csv, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("Username") == self.username:
                        path = row.get("Image_path", "")
                        return path if path and os.path.exists(path) else self.default_icon
        except Exception:
            pass
        return self.default_icon

    # CHANGE IMAGE
    def browse_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.gif;*.bmp")]
        )
        if file_path:
            self.profile_img_path = file_path
            self.update_profile_icon(file_path)
            self.update_csv_image(file_path)
            messagebox.showinfo("Success", "Profile image updated successfully!")

            # Notify dashboard instantly and close window
            if self.on_save:
                # call callback with latest values (username, gmail, phone)
                try:
                    self.on_save(self.username, self.gmail, self.phone)
                except Exception as e:
                    print("on_save callback error (image):", e)
            self.root.destroy()

    # SAVE CHANGES
    def save_profile(self):
        new_name = self.entry_username.get().strip()
        if not new_name:
            messagebox.showerror("Error", "Username cannot be empty!")
            return

        if new_name != self.username:
            self.update_csv_username(new_name)
            self.username = new_name
            messagebox.showinfo("Saved", "Profile updated successfully!")
        else:
            messagebox.showinfo("Saved", "No changes detected.")

        # Notify dashboard instantly and close window
        if self.on_save:
            try:
                self.on_save(self.username, self.gmail, self.phone)
            except Exception as e:
                print("on_save callback error (save):", e)
        self.root.destroy()

    # CSV UPDATE (IMAGE)
    def update_csv_image(self, new_path):
        rows = []
        if os.path.exists(self.users_csv):
            try:
                with open(self.users_csv, "r", newline="", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    headers = reader.fieldnames
                    for row in reader:
                        if row.get("Username") == self.username:
                            row["Image_path"] = new_path
                        rows.append(row)
            except Exception:
                headers = ["Username", "Gmail", "Phone", "Image_path"]
        else:
            headers = ["Username", "Gmail", "Phone", "Image_path"]
            rows = [{
                "Username": self.username,
                "Gmail": self.gmail,
                "Phone": self.phone,
                "Image_path": new_path
            }]

        try:
            with open(self.users_csv, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                writer.writerows(rows)
        except Exception as e:
            print("Failed writing CSV (image):", e)

    # CSV UPDATE
    def update_csv_username(self, new_username):
        rows = []
        headers = None
        if os.path.exists(self.users_csv):
            try:
                with open(self.users_csv, "r", newline="", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    headers = reader.fieldnames
                    for row in reader:
                        if row.get("Username") == self.username:
                            row["Username"] = new_username
                        rows.append(row)
            except Exception:
                headers = None

        if headers:
            try:
                with open(self.users_csv, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=headers)
                    writer.writeheader()
                    writer.writerows(rows)
            except Exception as e:
                messagebox.showerror("Error", f"Could not update username: {e}")
        else:
            messagebox.showerror("Error", "Could not update username. users.csv missing or invalid.")

# UserDashboard

class UserDashboard:
    def __init__(self, root, username, gmail=None, phone=None):
        self.root = root
        self.root.title("User Dashboard - Cyber Security")
        self.root.geometry("900x600")
        self.root.minsize(750, 520)
        self.root.config(bg="#e9eff6")

        self.username = username
        self.gmail = gmail
        self.phone = phone

        self.default_icon = "icon.png"
        self.users_csv = "users.csv"

        # Load user image and info from CSV
        self.load_user_info_from_csv()

        # HEADER
        header = tk.Frame(root, bg="#1565c0", height=80)
        header.pack(fill="x")

        # create inner frame for layout control
        header_inner = tk.Frame(header, bg="#1565c0")
        header_inner.pack(fill="both", expand=True, padx=10, pady=6)

        header_inner.columnconfigure(0, weight=0)  # icon
        header_inner.columnconfigure(1, weight=1)  # name & info
        header_inner.columnconfigure(2, weight=0)  # placeholder (if you want buttons later)

        # Profile icon (clickable)
        self.profile_icon = tk.Label(header_inner, bg="#1565c0", cursor="hand2")
        self.profile_icon.grid(row=0, column=0, sticky="w", padx=(6, 10))
        self.profile_icon.bind("<Button-1>", self.open_profile_file)
        # set initial icon
        self.update_profile_icon(getattr(self, "profile_img_path", self.default_icon), size=(64, 64))

        name_frame = tk.Frame(header_inner, bg="#345d8b")
        name_frame.grid(row=0, column=1, sticky="w", padx=6, pady=2)
        name_frame.columnconfigure(0, weight=1)

        self.username_label = tk.Label(
            name_frame, text=f"{self.username}",
            font=("Arial", 18, "bold"), bg="#345d8b", fg="white"
        )
        self.username_label.pack(anchor="w", padx=6, pady=(6, 0))

        self.info_text = f"📧 {self.gmail if self.gmail else ''}     📱 {self.phone if self.phone else ''}"
        self.user_info = tk.Label(
            name_frame, text=self.info_text,
            font=("Arial", 10), bg="#345d8b", fg="white", justify="left"
        )
        self.user_info.pack(anchor="w", padx=6, pady=(0, 6))
      
        self.sidebar = tk.Frame(root, bg="#ffffff", width=200)
        self.sidebar.pack(side="left", fill="y")

        tk.Label(
            self.sidebar, text="Dashboard", bg="white", fg="#1565c0",
            font=("Arial", 16, "bold")
        ).pack(pady=(30, 20))

        self.btn_attacks = tk.Button(
            self.sidebar, text="⚔️ Attacks", font=("Arial", 13),
            bg="#e9eff6", fg="#333", relief="flat", width=18,
            cursor="hand2", command=self.show_attacks
        )
        self.btn_attacks.pack(pady=10)

        self.btn_types = tk.Button(
            self.sidebar, text="🧠 Types of Attacks ▾", font=("Arial", 13),
            bg="#e9eff6", fg="#333", relief="flat", width=18,
            cursor="hand2", command=self.toggle_dropdown
        )
        self.btn_types.pack(pady=5)

        

        # QUICK TOOLS (Kali/nmap/wireshark)
        # small separator label
        self.dropdown_frame = tk.Frame(self.sidebar, bg="#f7f9fc")
        self.dropdown_visible = False

        self.attack_types = [
            "Network Attacks", "Application Attacks",
            "Physical Attacks", "Insider Threats"
        ]
        self.type_buttons = []
        for attack_type in self.attack_types:
            btn = tk.Button(
                self.dropdown_frame, text=f"• {attack_type}",
                font=("Arial", 11), bg="#f7f9fc", fg="#333",
                relief="flat", anchor="w", width=20, cursor="hand2",
                command=lambda t=attack_type: self.show_type_details(t),
            )
            btn.pack(padx=10, pady=2, anchor="w")
            self.type_buttons.append(btn)

        tk.Label(self.sidebar, text="Tools", bg="white", fg="#1565c0",
                font=("Arial", 14, "bold")).pack(pady=(12, 6))

        tk.Button(
            self.sidebar, text="🖥️ Kali (VirtualBox)", font=("Arial", 13),
            bg="#e9eff6", fg="#333", relief="flat", width=18,
            cursor="hand2", command=self.show_kali_panel
        ).pack(pady=5)

        tk.Button(
            self.sidebar, text="🔍 Nmap (Zenmap GUI)", font=("Arial", 13),
            bg="#e9eff6", fg="#333", relief="flat", width=18,
            cursor="hand2", command=self.show_nmap_panel
        ).pack(pady=5)

        tk.Button(
            self.sidebar, text="📡 Wireshark", font=("Arial", 13),
            bg="#e9eff6", fg="#333", relief="flat", width=18,
            cursor="hand2", command=self.show_wireshark_panel
        ).pack(pady=5)

        # RIGHT-SIDE CONTENT FRAME
        self.content_frame = tk.Frame(root, bg="white", bd=0, relief="ridge")
        self.content_frame.pack(side="left", fill="both", expand=True, padx=15, pady=20)

        # default welcome label
        self.default_label = tk.Label(
            self.content_frame,
            text="Welcome to your Cyber Security Dashboard 👋\n\nClick a tool on the left to open its panel here.",
            font=("Arial", 16, "bold"), bg="white", fg="#1565c0",
            wraplength=700, justify="center"
        )
        self.default_label.pack(expand=True)

        # keep references for ip entry widgets so we can validate
        self.ip_entry_widget = None
        self.current_scope = None

        # PROFILE AUTO-UPDATE
        self.root.bind("<FocusIn>", self.check_profile_update)

        # COORDINATION FLAGS
        # Event used so monitor waits until the initial auto-check scan finishes.
        self.initial_scan_done = threading.Event()
        # True while any scan is running (initial or monitor-initiated)
        self.scanning_in_progress = False
        # Keep a set of device serials that have already been scanned during this session
        self.scanned_devices = set()

        # Start regular device-monitor thread (detects new devices/disconnects)
        threading.Thread(target=self.monitor_device_connection, daemon=True).start()

        # INITIAL AUTO CHECK
        # When the dashboard starts we scan any device(s) already connected once and mark them as scanned.
        duration_conn = random.randint(10, 20)
        self._initial_check_started = True
        self._show_progress_modal(
            title_text="Checking for device connection...",
            duration_seconds=duration_conn,
            on_finish=self._after_connection_check
        )

    # helper: get connected device ids
    def get_connected_devices(self):
        """Return a set of adb device serials currently connected (authorized 'device' state)."""
        try:
            res = subprocess.run(["adb", "devices"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
            out = (res.stdout or "") + (res.stderr or "")
            lines = [l.strip() for l in out.splitlines() if l.strip()]
            devices = set()
            for line in lines[1:]:
                if not line or line.startswith("List"):
                    continue
                parts = line.split()
                if len(parts) >= 2 and parts[1] == "device":
                    devices.add(parts[0])
                else:
                    # some adb outputs may be "<serial> device" without a tab
                    if line.endswith("device"):
                        devices.add(line.rsplit(" ", 1)[0])
            return devices
        except Exception:
            return set()

    # LOAD USER INFO
    def load_user_info_from_csv(self):
        """Load user info from CSV file"""
        if os.path.exists(self.users_csv):
            try:
                with open(self.users_csv, "r", newline="", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row.get("Username") == self.username:
                            self.gmail = row.get("Gmail", self.gmail)
                            self.phone = row.get("Phone", self.phone)
                            self.profile_img_path = row.get("Image_path", self.default_icon)
                            return
            except Exception:
                # ignore problems reading CSV, use defaults
                pass
        self.profile_img_path = self.default_icon

    def clear_content(self):
        """Remove all widgets from the right-side content_frame."""
        for w in self.content_frame.winfo_children():
            try:
                w.destroy()
            except Exception:
                pass

    def show_kali_panel(self):
        """Render Kali VirtualBox panel inside content_frame."""
        self.clear_content()
        title = tk.Label(self.content_frame, text="🖥️ Kali Linux (VirtualBox)",
                         font=("Arial", 18, "bold"), bg="white", fg="#1565c0")
        title.pack(pady=(12, 8), anchor="w", padx=8)

        desc = ("Start your Kali VM via VirtualBox (VBoxManage). "
                f"VM name: {TOOLS_CONFIG.get('kali_vm_name', '<not set>')}\n\n"
                "Click Launch to start the VM (VirtualBox must be installed).")
        tk.Label(self.content_frame, text=desc, bg="white", fg="#333", wraplength=760, justify="left").pack(padx=10)

        status_frame = tk.Frame(self.content_frame, bg="white")
        status_frame.pack(pady=10, anchor="w", padx=10)

        vbox_path = TOOLS_CONFIG.get("vboxmanage_path", "")
        found = os.path.exists(vbox_path)
        tk.Label(status_frame, text=f"VBoxManage: {vbox_path}  ", bg="white", fg="#333").pack(side="left")
        tk.Label(status_frame, text="✅ Found" if found else "❌ Missing",
                 bg="white", fg="green" if found else "red", font=("Arial", 11, "bold")).pack(side="left", padx=(8, 0))

        btn_frame = tk.Frame(self.content_frame, bg="white")
        btn_frame.pack(pady=(8, 6), anchor="w", padx=10)

        tk.Button(btn_frame, text="Launch Kali VM", bg="#2ecc71", fg="white", width=16,
                  command=self.launch_kali).pack(side="left", padx=(0, 8))
        tk.Button(btn_frame, text="VM Info", width=12, command=self.show_vbox_vms).pack(side="left", padx=6)

        tk.Button(self.content_frame, text="← Back to Dashboard", command=self.show_default, bg="#f0f0f0").pack(pady=(14, 0))

    def show_nmap_panel(self):
        self.clear_content()
        title = tk.Label(self.content_frame, text="🔍 Nmap / Zenmap GUI",
                         font=("Arial", 18, "bold"), bg="white", fg="#1565c0")
        title.pack(pady=(12, 8))

        desc = ("This panel opens the Zenmap GUI (Nmap front-end) or Nmap executable.\n"
                "Configured path: " + TOOLS_CONFIG.get("nmap_path", "<not set>"))
        tk.Label(self.content_frame, text=desc, bg="white", fg="#333", wraplength=760, justify="left").pack(padx=10)

        status_frame = tk.Frame(self.content_frame, bg="white")
        status_frame.pack(pady=12)

        nmap_path = TOOLS_CONFIG.get("nmap_path")
        found = os.path.exists(nmap_path)
        tk.Label(status_frame, text=f"Path: {nmap_path}  ", bg="white").pack(side="left", padx=(0, 8))
        ind = tk.Label(status_frame, text="✅ Found" if found else "❌ Missing", bg="white",
                       fg="green" if found else "red", font=("Arial", 11, "bold"))
        ind.pack(side="left")

        btn_frame = tk.Frame(self.content_frame, bg="white")
        btn_frame.pack(pady=(10, 6))

        launch_btn = tk.Button(btn_frame, text="Launch Zenmap", width=18, bg="#2ecc71", fg="white",
                               command=self.launch_nmap)
        launch_btn.pack(side="left", padx=6)

        explore_btn = tk.Button(btn_frame, text="Open Containing Folder", width=18,
                                command=lambda p=nmap_path: self.open_containing_folder(p))
        explore_btn.pack(side="left", padx=6)

        back_btn = tk.Button(self.content_frame, text="← Back to Dashboard", command=self.show_default)
        back_btn.pack(pady=(14, 0))

    def show_wireshark_panel(self):
        self.clear_content()
        title = tk.Label(self.content_frame, text="📡 Wireshark",
                         font=("Arial", 18, "bold"), bg="white", fg="#1565c0")
        title.pack(pady=(12, 8))

        desc = ("This panel launches Wireshark (packet capture / analysis).\n"
                "Configured path: " + TOOLS_CONFIG.get("wireshark_path", "<not set>"))
        tk.Label(self.content_frame, text=desc, bg="white", fg="#333", wraplength=760, justify="left").pack(padx=10)

        status_frame = tk.Frame(self.content_frame, bg="white")
        status_frame.pack(pady=12)

        ws_path = TOOLS_CONFIG.get("wireshark_path")
        found = os.path.exists(ws_path)
        tk.Label(status_frame, text=f"Path: {ws_path}  ", bg="white").pack(side="left", padx=(0, 8))
        ind = tk.Label(status_frame, text="✅ Found" if found else "❌ Missing", bg="white",
                       fg="green" if found else "red", font=("Arial", 11, "bold"))
        ind.pack(side="left")

        btn_frame = tk.Frame(self.content_frame, bg="white")
        btn_frame.pack(pady=(10, 6))

        launch_btn = tk.Button(btn_frame, text="Launch Wireshark", width=18, bg="#2ecc71", fg="white",
                               command=self.launch_wireshark)
        launch_btn.pack(side="left", padx=6)

        explore_btn = tk.Button(btn_frame, text="Open Containing Folder", width=18,
                                command=lambda p=ws_path: self.open_containing_folder(p))
        explore_btn.pack(side="left", padx=6)

        back_btn = tk.Button(self.content_frame, text="← Back to Dashboard", command=self.show_default)
        back_btn.pack(pady=(14, 0))

    def show_default(self):
        self.clear_content()
        self.default_label = tk.Label(
            self.content_frame,
            text="Welcome to your Cyber Security Dashboard 👋\n\nClick a tool on the left to open its panel here.",
            font=("Arial", 16, "bold"), bg="white", fg="#1565c0",
            wraplength=700, justify="center"
        )
        self.default_label.pack(expand=True)

    # actual launch
    def launch_kali(self):
        vbox_path = TOOLS_CONFIG.get("vboxmanage_path")
        vm_name = TOOLS_CONFIG.get("kali_vm_name")
        if not os.path.exists(vbox_path):
            messagebox.showerror("Error", f"VBoxManage not found at:\n{vbox_path}")
            return
        try:
            subprocess.Popen([vbox_path, "startvm", vm_name, "--type", "gui"])
            messagebox.showinfo("Kali Linux", f"✅ Launching VM: {vm_name}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start Kali VM:\n{e}")

    def launch_nmap(self):
        nmap_path = TOOLS_CONFIG.get("nmap_path")
        if not os.path.exists(nmap_path):
            messagebox.showerror("Error", f"Nmap not found at:\n{nmap_path}")
            return
        try:
            if nmap_path.lower().endswith(".lnk"):
                os.startfile(nmap_path)
            else:
                subprocess.Popen([nmap_path])
            messagebox.showinfo("Nmap", "✅ Nmap (Zenmap GUI) launched successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open Nmap:\n{e}")

    def launch_wireshark(self):
        ws_path = TOOLS_CONFIG.get("wireshark_path")
        if not os.path.exists(ws_path):
            messagebox.showerror("Error", f"Wireshark not found at:\n{ws_path}")
            return
        try:
            subprocess.Popen([ws_path])
            messagebox.showinfo("Wireshark", "✅ Wireshark launched successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open Wireshark:\n{e}")

    def show_vbox_vms(self):
        """Show VMs listed by VBoxManage (if available) in a small popup."""
        vbox = TOOLS_CONFIG.get("vboxmanage_path")
        if not os.path.exists(vbox):
            messagebox.showerror("VBoxManage", f"VBoxManage not found at:\n{vbox}")
            return
        try:
            out = subprocess.check_output([vbox, "list", "vms"], stderr=subprocess.STDOUT, text=True)
            if not out.strip():
                out = "<no VMs found>"
            popup = tk.Toplevel(self.root)
            popup.title("VirtualBox VMs")
            tk.Label(popup, text="VBoxManage list vms output:", font=("Arial", 11, "bold")).pack(padx=10, pady=(8, 4))
            text = tk.Text(popup, width=80, height=12)
            text.pack(padx=10, pady=(0, 8))
            text.insert("1.0", out)
            text.config(state="disabled")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("VBoxManage error", f"Error running VBoxManage:\n{e.output}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def open_containing_folder(self, path):
        """Open the folder containing the given path (if valid)."""
        if not path:
            messagebox.showerror("Error", "No path provided.")
            return
        folder = path if os.path.isdir(path) else os.path.dirname(path)
        if not os.path.exists(folder):
            messagebox.showerror("Error", f"Folder does not exist:\n{folder}")
            return
        try:
            if sys.platform.startswith("win"):
                os.startfile(folder)
            elif sys.platform.startswith("darwin"):
                subprocess.Popen(["open", folder])
            else:
                subprocess.Popen(["xdg-open", folder])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open folder:\n{e}")

    # IMAGE HANDLING
    def update_profile_icon(self, path, size=(60, 60)):
        photo = self.make_circle_image(path, size=size)
        if photo:
            self.profile_photo = photo
            self.profile_icon.config(image=self.profile_photo)
        else:
            self.profile_icon.config(text="👤", font=("Arial", 40), fg="white")

    def make_circle_image(self, path, size=(60, 60)):
        try:
            img = Image.open(path).convert("RGBA").resize(size, Image.LANCZOS)
            mask = Image.new("L", size, 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, size[0], size[1]), fill=255)
            img.putalpha(mask)
            return ImageTk.PhotoImage(img)
        except Exception:
            return None

    # DYNAMIC PROFILE UPDATE
    def check_profile_update(self, event=None):
        """Auto update dashboard info when returning from profile"""
        old_username = self.username
        old_img = getattr(self, "profile_img_path", None)
        old_gmail = self.gmail
        old_phone = self.phone
        self.load_user_info_from_csv()

        # update username immediately if changed
        if self.username != old_username or self.gmail != old_gmail or self.phone != old_phone:
            self.username_label.config(text=self.username)
            self.user_info.config(
                text=f"📧 {self.gmail if self.gmail else ''}     📱 {self.phone if self.phone else ''}"
            )
            self.update_profile_icon(self.profile_img_path, size=(64, 64))

    # MANUAL UPDATE
    def update_username(self, new_username):
        """Called directly from profile to update username immediately"""
        self.username = new_username
        self.username_label.config(text=self.username)

    # OPEN PROFILE
    def open_profile_file(self, event=None):
        """
        Open the profile Toplevel window and pass a callback (on_save)
        so dashboard can update instantly when the profile changes.
        This replaces subprocess.Popen logic with a local Toplevel.
        """
        try:
            # instantiate ProfileWindow with a callback
            ProfileWindow(
                parent=self.root,
                username=self.username,
                gmail=self.gmail or "",
                phone=self.phone or "",
                on_save=self._profile_saved_callback
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open profile: {e}")

    # Tool launch helpers
    # In-dashboard tool console
    def _spawn_tool_panel(self, title, cmd_list, allow_input=True, gui_fallback=None, web_fallback=None):
        """
        Spawn a Toplevel panel and run cmd_list (list of strings) streaming stdout/stderr.
        allow_input: show input box to send lines to stdin (best-effort).
        gui_fallback: if provided and CLI not found, will try to launch the GUI executable externally.
        web_fallback: open documentation site if tool missing.
        """
        import subprocess, threading, shutil, webbrowser
        from tkinter import Toplevel, Frame, Button, Entry, Label
        from tkinter.scrolledtext import ScrolledText

        # check executable presence
        exe = cmd_list[0]
        if shutil.which(exe) is None:
            msg = f"Executable '{exe}' not found in PATH."
            if gui_fallback and shutil.which(gui_fallback):
                # open gui externally
                try:
                    subprocess.Popen([gui_fallback])
                    messagebox.showinfo("Launched GUI", f"'{gui_fallback}' launched externally (GUI).")
                    return
                except Exception as e:
                    messagebox.showerror("Launch error", f"Could not launch GUI fallback: {e}")
                    return
            if web_fallback:
                webbrowser.open(web_fallback)
                messagebox.showinfo("Not found", msg + f" Opening {web_fallback}")
                return
            else:
                messagebox.showerror("Not found", msg)
                return

        panel = Toplevel(self.root)
        panel.title(title)
        panel.geometry("820x480")
        panel.transient(self.root)

        # Output area
        out_frame = Frame(panel)
        out_frame.pack(fill="both", expand=True, padx=8, pady=6)
        txt = ScrolledText(out_frame, wrap="word", font=("Consolas", 10))
        txt.pack(fill="both", expand=True)

        # Controls frame
        ctrl = Frame(panel)
        ctrl.pack(fill="x", padx=8, pady=(0, 8))
        status_lbl = Label(ctrl, text="Starting...", width=30)
        status_lbl.pack(side="left", padx=(0, 8))

        stop_btn = Button(ctrl, text="Stop", bg="#c62828", fg="white")
        stop_btn.pack(side="right", padx=6)

        # Input entry
        entry = None
        send_btn = None
        if allow_input:
            entry = Entry(ctrl, width=60)
            entry.pack(side="right", padx=(6, 0))
            send_btn = Button(ctrl, text="Send")
            send_btn.pack(side="right", padx=(0, 6))

        # spawn process
        try:
            # Use text mode False and decode manually to avoid decode errors
            proc = subprocess.Popen(cmd_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, bufsize=0)
        except Exception as e:
            messagebox.showerror("Failed to start", f"Could not start {exe}: {e}")
            panel.destroy()
            return

        stop_requested = threading.Event()

        def safe_insert(s):
            # schedule UI insert on main thread
            def _do():
                try:
                    txt.insert("end", s)
                    txt.see("end")
                except Exception:
                    pass
            self.root.after(0, _do)

        def reader_thread(stream, label_prefix=""):
            while True:
                if stop_requested.is_set():
                    break
                try:
                    data = stream.readline()
                    if not data:
                        break
                    # decode safely
                    if isinstance(data, bytes):
                        text = data.decode("utf-8", errors="replace")
                    else:
                        text = str(data)
                    safe_insert(f"{label_prefix}{text}")
                except Exception as e:
                    safe_insert(f"[Reader error] {e}\n")
                    break

        # start stdout/stderr readers
        t_out = threading.Thread(target=reader_thread, args=(proc.stdout, ""), daemon=True)
        t_err = threading.Thread(target=reader_thread, args=(proc.stderr, "[ERR] "), daemon=True)
        t_out.start(); t_err.start()

        def stop_proc():
            try:
                stop_requested.set()
                # try graceful termination
                proc.terminate()
                # wait a short time then kill
                try:
                    proc.wait(timeout=2)
                except Exception:
                    proc.kill()
                status_lbl.config(text="Stopped")
            except Exception as e:
                status_lbl.config(text=f"Stop error: {e}")

        stop_btn.config(command=stop_proc)

        def send_input():
            if not entry:
                return
            line = entry.get()
            if not line:
                return
            try:
                # ensure newline
                tosend = (line + "\n").encode("utf-8", errors="replace")
                proc.stdin.write(tosend)
                proc.stdin.flush()
                safe_insert(f"> {line}\n")
                entry.delete(0, "end")
            except Exception as e:
                safe_insert(f"[Input error] {e}\n")

        if send_btn:
            send_btn.config(command=send_input)
            entry.bind("<Return>", lambda ev: send_input())

        # When panel closes, stop process
        def on_close():
            stop_proc()
            panel.destroy()
        panel.protocol("WM_DELETE_WINDOW", on_close)

        # update status when proc exits
        def watcher():
            proc.wait()
            safe_insert(f"\n[Process exited with code {proc.returncode}]\n")
            status_lbl.config(text=f"Exited ({proc.returncode})")
        threading.Thread(target=watcher, daemon=True).start()

        return panel  # panel returned in case caller wants reference

    # wrappers for specific tools
    def open_nmap_panel(self):
        """Open an in-dashboard nmap runner. Prompts for target/args then runs nmap and streams output."""
        import shutil
        from tkinter import simpledialog, messagebox

        # ensure helper _spawn_tool_panel exists in the class
        if not hasattr(self, "_spawn_tool_panel"):
            messagebox.showerror("Error", "_spawn_tool_panel not available.")
            return

        if shutil.which("nmap") is None:
            messagebox.showerror("nmap not found", "nmap not found in PATH. Please install nmap.")
            return

        # ask for target/args (simpledialog is imported here)
        target = simpledialog.askstring("nmap target", "Enter target (IP or domain):", parent=self.root)
        if not target:
            return
        args = simpledialog.askstring("nmap args", "Enter additional nmap args (e.g. -sS -p 1-1000) or leave blank:", parent=self.root) or ""
        cmd = ["nmap"] + (args.split() if args.strip() else []) + [target]
        # call the generic panel spawner
        self._spawn_tool_panel(f"nmap - {target}", cmd, allow_input=False)


    def open_tshark_panel(self):
        """Open tshark (CLI Wireshark) inside dashboard. If not installed, prompt to open Wireshark externally."""
        import shutil
        if shutil.which("tshark"):
            # ask capture interface / count
            from tkinter import simpledialog
            iface = simpledialog.askstring("tshark interface", "Interface (leave blank for default):", parent=self.root) or ""
            count = simpledialog.askstring("capture count", "Number of packets to capture (leave blank for continuous):", parent=self.root) or ""
            cmd = ["tshark"]
            if iface:
                cmd += ["-i", iface]
            if count.isdigit():
                cmd += ["-c", count]
            self._spawn_tool_panel("tshark (Wireshark CLI)", cmd, allow_input=False, web_fallback="https://www.wireshark.org/download.html")
        else:
            # try to open wireshark GUI if present
            import shutil
            if shutil.which("wireshark"):
                try:
                    subprocess.Popen(["wireshark"])
                    messagebox.showinfo("Launched", "Wireshark launched externally.")
                except Exception as e:
                    messagebox.showerror("Error", f"Could not launch Wireshark: {e}")
            else:
                messagebox.showerror("Not found", "tshark / Wireshark not found. Please install Wireshark.")

    def open_metasploit_panel(self):
        """Open msfconsole inside dashboard (best-effort interactive)."""
        import shutil
        if shutil.which("msfconsole") is None:
            messagebox.showerror("msfconsole not found", "msfconsole not found in PATH. Install Metasploit Framework first.")
            return
        self._spawn_tool_panel("Metasploit (msfconsole)", ["msfconsole"], allow_input=True, web_fallback="https://metasploit.help.rapid7.com/docs")

    def open_kali_shell_panel(self):
        """
        Open a shell panel. On Linux will try '/bin/bash' or '/bin/sh'. On Windows uses 'powershell' or 'cmd'.
        This is effectively an in-dashboard shell rather than a full Kali desktop.
        """
        import platform, shutil
        plat = platform.system()
        if plat == "Windows":
            # try powershell then cmd
            if shutil.which("powershell"):
                self._spawn_tool_panel("Shell (PowerShell)", ["powershell", "-NoExit", "-Command", "echo 'PowerShell ready'"], allow_input=True)
            else:
                self._spawn_tool_panel("Shell (cmd)", ["cmd", "/K", "echo cmd ready"], allow_input=True)
        else:
            sh = "/bin/bash" if os.path.exists("/bin/bash") else ("/bin/sh" if os.path.exists("/bin/sh") else None)
            if sh:
                self._spawn_tool_panel("Shell", [sh, "-i"], allow_input=True)
            else:
                messagebox.showerror("Shell not found", "No shell found on system.")


    def _profile_saved_callback(self, new_username, new_gmail, new_phone):
        """
        Called by ProfileWindow when user saves or updates image.
        We'll reload CSV and update the dashboard header accordingly.
        """
        # Important: do not change CSV logic here; simply reload and refresh UI
        try:
            # If username changed, update internal username
            if new_username and new_username != self.username:
                self.username = new_username
            # update gmail/phone if provided
            if new_gmail:
                self.gmail = new_gmail
            if new_phone:
                self.phone = new_phone

            # reload latest data from CSV (so image path updates are picked up)
            self.load_user_info_from_csv()

            # update labels and icon immediately
            self.username_label.config(text=self.username)
            self.user_info.config(text=f"📧 {self.gmail if self.gmail else ''}     📱 {self.phone if self.phone else ''}")
            self.update_profile_icon(self.profile_img_path, size=(64, 64))
        except Exception as e:
            print("Profile saved callback error:", e)

    # ATTACKS DESCRIPTION
    def show_attacks(self, scope=None):
        # Clear old widgets
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Reset stored entry widget and scope
        self.ip_entry_widget = None
        self.current_scope = scope
        # ------------------------
        # 4) General attacks view: buttons + scrollable zoomable description area
        # ------------------------
        attack_info = {
            "Brute Force": (
                "Brute Force Attack\n\n"
                "Overview:\n"
                "A brute force attack is an exhaustive search technique where an attacker attempts all possible "
                "combinations of credentials or cryptographic keys until the correct one is discovered. In practice, "
                "attackers combine dictionary lists (commonly used passwords), credential stuffing from breached databases, "
                "and automated password generation when targeting authentication systems.\n\n"
                "How attackers execute it:\n"
                "- Automated tooling: Attackers use scripts and tools that iterate rapidly over millions of username/password "
                "pairs or key permutations, often distributed across many hosts to avoid local rate limits.\n"
                "- Credential stuffing: Re-using leaked username/password pairs from breaches against other services.\n"
                "- Target selection: Focus on high-value accounts (administrators, service accounts) or poorly protected endpoints.\n\n"
                "Operational limitations and detection:\n"
                "- Rate limiting, account lockouts, multi-factor authentication (MFA), and anomaly detection substantially "
                "increase the time, cost, and likelihood of detection for brute force attempts.\n"
                "- Effective defenses shift attackers toward credential-stuffing strategies where social engineering or "
                "prior breaches supply valid pairs.\n\n"
                "Prevention and mitigation:\n"
                "- Enforce strong password policies and require unique passwords.\n"
                "- Implement MFA (TOTP, hardware tokens) so passwords alone are insufficient.\n"
                "- Apply progressive rate-limiting, account lockout thresholds, and IP reputation blocking.\n"
                "- Monitor authentication logs for abnormal patterns (spikes of failed logins, geographically impossible logins)."
            ),
            "SQL Injection": (
                "SQL Injection (SQLi)\n\n"
                "Overview:\n"
                "SQL injection is a server-side vulnerability in which untrusted input is inserted into database queries, "
                "allowing attackers to manipulate SQL commands executed by the database. Successful exploitation can lead to "
                "data exfiltration, data modification, authentication bypass, or complete system compromise depending on database privileges.\n\n"
                "How attackers execute it:\n"
                "- Payload injection: Attackers craft input containing SQL statements or operators (e.g., ' OR '1'='1) which, "
                "when concatenated into application SQL, alter the intended query logic.\n"
                "- Blind SQLi: When applications suppress error output, attackers infer data existence via boolean or timing-based probes.\n"
                "- Chaining: SQLi can be combined with other flaws to escalate privileges, write web shells, or pivot laterally.\n\n"
                "Operational limitations and detection:\n"
                "- SQLi requires the application to build dynamic SQL from unsanitized input. Proper parameterization removes the attack surface.\n"
                "- Web application firewalls (WAFs) can detect common patterns but may be bypassed by obfuscated payloads.\n\n"
                "Prevention and mitigation:\n"
                "- Use parameterized queries / prepared statements or ORM APIs that separate code from data.\n"
                "- Employ strict input validation, output encoding, and least-privilege database accounts.\n"
                "- Conduct regular static and dynamic application security testing (SAST/DAST) and threat modeling.\n"
                "- Maintain database backups and implement monitoring/alerting for anomalous queries."
            ),
            "Ransomware": (
                "Ransomware\n\n"
                "Overview:\n"
                "Ransomware is malicious software that encrypts files or critical data and demands payment for the decryption keys. "
                "Modern ransomware operations are frequently run by organized cybercriminal groups employing sophisticated extortion "
                "techniques, including data exfiltration followed by threats to publish stolen data.\n\n"
                "How attackers execute it:\n"
                "- Initial access: Through phishing, compromised remote access (RDP) credentials, vulnerable internet-facing services, "
                "or supply-chain compromises.\n"
                "- Lateral movement: After gaining access, attackers escalate privileges, move laterally across the network, and deploy "
                "privilege escalation tools to reach backup servers and domain controllers.\n"
                "- Payload deployment: The ransomware encryptor is executed, often combined with data exfiltration to strengthen extortion leverage.\n\n"
                "Operational limitations and detection:\n"
                "- Ransomware campaigns require sufficient access and privilege to encrypt meaningful volumes of data; good segmentation and "
                "backup hygiene reduce their impact.\n"
                "- Detection is possible via EDR telemetry (process behavior, mass file modifications) and abnormal network exfiltration.\n\n"
                "Prevention and mitigation:\n"
                "- Maintain immutable, offline, or air-gapped backups and test restore procedures frequently.\n"
                "- Apply timely patching, restrict remote access, and use MFA for administrative interfaces.\n"
                "- Deploy EDR/XDR solutions, network segmentation, and least-privilege principles for service accounts.\n"
                "- Prepare an incident response plan and coordinate with legal/forensics experts before paying ransom."
            ),
            "Denial of Service": (
                "Denial of Service (DoS / DDoS)\n\n"
                "Overview:\n"
                "Denial of Service attacks aim to make a resource, service, or network unavailable by overwhelming capacity or exploiting resource-"
                "intensive operations. Distributed Denial of Service (DDoS) uses many distributed systems (botnets) to amplify the effect.\n\n"
                "How attackers execute it:\n"
                "- Volumetric attacks: Floods of traffic saturate network bandwidth (UDP floods, amplification attacks).\n"
                "- Protocol attacks: Exploits weaknesses in protocol handling (SYN floods, fragmented packets) to exhaust connection tables.\n"
                "- Application-layer attacks: Target application endpoints with expensive requests (search queries, complex DB calls) to consume CPU and memory.\n\n"
                "Operational limitations and detection:\n"
                "- High-capacity attacks require substantial infrastructure or botnets; however, amplification techniques lower attacker resource requirements.\n"
                "- Distinguishing malicious traffic from legitimate spikes is a detection challenge for ops teams.\n\n"
                "Prevention and mitigation:\n"
                "- Use scalable DDoS protection services (cloud scrubbing, CDN fronting) to absorb volumetric traffic.\n"
                "- Implement rate-limiting, connection limits, SYN cookies, and filtering at edge routers/firewalls.\n"
                "- Harden application endpoints, cache aggressively, and design services to fail gracefully under load."
            ),
            "Phishing": (
                "Phishing (Social Engineering)\n\n"
                "Executive summary:\n"
                "Phishing is a social-engineering tactic where adversaries deceive users into divulging credentials, executing malware, or taking actions that grant attackers initial access. "
                "Phishing remains one of the highest-volume and most successful attack vectors due to human factors.\n\n"
                "Detailed execution profile:\n"
                "Attackers craft convincing messages (email, SMS, or messaging platforms) that mimic trusted senders. Campaigns may use spear-phishing — highly targeted content tailored to an individual — "
                "or broad spray-and-pray approaches. Malicious links lead to credential-harvesting pages or weaponized attachments that deploy ransomware or backdoors. Attackers often chain phishing with "
                "subsequent lateral movement and privilege escalation.\n\n"
                "Operational constraints and observables:\n"
                "Effective phishing depends on the quality of reconnaissance and message authenticity. Indicators include unusual sender addresses, mismatched domains, login attempts from new locations after clicks, "
                "and endpoint detections of macro-enabled documents or unknown executables.\n\n"
                "Controls and mitigations:\n"
                "1. Implement enterprise email protections (DMARC, DKIM, SPF), advanced phishing filters, and link-rewriting/safe-browsing features.\n"
                "2. Train users with repeated, contextual phishing simulations and provide clear reporting channels.\n"
                "3. Enforce MFA and conditional access policies so credential theft alone does not grant access.\n"
                "4. Isolate and inspect attachments in secure sandboxes, and monitor for post-click behavior such as token theft or anomalous sign-ins."
            ),
            "Firewall Attack": (
                "Firewall Attack (Firewall Evasion / Misconfiguration Abuse)\n\n"
                "Executive summary:\n"
                "Attacks against firewalls encompass attempts to bypass, misconfigure, or otherwise exploit perimeter controls to create unauthorized connectivity. Rather than a single technical exploit, "
                "these attacks frequently exploit policy gaps, overly permissive rules, or chain together misconfigurations in upstream services.\n\n"
                "Detailed execution profile:\n"
                "Adversaries enumerate firewall policies and probe allowed ports, oftentimes seeking to tunnel traffic over permitted protocols (HTTP, DNS, HTTPS) or exploit insecure VPN/remote-access paths. "
                "Techniques include protocol tunneling, port-hopping, use of legitimate cloud services as command-and-control, or leveraging misconfigured NAT rules to reach internal hosts.\n\n"
                "Operational constraints and observables:\n"
                "Successful evasion typically requires reconnaissance and understanding of network topology and allowed services. Observables include unusual authorized-protocol usage, unexpected long-lived sessions, "
                "and traffic that appears legitimate but carries anomalous payloads or destinations.\n\n"
                "Controls and mitigations:\n"
                "1. Apply least-privilege firewall rules and audit rule sets regularly to remove stale or overly broad permissions.\n"
                "2. Use deep-packet inspection, application-layer gateways, and behavior-based monitoring to detect protocol misuse.\n"
                "3. Enforce segmentation and micro-segmentation so that a bypass at the perimeter does not lead to wholesale access.\n"
                "4. Harden remote access (VPN) and require strong authentication, device posture checks, and logging of all administrative changes."
            ),
        }

        # Buttons grid
        grid_frame = tk.Frame(self.content_frame, bg="white")
        grid_frame.pack(pady=10)

        # Scrollable text area for descriptions
        text_frame = tk.Frame(self.content_frame, bg="white")
        text_frame.pack(fill="both", expand=True, padx=10, pady=10)

        text_widget = scrolledtext.ScrolledText(
            text_frame, wrap="word", font=("Arial", 11), height=15
        )
        text_widget.pack(fill="both", expand=True)
        text_widget.insert("end", "ℹ️ Select an attack above to view its full description...")
        text_widget.config(state="disabled")

        # Zoom controls (buttons)
        font_size = [11]  # mutable holder

        def zoom_in():
            font_size[0] += 1
            text_widget.config(font=("Arial", font_size[0]))

        def zoom_out():
            if font_size[0] > 8:
                font_size[0] -= 1
                text_widget.config(font=("Arial", font_size[0]))

        zoom_frame = tk.Frame(self.content_frame, bg="white")
        zoom_frame.pack(pady=(0, 8))
        tk.Button(zoom_frame, text="Zoom +", command=zoom_in, bg="#1565c0", fg="white").pack(side="left", padx=4)
        tk.Button(zoom_frame, text="Zoom -", command=zoom_out, bg="#1565c0", fg="white").pack(side="left", padx=4)

        # Show attack description function
        def show_attack_description(attack_name, btn=None):
            desc = attack_info.get(attack_name, "⚠️ Description not available for this attack.")
            text_widget.config(state="normal")
            text_widget.delete("1.0", "end")
            text_widget.insert("end", desc)
            text_widget.config(state="disabled")

        attacks = list(attack_info.keys())
        cols = 3
        for i, attack in enumerate(attacks):
            btn = tk.Button(
                grid_frame, text=attack, font=("Arial", 12),
                bg="#e9eff6", fg="#333", relief="groove",
                width=20, cursor="hand2",
                command=lambda t=attack: show_attack_description(t),
            )
            btn.grid(row=i // cols, column=i % cols, padx=8, pady=8)

    def on_attack_clicked(self, attack_name, scope):

        # ----------------------------
        # Step 1: Validate IP input
        # ----------------------------
        ip_entry = self.ip_entry_widget
        if ip_entry is None:
            messagebox.showerror("Error", "Please enter IP")
            return
        ip_text = ip_entry.get().strip()
        if not ip_text:
            messagebox.showerror("Error", "Please enter IP")
            return

        # Validate IP format
        try:
            ip_obj = ipaddress.ip_address(ip_text)
        except Exception:
            messagebox.showerror("Invalid IP", "Please enter a valid IP address.")
            return

        is_private = ip_obj.is_private
        if scope == 'Public' and is_private:
            messagebox.showerror("IP Type", "Enter public IP")
            return
        if scope == 'Private' and not is_private:
            messagebox.showerror("IP Type", "Enter private IP")
            return

        # ----------------------------
        # Step 2: Internal scanner function
        # ----------------------------
        def scan_ip_device(ip, ports=None, ping_first=True, tcp_timeout=1.0, save_csv=True):
            if ports is None:
                ports = [21, 22, 23, 25, 53, 80, 110, 139, 143, 443, 445, 3389, 5555, 8080, 9000, 5900]
            result = {
                "ip": ip,
                "ping": {"alive": False, "latency_ms": None},
                "probes": [],
                "guessed_device": None,
                "reasons": [],
                "risk_score": 0
            }

            # Ping test
            if ping_first:
                try:
                    param = "-n" if platform.system().lower() == "windows" else "-c"
                    start = time.time()
                    rc = subprocess.call(["ping", param, "1", ip],
                                         stdout=subprocess.DEVNULL,
                                         stderr=subprocess.DEVNULL)
                    latency = round((time.time() - start) * 1000, 2)
                    if rc == 0:
                        result["ping"]["alive"] = True
                        result["ping"]["latency_ms"] = latency
                        result["reasons"].append(f"Ping success ({latency} ms)")
                    else:
                        result["reasons"].append("Ping failed")
                except Exception as e:
                    result["reasons"].append(f"Ping error: {e}")

            # TCP port probes
            open_ports = []
            for port in ports:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(tcp_timeout)
                    start_time = time.time()
                    r = sock.connect_ex((ip, port))
                    elapsed = round((time.time() - start_time) * 1000, 1)
                    banner = ""
                    if r == 0:
                        try:
                            sock.send(b"HEAD / HTTP/1.0\r\n\r\n")
                            banner = sock.recv(64).decode(errors="ignore").strip()
                        except:
                            pass
                        result["probes"].append({
                            "port": port,
                            "open": True,
                            "response_ms": elapsed,
                            "banner": banner
                        })
                        open_ports.append(port)
                    else:
                        result["probes"].append({
                            "port": port,
                            "open": False,
                            "response_ms": elapsed,
                            "banner": ""
                        })
                    sock.close()
                except Exception as e:
                    result["probes"].append({
                        "port": port,
                        "open": False,
                        "error": str(e)
                    })

            # Guess device type
            guessed = "unknown"
            if 5555 in open_ports:
                guessed = "android"
                result["reasons"].append("Port 5555 (ADB) open - Android likely")
            elif 3389 in open_ports:
                guessed = "windows"
                result["reasons"].append("RDP port open - Windows likely")
            elif 22 in open_ports and 80 not in open_ports:
                guessed = "linux"
                result["reasons"].append("SSH open, no HTTP - Linux likely")
            elif 80 in open_ports or 443 in open_ports:
                guessed = "web/server"
                result["reasons"].append("Web ports open - Server or router likely")
            result["guessed_device"] = guessed

            # Risk scoring
            risk_score = 0
            danger_ports = [23, 21, 139, 445, 5555, 3389, 5900]
            for p in open_ports:
                if p in danger_ports:
                    risk_score += 20
                else:
                    risk_score += 5
            if "admin" in str(result).lower() or "login" in str(result).lower():
                risk_score += 15
            if risk_score > 100:
                risk_score = 100
            result["risk_score"] = risk_score

            # Save CSV 
            csv_path = None
            if save_csv:
                csv_path = f"scan_report_{ip.replace('.', '_')}.csv"
                with open(csv_path, "w", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(["IP", "Port", "Open", "Response(ms)", "Banner"])
                    for pr in result["probes"]:
                        writer.writerow([ip, pr["port"], pr["open"], pr.get("response_ms", ""), pr.get("banner", "")])
                result["csv_path"] = csv_path

            return result

        # ----------------------------
        # Step 3: Perform Scan
        # ----------------------------
        try:
            report = scan_ip_device(ip_text)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to scan IP: {e}")
            return

        # ----------------------------
        # Step 4: Check if IP really exists
        # ----------------------------
        ping_alive = report.get("ping", {}).get("alive", False)
        open_ports = [p["port"] for p in report.get("probes", []) if p.get("open")]
        if not ping_alive and not open_ports:
            messagebox.showwarning("Unreachable",
                                   "The entered IP did not respond to ping and has no open ports.\n"
                                   "It may not exist, be offline, or be behind a firewall.")
            return

        # ----------------------------
        # Step 5: Analyze & show results
        # ----------------------------
        guessed = report.get("guessed_device", "unknown")
        csv_path = report.get("csv_path")
        risk_score = report.get("risk_score", 0)
        reasons = report.get("reasons", [])

        summary = [
            f"IP: {ip_text}",
            f"Scope: {scope}",
            f"Device Type: {guessed}",
            f"Open Ports: {open_ports if open_ports else 'None'}",
            f"Risk Score: {risk_score}/100",
            "",
            "Reasons:",
        ]
        for r in reasons:
            summary.append(f" - {r}")
        summary.append("")
        summary.append(f"Report saved to: {csv_path}" if csv_path else "No CSV report saved.")

        if risk_score >= 70:
            messagebox.showerror("Compromised Device Detected", "\n".join(summary))
        elif risk_score >= 40:
            messagebox.showwarning("Potentially Vulnerable Device", "\n".join(summary))
        else:
            messagebox.showinfo("Device Appears Safe", "\n".join(summary))

    def _show_progress_modal(self, title_text, duration_seconds, on_finish):
        top = Toplevel(self.root)
        top.title("Scanning")
        w, h = 420, 140
        sw, sh = top.winfo_screenwidth(), top.winfo_screenheight()
        x, y = max(0, (sw - w) // 2), max(0, (sh - h) // 2)
        top.geometry(f"{w}x{h}+{x}+{y}")
        top.resizable(False, False)
        top.transient(self.root)
        top.grab_set()
        tk.Label(top, text=title_text, font=("Arial", 12, "bold")).pack(pady=(10, 6))
        status_lbl = tk.Label(top, text="Starting...", font=("Arial", 10))
        status_lbl.pack()
        canvas = tk.Canvas(top, width=360, height=24, bg="#e6f2ea", bd=0, highlightthickness=0)
        canvas.pack(pady=8)
        canvas.create_rectangle(0, 0, 360, 24, outline="#cfe9d6", width=1)
        fill = canvas.create_rectangle(2, 2, 2, 22, fill="#2ecc71", width=0)
        start_time = time.time()

        def animate():
            elapsed = time.time() - start_time
            progress = min(1.0, elapsed / max(0.1, duration_seconds))
            fill_width = 2 + int(356 * progress)
            canvas.coords(fill, 2, 2, fill_width, 22)
            status_lbl.config(text=f"{int(progress * 100)}% complete")
            if progress < 1.0:
                top.after(100, animate)
            else:
                top.destroy()
                try:
                    on_finish()
                except Exception as e:
                    print("on_finish error:", e)

        animate()

    def _after_connection_check(self):
        """
        At startup: if device(s) already connected, scan the first device and
        mark all currently-connected device serials as 'scanned' so monitor won't prompt again.
        If no device connected, mark initial_scan_done so monitor can prompt when a device connects.
        """
        try:
            devices = self.get_connected_devices()
        except Exception:
            devices = set()

        if not devices:
            messagebox.showinfo("Device Not Connected", "Your device is not connected.")
            # Mark initial auto-check as done so monitor can start working
            self.initial_scan_done.set()
            return
        else:
            # There are devices at startup.
            # Show connected message and scan the first device that exists (preserving behavior).
            # Then mark all currently-present devices as scanned to avoid later re-notifications.
            first_dev = next(iter(devices))
            # mark all currently connected devices as 'already scanned' to avoid duplicate prompts
            for d in devices:
                self.scanned_devices.add(d)

            # Inform user and run the initial scan for the first device
            model_name = self.get_device_model(first_dev)
            messagebox.showinfo("Device Connected", "Your mobile device is connected!")
            # mark scan in progress during the initial scan
            self.scanning_in_progress = True
            duration_scan = random.randint(15, 30)

            # When initial scan finishes we want to run _after_compromise_scan() which calls scan_device()
            # and then clear scanning flag and set initial_scan_done.
            self._show_progress_modal(
                title_text=f"Scanning your device ({model_name})...",
                duration_seconds=duration_scan,
                on_finish=self._after_compromise_scan
            )
            # Note: _after_compromise_scan will clear scanning flag and set initial_scan_done

    def _after_compromise_scan(self):
        try:
            # run the existing scan logic (now deeper)
            self.scan_device()
        except Exception as e:
            print("scan_device error:", e)
        finally:
            # initial auto-check / scan is finished — allow the monitor to start prompting
            self.scanning_in_progress = False
            self.initial_scan_done.set()

    def toggle_dropdown(self):
        """
        Show/hide the dropdown_frame containing attack-type buttons.
        It will always appear directly below the '🧠 Types of Attacks ▾' button
        and above the 'Tools' label + Kali/Nmap/Wireshark buttons.
        """
        try:
            if self.dropdown_visible:
                # Hide it
                self.dropdown_frame.pack_forget()
                self.btn_types.config(text="🧠 Types of Attacks ▾")
                self.dropdown_visible = False
            else:
                # Show it right BELOW the 'Types of Attacks' button
                self.dropdown_frame.pack(after=self.btn_types, pady=2, anchor="w")
                self.btn_types.config(text="🧠 Types of Attacks ▴")
                self.dropdown_visible = True
        except Exception as e:
            print("toggle_dropdown error:", e)

    def show_type_details(self, attack_type):
        # Clear right-side content (do not modify other app logic)
        for w in self.content_frame.winfo_children():
            w.destroy()

        title = tk.Label(
            self.content_frame,
            text=f"🧠 {attack_type}",
            font=("Arial", 18, "bold"),
            bg="white", fg="#1565c0"
        )
        title.pack(pady=(12, 8), anchor="w", padx=8)

        # long professional descriptions for each attack type (detailed briefs)
        descriptions = {
            "Network Attacks": (
                "Network Attacks — Professional Threat Brief\n\n"
                "Executive summary:\n"
                "Network attacks target the critical infrastructure responsible for transporting, switching, "
                "and securing network traffic: routers, switches, firewalls, VPN gateways, load balancers, and "
                "the protocol implementations that govern their behavior. The motivations range from data exfiltration "
                "and service disruption to establishing persistent footholds for downstream operations. Attackers leverage "
                "device vulnerabilities, misconfigurations, weak management access, and protocol weaknesses to achieve their objectives.\n\n"
                "Detailed tactics and execution:\n"
                "Adversaries typically begin with comprehensive reconnaissance — passive DNS, WHOIS, service discovery, "
                "and active port scanning — to build an inventory of reachable assets. They seek exposed management interfaces "
                "(SSH, Telnet, HTTP/HTTPS), outdated firmware, or default credentials. Common exploitation techniques include "
                "exploiting known CVEs in network device OS components, using stolen credentials for management planes, and "
                "leveraging supply-chain weaknesses to deploy malicious firmware or configuration changes.\n\n"
                "Once initial footholds are obtained, techniques for escalation include ARP/NDP spoofing, DNS manipulation, "
                "route injection (BGP hijacking), and protocol tunneling to traverse segmented environments. Attackers may "
                "deploy sniffers to capture sensitive traffic, redirect flows to infrastructure they control, or proxy communications "
                "through legitimate services to evade detection.\n\n"
                "Operational indicators and detection:\n"
                "Beacons that a network is under active attack often include unexpected routing changes, sudden anomalous "
                "traffic flows, asymmetric traffic patterns, a burst of failed authentication attempts to management interfaces, "
                "and new or unusual TLS certificates. Packet-level anomalies such as repetitive ARP requests, excessive DNS queries, "
                "or abnormal fragmentation can indicate manipulation. Good instrumentation (NetFlow/sFlow, enriched logs, IDS/IPS telemetry) "
                "is necessary to surface subtle anomalies before they escalate.\n\n"
                "Limitations and attacker constraints:\n"
                "Large-scale network attacks often require substantial infrastructure or compromised hosts (botnets). Sophisticated "
                "actors mitigate this by leveraging amplification vectors or embedding C2 into widely used protocols and cloud services. "
                "However, strong segmentation, rigorous access controls, and robust telemetry can significantly raise the cost and complexity "
                "for attackers.\n\n"
                "Defensive controls and mitigations:\n"
                "• Maintain an authoritative asset inventory and apply vendor firmware updates promptly. Remove or isolate legacy devices.\n"
                "• Enforce least-privilege admin access, unique credentials, and MFA for all management interfaces.\n"
                "• Implement network segmentation and micro-segmentation to limit lateral movement.\n"
                "• Deploy flow and packet telemetry (NetFlow, IDS/IPS) and correlate with endpoint and identity signals.\n"
                "• Use route monitoring and BGP origin validation where applicable. Employ DDoS mitigation and cloud-based scrubbing services "
                "for volumetric resilience.\n\n"
                "Final note:\n"
                "A layered defense that couples preventive hardening with real-time, context-rich detection and validated incident response playbooks "
                "is the most effective approach to reduce risk from network attacks."
            ),
            "Application Attacks": (
            "Application Attacks — Professional Threat Brief\n\n"
            "Executive summary:\n"
            "Application attacks target the application stack — web apps, APIs, mobile backends, and integrated services — where business logic "
            "and data processing occur. These attacks exploit coding errors, insecure design, weak authentication, and insecure dependencies, "
            "often yielding data breaches, account takeover, or remote code execution.\n\n"
            "Detailed tactics and execution:\n"
            "Typical approaches include input-based injections (SQL, command, LDAP), authentication bypass (session fixation, token tampering), "
            "authorization flaws (insecure direct object references, vertical privilege escalation), and abuse of APIs or business logic. Attackers "
            "may chain these with supply-chain compromises (malicious libraries) or unsafe deserialization to achieve remote execution. Automated scanners "
            "identify low-hanging vulnerabilities while skilled adversaries use custom payloads and blind testing techniques to extract data when direct errors are suppressed.\n\n"
            "Operational indicators and detection:\n"
            "Indicators include unusual query patterns (queries accessing metadata tables or performing wide UNION selects), abnormal API call sequences, "
            "unexpected POST requests to admin endpoints, and data exfiltration patterns such as large or frequent exports. Application logs, WAF alerts, "
            "and instrumentation from runtime agents provide critical signals.\n\n"
            "Limitations and attacker constraints:\n"
            "Exploitation typically requires a vulnerable code path or misconfigured service. Modern frameworks and safe libraries raise the bar when "
            "used correctly, but legacy systems and bespoke code often remain exposed. Detection is complicated by legitimate but complex traffic patterns.\n\n"
            "Defensive controls and mitigations:\n"
            "• Integrate security into the SDLC: SAST, DAST, dependency scanning, threat modeling, and secure code review.\n"
            "• Use parameterized queries, strict input validation, and avoid unsafe dynamic code execution.\n"
            "• Enforce strong authentication, session management, and least privilege for APIs. Use rate limits and anomaly detection for sensitive operations.\n"
            "• Employ runtime protections (WAF tuned to application behavior, RASP) and robust logging for forensic analysis.\n"
            "• Maintain an incident response capability that includes data recovery, rapid patching capability, and coordinated disclosure plans.\n\n"
            "Final note:\n"
            "Application security depends on reducing developer-introduced risk, continuously testing both code and dependencies, and having the telemetry to detect misuse quickly."
            ),
            "Physical Attacks": (
            "Physical Attacks — Professional Threat Brief\n\n"
            "Executive summary:\n"
            "Physical attacks compromise the tangible elements of information systems: hardware, storage media, supply-chain components, and the controlled "
            "spaces that house them. Because they bypass many purely digital controls, the consequences can include credential theft, hardware implants, "
            "and long-lived persistent access that is extremely difficult to remediate.\n\n"
            "Detailed tactics and execution:\n"
            "Physical tactics range from opportunistic theft (unlocked devices, unattended media) to sophisticated tampering (firmware implants, supply-chain insertion). "
            "Attackers may exploit logistics or maintenance windows to swap devices, introduce malicious peripherals, or install covert listening devices. Social engineering, "
            "tailgating, and compromised contractors are common enablers. In some cases, side-channel attacks (power, electromagnetic emanations) can leak sensitive information.\n\n"
            "Operational indicators and detection:\n"
            "Indicators are often non-digital: unexpected device behavior after maintenance, unexplained hardware changes, new MAC addresses on the network, or anomalous location "
            "of critical devices. Inventory reconciliation, tamper-evident seals, and physical access logs are key to detection. Digital telemetry may show new credentials, service registrations, "
            "or management-plane changes following a physical compromise.\n\n"
            "Limitations and attacker constraints:\n"
            "Physical attacks usually require local presence or collusion and thus are more expensive and targeted than many remote attacks. However, the payoff can be disproportionately high, "
            "especially against high-value targets or when combined with insider knowledge.\n\n"
            "Defensive controls and mitigations:\n"
            "• Physical security: controlled entry, card access, CCTV, badge audits, and visitor escorting.\n"
            "• Asset management: strict inventory, tamper-evident packaging, and chain-of-custody for devices in transit.\n"
            "• Device hardening: disk encryption, hardware-backed keys, secure boot, and locked configuration for management interfaces.\n"
            "• Personnel controls: background checks for contractors, least-privilege for maintenance accounts, and separation of duties.\n"
            "• Incident processes: rapid isolation of devices, forensic imaging, and coordinated legal/forensic response when physical tampering is suspected.\n\n"
            "Final note:\n"
            "Mitigating physical attacks requires thinking beyond software controls — investing in processes, physical controls, and supply-chain validation is essential."
            ),

            "Insider Threats": (
            "Insider Threats — Professional Threat Brief\n\n"
            "Executive summary:\n"
            "Insider threats originate from users or processes with legitimate access who misuse or inadvertently enable access to sensitive information. These can be "
            "malicious (disgruntled employees, espionage) or accidental (misconfiguration, negligent handling). Insiders are dangerous because they operate with valid credentials "
            "and context, which makes detection and prevention significantly harder.\n\n"
            "Detailed tactics and execution:\n"
            "Malicious insiders may exfiltrate data over extended periods using legitimate channels, create backdoors, or collude with external actors. Accidental insiders "
            "introduce risk through misconfigured cloud buckets, insecure sharing, or falling for social engineering that provides attackers with plausible access. "
            "Insider attacks often blend with privileged misuse, credential theft, or misuse of administrative tooling.\n\n"
            "Operational indicators and detection:\n"
            "Insider risk indicators include anomalous patterns of data access (large exports, off-hours access), privilege escalation events, repeated failed attempts at "
            "sensitive resources, or the creation of new admin connections. Behavioral analytics, DLP, and tight logging of privileged actions are primary detection mechanisms.\n\n"
            "Limitations and attacker constraints:\n"
            "Because insiders have legitimate access, technical controls alone may not be sufficient. Behavioral detection and strong process controls are required to limit impact.\n\n"
            "Defensive controls and mitigations:\n"
            "• Principle of least privilege: minimize standing access and use just-in-time elevation for sensitive actions.\n"
            "• Segregation of duties and approval workflows for high-risk operations.\n"
            "• DLP and exfiltration detection: monitor data movement, block suspicious transfers, and require approvals for bulk exports.\n"
            "• Personnel and process controls: background checks, exit protocols, and clear reporting channels for suspicious behavior.\n"
            "• Continuous monitoring and behavioral baselining to detect deviations from normal access patterns.\n\n"
            "Final note:\n"
            "Insider risk is as much organizational as technical — culture, HR practices, and clear governance combined with robust telemetry form the most effective defense."
            ),
        }

        # Create scrollable text area
        from tkinter import scrolledtext as st
        text_frame = tk.Frame(self.content_frame, bg="white")
        text_frame.pack(fill="both", expand=True, padx=10, pady=(0, 12))

        text_widget = st.ScrolledText(text_frame, wrap="word", font=("Arial", 11), height=20)
        text_widget.pack(fill="both", expand=True)
        text_widget.insert("1.0", descriptions.get(attack_type, "Description not available."))
        text_widget.config(state="disabled")
        text_widget.yview_moveto(0.0)

        # Add a small "Copy Summary" and "Zoom" bar below the text area (non-intrusive)
        ctrl_frame = tk.Frame(self.content_frame, bg="white")
        ctrl_frame.pack(fill="x", padx=10, pady=(0, 8))

        def copy_summary():
            try:
                txt = descriptions.get(attack_type, "")
                self.root.clipboard_clear()
                self.root.clipboard_append(txt)
                messagebox.showinfo("Copied", "Description copied to clipboard.")
            except Exception as e:
                messagebox.showerror("Copy failed", f"Could not copy: {e}")

        # Zoom handlers
        font_size = [11]

        def zoom_in():
            font_size[0] += 1
            text_widget.config(font=("Arial", font_size[0]))

        def zoom_out():
            if font_size[0] > 8:
                font_size[0] -= 1
                text_widget.config(font=("Arial", font_size[0]))

        tk.Button(ctrl_frame, text="Copy Summary", command=copy_summary, bg="#1565c0", fg="white").pack(side="left", padx=(0, 6))
        tk.Button(ctrl_frame, text="Zoom +", command=zoom_in, bg="#1565c0", fg="white").pack(side="left", padx=4)
        tk.Button(ctrl_frame, text="Zoom -", command=zoom_out, bg="#1565c0", fg="white").pack(side="left", padx=4)

    # DEVICE MONITOR
    def get_device_model(self, device_id):
        try:
            model_result = subprocess.run(
                ["adb", "-s", device_id, "shell", "getprop", "ro.product.model"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            return model_result.stdout.strip() or "Unknown Device"
        except Exception:
            return "Unknown Device"

    def monitor_device_connection(self):
        """
        Continuous monitor that runs during the session.
        It will wait until the initial auto-check finishes (initial_scan_done event)
        so they don't overlap. New devices are filtered against self.scanned_devices
        to avoid prompting for devices that were already scanned at startup or by the user.
        """

        prev_devices = set()
        while True:
            # Wait until initial auto-check completed (either found or not found)
            if not self.initial_scan_done.is_set():
                # Sleep briefly and loop — do not block UI
                time.sleep(0.2)
                continue

            try:
                result = subprocess.run(["adb", "devices"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                lines = result.stdout.strip().split("\n")
                devices = {line.split()[0] for line in lines[1:] if "device" in line and not line.startswith("List")}
                new_devices = devices - prev_devices
                removed_devices = prev_devices - devices

                # Only prompt for new devices that have NOT been scanned in this session
                unscanned_new = {d for d in new_devices if d not in self.scanned_devices}

                for dev in unscanned_new:
                    # fetch model name (safe quick call)
                    model_name = self.get_device_model(dev)
                    # Schedule a check on the main thread. If scanning is in progress,
                    # the helper _notify_device_arrival will wait and retry.
                    self.root.after(0, lambda d=dev, m=model_name: self._notify_device_arrival(d, m))

                # If devices were removed, remove their IDs from scanned_devices so a reconnect triggers a new scan
                for removed in removed_devices:
                    try:
                        if removed in self.scanned_devices:
                            self.scanned_devices.discard(removed)
                        # schedule UI warning showing which device disconnected (if known)
                        self.root.after(0, (lambda rid=removed: messagebox.showwarning("Device Disconnected", f"Device Disconnected: {rid}")))

                    except Exception:
                        # schedule generic warning if something went wrong
                        self.root.after(0, lambda: messagebox.showwarning("Device Disconnected", "Device Disconnected!"))

                prev_devices = devices
            except Exception as e:
                print("ADB error:", e)
            time.sleep(2)

    def _notify_device_arrival(self, device_id, model_name):
        """
        Called on the main/UI thread when monitor detects a new device.
        If a scan is currently running, retry after a short delay until the scanner is free.
        """
        try:
            if self.scanning_in_progress:
                # try again after 1 second (UI-safe)
                self.root.after(1000, lambda: self._notify_device_arrival(device_id, model_name))
                return
            # not scanning -> prompt user with device info and pass device_id through ask_user_to_scan
            self.ask_user_to_scan(model_name, device_id=device_id)
        except Exception as e:
            print("notify_device_arrival error:", e)

    def ask_user_to_scan(self, model_name, device_id=None):
        user_choice = messagebox.askyesno("Device Connected", f"Device Connected: {model_name}\nDo you want to start scanning?")
        if user_choice:
            # mark scanning in progress while user-initiated scan runs
            self.scanning_in_progress = True

            # We want to run after_device_scan after progress modal finishes,
            # but also mark this device as scanned so monitor won't prompt again for it.
            def on_finish_wrapper():
                try:
                    # run the deep scan as part of user initiated scan:
                    self.after_device_scan()
                finally:
                    # Mark device as scanned (if we have its id) so the monitor won't notify again.
                    if device_id:
                        self.scanned_devices.add(device_id)

            self._show_progress_modal("Scanning your device...", 10, on_finish_wrapper)

    def after_device_scan(self):
        # run the deeper scan (non-destructive) and show results
        try:
            self.scan_device()
        except Exception as e:
            print("after_device_scan scan error:", e)
        finally:
            # scanning finished - clear flag so monitor can prompt later
            self.scanning_in_progress = False

    # Device check helpers moved from Login (unchanged logic)
    def is_device_connected(self):
        """Return True if adb reports an attached & authorized device. If adb not available, fallback to False."""
        try:
            res = subprocess.run(["adb", "devices"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
            out = (res.stdout or "") + (res.stderr or "")
            lines = [l.strip() for l in out.splitlines() if l.strip()]
            for line in lines:
                if line.lower().startswith("list of devices"):
                    continue
                # adb lines like: <serial>\tdevice  or "<serial> device"
                if "\tdevice" in line or line.endswith("device"):
                    # ensure it's not "unauthorized"
                    if "unauthorized" in line.lower():
                        return False
                    return True
            return False
        except Exception:
            # adb missing or error -> consider not connected
            return False

    def scan_device(self, ip=None, allow_remote_connect=False):
        """
        Professional deep Android compromise scanner via ADB.
        Non-destructive, structured risk scoring, and detailed evidence logging.

        Parameters:
            ip (str): Optional IP address for remote device (e.g., 192.168.1.10)
            allow_remote_connect (bool): Must be True to attempt adb connect <ip>

        Returns:
            compromised (bool), risk_score (int), csv_path (str)
        """
        import subprocess, os, csv, time, re, socket
        from tkinter import messagebox

        # Setup
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        folder = "scans"
        os.makedirs(folder, exist_ok=True)
        csv_path = os.path.join(folder, f"scan_report_{timestamp}.csv")
        raw_log = os.path.join(folder, f"scan_raw_{timestamp}.log")

        def log_raw(line):
            with open(raw_log, "a", encoding="utf-8") as f:
                f.write(f"[{time.strftime('%H:%M:%S')}] {line}\n")

        def adb_run(cmd, timeout=8):
            try:
                p = subprocess.run(["adb"] + cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   text=True, timeout=timeout)
                out = (p.stdout or "") + (p.stderr or "")
                log_raw(f"$ adb {' '.join(cmd)}\n{out}\n{'-'*40}")
                return out.strip()
            except Exception as e:
                log_raw(f"ADB ERROR: {e}")
                return ""

        def adb_shell(cmd, timeout=8):
            if isinstance(cmd, str):
                cmd = [cmd]
            return adb_run(["shell"] + cmd, timeout=timeout)

        # Pre-checks
        adb_ok = adb_run(["version"])
        if not adb_ok:
            messagebox.showerror("ADB Error", "ADB not found or not in PATH.")
            return False, 0, csv_path

        if ip and allow_remote_connect:
            conn = adb_run(["connect", ip], timeout=10)
            log_raw(f"ADB connect result: {conn}")

        devs = adb_run(["devices", "-l"])
        if "device" not in devs.lower():
            messagebox.showerror("No Device", "No ADB device connected or authorized.")
            return False, 0, csv_path

        # Begin scan
        compromised = False
        possible_attacks = []
        results = []
        category_scores = {
            "remote": 0,
            "persistence": 0,
            "privilege": 0,
            "evasion": 0,
            "evidence": 0
        }

        def mark(category, reason, points):
            results.append(f"[{category.upper()}] {reason}")
            category_scores[category] = max(category_scores[category], points)
            log_raw(f"Indicator -> {category}: {reason} (+{points})")

        # 1) ADB properties
        ro_debuggable = adb_shell("getprop ro.debuggable")
        if ro_debuggable.strip() == "1":
            mark("evasion", "ADB debugging enabled (ro.debuggable=1)", 10)

        tcp_port = adb_shell("getprop service.adb.tcp.port") or adb_shell("getprop persist.adb.tcp.port")
        netstat = adb_shell("netstat -tuln") or adb_shell("ss -ltn")
        if "5555" in tcp_port or "5555" in netstat:
            mark("remote", "ADB over TCP (port 5555 open)", 25)

        # 2) Suspicious packages
        pkgs = adb_shell("pm list packages -3")
        if not pkgs:
            pkgs = adb_shell("pm list packages")
        sus_keywords = [
            "spy", "rat", "trojan", "keylogger", "remote",
            "vnc", "frida", "teamviewer", "mspy", "droidjack", "flexispy"
        ]
        sus_found = [kw for kw in sus_keywords if kw in (pkgs or "").lower()]
        if sus_found:
            mark("persistence", f"Suspicious package keywords found: {', '.join(sus_found)}", 25)

        # 3) Root/su binaries
        for path in ["/system/xbin/su", "/system/bin/su", "/sbin/su", "/su/bin/su"]:
            if "No such" not in adb_shell(f"ls {path}"):
                mark("privilege", f"Root binary found at {path}", 20)
                break

        which_su = adb_shell("which su")
        if which_su and "no su" not in which_su.lower():
            mark("privilege", f"'su' binary present: {which_su.strip()}", 20)

        # 4) SELinux
        selinux = adb_shell("getenforce")
        if selinux and selinux.lower() != "enforcing":
            mark("evasion", f"SELinux not enforcing ({selinux})", 10)

        # 5) Verified Boot / Build tags
        vbstate = adb_shell("getprop ro.boot.verifiedbootstate")
        tags = adb_shell("getprop ro.build.tags")
        if ("orange" in (vbstate or "").lower() or
            "yellow" in (vbstate or "").lower() or
            "test-keys" in (tags or "").lower()):
            mark("evasion", f"Non-production build or verified boot off (state={vbstate}, tags={tags})", 10)

        # 6) Accessibility / Device Admin
        acc = adb_shell("settings get secure enabled_accessibility_services")
        if acc and acc.strip() != "null":
            mark("persistence", f"Accessibility services enabled: {acc}", 15)

        admins = adb_shell("dumpsys device_policy | grep 'admin'")
        if admins and "admin" in admins.lower():
            mark("persistence", "Device admin apps active", 10)

        # 7) Frida / instrumentation detection
        ps = adb_shell("ps -A")
        if re.search(r"frida|xposed|substrate|magisk", ps or "", re.I):
            mark("evasion", "Frida/Xposed/Magisk process detected", 20)

        tcp = adb_shell("cat /proc/net/tcp")
        if "27042" in (tcp or "") or "27043" in (tcp or ""):
            mark("remote", "Frida-like port (27042/27043) listening", 25)

        # 8) /system writable
        mounts = adb_shell("mount")
        if any(" /system " in ln and "rw" in ln for ln in (mounts or "").splitlines()):
            mark("privilege", "/system partition mounted writable", 15)

        # 9) Suspicious hosts file entries
        hosts = adb_shell("cat /etc/hosts")
        if any(bad in (hosts or "").lower() for bad in ["malicious", "ads", "tracking"]):
            mark("evidence", "Suspicious entries in /etc/hosts", 10)

        # 10) Logcat indicators
        logs = (adb_shell("logcat -d -t 100 | grep -i 'frida\\|su\\|xposed\\|exploit'") or "")[:500]
        if logs:
            mark("evidence", "Suspicious traces in logcat", 10)

        # Risk score aggregation
        risk_score = min(100, sum(category_scores.values()))
        compromised = risk_score >= 25  # threshold for 'compromised'

        #  Save CSV Report
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Scan Timestamp", timestamp])
            writer.writerow(["Device Status", "COMPROMISED" if compromised else "SAFE"])
            writer.writerow(["Total Risk Score (0–100)", risk_score])
            writer.writerow([])
            writer.writerow(["Category", "Score"])
            for cat, val in category_scores.items():
                writer.writerow([cat, val])
            writer.writerow([])
            writer.writerow(["Detected Indicators"])
            for r in results:
                writer.writerow([r])
            writer.writerow([])
            writer.writerow(["Raw Log File", raw_log])

        #  User Feedback 
        if compromised:
            msg = (
                f"⚠️ Device appears COMPROMISED!\n\n"
                f"Risk Score: {risk_score}/100\n\n"
                f"Possible Issues:\n - " + "\n - ".join(set(r for r in results)) +
                f"\n\nFull log saved to:\n{raw_log}"
            )
            messagebox.showerror("Scan Result - Compromised", msg)
        else:
            msg = (
                f"✅ Device appears SAFE.\n\n"
                f"Risk Score: {risk_score}/100\n\n"
                f"Detailed log saved to:\n{raw_log}"
            )
            messagebox.showinfo("Scan Result - Safe", msg)

        return compromised, risk_score, csv_path


if __name__ == "__main__":
    root = tk.Tk()
    username = sys.argv[1] if len(sys.argv) > 1 else "Guest"
    gmail = sys.argv[2] if len(sys.argv) > 2 else "guest@example.com"
    phone = sys.argv[3] if len(sys.argv) > 3 else "0000000000"

    app = UserDashboard(root, username=username, gmail=gmail, phone=phone)
    root.mainloop()
