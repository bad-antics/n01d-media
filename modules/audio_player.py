"""
Audio Player Module for N01D Media Suite
Supports playback, visualization, and basic editing
"""

import customtkinter as ctk
from pathlib import Path
from typing import Optional, List
import subprocess
import threading
import math
import struct
import os

# Audio libraries
try:
    import pygame
    pygame.mixer.init()
    HAS_PYGAME = True
except ImportError:
    HAS_PYGAME = False

try:
    import wave
    HAS_WAVE = True
except ImportError:
    HAS_WAVE = False


class AudioPlayer(ctk.CTkFrame):
    """Audio player with waveform visualization"""
    
    def __init__(self, parent, theme, app=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.theme = theme
        self.app = app
        self.current_file: Optional[Path] = None
        
        # Audio state
        self.is_playing = False
        self.duration = 0
        self.position = 0
        self.waveform_data: List[float] = []
        
        self.configure(fg_color=theme.colors['bg'])
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Build UI
        self._create_toolbar()
        self._create_waveform_area()
        self._create_controls()
        self._create_metadata_panel()
        
        # Update timer
        self._update_id = None
        
    def _create_toolbar(self):
        """Create the top toolbar"""
        toolbar = ctk.CTkFrame(self, height=40, fg_color=self.theme.colors['bg_light'])
        toolbar.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        toolbar.grid_columnconfigure(1, weight=1)
        
        # File info
        self.file_label = ctk.CTkLabel(
            toolbar,
            text="No audio loaded",
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
        
        self.convert_btn = ctk.CTkButton(
            actions_frame,
            text="🔄 Convert",
            font=ctk.CTkFont(family="JetBrains Mono", size=11),
            width=90,
            height=28,
            fg_color=self.theme.colors['bg'],
            hover_color=self.theme.colors['bg_hover'],
            command=self.show_convert_dialog
        )
        self.convert_btn.pack(side="left", padx=3)
        
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
        
    def _create_waveform_area(self):
        """Create the waveform display area"""
        self.waveform_frame = ctk.CTkFrame(
            self,
            fg_color=self.theme.colors['bg_dark'],
            corner_radius=8
        )
        self.waveform_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.waveform_frame.grid_columnconfigure(0, weight=1)
        self.waveform_frame.grid_rowconfigure(0, weight=1)
        
        # Canvas for waveform
        self.waveform_canvas = ctk.CTkCanvas(
            self.waveform_frame,
            bg=self.theme.colors['bg_dark'],
            highlightthickness=0
        )
        self.waveform_canvas.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        # Placeholder text
        self.placeholder = ctk.CTkLabel(
            self.waveform_frame,
            text="🎵\n\nDrop an audio file here\nor use Open File",
            font=ctk.CTkFont(family="JetBrains Mono", size=16),
            text_color=self.theme.colors['text_muted']
        )
        self.placeholder.grid(row=0, column=0)
        
        # Click to open
        self.placeholder.bind("<Button-1>", lambda e: self.app.open_file() if self.app else None)
        
        # Bind resize
        self.waveform_canvas.bind("<Configure>", self._on_resize)
        
    def _create_controls(self):
        """Create playback controls"""
        controls = ctk.CTkFrame(self, height=80, fg_color=self.theme.colors['bg_light'])
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
        
        self.stop_btn = ctk.CTkButton(btn_frame, text="⏹", command=self.stop, **btn_style)
        self.stop_btn.pack(side="left", padx=3)
        
        # Center: Timeline and time
        center_frame = ctk.CTkFrame(controls, fg_color="transparent")
        center_frame.grid(row=0, column=1, sticky="ew", padx=20, pady=10)
        center_frame.grid_columnconfigure(0, weight=1)
        
        self.timeline = ctk.CTkSlider(
            center_frame,
            from_=0,
            to=100,
            height=16,
            fg_color=self.theme.colors['bg_hover'],
            progress_color=self.theme.colors['purple'],
            button_color=self.theme.colors['purple'],
            command=self.seek
        )
        self.timeline.grid(row=0, column=0, sticky="ew")
        self.timeline.set(0)
        
        self.time_label = ctk.CTkLabel(
            center_frame,
            text="00:00 / 00:00",
            font=ctk.CTkFont(family="JetBrains Mono", size=12),
            text_color=self.theme.colors['text_dim']
        )
        self.time_label.grid(row=1, column=0, pady=(5, 0))
        
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
        
    def _create_metadata_panel(self):
        """Create the metadata display panel"""
        self.metadata_frame = ctk.CTkFrame(
            self,
            height=80,
            fg_color=self.theme.colors['bg_light'],
            corner_radius=8
        )
        self.metadata_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=(5, 10))
        
        # Metadata labels
        info_frame = ctk.CTkFrame(self.metadata_frame, fg_color="transparent")
        info_frame.pack(fill="x", padx=20, pady=15)
        
        self.metadata_labels = {}
        for i, (key, label) in enumerate([
            ("format", "Format"),
            ("bitrate", "Bitrate"),
            ("sample_rate", "Sample Rate"),
            ("channels", "Channels"),
            ("duration", "Duration"),
        ]):
            frame = ctk.CTkFrame(info_frame, fg_color="transparent")
            frame.pack(side="left", padx=20)
            
            ctk.CTkLabel(
                frame,
                text=label,
                font=ctk.CTkFont(family="JetBrains Mono", size=10),
                text_color=self.theme.colors['text_muted']
            ).pack()
            
            self.metadata_labels[key] = ctk.CTkLabel(
                frame,
                text="--",
                font=ctk.CTkFont(family="JetBrains Mono", size=12, weight="bold"),
                text_color=self.theme.colors['text']
            )
            self.metadata_labels[key].pack()
            
    def load_file(self, filepath: Path):
        """Load an audio file"""
        self.current_file = filepath
        self.file_label.configure(text=filepath.name)
        self.placeholder.grid_forget()
        
        # Load with pygame
        if HAS_PYGAME:
            try:
                pygame.mixer.music.load(str(filepath))
                pygame.mixer.music.set_volume(self.volume_slider.get() / 100)
            except Exception as e:
                if self.app:
                    self.app.status_bar.set_message(f"Error loading audio: {e}", error=True)
                return
                
        # Get metadata using ffprobe
        self._load_metadata(filepath)
        
        # Generate waveform
        self._generate_waveform(filepath)
        
        # Start update loop
        self._start_update()
        
    def _load_metadata(self, filepath: Path):
        """Load audio metadata using ffprobe"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet',
                '-print_format', 'json',
                '-show_format', '-show_streams',
                str(filepath)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            import json
            data = json.loads(result.stdout)
            
            # Extract info
            fmt = data.get('format', {})
            streams = data.get('streams', [{}])
            audio_stream = next((s for s in streams if s.get('codec_type') == 'audio'), {})
            
            # Update labels
            self.metadata_labels['format'].configure(text=fmt.get('format_name', 'Unknown').upper())
            
            bitrate = fmt.get('bit_rate', '')
            if bitrate:
                bitrate = f"{int(bitrate) // 1000} kbps"
            self.metadata_labels['bitrate'].configure(text=bitrate or '--')
            
            sample_rate = audio_stream.get('sample_rate', '')
            if sample_rate:
                sample_rate = f"{int(sample_rate) // 1000} kHz"
            self.metadata_labels['sample_rate'].configure(text=sample_rate or '--')
            
            channels = audio_stream.get('channels', '')
            channel_map = {1: 'Mono', 2: 'Stereo', 6: '5.1', 8: '7.1'}
            self.metadata_labels['channels'].configure(text=channel_map.get(channels, str(channels) if channels else '--'))
            
            duration = float(fmt.get('duration', 0))
            self.duration = duration
            self.metadata_labels['duration'].configure(text=self._format_time(int(duration * 1000)))
            
        except Exception as e:
            print(f"Metadata error: {e}")
            
    def _generate_waveform(self, filepath: Path):
        """Generate waveform visualization data"""
        def generate():
            try:
                # Use ffmpeg to extract raw audio data
                cmd = [
                    'ffmpeg', '-i', str(filepath),
                    '-ac', '1',  # Mono
                    '-ar', '8000',  # Low sample rate
                    '-f', 's16le',  # Raw 16-bit
                    '-'
                ]
                result = subprocess.run(cmd, capture_output=True)
                
                # Parse samples
                samples = []
                data = result.stdout
                for i in range(0, len(data) - 1, 2):
                    sample = struct.unpack('<h', data[i:i+2])[0]
                    samples.append(abs(sample) / 32768.0)
                    
                # Downsample to ~500 points
                if len(samples) > 500:
                    step = len(samples) // 500
                    samples = [max(samples[i:i+step]) for i in range(0, len(samples), step)]
                    
                self.waveform_data = samples
                self.after(0, self._draw_waveform)
                
            except Exception as e:
                print(f"Waveform error: {e}")
                
        threading.Thread(target=generate, daemon=True).start()
        
    def _draw_waveform(self):
        """Draw the waveform on canvas"""
        self.waveform_canvas.delete("all")
        
        if not self.waveform_data:
            return
            
        width = self.waveform_canvas.winfo_width()
        height = self.waveform_canvas.winfo_height()
        
        if width <= 1 or height <= 1:
            return
            
        mid_y = height // 2
        bar_width = max(2, width // len(self.waveform_data))
        
        for i, amp in enumerate(self.waveform_data):
            x = int(i * width / len(self.waveform_data))
            bar_height = int(amp * mid_y * 0.9)
            
            # Color gradient based on position
            if self.duration > 0:
                progress = i / len(self.waveform_data)
                current_progress = self.position / self.duration if self.duration else 0
                
                if progress <= current_progress:
                    color = self.theme.colors['purple']
                else:
                    color = self.theme.colors['text_muted']
            else:
                color = self.theme.colors['purple']
                
            self.waveform_canvas.create_rectangle(
                x, mid_y - bar_height,
                x + bar_width - 1, mid_y + bar_height,
                fill=color, outline=''
            )
            
    def _on_resize(self, event):
        """Handle canvas resize"""
        self._draw_waveform()
        
    def toggle_play(self):
        """Toggle play/pause"""
        if not HAS_PYGAME or not self.current_file:
            return
            
        if self.is_playing:
            pygame.mixer.music.pause()
            self.play_btn.configure(text="▶")
        else:
            if pygame.mixer.music.get_pos() == -1:
                pygame.mixer.music.play()
            else:
                pygame.mixer.music.unpause()
            self.play_btn.configure(text="⏸")
            
        self.is_playing = not self.is_playing
        
    def stop(self):
        """Stop playback"""
        if HAS_PYGAME:
            pygame.mixer.music.stop()
        self.is_playing = False
        self.position = 0
        self.play_btn.configure(text="▶")
        self.timeline.set(0)
        self._draw_waveform()
        
    def seek(self, value):
        """Seek to position"""
        if HAS_PYGAME and self.duration > 0:
            pos = (value / 100) * self.duration
            pygame.mixer.music.play(start=pos)
            self.position = pos
            if not self.is_playing:
                pygame.mixer.music.pause()
                
    def set_volume(self, value):
        """Set volume"""
        if HAS_PYGAME:
            pygame.mixer.music.set_volume(value / 100)
            
    def skip_forward(self):
        """Skip forward 10 seconds"""
        if self.duration > 0:
            new_pos = min(self.position + 10, self.duration)
            self.seek((new_pos / self.duration) * 100)
            
    def skip_backward(self):
        """Skip backward 10 seconds"""
        if self.duration > 0:
            new_pos = max(self.position - 10, 0)
            self.seek((new_pos / self.duration) * 100)
            
    def _start_update(self):
        """Start the UI update loop"""
        self._update_ui()
        
    def _update_ui(self):
        """Update UI elements"""
        if HAS_PYGAME and self.is_playing:
            # Get position (pygame returns ms since play started)
            pos = pygame.mixer.music.get_pos()
            if pos >= 0:
                self.position = pos / 1000
                
                if self.duration > 0:
                    progress = (self.position / self.duration) * 100
                    self.timeline.set(progress)
                    
                    # Update time label
                    current_str = self._format_time(int(self.position * 1000))
                    duration_str = self._format_time(int(self.duration * 1000))
                    self.time_label.configure(text=f"{current_str} / {duration_str}")
                    
                    # Redraw waveform for progress
                    self._draw_waveform()
                    
        # Schedule next update
        self._update_id = self.after(100, self._update_ui)
        
    def _format_time(self, ms: int) -> str:
        """Format milliseconds as MM:SS"""
        seconds = ms // 1000
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes:02d}:{secs:02d}"
        
    def show_convert_dialog(self):
        """Show format conversion dialog"""
        if not self.current_file:
            return
        # Would open conversion dialog
        if self.app:
            self.app.switch_module("encoder")
            
    def show_trim_dialog(self):
        """Show trim dialog"""
        if not self.current_file:
            return
        # Similar to video trim dialog
        pass
        
    def destroy(self):
        """Clean up on destroy"""
        if self._update_id:
            self.after_cancel(self._update_id)
        if HAS_PYGAME:
            pygame.mixer.music.stop()
        super().destroy()
