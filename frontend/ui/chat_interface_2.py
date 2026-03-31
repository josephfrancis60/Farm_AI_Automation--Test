"""
Echo — Farm AI Agent Desktop UI (v4)
Refined HUD: Fixed message width (no more cut-offs), Added alert messages, Better spacing.
"""

import customtkinter as ctk
import tkinter as tk
import threading
import time
import os
import uuid
import queue
from datetime import datetime, timedelta, timezone
import sys
import requests # Added for health check

# Add the backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend")))

# ─── Optional Imports ───────────────────────────────────────────────────────
try:
    import speech_recognition as sr
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

# ─── Colors (exact match to HTML) ───────────────────────────────────────────
C = {
    "bg":          "#050a0f",
    "bg2":         "#070d14",
    "bg3":         "#06080e",
    "border":      "#0e2a3a",
    "cyan":        "#00d4ff",
    "cyan_dim":    "#00688a",
    "cyan_dark":   "#003a4a",
    "green":       "#00ff88",
    "green_dim":   "#00994d",
    "amber":       "#ffaa00",
    "amber_dim":   "#7a5000",
    "red":         "#ff4444",
    "text":        "#a8d8ea",
    "text_dim":    "#3a6a7a",
    "user_text":   "#80ffb8",
    "alert_text":  "#ffcc66",
    "error_text":  "#ff8888",
}

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class JarvisUI:
    """Main Echo desktop chat interface."""

    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Echo — Farm AI Agent")
        self.root.geometry("1400x820")
        self.root.minsize(1000, 700)
        self.root.configure(fg_color=C["bg"])

        # ─── State ───
        self.is_online = True
        self.busy = False
        self.reminders: list[dict] = []
        self._seen_alert_ids: set = set()
        self.listening = False
        if VOICE_AVAILABLE:
            self.recognizer = sr.Recognizer()
            self.recognizer.pause_threshold = 2.5 # Wait longer before cutting off speech
        else:
            self.recognizer = None
        self.microphone = None
        self._msg_queue: queue.Queue = queue.Queue()
        self._tts_lock = threading.Lock()
        self._tts_engine = None
        self._last_report_spoken: str = ""

        # ─── Build UI ────────────────────────────────────────────────────────
        self._build_header()
        self._build_footer()
        self._build_main_area()

        if TTS_AVAILABLE:
            self._init_tts()

        # ─── Background threads ───────────────────────────────────────────────
        self._start_health_check_thread() # New health check thread
        self._start_reminder_thread()
        self._start_alert_poll_thread()
        self._start_report_watch_thread()
        self._start_queue_processor()

        # Welcome sequence
        welcome_text = "Welcome back sir. How may I assist you."
        self.root.after(300, lambda: self._add_message("jarvis", "JARVIS", welcome_text))
        self.root.after(400, lambda: threading.Thread(
            target=self._speak,
            args=(welcome_text,),
            daemon=True
        ).start())

    # ══════════════════════════════════════════════════════════════════════════
    #  LOGIC & TTS & TIME
    # ══════════════════════════════════════════════════════════════════════════
    
    def _utc_to_local(self, utc_str: str, fmt: str = "%Y-%m-%dT%H:%M:%SZ"):
        """Converts a UTC time string to local time string."""
        try:
            # Parse as UTC
            dt_utc = datetime.strptime(utc_str, fmt).replace(tzinfo=timezone.utc)
            # Convert to local timezone
            dt_local = dt_utc.astimezone()
            return dt_local
        except Exception:
            return None

    def _init_tts(self):
        try:
            self._tts_engine = pyttsx3.init()
            self._tts_engine.setProperty("rate", 165)
            self._tts_engine.setProperty("volume", 1.0)
            voices = self._tts_engine.getProperty("voices")
            for v in voices:
                if any(k in v.name.lower() for k in ["male", "david", "daniel"]):
                    self._tts_engine.setProperty("voice", v.id)
                    break
        except Exception:
            self._tts_engine = None

    def _speak(self, text: str):
        if not self._tts_engine: return
        with self._tts_lock:
            try:
                self._tts_engine.say(text)
                self._tts_engine.runAndWait()
            except Exception: pass

    def _start_health_check_thread(self):
        def _check():
            prev_online = True
            while True:
                try:
                    # Ping the FastAPI backend health endpoint
                    response = requests.get("http://localhost:8000/health", timeout=2)
                    online = (response.status_code == 200)
                except:
                    online = False

                if online != prev_online:
                    if online:
                        self.is_online = True
                        self._status_var.set("ONLINE")
                        self._msg_queue.put(("speak", None, "Sir, connectivity has been restored. My processing cores are now online."))
                        self._msg_queue.put(("jarvis", "JARVIS", "Connectivity restored. Systems operational."))
                    else:
                        self.is_online = False
                        self._status_var.set("OFFLINE")
                        self._msg_queue.put(("speak", None, "Servers are down...."))
                        self._msg_queue.put(("error", "SYSTEM", "Servers are down...."))
                    prev_online = online
                
                time.sleep(5)
        threading.Thread(target=_check, daemon=True).start()

    # ══════════════════════════════════════════════════════════════════════════
    #  UI BUILDERS
    # ══════════════════════════════════════════════════════════════════════════

    def _build_header(self):
        hdr = tk.Frame(self.root, bg=C["bg2"], height=56)
        hdr.pack(fill="x", side="top")
        hdr.pack_propagate(False)

        logo_frame = tk.Frame(hdr, bg=C["bg2"])
        logo_frame.pack(side="left", padx=24, pady=10)
        tk.Label(logo_frame, text="ECHO", font=("Courier New", 22, "bold"),
                 fg=C["cyan"], bg=C["bg2"]).pack(side="left")

        right = tk.Frame(hdr, bg=C["bg2"])
        right.pack(side="right", padx=24)
        tk.Label(right, text="llama-3.1-8b · groq", font=("Courier New", 10),
                 fg=C["text_dim"], bg=C["bg"]).pack(side="left", padx=(0, 16))

        self._status_dot = tk.Canvas(right, width=10, height=10, bg=C["bg2"], highlightthickness=0)
        self._status_dot.pack(side="left", padx=(0, 8))
        self._draw_dot(C["cyan"])

        self._status_var = tk.StringVar(value="ONLINE")
        self._status_lbl = tk.Label(right, textvariable=self._status_var, font=("Courier New", 11),
                                    fg=C["cyan"], bg=C["bg2"])
        self._status_lbl.pack(side="left")

        tk.Frame(self.root, bg=C["border"], height=1).pack(fill="x")
        self._blink_state = True
        self._blink_dot()

    def _draw_dot(self, color):
        self._status_dot.delete("all")
        self._status_dot.create_oval(1, 1, 9, 9, fill=color, outline=color)

    def _blink_dot(self):
        color = (C["cyan"] if self._blink_state else C["cyan_dark"]) if self.is_online \
                else (C["red"] if self._blink_state else "#3a0000")
        self._draw_dot(color)
        self._blink_state = not self._blink_state
        self.root.after(1200, self._blink_dot)

    def _build_main_area(self):
        """Builds a two-column HUD: Chat (Wide Messages) and System Monitor."""
        outer = tk.Frame(self.root, bg=C["bg"])
        outer.pack(fill="both", expand=True)

        # ── COMBINED MONITOR PANEL (Right) ──
        monitor_col = tk.Frame(outer, bg=C["bg3"], width=320)
        monitor_col.pack(side="right", fill="y")
        monitor_col.pack_propagate(False)
        tk.Frame(outer, bg=C["border"], width=1).pack(side="right", fill="y")

        # Header for Monitor
        tk.Label(monitor_col, text="SYSTEM MONITOR / ALERTS", font=("Courier New", 11, "bold"),
                 fg=C["text_dim"], bg=C["bg3"]).pack(pady=(16, 4), padx=16, anchor="w")
        tk.Frame(monitor_col, bg=C["border"], height=1).pack(fill="x", padx=16, pady=(0, 10))

        # Scrollable Monitor Canvas
        mon_wrap = tk.Frame(monitor_col, bg=C["bg3"])
        mon_wrap.pack(fill="both", expand=True)

        self._mon_canvas = tk.Canvas(mon_wrap, bg=C["bg3"], highlightthickness=0, bd=0)
        self._mon_sb = ctk.CTkScrollbar(mon_wrap, orientation="vertical", width=10,
                                         fg_color=C["bg3"], button_color=C["border"],
                                         button_hover_color=C["cyan_dim"],
                                         command=self._mon_canvas.yview)
        self._mon_inner = tk.Frame(self._mon_canvas, bg=C["bg3"])
        self._mon_inner.bind("<Configure>", lambda e: self._mon_canvas.configure(
            scrollregion=self._mon_canvas.bbox("all")))
        self._mon_canvas.create_window((0,0), window=self._mon_inner, anchor="nw")
        self._mon_canvas.configure(yscrollcommand=self._mon_sb.set)
        self._mon_canvas.pack(side="left", fill="both", expand=True)
        self._mon_sb.pack(side="right", fill="y")

        # Monitor sections
        self._rem_list_frame = tk.Frame(self._mon_inner, bg=C["bg3"])
        self._rem_list_frame.pack(fill="x", padx=10)
        self._alert_list_frame = tk.Frame(self._mon_inner, bg=C["bg3"])
        self._alert_list_frame.pack(fill="x", padx=10, pady=(20, 0))

        self._render_reminders()
        self._render_alerts_panel()

        # ── CHAT COLUMN (Left) ──
        chat_col = tk.Frame(outer, bg=C["bg"])
        chat_col.pack(side="left", fill="both", expand=True)

        # Typing Indicator
        self._typing_frame = tk.Frame(chat_col, bg=C["bg2"], height=30)
        self._typing_lbl = tk.Label(self._typing_frame, text="● ● ● ECHO IS PROCESSING...",
                                     font=("Courier New", 10), fg=C["cyan_dim"], bg=C["bg2"])
        self._typing_lbl.pack(padx=20, pady=4)
        self._typing_visible = False

        # Chat Canvas
        chat_wrap = tk.Frame(chat_col, bg=C["bg"])
        chat_wrap.pack(fill="both", expand=True)

        self._chat_canvas = tk.Canvas(chat_wrap, bg=C["bg"], highlightthickness=0, bd=0)
        self._chat_sb = ctk.CTkScrollbar(chat_wrap, orientation="vertical", width=12,
                                          fg_color=C["bg"], button_color=C["border"],
                                          button_hover_color=C["cyan_dim"],
                                          command=self._chat_canvas.yview)
        self._chat_inner = tk.Frame(self._chat_canvas, bg=C["bg"])
        self._chat_inner.bind("<Configure>", lambda e: self._chat_canvas.configure(
            scrollregion=self._chat_canvas.bbox("all")))
        self._chat_win = self._chat_canvas.create_window((0,0), window=self._chat_inner, anchor="nw")
        self._chat_canvas.configure(yscrollcommand=self._chat_sb.set)
        self._chat_canvas.bind("<Configure>", self._on_chat_resize)
        self._chat_canvas.pack(side="left", fill="both", expand=True)
        self._chat_sb.pack(side="right", fill="y")

        # Canvas Scrolling logic
        self._chat_canvas.bind("<Enter>", lambda e: self._chat_canvas.bind_all("<MouseWheel>", self._on_chat_mousewheel))
        self._chat_canvas.bind("<Leave>", lambda e: self._chat_canvas.unbind_all("<MouseWheel>"))
        self._mon_canvas.bind("<Enter>", lambda e: self._mon_canvas.bind_all("<MouseWheel>", self._on_mon_mousewheel))
        self._mon_canvas.bind("<Leave>", lambda e: self._mon_canvas.unbind_all("<MouseWheel>"))

        # Global Key Bindings
        self.root.bind("<KeyPress-m>", self._on_m_key)

    def _on_chat_resize(self, event):
        # Update width of chat inner frame to fill canvas
        self._chat_canvas.itemconfig(self._chat_win, width=event.width)

    def _on_chat_mousewheel(self, event):
        self._chat_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_mon_mousewheel(self, event):
        self._mon_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_m_key(self, event):
        # Only trigger if not typing in the entry box
        if self.root.focus_get() != self._text_in:
            self._toggle_mic()

    def _build_footer(self):
        tk.Frame(self.root, bg=C["border"], height=1).pack(fill="x")
        footer = tk.Frame(self.root, bg=C["bg2"], height=70)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        inner = tk.Frame(footer, bg=C["bg2"])
        inner.pack(fill="both", expand=True, padx=20, pady=12)

        self._mic_btn = tk.Button(inner, text="🎤", font=("Segoe UI Emoji", 15),
                                   bg=C["bg"], fg=C["cyan"], relief="flat", bd=0,
                                   activebackground=C["cyan_dark"], activeforeground=C["cyan"],
                                   command=self._toggle_mic)
        self._mic_btn.pack(side="left", padx=(0, 10))

        self._text_in = tk.Entry(inner, bg=C["bg"], fg=C["text"], insertbackground=C["cyan"],
                                  font=("Courier New", 13), relief="flat", bd=1,
                                  highlightbackground=C["border"], highlightcolor=C["cyan_dim"],
                                  highlightthickness=1)
        self._text_in.pack(side="left", fill="x", expand=True, ipady=8)
        self._text_in.bind("<Return>", lambda e: self._send_text())

        self._proc_status_var = tk.StringVar(value="")
        tk.Label(inner, textvariable=self._proc_status_var, font=("Courier New", 9),
                 fg=C["text_dim"], bg=C["bg2"], width=15).pack(side="left", padx=10)

        self._send_btn = tk.Button(inner, text="SEND", font=("Courier New", 11, "bold"),
                                    bg=C["bg"], fg=C["cyan"], relief="flat", bd=1,
                                    highlightthickness=1, highlightbackground=C["cyan_dim"],
                                    padx=20, cursor="hand2", command=self._send_text)
        self._send_btn.pack(side="left")

    # ══════════════════════════════════════════════════════════════════════════
    #  MESSAGE BUBBLES (Enhanced Width & Wrapping)
    # ══════════════════════════════════════════════════════════════════════════

    def _add_message(self, mtype: str, sender: str, text: str):
        now = datetime.now().strftime("%I:%M %p")
        is_user = mtype == "user"

        styles = {
            "jarvis": {"bg": C["bg2"], "bord": C["cyan"], "meta": C["cyan_dim"], "fg": C["text"]},
            "user":   {"bg": "#04100a", "bord": C["green"], "meta": C["green_dim"], "fg": C["user_text"]},
            "alert":  {"bg": "#100900", "bord": C["amber"], "meta": "#7a5000", "fg": C["alert_text"]},
            "error":  {"bg": "#100404", "bord": C["red"], "meta": "#7a1a1a", "fg": C["error_text"]},
        }
        s = styles.get(mtype, styles["jarvis"])

        line = tk.Frame(self._chat_inner, bg=C["bg"])
        line.pack(fill="x", padx=0, pady=(10, 0))

        meta = tk.Label(line, text=f"{sender} · {now}", font=("Courier New", 9),
                        fg=s["meta"], bg=C["bg"])
        meta.pack(anchor="e" if is_user else "w", padx=24)

        # Bubble Container
        wrap = tk.Frame(line, bg=s["bord"])
        wrap.pack(side="right" if is_user else "left", padx=0, expand=False)

        inner = tk.Frame(wrap, bg=s["bg"])
        inner.pack(padx=(2 if not is_user else 0, 0 if not is_user else 2), pady=0)

        # Use width=80 to allow more space before wrapping, and height dynamic
        txt = tk.Text(inner, wrap="word", bg=s["bg"], fg=s["fg"], font=("Courier New", 13),
                      relief="flat", bd=0, padx=16, pady=12, width=85, height=1)
        txt.insert("end", text)
        txt.configure(state="disabled")

        # Dynamic Height Calculation
        def _update_height():
            # Get content stats
            lcount = int(txt.index("end-1c").split(".")[0])
            txt.configure(height=max(lcount, 1))

        # We must wait for the text widget to wrap before we know the line count
        self.root.after(10, _update_height)
        txt.pack(fill="x", expand=True)

        self.root.after(100, lambda: self._chat_canvas.yview_moveto(1.0))

    # ══════════════════════════════════════════════════════════════════════════
    #  MONITOR UPDATES (Fixed Spacing & Content)
    # ══════════════════════════════════════════════════════════════════════════

    def _render_reminders(self):
        for w in self._rem_list_frame.winfo_children(): w.destroy()
        tk.Label(self._rem_list_frame, text="REMINIDERS", font=("Courier New", 9, "bold"),
                 fg=C["amber_dim"], bg=C["bg3"]).pack(anchor="w", pady=(5,5))
        pending = [r for r in self.reminders if not r.get("fired")]
        if not pending:
            tk.Label(self._rem_list_frame, text="NO REMINDERS", font=("Courier New", 10),
                     fg="#1a2a3a", bg=C["bg3"]).pack(pady=10)
        for r in pending:
            self._make_rem_card(r)

    def _make_rem_card(self, r):
        c = tk.Frame(self._rem_list_frame, bg=C["bg2"])
        c.pack(fill="x", pady=4)
        tk.Frame(c, bg=C["amber"], width=3).pack(side="left", fill="y")
        cnt = tk.Frame(c, bg=C["bg2"], padx=8, pady=8)
        cnt.pack(side="left", fill="x", expand=True)
        dt_local = self._utc_to_local(r["due_time"])
        due_str = dt_local.strftime("%I:%M %p") if dt_local else r["due_time"]
        
        tk.Label(cnt, text=f"{r['title']} (Due: {due_str})", font=("Courier New", 10, "bold"), fg="#d4a843", bg=C["bg2"], anchor="w", wraplength=220).pack(fill="x")
        tk.Button(cnt, text="DEL", font=("Courier New", 8), bg=C["bg2"], fg="#5a2a2a",
                  relief="flat", bd=1, command=lambda: self._del_rem(r["id"])).pack(anchor="e")

    def _del_rem(self, rid):
        self.reminders = [r for r in self.reminders if r["id"] != rid]
        self._render_reminders()

    def _render_alerts_panel(self):
        for w in self._alert_list_frame.winfo_children(): w.destroy()
        tk.Label(self._alert_list_frame, text="ALERTS", font=("Courier New", 9, "bold"),
                 fg=C["cyan_dim"], bg=C["bg3"]).pack(anchor="w", pady=(5,5))
        try:
            from alerts.alert_manager import get_active_alerts
            all_alerts = get_active_alerts()
            
            # Filtering Logic (Use UTC for consistency with backend)
            today_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            alerts = []
            for a in all_alerts:
                ts = a.get("timestamp", "") # ISO: 2026-03-24T...
                if ts.startswith(today_utc):
                    alerts.append(a)
                else:
                    # Previous days: filter out non-essential alerts
                    title = a.get("title", "").lower()
                    if "catch-up" not in title and "downtime" not in title:
                        alerts.append(a)
            
            alerts = alerts[:20] # Show up to 20 filtered alerts
        except: alerts = []
        if not alerts:
            tk.Label(self._alert_list_frame, text="CLEARED", font=("Courier New", 10),
                     fg="#1a2a3a", bg=C["bg3"]).pack(pady=10)
        for a in alerts:
            self._make_alert_card(a)

    def _make_alert_card(self, a):
        cat = a.get("category", "INFO")
        bc = {"WARNING": C["amber"], "ERROR": C["red"], "SUCCESS": C["green"]}.get(cat, C["cyan"])
        c = tk.Frame(self._alert_list_frame, bg=C["bg2"])
        c.pack(fill="x", pady=4) # Added spacing between alert cards
        tk.Frame(c, bg=bc, width=3).pack(side="left", fill="y")
        cnt = tk.Frame(c, bg=C["bg2"], padx=10, pady=10) # More internal padding
        cnt.pack(side="left", fill="x", expand=True)

        dt_local = self._utc_to_local(a["timestamp"])
        ts_str = dt_local.strftime("%I:%M %p") if dt_local else ""
        
        # Title
        tk.Label(cnt, text=f"{a['title']} · {ts_str}", font=("Courier New", 10, "bold"),
                 fg=C["text"], bg=C["bg2"], anchor="w", wraplength=250).pack(fill="x")

        # Message (NEW: Added this back as it was missing!)
        msg = a.get("message", "")
        if msg:
            tk.Label(cnt, text=msg, font=("Courier New", 9),
                     fg=C["text_dim"], bg=C["bg2"], anchor="w",
                     wraplength=250, justify="left").pack(fill="x", pady=(2, 0))

        # Clear Button
        def _clr(aid=a["id"]):
            from alerts.alert_manager import remove_alert
            remove_alert(aid)
            self._msg_queue.put(("redraw", None, None))
        tk.Button(cnt, text="CLR", font=("Courier New", 8), bg=C["bg2"], fg="#3a1a1a",
                  relief="flat", bd=1, highlightthickness=0, command=_clr).pack(anchor="e", pady=(4, 0))

    # ══════════════════════════════════════════════════════════════════════════
    #  CORE LOGIC & THREADS
    # ══════════════════════════════════════════════════════════════════════════

    def _handle(self, text: str):
        if not text.strip() or self.busy: return
        self.busy = True
        self._set_busy_ui(True)
        self._add_message("user", "YOU", text)

        def _run():
            try:
                from agents.run_agent import run_agent
                reply = run_agent(text)
                self._msg_queue.put(("jarvis", "JARVIS", reply))
                self._msg_queue.put(("speak", None, reply))
                self._try_rem(text, reply)
            except Exception as e:
                self._msg_queue.put(("error", "ERROR", str(e)))
            finally:
                self._msg_queue.put(("_done", None, None))

        threading.Thread(target=_run, daemon=True).start()

    def _set_busy_ui(self, busy):
        self._proc_status_var.set("PROCESSING..." if busy else "")
        self._send_btn.configure(state="disabled" if busy else "normal")
        if busy:
            self._typing_frame.pack(fill="x", before=self._chat_canvas.master)
        else:
            self._typing_frame.pack_forget()

    def _start_queue_processor(self):
        def _poll():
            try:
                while True:
                    m, s, t = self._msg_queue.get_nowait()
                    if m == "_done": self._set_busy_ui(False)
                    elif m == "speak": threading.Thread(target=self._speak, args=(t,), daemon=True).start()
                    elif m == "redraw":
                        self._render_reminders()
                        self._render_alerts_panel()
                    elif m == "alert_new":
                        self._add_message("alert", "SYSTEM", f"🔔 {s.get('title', 'Unknown Alert')}")
                        self._render_alerts_panel()
                    elif m in ["jarvis", "user", "error"]: self._add_message(m, s or "AGENT", t)
            except queue.Empty: pass
            self.root.after(100, _poll)
        self.root.after(100, _poll)

    def _try_rem(self, uin, rep):
        # Removed regex-based local reminder creation.
        # Reminders are now exclusively synced from the backend `alerts/active_reminders.json`.
        pass

    def _start_reminder_thread(self):
        def _c():
            while True:
                time.sleep(5)
                n_utc = datetime.now(timezone.utc)
                try:
                    from alerts.reminder_manager import get_active_reminders, remove_reminder
                    backend_rems = get_active_reminders()
                    
                    self.reminders = []
                    
                    for r in backend_rems:
                        try:
                            # Parse UTC time
                            dt_rem_utc = datetime.strptime(r["due_time"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                            
                            if not r.get("fired") and dt_rem_utc <= n_utc:
                                # Reminder is due!
                                r["fired"] = True
                                self._msg_queue.put(("alert", "⚡ REMINDER", r["title"]))
                                self._msg_queue.put(("speak", None, f"Reminder: {r['title']}"))
                                
                                # Process system trigger so the agent can announce it naturally
                                msg_text = f"[SYSTEM TRIGGER: REMINDER DUE] Title: {r['title']}, Message: {r.get('message', '')}. Please announce this naturally."
                                
                                # We need to invoke the agent for the natural announcement, similar to user providing input
                                def _trigger_agent(text):
                                    try:
                                        from agents.run_agent import run_agent
                                        reply = run_agent(text)
                                        self._msg_queue.put(("jarvis", "JARVIS", reply))
                                        self._msg_queue.put(("speak", None, reply))
                                    except Exception as e:
                                        self._msg_queue.put(("error", "ERROR", str(e)))
                                        
                                threading.Thread(target=_trigger_agent, args=(msg_text,), daemon=True).start()
                                
                                # Remove from backend file so it doesn't trigger again globally
                                remove_reminder(r["id"])
                            else:
                                # Still pending or just fired, add to UI list
                                self.reminders.append(r)
                                
                        except Exception:
                            continue
                            
                    self._msg_queue.put(("redraw", None, None))
                except Exception:
                    pass
        threading.Thread(target=_c, daemon=True).start()

    def _start_alert_poll_thread(self):
        def _p():
            while True:
                time.sleep(20)
                try:
                    from alerts.alert_manager import get_active_alerts
                    al = get_active_alerts()
                    new = [a for a in al if a["id"] not in self._seen_alert_ids]
                    for a in new:
                        self._seen_alert_ids.add(a["id"])
                        self._msg_queue.put(("alert_new", a, None))
                except: pass
        threading.Thread(target=_p, daemon=True).start()

    def _start_report_watch_thread(self):
        def _w():
            while True:
                time.sleep(60)
                try:
                    now_utc = datetime.now(timezone.utc)
                    td = now_utc.strftime("%Y-%m-%d")
                    if td == self._last_report_spoken: continue
                    if now_utc.hour < 17: continue
                    rf = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "reports", "daily_reports", f"report_{td}.txt"))
                    if os.path.exists(rf):
                        self._last_report_spoken = td
                        self._msg_queue.put(("jarvis", "SYSTEM", f"📋 Daily report for {td} generated and sent via SMS."))
                        self._msg_queue.put(("speak", None, "Sir, the daily report has been generated and sent via SMS. Please check your phone."))
                except: pass
        threading.Thread(target=_w, daemon=True).start()

    def _toggle_mic(self):
        if self.listening: self.listening = False
        else:
            self.listening = True
            threading.Thread(target=self._listen, daemon=True).start()

    def _listen(self):
        self._proc_status_var.set("LISTENING...")
        try:
            with sr.Microphone() as src:
                self.recognizer.adjust_for_ambient_noise(src, 0.3)
                aud = self.recognizer.listen(src, timeout=5)
            self._proc_status_var.set("PROCESSING...")
            t = self.recognizer.recognize_google(aud)
            self.root.after(0, lambda: (self._text_in.delete(0, "end"), self._text_in.insert(0, t), self._send_text()))
        except: self._proc_status_var.set("")
        finally: self.listening = False

    def _send_text(self):
        t = self._text_in.get().strip()
        if t: self._text_in.delete(0, "end"); self._handle(t)

    def run(self): self.root.mainloop()

def start_ui_jarvis(): JarvisUI().run()

if __name__ == "__main__": start_ui_jarvis()
