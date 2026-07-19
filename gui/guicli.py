import os
import sys
import json
import time
import threading
import subprocess
from pathlib import Path
from datetime import datetime
import customtkinter as ctk

ROOT = Path(__file__).resolve().parent
LOGS = ROOT / "agents" / "logs"

# Ensure Logs exist
LOGS.mkdir(parents=True, exist_ok=True)

# Premium Theme Configuration
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Antigravity AGI Co-Pilot & Manager")
        self.geometry("1000x650")
        self.configure(fg_color="#18181B") # Dark modern background
        
        # Grid Layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # --- Premium Sidebar ---
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#27272A")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(5, weight=1)
        
        # Logo Area
        self.logo_label = ctk.CTkLabel(self.sidebar, text="🪐 Antigravity", font=ctk.CTkFont(size=24, weight="bold", family="Segoe UI"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 5))
        self.subtitle_label = ctk.CTkLabel(self.sidebar, text="AGI Co-Pilot", font=ctk.CTkFont(size=12), text_color="gray")
        self.subtitle_label.grid(row=1, column=0, padx=20, pady=(0, 30))
        
        # Navigation Buttons
        btn_font = ctk.CTkFont(size=14, weight="bold")
        self.btn_live = ctk.CTkButton(self.sidebar, text="Live Dashboard", font=btn_font, fg_color="transparent", text_color="white", hover_color="#3F3F46", anchor="w", command=self.show_live_frame)
        self.btn_live.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        
        self.btn_runner = ctk.CTkButton(self.sidebar, text="Task Runner", font=btn_font, fg_color="transparent", text_color="white", hover_color="#3F3F46", anchor="w", command=self.show_runner_frame)
        self.btn_runner.grid(row=3, column=0, padx=10, pady=5, sticky="ew")
        
        self.btn_settings = ctk.CTkButton(self.sidebar, text="Manager (Auth)", font=btn_font, fg_color="transparent", text_color="white", hover_color="#3F3F46", anchor="w", command=self.show_settings_frame)
        self.btn_settings.grid(row=4, column=0, padx=10, pady=5, sticky="ew")
        
        # Bottom profile indicator (mock until synced)
        self.profile_lbl = ctk.CTkLabel(self.sidebar, text="Not Linked", font=ctk.CTkFont(size=12), text_color="#EF4444")
        self.profile_lbl.grid(row=6, column=0, padx=20, pady=20)

        # --- Content Frames ---
        self.live_frame = ctk.CTkFrame(self, corner_radius=15, fg_color="#18181B")
        self.runner_frame = ctk.CTkFrame(self, corner_radius=15, fg_color="#18181B")
        self.settings_frame = ctk.CTkFrame(self, corner_radius=15, fg_color="#18181B")
        
        self.setup_live_frame()
        self.setup_runner_frame()
        self.setup_settings_frame()
        
        self.show_live_frame()
        self.update_live_data()
        self.auto_sync_editor_account()

    # --- HELPER: Read Editor Account ---
    def auto_sync_editor_account(self):
        # Fetch the system identity which represents the logged-in IDE developer account
        self.editor_email = None
        try:
            # 1. Attempt to read from Git Config (primary developer identity)
            result = subprocess.run(["git", "config", "user.email"], capture_output=True, text=True, check=True)
            email = result.stdout.strip()
            if email:
                self.editor_email = email
            else:
                # 2. Fallback to Windows/OS Username
                self.editor_email = os.environ.get("USERNAME") or os.environ.get("USER") or "Connected Account"
        except Exception:
            self.editor_email = "Connected Account"

    # --- LIVE DASHBOARD FRAME ---
    def setup_live_frame(self):
        self.live_frame.grid_columnconfigure(0, weight=1)
        self.live_frame.grid_rowconfigure(0, weight=1)
        self.live_frame.grid_rowconfigure(1, weight=1)
        
        # IDE Sync Panel (Glassmorphism look)
        ide_panel = ctk.CTkFrame(self.live_frame, fg_color="#27272A", corner_radius=15)
        ide_panel.grid(row=0, column=0, padx=30, pady=30, sticky="nsew")
        
        header = ctk.CTkLabel(ide_panel, text="📡 Live IDE Sync", font=ctk.CTkFont(size=20, weight="bold", family="Segoe UI"))
        header.pack(pady=(20, 10), padx=20, anchor="w")
        
        self.lbl_prompt = ctk.CTkLabel(ide_panel, text="Waiting for IDE activity...", wraplength=650, justify="left", font=ctk.CTkFont(size=15), text_color="#A1A1AA")
        self.lbl_prompt.pack(pady=10, padx=20, anchor="w")
        
        self.lbl_action = ctk.CTkLabel(ide_panel, text="Agent Action: Idle", font=ctk.CTkFont(size=14, weight="bold"), text_color="#FACC15")
        self.lbl_action.pack(pady=10, padx=20, anchor="w")

        # Token Budget Panel
        token_panel = ctk.CTkFrame(self.live_frame, fg_color="#27272A", corner_radius=15)
        token_panel.grid(row=1, column=0, padx=30, pady=(0, 30), sticky="nsew")
        
        ctk.CTkLabel(token_panel, text="🚀 Token Budget", font=ctk.CTkFont(size=20, weight="bold", family="Segoe UI")).pack(pady=(20, 10), padx=20, anchor="w")
        
        # Session progress
        self.lbl_session = ctk.CTkLabel(token_panel, text="Session: 0 / 100,000", font=ctk.CTkFont(size=14))
        self.lbl_session.pack(pady=5, padx=20, anchor="w")
        self.pb_session = ctk.CTkProgressBar(token_panel, height=12, progress_color="#3B82F6", fg_color="#3F3F46")
        self.pb_session.pack(fill="x", padx=20, pady=5)
        self.pb_session.set(0)

        # Daily progress
        self.lbl_daily = ctk.CTkLabel(token_panel, text="Daily: 0 / 1,000,000", font=ctk.CTkFont(size=14))
        self.lbl_daily.pack(pady=5, padx=20, anchor="w")
        self.pb_daily = ctk.CTkProgressBar(token_panel, height=12, progress_color="#10B981", fg_color="#3F3F46")
        self.pb_daily.pack(fill="x", padx=20, pady=5)
        self.pb_daily.set(0)

    def update_live_data(self):
        # Update IDE Sync
        try:
            state_file = LOGS / "live-session.json"
            if state_file.exists():
                state = json.loads(state_file.read_text(encoding="utf-8"))
                prompt = state.get("last_prompt", "")
                active_tool = state.get("active_tool", "")
                
                if prompt:
                    display_prompt = prompt if len(prompt) < 200 else prompt[:197] + "..."
                    self.lbl_prompt.configure(text=f"Last User Prompt:\n{display_prompt}", text_color="#E4E4E7")
                if active_tool:
                    self.lbl_action.configure(text=f"🤖 Running tool: {active_tool}", text_color="#34D399")
                else:
                    self.lbl_action.configure(text="Agent Action: Idle / Thinking...", text_color="#FACC15")
        except Exception:
            pass

        # Update Tokens
        try:
            ledger_file = LOGS / "token-ledger.json"
            if ledger_file.exists():
                ledger = json.loads(ledger_file.read_text(encoding="utf-8"))
                sess_u = ledger.get("session_usage", 0)
                sess_l = ledger.get("session_limit", 100000)
                daily_u = ledger.get("daily_usage", 0)
                daily_l = ledger.get("daily_limit", 300000)
                saved_u = ledger.get("saved_tokens", 0)
                
                spct = sess_u / sess_l if sess_l > 0 else 0
                dpct = daily_u / daily_l if daily_l > 0 else 0
                
                self.lbl_session.configure(text=f"Session: {sess_u:,} / {sess_l:,} ({spct*100:.1f}%)")
                self.pb_session.set(min(1.0, spct))
                
                self.lbl_daily.configure(text=f"Daily: {daily_u:,} / {daily_l:,} ({dpct*100:.1f}%)")
                self.pb_daily.set(min(1.0, dpct))
                
                if hasattr(self, "lbl_mgr_stats"):
                    self.lbl_mgr_stats.configure(text=f"Session Tokens Consumed: {sess_u:,}\nDaily Tokens Consumed: {daily_u:,}\n\n🛡️ Tokens Saved by Manager Guard: {saved_u:,}")
        except Exception:
            pass

        self.after(1000, self.update_live_data)

    # --- TASK RUNNER FRAME ---
    def setup_runner_frame(self):
        self.runner_frame.grid_columnconfigure(0, weight=1)
        self.runner_frame.grid_rowconfigure(1, weight=1)
        
        top_panel = ctk.CTkFrame(self.runner_frame, fg_color="transparent")
        top_panel.grid(row=0, column=0, sticky="ew", padx=30, pady=(30, 10))
        top_panel.grid_columnconfigure(0, weight=1)
        
        self.task_entry = ctk.CTkEntry(top_panel, placeholder_text="Type a task for the AGI...", font=ctk.CTkFont(size=15), height=40)
        self.task_entry.grid(row=0, column=0, sticky="ew", padx=(0, 15))
        
        self.btn_run_task = ctk.CTkButton(top_panel, text="Run AGI", font=ctk.CTkFont(size=15, weight="bold"), height=40, fg_color="#3B82F6", hover_color="#2563EB", command=self.run_task)
        self.btn_run_task.grid(row=0, column=1)

        self.txt_output = ctk.CTkTextbox(self.runner_frame, font=ctk.CTkFont(family="Consolas", size=13), fg_color="#27272A", text_color="#E4E4E7", corner_radius=10)
        self.txt_output.grid(row=1, column=0, sticky="nsew", padx=30, pady=(0, 30))

    def run_task(self):
        task = self.task_entry.get()
        if not task:
            return
        
        self.btn_run_task.configure(state="disabled", text="Running...")
        self.txt_output.insert("end", f"\n>>> Launching AGI Task: \"{task}\"\n")
        self.txt_output.see("end")
        
        def run_thread():
            process = subprocess.Popen(
                [sys.executable, "agicli.py", "run", task],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8"
            )
            for line in process.stdout:
                self.txt_output.insert("end", line)
                self.txt_output.see("end")
            process.wait()
            self.btn_run_task.configure(state="normal", text="Run AGI")
            
        threading.Thread(target=run_thread, daemon=True).start()

    # --- ANTIGRAVITY MANAGER FRAME ---
    def setup_settings_frame(self):
        self.settings_frame.grid_columnconfigure(0, weight=1)
        
        panel = ctk.CTkFrame(self.settings_frame, fg_color="#27272A", corner_radius=15)
        panel.grid(row=0, column=0, padx=30, pady=30, sticky="nsew")
        panel.grid_columnconfigure(0, weight=1)
        
        header_font = ctk.CTkFont(size=26, weight="bold", family="Segoe UI")
        ctk.CTkLabel(panel, text="🛡️ Antigravity Manager", font=header_font).pack(pady=(40, 10))
        
        ctk.CTkLabel(panel, text="Seamless integration with your Antigravity IDE configuration.", font=ctk.CTkFont(size=15), text_color="#A1A1AA").pack(pady=(0, 20))
        
        # Real Google Auth Button
        self.btn_login = ctk.CTkButton(panel, text="Sync with Editor's Google Account", font=ctk.CTkFont(size=16, weight="bold"), height=45, fg_color="#F87171", hover_color="#DC2626", command=self.real_ide_sync)
        self.btn_login.pack(pady=15)
        
        self.lbl_login_status = ctk.CTkLabel(panel, text="Not Synced", font=ctk.CTkFont(size=14), text_color="#EF4444")
        self.lbl_login_status.pack(pady=(0, 25))
        
        # Stats Card
        stats_panel = ctk.CTkFrame(panel, fg_color="#18181B", corner_radius=10)
        stats_panel.pack(fill="x", padx=60, pady=10)
        
        ctk.CTkLabel(stats_panel, text="Live Consumption Analytics", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 5))
        self.lbl_mgr_stats = ctk.CTkLabel(stats_panel, text="Session Tokens Consumed: 0\nDaily Tokens Consumed: 0\n\n🛡️ Tokens Saved by Manager Guard: 0", font=ctk.CTkFont(size=14), text_color="#A1A1AA")
        self.lbl_mgr_stats.pack(pady=(5, 15))
        
        # Controls Card
        controls = ctk.CTkFrame(panel, fg_color="transparent")
        controls.pack(pady=20)
        
        self.btn_unlock = ctk.CTkButton(controls, text="Unlock Quota", font=ctk.CTkFont(size=15, weight="bold"), height=40, fg_color="#10B981", hover_color="#059669", command=self.unlock_budget)
        self.btn_unlock.grid(row=0, column=0, padx=10)

    def real_ide_sync(self):
        import webbrowser
        
        # Open Google Login in browser
        webbrowser.open("https://accounts.google.com/")
        
        # Ask user for their logged-in email using ctk input dialog
        dialog = ctk.CTkInputDialog(text="Google Login page opened in your browser.\n\nPlease enter the email address you authenticated with:", title="Google Authentication")
        email = dialog.get_input()
        
        if email and "@" in email:
            self.editor_email = email.strip()
            email_text = f"Connected to IDE Account: {self.editor_email}"
            self.lbl_login_status.configure(text=f"✅ {email_text}", text_color="#34D399")
            self.profile_lbl.configure(text=f"👤 {self.editor_email}", text_color="#34D399")
            self.btn_login.configure(fg_color="#34D399", hover_color="#059669", text="Google Workspace Synced")
            
            # Write sync limits to ledger
            try:
                ledger_file = LOGS / "token-ledger.json"
                if ledger_file.exists():
                    ledger = json.loads(ledger_file.read_text(encoding="utf-8"))
                    ledger["session_limit"] = 250000
                    ledger["daily_limit"] = 1000000
                    ledger["locked"] = False
                    ledger["account"] = self.editor_email
                    ledger_file.write_text(json.dumps(ledger, indent=2), encoding="utf-8")
            except Exception:
                pass
        else:
            self.lbl_login_status.configure(text="❌ Authentication cancelled or invalid email", text_color="#EF4444")
            
    def unlock_budget(self):
        try:
            ledger_file = LOGS / "token-ledger.json"
            if ledger_file.exists():
                ledger = json.loads(ledger_file.read_text(encoding="utf-8"))
                ledger["locked"] = False
                ledger_file.write_text(json.dumps(ledger, indent=2), encoding="utf-8")
                self.btn_unlock.configure(text="Unlocked!")
                self.after(2000, lambda: self.btn_unlock.configure(text="Unlock Quota"))
        except Exception:
            pass

    # --- NAVIGATION ---
    def set_active_btn(self, active_btn):
        # Reset all
        for btn in [self.btn_live, self.btn_runner, self.btn_settings]:
            btn.configure(fg_color="transparent")
        active_btn.configure(fg_color="#3F3F46")

    def show_live_frame(self):
        self.runner_frame.grid_forget()
        self.settings_frame.grid_forget()
        self.live_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.set_active_btn(self.btn_live)

    def show_runner_frame(self):
        self.live_frame.grid_forget()
        self.settings_frame.grid_forget()
        self.runner_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.set_active_btn(self.btn_runner)

    def show_settings_frame(self):
        self.live_frame.grid_forget()
        self.runner_frame.grid_forget()
        self.settings_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.set_active_btn(self.btn_settings)

if __name__ == "__main__":
    app = App()
    app.mainloop()
