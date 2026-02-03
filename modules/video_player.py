"""
Video Player Module for N01D Media Suite
Supports playback, trimming, and basic editing
"""

import customtkinter as ctk
from pathlib import Path
from typing import Optional
import subprocess
import threading
import os
import tempfile

# Try to import video libraries
try:
    import vlc
    HAS_VLC = True
except ImportError:
    HAS_VLC = False

try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


class VideoPlayer(ctk.CTkFrame):
    """Video player with playback controls and basic editing"""
    
    def __init__(self, parent, theme, app=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.theme = theme
        self.app = app
        self.current_file: Optional[Path] = None
        
        # VLC instance
        self.vlc_instance = None
        self.player = None
        self.media = None
        self.is_playing = False
        self.duration = 0
        
        self.configure(fg_color=theme.colors['bg'])
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Build UI
        self._create_toolbar()
        self._create_video_area()
        self._create_controls()
        self._create_timeline()
        
        # Initialize VLC
        self._init_vlc()
        
        # Update timer
        self._update_id = None
        
    def _init_vlc(self):
        """Initialize VLC player"""
        if not HAS_VLC:
            return
            
        try:
            self.vlc_instance = vlc.Instance('--no-xlib', '--quiet')
            self.player = self.vlc_instance.media_player_new()
        except Exception as e:
            print(f"VLC init error: {e}")
            self.vlc_instance = None
            self.player = None
            
    def _create_toolbar(self):
        """Create the top toolbar"""
        toolbar = ctk.CTkFrame(self, height=40, fg_color=self.theme.colors['bg_light'])
        toolbar.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        toolbar.grid_columnconfigure(1, weight=1)
        
        # File info
        self.file_label = ctk.CTkLabel(
            toolbar,
            text="No video loaded",
            font=ctk.CTkFont(family="JetBrains Mono", size=12),
            text_color=self.theme.colors['text_dim']
        )
        self.file_label.grid(row=0, column=0, padx=15, pady=8)
        
        # Spacer
        spacer = ctk.CTkFrame(toolbar, fg_color="transparent")
        spacer.grid(row=0, column=1, sticky="ew")
        
        # Action buttons
        actions_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        actions_frame.grid(row=0, column=2, padx=10, pady=5)
        
        self.screenshot_btn = ctk.CTkButton(
            actions_frame,
            text="📷 Screenshot",
            font=ctk.CTkFont(family="JetBrains Mono", size=11),
            width=100,
            height=28,
            fg_color=self.theme.colors['bg'],
            hover_color=self.theme.colors['bg_hover'],
            command=self.take_screenshot
        )
        self.screenshot_btn.pack(side="left", padx=3)
        
        self.trim_btn = ctk.CTkButton(
            actions_frame,
            text="✂️ Trim",
            font=ctk.CTkFont(family="JetBrains Mono", size=11),
            width=80,
            height=28,
            fg_color=self.theme.colors['bg'],
            hover_color=self.theme.colors['bg_hover'],
            command=self.show_trim_dialog
        )
        self.trim_btn.pack(side="left", padx=3)
        
    def _create_video_area(self):
        """Create the video display area"""
        self.video_frame = ctk.CTkFrame(
            self,
            fg_color=self.theme.colors['bg_dark'],
            corner_radius=8
        )
        self.video_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.video_frame.grid_columnconfigure(0, weight=1)
        self.video_frame.grid_rowconfigure(0, weight=1)
        
        # Video canvas/placeholder
        self.video_canvas = ctk.CTkLabel(
            self.video_frame,
            text="🎬\n\nDrop a video file here\nor use Open File",
            font=ctk.CTkFont(family="JetBrains Mono", size=16),
            text_color=self.theme.colors['text_muted']
        )
        self.video_canvas.grid(row=0, column=0, sticky="nsew")
        
        # Click to open
        self.video_canvas.bind("<Button-1>", lambda e: self.app.open_file() if self.app else None)
        
    def _create_controls(self):
        """Create playback controls"""
        controls = ctk.CTkFrame(self, height=60, fg_color=self.theme.colors['bg_light'])
        controls.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        controls.grid_columnconfigure(1, weight=1)
        
        # Left: Playback buttons
        btn_frame = ctk.CTkFrame(controls, fg_color="transparent")
        btn_frame.grid(row=0, column=0, padx=15, pady=10)
        
        btn_style = {
            "width": 40,
            "height": 40,
            "corner_radius": 20,
            "font": ctk.CTkFont(size=18),
            "fg_color": self.theme.colors['bg'],
            "hover_color": self.theme.colors['bg_hover'],
        }
        
        self.prev_btn = ctk.CTkButton(btn_frame, text="⏮", command=self.skip_backward, **btn_style)
        self.prev_btn.pack(side="left", padx=3)
        
        self.play_btn = ctk.CTkButton(
            btn_frame, 
            text="▶", 
            command=self.toggle_play,
            width=50,
            height=50,
            corner_radius=25,
            font=ctk.CTkFont(size=22),
            fg_color=self.theme.colors['accent'],
            hover_color=self.theme.colors['accent_hover'],
            text_color=self.theme.colors['bg_dark']
        )
        self.play_btn.pack(side="left", padx=8)
        
        self.next_btn = ctk.CTkButton(btn_frame, text="⏭", command=self.skip_forward, **btn_style)
        self.next_btn.pack(side="left", padx=3)
        
        # Center: Time display
        time_frame = ctk.CTkFrame(controls, fg_color="transparent")
        time_frame.grid(row=0, column=1, pady=10)
        
        self.time_label = ctk.CTkLabel(
            time_frame,
            text="00:00:00 / 00:00:00",
            font=ctk.CTkFont(family="JetBrains Mono", size=14),
            text_color=self.theme.colors['text']
        )
        self.time_label.pack()
        
        # Right: Volume
        vol_frame = ctk.CTkFrame(controls, fg_color="transparent")
        vol_frame.grid(row=0, column=2, padx=15, pady=10)
        
        vol_icon = ctk.CTkLabel(vol_frame, text="🔊", font=ctk.CTkFont(size=16))
        vol_icon.pack(side="left", padx=5)
        
        self.volume_slider = ctk.CTkSlider(
            vol_frame,
            from_=0,
            to=100,
            width=100,
            height=16,
            number_of_steps=100,
            fg_color=self.theme.colors['bg_hover'],
            progress_color=self.theme.colors['accent'],
            button_color=self.theme.colors['accent'],
            command=self.set_volume
        )
        self.volume_slider.set(80)
        self.volume_slider.pack(side="left", padx=5)
        
    def _create_timeline(self):
        """Create the timeline/seek bar"""
        timeline_frame = ctk.CTkFrame(self, height=40, fg_color="transparent")
        timeline_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 10))
        timeline_frame.grid_columnconfigure(0, weight=1)
        
        self.timeline = ctk.CTkSlider(
            timeline_frame,
            from_=0,
            to=100,
            height=20,
            fg_color=self.theme.colors['bg_light'],
            progress_color=self.theme.colors['cyan'],
            button_color=self.theme.colors['cyan'],
            command=self.seek
        )
        self.timeline.grid(row=0, column=0, sticky="ew")
        self.timeline.set(0)
        
    def load_file(self, filepath: Path):
        """Load a video file"""
        self.current_file = filepath
        self.file_label.configure(text=filepath.name)
        
        if not HAS_VLC or not self.player:
            self.video_canvas.configure(
                text="⚠️ VLC not available\nInstall python-vlc to enable playback"
            )
            return
            
        try:
            # Create media
            self.media = self.vlc_instance.media_new(str(filepath))
            self.player.set_media(self.media)
            
            # Get window ID for video output
            if os.name == 'nt':
                self.player.set_hwnd(self.video_frame.winfo_id())
            else:
                self.player.set_xwindow(self.video_frame.winfo_id())
                
            # Parse media for duration
            self.media.parse()
            self.duration = self.media.get_duration()
            
            # Update canvas
            self.video_canvas.configure(text="")
            
            # Start update loop
            self._start_update()
            
        except Exception as e:
            self.video_canvas.configure(text=f"Error loading video:\n{e}")
            
    def toggle_play(self):
        """Toggle play/pause"""
        if not self.player:
            return
            
        if self.is_playing:
            self.player.pause()
            self.play_btn.configure(text="▶")
        else:
            self.player.play()
            self.play_btn.configure(text="⏸")
            
        self.is_playing = not self.is_playing
        
    def stop(self):
        """Stop playback"""
        if self.player:
            self.player.stop()
        self.is_playing = False
        self.play_btn.configure(text="▶")
        
    def seek(self, value):
        """Seek to position"""
        if self.player and self.duration > 0:
            pos = value / 100
            self.player.set_position(pos)
            
    def set_volume(self, value):
        """Set volume"""
        if self.player:
            self.player.audio_set_volume(int(value))
            
    def skip_forward(self):
        """Skip forward 10 seconds"""
        if self.player:
            current = self.player.get_time()
            self.player.set_time(current + 10000)
            
    def skip_backward(self):
        """Skip backward 10 seconds"""
        if self.player:
            current = self.player.get_time()
            self.player.set_time(max(0, current - 10000))
            
    def _start_update(self):
        """Start the UI update loop"""
        self._update_ui()
        
    def _update_ui(self):
        """Update UI elements"""
        if self.player and self.is_playing:
            # Update time
            current = self.player.get_time()
            duration = self.player.get_length()
            
            if duration > 0:
                # Update timeline
                pos = (current / duration) * 100
                self.timeline.set(pos)
                
                # Update time label
                current_str = self._format_time(current)
                duration_str = self._format_time(duration)
                self.time_label.configure(text=f"{current_str} / {duration_str}")
                
        # Schedule next update
        self._update_id = self.after(100, self._update_ui)
        
    def _format_time(self, ms: int) -> str:
        """Format milliseconds as HH:MM:SS"""
        seconds = ms // 1000
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        
    def take_screenshot(self):
        """Take a screenshot of current frame"""
        if not self.player or not self.current_file:
            return
            
        # Pause playback
        was_playing = self.is_playing
        if was_playing:
            self.player.pause()
            
        # Get current position
        pos = self.player.get_time() / 1000
        
        # Use ffmpeg to extract frame
        output = self.current_file.parent / f"{self.current_file.stem}_screenshot_{int(pos)}.png"
        
        cmd = [
            'ffmpeg', '-ss', str(pos),
            '-i', str(self.current_file),
            '-vframes', '1',
            '-y', str(output)
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, check=True)
            if self.app:
                self.app.status_bar.set_message(f"Screenshot saved: {output.name}")
        except subprocess.CalledProcessError as e:
            if self.app:
                self.app.status_bar.set_message("Screenshot failed", error=True)
                
        # Resume if was playing
        if was_playing:
            self.player.play()
            
    def show_trim_dialog(self):
        """Show trim dialog"""
        if not self.current_file:
            return
            
        dialog = TrimDialog(self, self.theme, self.current_file, self.duration)
        
    def destroy(self):
        """Clean up on destroy"""
        if self._update_id:
            self.after_cancel(self._update_id)
        if self.player:
            self.player.stop()
        super().destroy()


class TrimDialog(ctk.CTkToplevel):
    """Dialog for trimming video"""
    
    def __init__(self, parent, theme, filepath: Path, duration: int):
        super().__init__(parent)
        self.theme = theme
        self.filepath = filepath
        self.duration = duration
        
        self.title("Trim Video")
        self.geometry("500x250")
        self.configure(fg_color=theme.colors['bg'])
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        self._create_ui()
        
    def _create_ui(self):
        """Create dialog UI"""
        # Title
        title = ctk.CTkLabel(
            self,
            text="✂️ Trim Video",
            font=ctk.CTkFont(family="JetBrains Mono", size=18, weight="bold"),
            text_color=self.theme.colors['accent']
        )
        title.pack(pady=20)
        
        # Input fields
        fields_frame = ctk.CTkFrame(self, fg_color="transparent")
        fields_frame.pack(fill="x", padx=30, pady=10)
        
        # Start time
        start_frame = ctk.CTkFrame(fields_frame, fg_color="transparent")
        start_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(
            start_frame,
            text="Start Time:",
            font=ctk.CTkFont(family="JetBrains Mono", size=12),
            width=100
        ).pack(side="left")
        
        self.start_entry = ctk.CTkEntry(
            start_frame,
            placeholder_text="00:00:00",
            font=ctk.CTkFont(family="JetBrains Mono", size=12),
            fg_color=self.theme.colors['bg_light'],
            border_color=self.theme.colors['border']
        )
        self.start_entry.pack(side="left", fill="x", expand=True, padx=10)
        
        # End time
        end_frame = ctk.CTkFrame(fields_frame, fg_color="transparent")
        end_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(
            end_frame,
            text="End Time:",
            font=ctk.CTkFont(family="JetBrains Mono", size=12),
            width=100
        ).pack(side="left")
        
        self.end_entry = ctk.CTkEntry(
            end_frame,
            placeholder_text="00:00:00",
            font=ctk.CTkFont(family="JetBrains Mono", size=12),
            fg_color=self.theme.colors['bg_light'],
            border_color=self.theme.colors['border']
        )
        self.end_entry.pack(side="left", fill="x", expand=True, padx=10)
        
        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=30)
        
        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            font=ctk.CTkFont(family="JetBrains Mono", size=12),
            fg_color=self.theme.colors['bg_light'],
            hover_color=self.theme.colors['bg_hover'],
            width=100,
            command=self.destroy
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame,
            text="Trim",
            font=ctk.CTkFont(family="JetBrains Mono", size=12),
            fg_color=self.theme.colors['accent'],
            hover_color=self.theme.colors['accent_hover'],
            text_color=self.theme.colors['bg_dark'],
            width=100,
            command=self.trim
        ).pack(side="left", padx=10)
        
    def trim(self):
        """Perform the trim operation"""
        start = self.start_entry.get() or "00:00:00"
        end = self.end_entry.get()
        
        output = self.filepath.parent / f"{self.filepath.stem}_trimmed{self.filepath.suffix}"
        
        cmd = ['ffmpeg', '-i', str(self.filepath), '-ss', start]
        
        if end:
            cmd.extend(['-to', end])
            
        cmd.extend(['-c', 'copy', '-y', str(output)])
        
        try:
            subprocess.run(cmd, capture_output=True, check=True)
            self.destroy()
        except subprocess.CalledProcessError as e:
            print(f"Trim error: {e}")
