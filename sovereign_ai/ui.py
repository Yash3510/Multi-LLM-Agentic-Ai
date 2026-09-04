import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from .auth import AuthService
from .conversations import ConversationService
from .files import FileService
from .health import check
from .markdown import render


class SovereignApp(tk.Tk):
    def __init__(self, db, provider, settings):
        super().__init__()
        self.title("Sovereign AI | Local Workbench")
        self.geometry("1120x720")
        self.minsize(860, 560)
        self.db, self.provider, self.settings = db, provider, settings
        self.auth, self.conversations = AuthService(db), ConversationService(db)
        self.files = FileService(db, settings.storage_dir)
        self.current_conversation = None
        self.model_var = tk.StringVar(value=settings.default_model)
        self.stop_event = threading.Event()
        self._style()
        self.show_auth()

    def _style(self):
        self.configure(bg="#101820")
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TButton", padding=8, background="#1e4057", foreground="white")
        style.configure("TLabel", background="#101820", foreground="#d8e5ed")
        style.configure("Title.TLabel", font=("Segoe UI", 22, "bold"), foreground="#f4b942")
        style.configure("Card.TFrame", background="#172631")

    def clear(self):
        for widget in self.winfo_children(): widget.destroy()

    def show_auth(self):
        self.clear()
        frame = ttk.Frame(self, padding=42, style="Card.TFrame")
        frame.place(relx=.5, rely=.5, anchor="center", width=430, height=360)
        ttk.Label(frame, text="SOVEREIGN AI", style="Title.TLabel").pack(pady=(18, 4))
        ttk.Label(frame, text="Fully local industrial knowledge workbench").pack(pady=(0, 24))
        if not self.auth.has_admin():
            self._auth_form(frame, True)
        else:
            self._auth_form(frame, False)

    def _auth_form(self, parent, setup):
        ttk.Label(parent, text="Create administrator" if setup else "Local sign in").pack(anchor="w")
        user = ttk.Entry(parent); user.pack(fill="x", pady=(6, 12)); user.focus_set()
        password = ttk.Entry(parent, show="*"); password.pack(fill="x", pady=(0, 20))
        if setup: ttk.Label(parent, text="Minimum 8-character password").pack(anchor="w")
        def submit():
            try:
                if setup:
                    self.auth.create_admin(user.get(), password.get()); messagebox.showinfo("Ready", "Administrator created.")
                elif not self.auth.login(user.get(), password.get()):
                    raise ValueError("Invalid username or password")
                self.show_main()
            except Exception as exc: messagebox.showerror("Authentication", str(exc))
        ttk.Button(parent, text="Create and continue" if setup else "Sign in", command=submit).pack(fill="x", pady=12)
        password.bind("<Return>", lambda _: submit())

    def show_main(self):
        self.clear()
        self.sidebar = ttk.Frame(self, padding=18, style="Card.TFrame"); self.sidebar.pack(side="left", fill="y")
        ttk.Label(self.sidebar, text="SOVEREIGN AI", style="Title.TLabel").pack(anchor="w", pady=(0, 28))
        self.model_box = ttk.Combobox(self.sidebar, textvariable=self.model_var, values=list(self.provider.list_models()) or [self.settings.default_model], state="normal", width=22)
        self.model_box.pack(anchor="w", pady=(0, 20))
        ttk.Button(self.sidebar, text="+ New conversation", command=self.new_conversation).pack(fill="x", pady=3)
        ttk.Label(self.sidebar, text="History").pack(anchor="w", pady=(22, 5))
        self.history = tk.Listbox(self.sidebar, height=10, width=24, bg="#0b1218", fg="#d8e5ed", relief="flat", highlightthickness=0)
        self.history.pack(fill="x", pady=(0, 8))
        self.history.bind("<<ListboxSelect>>", self.select_conversation)
        self.refresh_history()
        ttk.Button(self.sidebar, text="Files", command=self.show_files).pack(fill="x", pady=3)
        ttk.Button(self.sidebar, text="System status", command=self.show_status).pack(fill="x", pady=3)
        ttk.Button(self.sidebar, text="Settings", command=self.show_settings).pack(fill="x", pady=3)
        ttk.Button(self.sidebar, text="Logout", command=self.show_auth).pack(fill="x", pady=(26, 3))
        self.body = ttk.Frame(self, padding=24); self.body.pack(side="right", expand=True, fill="both")
        self.show_chat()

    def refresh_history(self):
        self.history.delete(0, "end")
        for row in self.conversations.list():
            self.history.insert("end", f"{row['id']}: {row['title'][:20]}")

    def select_conversation(self, _event=None):
        selected = self.history.curselection()
        if selected:
            rows = self.conversations.list()
            self.current_conversation = rows[selected[0]]["id"]
            self.show_chat()

    def new_conversation(self):
        self.current_conversation = self.conversations.create("New conversation", self.model_var.get()); self.show_chat()

    def show_chat(self):
        for widget in self.body.winfo_children(): widget.destroy()
        ttk.Label(self.body, text="Chat workspace", style="Title.TLabel").pack(anchor="w")
        self.chat = tk.Text(self.body, wrap="word", bg="#0b1218", fg="#d8e5ed", insertbackground="white", relief="flat", padx=18, pady=16)
        self.chat.pack(expand=True, fill="both", pady=16); self.chat.configure(state="disabled")
        bottom = ttk.Frame(self.body); bottom.pack(fill="x")
        self.prompt = tk.Text(bottom, height=3, wrap="word", bg="#172631", fg="white", insertbackground="white", relief="flat", padx=10, pady=8); self.prompt.pack(side="left", expand=True, fill="x")
        ttk.Button(bottom, text="Stop", command=self.stop_generation).pack(side="left", padx=(10, 0))
        ttk.Button(bottom, text="Send", command=self.send).pack(side="left", padx=(6, 0))
        if self.current_conversation:
            for row in self.conversations.messages(self.current_conversation): self.append_chat(row["role"], row["content"])

    def stop_generation(self):
        self.stop_event.set()

    def append_chat(self, role, content):
        self.chat.configure(state="normal")
        self.chat.insert("end", f"{role.upper()}\n", "heading")
        render(self.chat, content)
        self.chat.insert("end", "\n\n")
        self.chat.see("end"); self.chat.configure(state="disabled")

    def send(self):
        prompt = self.prompt.get("1.0", "end").strip()
        if not prompt: return
        if not self.current_conversation:
            self.new_conversation()
        self.prompt.delete("1.0", "end"); self.append_chat("user", prompt)
        self.conversations.add_message(self.current_conversation, "user", prompt)
        self.append_chat("assistant", "")
        self.stop_event.clear(); tokens = queue.Queue()
        messages = [dict(row) for row in self.conversations.messages(self.current_conversation)]
        def run():
            try: self.provider.stream(messages, self.model_var.get(), tokens.put, self.stop_event); tokens.put(None)
            except Exception as exc: tokens.put(f"\n[Local model error: {exc}]\n"); tokens.put(None)
        threading.Thread(target=run, daemon=True).start(); self._poll_tokens(tokens, "")
        self.refresh_history()

    def _poll_tokens(self, tokens, full):
        try:
            while True:
                token = tokens.get_nowait()
                if token is None:
                    if full: self.conversations.add_message(self.current_conversation, "assistant", full)
                    return
                full += token; self.chat.configure(state="normal"); self.chat.insert("end", token); self.chat.see("end"); self.chat.configure(state="disabled")
        except queue.Empty: self.after(50, self._poll_tokens, tokens, full)

    def show_files(self):
        for widget in self.body.winfo_children(): widget.destroy()
        ttk.Label(self.body, text="Secure files", style="Title.TLabel").pack(anchor="w")
        ttk.Button(self.body, text="Upload file", command=self.upload).pack(anchor="w", pady=16)
        self.file_list = tk.Listbox(self.body, bg="#0b1218", fg="#d8e5ed", relief="flat"); self.file_list.pack(expand=True, fill="both")
        for row in self.files.list_files(): self.file_list.insert("end", f"{row['original_name']}  |  {row['size']:,} bytes  |  {row['created_at']}")

    def upload(self):
        source = filedialog.askopenfilename()
        if source:
            try: self.files.store(source); self.show_files()
            except Exception as exc: messagebox.showerror("Upload", str(exc))

    def show_status(self):
        for widget in self.body.winfo_children(): widget.destroy()
        ttk.Label(self.body, text="System status", style="Title.TLabel").pack(anchor="w", pady=(0, 20))
        for name, (ok, detail) in check(self.db, self.provider, self.settings.storage_dir).items():
            ttk.Label(self.body, text=("● " if ok else "○ ") + f"{name}: {detail}", foreground="#74c69d" if ok else "#f28482").pack(anchor="w", pady=8)

    def show_settings(self):
        for widget in self.body.winfo_children(): widget.destroy()
        ttk.Label(self.body, text="Settings", style="Title.TLabel").pack(anchor="w", pady=(0, 20))
        ttk.Label(self.body, text="Local model backend").pack(anchor="w")
        ttk.Label(self.body, text=self.settings.local_model_url).pack(anchor="w", pady=(4, 18))
        ttk.Label(self.body, text="Data directory").pack(anchor="w")
        ttk.Label(self.body, text=str(self.settings.data_dir)).pack(anchor="w", pady=(4, 18))
        ttk.Label(self.body, text="Sovereignty mode: local-only\nNo cloud APIs, telemetry, or external search are configured.").pack(anchor="w")
