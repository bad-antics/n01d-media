#!/usr/bin/env python3
"""
N01D Media - Screen Recorder Module
Record screen, webcam, and audio with FFmpeg
"""

import customtkinter as ctk
from pathlib import Path
import subprocess
import threading
import time
import os
import signal
from datetime import datetime
from typing import Optional, Callable
import json


class ScreenRecorder(ctk.CTkFrame):
    """Screen recorder with multiple capture modes"""
    
    PRESETS = {
        "screen_only": {
            "name": "Screen Only",
            "icon": "🖥️",
            "description": "Record screen without audio"
        },
        "screen_audio": {
            "name": "Screen + Audio",
            "icon": "🎬",
            "description": "Record screen with system audio"
        },
        "screen_mic": {
            "name": "Screen + Mic",
            "icon": "🎙️",
            "description": "Record screen with microphone"
        },
        "screen_all": {
            "name": "Screen + All Audio",
            "icon": "📹",
            "description": "Record screen with system audio and mic"
        },
        "webcam": {
            "name": "Webcam Only",
            "icon": "📷",
            "description": "Record from webcam"
        },
        "webcam_screen": {
            "name": "Webcam + Screen",
            "icon": "🎥",
            "description": "Picture-in-picture recording"
        }
    }
    
    FORMATS = ["mp4", "mkv", "webm", "avi", "mov"]
    QUALITY_PRESETS = {
        "low": {"crf": 28, "preset": "ultrafast", "label": "Low (Fast)"},
        "medium": {"crf": 23, "preset": "fast", "label": "Medium"},
        "high": {"crf": 18, "preset": "medium", "label": "High"},
        "lossless": {"crf": 0, "preset": "slow", "label": "Lossless"}
    }
    
    def __init__(self, master, theme=None, status_callback: Optional[Callable] = None, **kwargs):
        super().__init__(master, **kwargs)
        
        self.theme = theme
        self.status_callback = status_callback
        
        # Recording state
        self.is_recording = False
        self.is_paused = False
        self.recording_process: Optional[subprocess.Popen] = None
        self.record_start_time: Optional[float] = None
        self.current_output_file: Optional[Path] = None
        
        # Settings
        self.output_dir = Path.home() / "Videos" / "N01D-Recordings"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.current_preset = "screen_audio"
        self.current_format = "mp4"
        self.current_quality = "medium"
        self.fps = 30
        self.countdown_seconds = 3
        
        # Configure
        self.configure(fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self._create_ui()
        self._start_timer_thread()
        
    def _create_ui(self):
        """Build the recorder interface"""
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        title = ctk.CTkLabel(
            header,
            text="🔴 Screen Recorder",
            font=ctk.CTkFont(family="JetBrains Mono", size=20, weight="bold")
        )
        title.pack(side="left")
        
        # Main content - two columns
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=1)
        content.grid_rowconfigure(0, weight=1)
        
        # Left: Recording controls
        left_panel = ctk.CTkFrame(content)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        self._create_preset_selector(left_panel)
        self._create_recording_controls(left_panel)
        
        # Right: Settings & Preview
        right_panel = ctk.CTkFrame(content)
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        
        self._create_settings_panel(right_panel)
        self._create_recordings_list(right_panel)
        
    def _create_preset_selector(self, parent):
        """Create recording preset buttons"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=15, pady=15)
        
        label = ctk.CTkLabel(
            frame,
            text="Recording Mode",
            font=ctk.CTkFont(family="JetBrains Mono", size=14, weight="bold")
        )
        label.pack(anchor="w", pady=(0, 10))
        
        self.preset_buttons = {}
        presets_grid = ctk.CTkFrame(frame, fg_color="transparent")
        presets_grid.pack(fill="x")
        
        for i, (preset_id, preset) in enumerate(self.PRESETS.items()):
            row, col = divmod(i, 2)
            
            btn = ctk.CTkButton(
                presets_grid,
                text=f"{preset['icon']} {preset['name']}",
                font=ctk.CTkFont(family="JetBrains Mono", size=11),
                fg_color="#2a2a3e" if preset_id != self.current_preset else "#00ff88",
                text_color="white" if preset_id != self.current_preset else "black",
                hover_color="#3a3a4e",
                height=50,
                corner_radius=8,
                command=lambda p=preset_id: self._select_preset(p)
            )
            btn.grid(row=row, column=col, padx=3, pady=3, sticky="ew")
            self.preset_buttons[preset_id] = btn
            
        presets_grid.grid_columnconfigure(0, weight=1)
        presets_grid.grid_columnconfigure(1, weight=1)
        
        # Description label
        self.preset_desc = ctk.CTkLabel(
            frame,
            text=self.PRESETS[self.current_preset]['description'],
            font=ctk.CTkFont(family="JetBrains Mono", size=11),
            text_color="#888"
        )
        self.preset_desc.pack(anchor="w", pady=(10, 0))
        
    def _create_recording_controls(self, parent):
        """Create the main recording controls"""
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Timer display
        timer_frame = ctk.CTkFrame(frame, fg_color="#1a1a2e", corner_radius=15)
        timer_frame.pack(fill="x", pady=20, padx=20)
        
        self.timer_label = ctk.CTkLabel(
            timer_frame,
            text="00:00:00",
            font=ctk.CTkFont(family="JetBrains Mono", size=48, weight="bold"),
            text_color="#00ff88"
        )
        self.timer_label.pack(pady=30)
        
        self.status_label = ctk.CTkLabel(
            timer_frame,
            text="Ready to Record",
            font=ctk.CTkFont(family="JetBrains Mono", size=14),
            text_color="#888"
        )
        self.status_label.pack(pady=(0, 20))
        
        # Control buttons
        controls = ctk.CTkFrame(frame, fg_color="transparent")
        controls.pack(fill="x", padx=20, pady=10)
        
        # Record button (big circular)
        self.record_btn = ctk.CTkButton(
            controls,
            text="⏺",
            font=ctk.CTkFont(size=40),
            width=100,
            height=100,
            corner_radius=50,
            fg_color="#ff3366",
            hover_color="#ff5588",
            command=self._toggle_recording
        )
        self.record_btn.pack(side="left", padx=10)
        
        # Pause button
        self.pause_btn = ctk.CTkButton(
            controls,
            text="⏸",
            font=ctk.CTkFont(size=30),
            width=70,
            height=70,
            corner_radius=35,
            fg_color="#555",
            hover_color="#666",
            state="disabled",
            command=self._toggle_pause
        )
        self.pause_btn.pack(side="left", padx=10)
        
        # Stop button
        self.stop_btn = ctk.CTkButton(
            controls,
            text="⏹",
            font=ctk.CTkFont(size=30),
            width=70,
            height=70,
            corner_radius=35,
            fg_color="#555",
            hover_color="#666",
            state="disabled",
            command=self._stop_recording
        )
        self.stop_btn.pack(side="left", padx=10)
        
        # Countdown toggle
        countdown_frame = ctk.CTkFrame(frame, fg_color="transparent")
        countdown_frame.pack(fill="x", padx=20, pady=10)
        
        self.countdown_var = ctk.BooleanVar(value=True)
        countdown_check = ctk.CTkCheckBox(
            countdown_frame,
            text="3-second countdown",
            variable=self.countdown_var,
            font=ctk.CTkFont(family="JetBrains Mono", size=12)
        )
        countdown_check.pack(side="left")
        
    def _create_settings_panel(self, parent):
        """Create settings controls"""
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="x", padx=15, pady=15)
        
        label = ctk.CTkLabel(
            frame,
            text="Settings",
            font=ctk.CTkFont(family="JetBrains Mono", size=14, weight="bold")
        )
        label.pack(anchor="w", padx=15, pady=(15, 10))
        
        settings_grid = ctk.CTkFrame(frame, fg_color="transparent")
        settings_grid.pack(fill="x", padx=15, pady=(0, 15))
        
        # Format
        ctk.CTkLabel(
            settings_grid,
            text="Format:",
            font=ctk.CTkFont(family="JetBrains Mono", size=12)
        ).grid(row=0, column=0, sticky="w", pady=5)
        
        self.format_var = ctk.StringVar(value=self.current_format)
        format_menu = ctk.CTkOptionMenu(
            settings_grid,
            values=self.FORMATS,
            variable=self.format_var,
            font=ctk.CTkFont(family="JetBrains Mono", size=11),
            width=120
        )
        format_menu.grid(row=0, column=1, sticky="e", pady=5, padx=5)
        
        # Quality
        ctk.CTkLabel(
            settings_grid,
            text="Quality:",
            font=ctk.CTkFont(family="JetBrains Mono", size=12)
        ).grid(row=1, column=0, sticky="w", pady=5)
        
        quality_values = [v['label'] for v in self.QUALITY_PRESETS.values()]
        self.quality_var = ctk.StringVar(value=self.QUALITY_PRESETS[self.current_quality]['label'])
        quality_menu = ctk.CTkOptionMenu(
            settings_grid,
            values=quality_values,
            variable=self.quality_var,
            font=ctk.CTkFont(family="JetBrains Mono", size=11),
            width=120
        )
        quality_menu.grid(row=1, column=1, sticky="e", pady=5, padx=5)
        
        # FPS
        ctk.CTkLabel(
            settings_grid,
            text="FPS:",
            font=ctk.CTkFont(family="JetBrains Mono", size=12)
        ).grid(row=2, column=0, sticky="w", pady=5)
        
        self.fps_var = ctk.StringVar(value=str(self.fps))
        fps_menu = ctk.CTkOptionMenu(
            settings_grid,
            values=["15", "24", "30", "60"],
            variable=self.fps_var,
            font=ctk.CTkFont(family="JetBrains Mono", size=11),
            width=120
        )
        fps_menu.grid(row=2, column=1, sticky="e", pady=5, padx=5)
        
        settings_grid.grid_columnconfigure(1, weight=1)
        
        # Output directory
        output_frame = ctk.CTkFrame(frame, fg_color="transparent")
        output_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        ctk.CTkLabel(
            output_frame,
            text="Save to:",
            font=ctk.CTkFont(family="JetBrains Mono", size=12)
        ).pack(anchor="w")
        
        self.output_label = ctk.CTkLabel(
            output_frame,
            text=str(self.output_dir),
            font=ctk.CTkFont(family="JetBrains Mono", size=10),
            text_color="#888"
        )
        self.output_label.pack(anchor="w")
        
        ctk.CTkButton(
            output_frame,
            text="Browse",
            font=ctk.CTkFont(family="JetBrains Mono", size=11),
            width=80,
            height=28,
            command=self._browse_output
        ).pack(anchor="w", pady=(5, 0))
        
    def _create_recordings_list(self, parent):
        """Create recent recordings list"""
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(15, 10))
        
        ctk.CTkLabel(
            header,
            text="Recent Recordings",
            font=ctk.CTkFont(family="JetBrains Mono", size=14, weight="bold")
        ).pack(side="left")
        
        ctk.CTkButton(
            header,
            text="📂 Open Folder",
            font=ctk.CTkFont(family="JetBrains Mono", size=10),
            width=100,
            height=25,
            command=self._open_output_folder
        ).pack(side="right")
        
        # Scrollable list
        self.recordings_scroll = ctk.CTkScrollableFrame(
            frame,
            fg_color="transparent"
        )
        self.recordings_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self._refresh_recordings_list()
        
    def _refresh_recordings_list(self):
        """Refresh the list of recent recordings"""
        for widget in self.recordings_scroll.winfo_children():
            widget.destroy()
            
        recordings = sorted(
            self.output_dir.glob("*.mp4"),
            key=lambda f: f.stat().st_mtime,
            reverse=True
        )[:10]
        
        if not recordings:
            ctk.CTkLabel(
                self.recordings_scroll,
                text="No recordings yet",
                font=ctk.CTkFont(family="JetBrains Mono", size=11),
                text_color="#666"
            ).pack(pady=20)
            return
            
        for rec in recordings:
            item = ctk.CTkFrame(self.recordings_scroll, fg_color="#2a2a3e", corner_radius=8)
            item.pack(fill="x", pady=2)
            
            info = ctk.CTkFrame(item, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True, padx=10, pady=8)
            
            name = ctk.CTkLabel(
                info,
                text=rec.name,
                font=ctk.CTkFont(family="JetBrains Mono", size=11),
                anchor="w"
            )
            name.pack(anchor="w")
            
            size_mb = rec.stat().st_size / (1024 * 1024)
            meta = ctk.CTkLabel(
                info,
                text=f"{size_mb:.1f} MB",
                font=ctk.CTkFont(family="JetBrains Mono", size=9),
                text_color="#888",
                anchor="w"
            )
            meta.pack(anchor="w")
            
            play_btn = ctk.CTkButton(
                item,
                text="▶",
                width=30,
                height=30,
                corner_radius=15,
                fg_color="#00ff88",
                text_color="black",
                hover_color="#00cc66",
                command=lambda p=rec: self._play_recording(p)
            )
            play_btn.pack(side="right", padx=10)
            
    def _select_preset(self, preset_id: str):
        """Select a recording preset"""
        self.current_preset = preset_id
        
        for pid, btn in self.preset_buttons.items():
            if pid == preset_id:
                btn.configure(fg_color="#00ff88", text_color="black")
            else:
                btn.configure(fg_color="#2a2a3e", text_color="white")
                
        self.preset_desc.configure(text=self.PRESETS[preset_id]['description'])
        
    def _toggle_recording(self):
        """Start or stop recording"""
        if self.is_recording:
            self._stop_recording()
        else:
            self._start_recording()
            
    def _start_recording(self):
        """Start recording with optional countdown"""
        if self.countdown_var.get():
            self._do_countdown(self._begin_capture)
        else:
            self._begin_capture()
            
    def _do_countdown(self, callback):
        """Show countdown before recording"""
        def countdown(n):
            if n > 0:
                self.timer_label.configure(text=str(n), text_color="#ff3366")
                self.status_label.configure(text="Starting...")
                self.after(1000, lambda: countdown(n - 1))
            else:
                self.timer_label.configure(text="00:00:00", text_color="#00ff88")
                callback()
                
        countdown(self.countdown_seconds)
        
    def _begin_capture(self):
        """Actually start the FFmpeg capture process"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ext = self.format_var.get()
        self.current_output_file = self.output_dir / f"recording_{timestamp}.{ext}"
        
        # Get quality settings
        quality_label = self.quality_var.get()
        quality_key = next(k for k, v in self.QUALITY_PRESETS.items() if v['label'] == quality_label)
        quality = self.QUALITY_PRESETS[quality_key]
        
        fps = int(self.fps_var.get())
        
        # Build FFmpeg command based on preset
        cmd = self._build_ffmpeg_command(quality, fps)
        
        if not cmd:
            self.status_label.configure(text="Error building command")
            return
            
        try:
            self.recording_process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            self.is_recording = True
            self.is_paused = False
            self.record_start_time = time.time()
            
            self.record_btn.configure(fg_color="#00ff88", text="⏺")
            self.pause_btn.configure(state="normal")
            self.stop_btn.configure(state="normal")
            self.status_label.configure(text="🔴 Recording...")
            
            if self.status_callback:
                self.status_callback(f"Recording to {self.current_output_file.name}")
                
        except Exception as e:
            self.status_label.configure(text=f"Error: {str(e)[:30]}")
            
    def _build_ffmpeg_command(self, quality: dict, fps: int) -> list:
        """Build FFmpeg command based on current settings"""
        cmd = ["ffmpeg", "-y"]
        
        preset = self.current_preset
        
        # Screen capture (Linux X11)
        if preset in ["screen_only", "screen_audio", "screen_mic", "screen_all"]:
            cmd.extend([
                "-f", "x11grab",
                "-framerate", str(fps),
                "-i", os.environ.get("DISPLAY", ":0")
            ])
            
        # Audio sources
        if preset in ["screen_audio", "screen_all"]:
            # System audio (PulseAudio)
            cmd.extend(["-f", "pulse", "-i", "default"])
            
        if preset in ["screen_mic", "screen_all"]:
            # Microphone
            cmd.extend(["-f", "pulse", "-i", "default"])
            
        # Webcam
        if preset in ["webcam", "webcam_screen"]:
            cmd.extend([
                "-f", "v4l2",
                "-framerate", str(fps),
                "-i", "/dev/video0"
            ])
            
        # Output options
        cmd.extend([
            "-c:v", "libx264",
            "-preset", quality['preset'],
            "-crf", str(quality['crf']),
            "-pix_fmt", "yuv420p"
        ])
        
        if preset not in ["screen_only", "webcam"]:
            cmd.extend(["-c:a", "aac", "-b:a", "128k"])
            
        cmd.append(str(self.current_output_file))
        
        return cmd
        
    def _toggle_pause(self):
        """Pause or resume recording"""
        if not self.recording_process:
            return
            
        if self.is_paused:
            # Resume
            self.recording_process.send_signal(signal.SIGCONT)
            self.is_paused = False
            self.pause_btn.configure(text="⏸")
            self.status_label.configure(text="🔴 Recording...")
        else:
            # Pause
            self.recording_process.send_signal(signal.SIGSTOP)
            self.is_paused = True
            self.pause_btn.configure(text="▶")
            self.status_label.configure(text="⏸ Paused")
            
    def _stop_recording(self):
        """Stop the recording"""
        if self.recording_process:
            try:
                # Send 'q' to FFmpeg to stop gracefully
                self.recording_process.stdin.write(b'q')
                self.recording_process.stdin.flush()
                self.recording_process.wait(timeout=5)
            except:
                self.recording_process.terminate()
                
            self.recording_process = None
            
        self.is_recording = False
        self.is_paused = False
        self.record_start_time = None
        
        self.record_btn.configure(fg_color="#ff3366", text="⏺")
        self.pause_btn.configure(state="disabled", text="⏸")
        self.stop_btn.configure(state="disabled")
        self.status_label.configure(text="Recording saved!")
        self.timer_label.configure(text="00:00:00")
        
        self._refresh_recordings_list()
        
        if self.status_callback:
            self.status_callback(f"Saved: {self.current_output_file.name}")
            
    def _start_timer_thread(self):
        """Start background thread for timer updates"""
        def update_timer():
            while True:
                if self.is_recording and not self.is_paused and self.record_start_time:
                    elapsed = time.time() - self.record_start_time
                    hours = int(elapsed // 3600)
                    minutes = int((elapsed % 3600) // 60)
                    seconds = int(elapsed % 60)
                    time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                    
                    try:
                        self.timer_label.configure(text=time_str)
                    except:
                        pass
                        
                time.sleep(0.5)
                
        thread = threading.Thread(target=update_timer, daemon=True)
        thread.start()
        
    def _browse_output(self):
        """Browse for output directory"""
        from tkinter import filedialog
        
        path = filedialog.askdirectory(
            initialdir=str(self.output_dir),
            title="Select Output Directory"
        )
        
        if path:
            self.output_dir = Path(path)
            self.output_label.configure(text=str(self.output_dir))
            self._refresh_recordings_list()
            
    def _open_output_folder(self):
        """Open output folder in file manager"""
        subprocess.run(["xdg-open", str(self.output_dir)])
        
    def _play_recording(self, path: Path):
        """Play a recording with default player"""
        subprocess.Popen(["xdg-open", str(path)])
        
    def cleanup(self):
        """Clean up resources"""
        if self.is_recording:
            self._stop_recording()
