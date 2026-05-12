"""
ui.py

Tkinter GUI layer.
Handles:
- Drag and drop
- User interaction
- Progress updates
- Notifications
"""

import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from tkinterdnd2 import DND_FILES, TkinterDnD

from crypto_utils import encrypt_file, decrypt_file


class SecureFileEncryptorUI:

    def __init__(self):

        self.root = TkinterDnD.Tk()

        self.root.title("Secure File Encryptor")

        self.root.geometry("760x500")

        self.root.configure(bg="#101820")

        self.selected_file = None

        self.setup_styles()

        self.create_widgets()

    def setup_styles(self):

        style = ttk.Style()

        style.theme_use("clam")

        style.configure(
            "TButton",
            font=("Segoe UI", 11, "bold"),
            padding=10
        )

        style.configure(
            "Cyber.TFrame",
            background="#101820"
        )

        style.configure(
            "Cyber.TLabel",
            background="#101820",
            foreground="#00FFCC",
            font=("Segoe UI", 11)
        )

    def create_widgets(self):

        frame = ttk.Frame(self.root, style="Cyber.TFrame")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        title = tk.Label(
            frame,
            text="SECURE FILE ENCRYPTOR",
            bg="#101820",
            fg="#00FFCC",
            font=("Consolas", 24, "bold")
        )
        title.pack(pady=20)

        self.drop_label = tk.Label(
            frame,
            text="Drag & Drop File Here",
            bg="#1B2838",
            fg="white",
            relief="ridge",
            height=5,
            font=("Segoe UI", 12)
        )

        self.drop_label.pack(fill="x", pady=10)

        self.drop_label.drop_target_register(DND_FILES)

        self.drop_label.dnd_bind("<<Drop>>", self.handle_drop)

        btn_frame = ttk.Frame(frame, style="Cyber.TFrame")
        btn_frame.pack(pady=10)

        ttk.Button(
            btn_frame,
            text="Select File",
            command=self.select_file
        ).grid(row=0, column=0, padx=10)

        ttk.Button(
            btn_frame,
            text="Encrypt",
            command=self.encrypt_action
        ).grid(row=0, column=1, padx=10)

        ttk.Button(
            btn_frame,
            text="Decrypt",
            command=self.decrypt_action
        ).grid(row=0, column=2, padx=10)

        ttk.Button(
            btn_frame,
            text="Clear",
            command=self.clear_ui
        ).grid(row=0, column=3, padx=10)

        self.file_label = ttk.Label(
            frame,
            text="No file selected",
            style="Cyber.TLabel"
        )

        self.file_label.pack(pady=10)

        self.size_label = ttk.Label(
            frame,
            text="",
            style="Cyber.TLabel"
        )

        self.size_label.pack()

        password_frame = ttk.Frame(frame, style="Cyber.TFrame")
        password_frame.pack(pady=10)

        ttk.Label(
            password_frame,
            text="Password:",
            style="Cyber.TLabel"
        ).grid(row=0, column=0, padx=5)

        self.password_entry = tk.Entry(
            password_frame,
            show="*",
            width=40,
            bg="#1B2838",
            fg="white",
            insertbackground="white"
        )

        self.password_entry.grid(row=0, column=1)

        self.progress = ttk.Progressbar(
            frame,
            orient="horizontal",
            mode="determinate",
            length=500
        )

        self.progress.pack(pady=20)

        self.status_label = ttk.Label(
            frame,
            text="Ready",
            style="Cyber.TLabel"
        )

        self.status_label.pack()

    def handle_drop(self, event):

        file_path = event.data.strip("{}")

        self.load_file(file_path)

    def select_file(self):

        path = filedialog.askopenfilename()

        if path:
            self.load_file(path)

    def load_file(self, path):

        self.selected_file = path

        self.file_label.config(
            text=f"Selected: {os.path.basename(path)}"
        )

        size_mb = os.path.getsize(path) / (1024 * 1024)

        self.size_label.config(
            text=f"Size: {size_mb:.2f} MB"
        )

    def update_progress(self, current, total):

        percent = (current / total) * 100

        self.progress["value"] = percent

        self.status_label.config(
            text=f"{percent:.1f}%"
        )

        self.root.update_idletasks()

    def encrypt_action(self):

        if not self.validate():
            return

        output = self.selected_file + ".sfe"

        threading.Thread(
            target=self.run_encrypt,
            args=(output,),
            daemon=True
        ).start()

    def decrypt_action(self):

        if not self.validate():
            return

        output = self.selected_file.replace(".sfe", "_decrypted")

        threading.Thread(
            target=self.run_decrypt,
            args=(output,),
            daemon=True
        ).start()

    def run_encrypt(self, output):

        try:

            encrypt_file(
                self.selected_file,
                output,
                self.password_entry.get(),
                self.update_progress
            )

            messagebox.showinfo(
                "Success",
                f"Encrypted:\n{output}"
            )

        except Exception as e:

            messagebox.showerror(
                "Error",
                str(e)
            )

    def run_decrypt(self, output):

        try:

            decrypt_file(
                self.selected_file,
                output,
                self.password_entry.get(),
                self.update_progress
            )

            messagebox.showinfo(
                "Success",
                f"Decrypted:\n{output}"
            )

        except Exception as e:

            messagebox.showerror(
                "Error",
                str(e)
            )

    def validate(self):

        if not self.selected_file:

            messagebox.showwarning(
                "Missing File",
                "Please select a file."
            )

            return False

        if not self.password_entry.get():

            messagebox.showwarning(
                "Missing Password",
                "Please enter a password."
            )

            return False

        return True

    def clear_ui(self):

        self.selected_file = None

        self.file_label.config(text="No file selected")

        self.size_label.config(text="")

        self.progress["value"] = 0

        self.status_label.config(text="Ready")

        self.password_entry.delete(0, tk.END)

    def run(self):

        self.root.mainloop()