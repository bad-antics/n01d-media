"""
Media Encoder Module for N01D Media Suite
Supports conversion between various audio, video, and image formats
"""

import customtkinter as ctk
from pathlib import Path
from typing import Optional, List, Dict
import subprocess
import threading
import json
import os
import re


class MediaEncoder(ctk.CTkFrame):
    """Media format converter and encoder"""
    
    def __init__(self, parent, theme, app=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.theme = theme
        self.app = app
        
        # Input files
        self.input_files: List[Path] = []
        self.output_dir: Optional[Path] = None
        
        # Encoding state
        self.is_encoding = False
        self.current_process: Optional[subprocess.Popen] = None
        
        self.configure(fg_color=theme.colors['bg'])
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        # Build UI
        self._create_header()
        self._create_input_section()
        self._create_settings_section()
        self._create_output_section()
        self._create_progress_section()
        
    def _create_header(self):
        """Create the header"""
        header = ctk.CTkFrame(self, height=60, fg_color=self.theme.colors['bg_light'])
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        header.grid_columnconfigure(1, weight=1)
        
        # Title
        title = ctk.CTkLabel(
            header,
            text="⚙️ Media Encoder",
            font=ctk.CTkFont(family="JetBrains Mono", size=18, weight="bold"),
            text_color=self.theme.colors['accent']
        )
        title.grid(row=0, column=0, padx=20, pady=15)
        
        # Subtitle
        subtitle = ctk.CTkLabel(
            header,
            text="Convert audio, video, and image formats with FFmpeg",
            font=ctk.CTkFont(family="JetBrains Mono", size=11),
            text_color=self.theme.colors['text_dim']
        )
        subtitle.grid(row=0, column=1, padx=10, pady=15, sticky="w")
        
    def _create_input_section(self):
        """Create the input file section"""
        input_frame = ctk.CTkFrame(self, fg_color=self.theme.colors['bg_light'], corner_radius=8)
        input_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        input_frame.grid_columnconfigure(0, weight=1)
        
        # Header
        header = ctk.CTkFrame(input_frame, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(15, 10))
        
        ctk.CTkLabel(
            header,
            text="INPUT FILES",
            font=ctk.CTkFont(family="JetBrains Mono", size=11, weight="bold"),
            text_color=self.theme.colors['text_dim']
        ).pack(side="left")
        
        ctk.CTkButton(
            header,
            text="+ Add Files",
            font=ctk.CTkFont(family="JetBrains Mono", size=11),
            width=100,
            height=28,
            fg_color=self.theme.colors['accent'],
            hover_color=self.theme.colors['accent_hover'],
            text_color=self.theme.colors['bg_dark'],
            command=self.add_files
        ).pack(side="right", padx=5)
        
        ctk.CTkButton(
            header,
            text="Clear All",
            font=ctk.CTkFont(family="JetBrains Mono", size=11),
            width=80,
            height=28,
            fg_color=self.theme.colors['bg'],
            hover_color=self.theme.colors['bg_hover'],
            command=self.clear_files
        ).pack(side="right")
        
        # File list
        self.file_list = ctk.CTkScrollableFrame(
            input_frame,
            height=100,
            fg_color=self.theme.colors['bg']
        )
        self.file_list.pack(fill="x", padx=15, pady=(0, 15))
        
        self.no_files_label = ctk.CTkLabel(
            self.file_list,
            text="No files added. Click 'Add Files' or drag and drop.",
            font=ctk.CTkFont(family="JetBrains Mono", size=11),
            text_color=self.theme.colors['text_muted']
        )
        self.no_files_label.pack(pady=30)
        
    def _create_settings_section(self):
        """Create the encoding settings section"""
        settings_frame = ctk.CTkFrame(self, fg_color=self.theme.colors['bg_light'], corner_radius=8)
        settings_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        settings_frame.grid_columnconfigure(0, weight=1)
        settings_frame.grid_columnconfigure(1, weight=1)
        
        # Format selection
        format_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        format_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=15, pady=15)
        format_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(
            format_frame,
            text="OUTPUT FORMAT",
            font=ctk.CTkFont(family="JetBrains Mono", size=11, weight="bold"),
            text_color=self.theme.colors['text_dim']
        ).grid(row=0, column=0, sticky="w", pady=(0, 10))
        
        # Category tabs
        self.format_tabs = ctk.CTkSegmentedButton(
            format_frame,
            values=["Video", "Audio", "Image"],
            font=ctk.CTkFont(family="JetBrains Mono", size=11),
            fg_color=self.theme.colors['bg'],
            selected_color=self.theme.colors['accent'],
            selected_hover_color=self.theme.colors['accent_hover'],
            unselected_color=self.theme.colors['bg_hover'],
            command=self._on_category_change
        )
        self.format_tabs.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)
        self.format_tabs.set("Video")
        
        # Format dropdown
        format_row = ctk.CTkFrame(format_frame, fg_color="transparent")
        format_row.grid(row=2, column=0, columnspan=2, sticky="ew", pady=10)
        
        ctk.CTkLabel(
            format_row,
            text="Format:",
            font=ctk.CTkFont(family="JetBrains Mono", size=11),
            width=80
        ).pack(side="left")
        
        self.format_dropdown = ctk.CTkComboBox(
            format_row,
            values=["MP4 (H.264)", "MKV (H.264)", "WebM (VP9)", "AVI", "MOV", "GIF"],
            font=ctk.CTkFont(family="JetBrains Mono", size=11),
            width=200,
            fg_color=self.theme.colors['bg'],
            border_color=self.theme.colors['border'],
            button_color=self.theme.colors['bg_hover'],
            dropdown_fg_color=self.theme.colors['bg_light'],
            command=self._on_format_change
        )
        self.format_dropdown.pack(side="left", padx=10)
        
        # Video settings
        self.video_settings = ctk.CTkFrame(settings_frame, fg_color="transparent")
        self.video_settings.grid(row=1, column=0, sticky="nsew", padx=15, pady=10)
        
        ctk.CTkLabel(
            self.video_settings,
            text="VIDEO SETTINGS",
            font=ctk.CTkFont(family="JetBrains Mono", size=11, weight="bold"),
            text_color=self.theme.colors['text_dim']
        ).pack(anchor="w", pady=(0, 10))
        
        # Resolution
        res_frame = ctk.CTkFrame(self.video_settings, fg_color="transparent")
        res_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(res_frame, text="Resolution:", width=80,
                    font=ctk.CTkFont(family="JetBrains Mono", size=11)).pack(side="left")
        
        self.resolution_dropdown = ctk.CTkComboBox(
            res_frame,
            values=["Original", "3840x2160 (4K)", "1920x1080 (1080p)", "1280x720 (720p)", "854x480 (480p)", "Custom"],
            font=ctk.CTkFont(family="JetBrains Mono", size=11),
            width=180,
            fg_color=self.theme.colors['bg'],
            border_color=self.theme.colors['border']
        )
        self.resolution_dropdown.pack(side="left", padx=10)
        
        # Bitrate
        bitrate_frame = ctk.CTkFrame(self.video_settings, fg_color="transparent")
        bitrate_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(bitrate_frame, text="Video Bitrate:", width=80,
                    font=ctk.CTkFont(family="JetBrains Mono", size=11)).pack(side="left")
        
        self.video_bitrate = ctk.CTkEntry(
            bitrate_frame,
            width=100,
            placeholder_text="Auto",
            font=ctk.CTkFont(family="JetBrains Mono", size=11),
            fg_color=self.theme.colors['bg'],
            border_color=self.theme.colors['border']
        )
        self.video_bitrate.pack(side="left", padx=10)
        
        ctk.CTkLabel(bitrate_frame, text="kbps",
                    font=ctk.CTkFont(family="JetBrains Mono", size=11),
                    text_color=self.theme.colors['text_dim']).pack(side="left")
        
        # FPS
        fps_frame = ctk.CTkFrame(self.video_settings, fg_color="transparent")
        fps_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(fps_frame, text="Frame Rate:", width=80,
                    font=ctk.CTkFont(family="JetBrains Mono", size=11)).pack(side="left")
        
        self.fps_dropdown = ctk.CTkComboBox(
            fps_frame,
            values=["Original", "60", "30", "24", "15"],
            font=ctk.CTkFont(family="JetBrains Mono", size=11),
            width=100,
            fg_color=self.theme.colors['bg'],
            border_color=self.theme.colors['border']
        )
        self.fps_dropdown.pack(side="left", padx=10)
        
        ctk.CTkLabel(fps_frame, text="fps",
                    font=ctk.CTkFont(family="JetBrains Mono", size=11),
                    text_color=self.theme.colors['text_dim']).pack(side="left")
        
        # Audio settings
        self.audio_settings = ctk.CTkFrame(settings_frame, fg_color="transparent")
        self.audio_settings.grid(row=1, column=1, sticky="nsew", padx=15, pady=10)
        
        ctk.CTkLabel(
            self.audio_settings,
            text="AUDIO SETTINGS",
            font=ctk.CTkFont(family="JetBrains Mono", size=11, weight="bold"),
            text_color=self.theme.colors['text_dim']
        ).pack(anchor="w", pady=(0, 10))
        
        # Audio codec
        codec_frame = ctk.CTkFrame(self.audio_settings, fg_color="transparent")
        codec_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(codec_frame, text="Codec:", width=80,
                    font=ctk.CTkFont(family="JetBrains Mono", size=11)).pack(side="left")
        
        self.audio_codec = ctk.CTkComboBox(
            codec_frame,
            values=["AAC", "MP3", "FLAC", "Opus", "Copy"],
            font=ctk.CTkFont(family="JetBrains Mono", size=11),
            width=120,
            fg_color=self.theme.colors['bg'],
            border_color=self.theme.colors['border']
        )
        self.audio_codec.pack(side="left", padx=10)
        
        # Audio bitrate
        abitrate_frame = ctk.CTkFrame(self.audio_settings, fg_color="transparent")
        abitrate_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(abitrate_frame, text="Bitrate:", width=80,
                    font=ctk.CTkFont(family="JetBrains Mono", size=11)).pack(side="left")
        
        self.audio_bitrate = ctk.CTkComboBox(
            abitrate_frame,
            values=["320k", "256k", "192k", "128k", "96k"],
            font=ctk.CTkFont(family="JetBrains Mono", size=11),
            width=100,
            fg_color=self.theme.colors['bg'],
            border_color=self.theme.colors['border']
        )
        self.audio_bitrate.set("192k")
        self.audio_bitrate.pack(side="left", padx=10)
        
        # Sample rate
        sample_frame = ctk.CTkFrame(self.audio_settings, fg_color="transparent")
        sample_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(sample_frame, text="Sample Rate:", width=80,
                    font=ctk.CTkFont(family="JetBrains Mono", size=11)).pack(side="left")
        
        self.sample_rate = ctk.CTkComboBox(
            sample_frame,
            values=["Original", "48000", "44100", "22050"],
            font=ctk.CTkFont(family="JetBrains Mono", size=11),
            width=100,
            fg_color=self.theme.colors['bg'],
            border_color=self.theme.colors['border']
        )
        self.sample_rate.pack(side="left", padx=10)
        
        ctk.CTkLabel(sample_frame, text="Hz",
                    font=ctk.CTkFont(family="JetBrains Mono", size=11),
                    text_color=self.theme.colors['text_dim']).pack(side="left")
        
        # Preset
        preset_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        preset_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=15, pady=10)
        
        ctk.CTkLabel(
            preset_frame,
            text="ENCODING PRESET",
            font=ctk.CTkFont(family="JetBrains Mono", size=11, weight="bold"),
            text_color=self.theme.colors['text_dim']
        ).pack(anchor="w", pady=(0, 10))
        
        self.preset_slider = ctk.CTkSlider(
            preset_frame,
            from_=0, to=8,
            number_of_steps=8,
            height=20,
            fg_color=self.theme.colors['bg_hover'],
            progress_color=self.theme.colors['purple'],
            button_color=self.theme.colors['purple'],
            command=self._on_preset_change
        )
        self.preset_slider.set(4)
        self.preset_slider.pack(fill="x", pady=5)
        
        presets_labels = ctk.CTkFrame(preset_frame, fg_color="transparent")
        presets_labels.pack(fill="x")
        
        for i, label in enumerate(["ultrafast", "", "fast", "", "medium", "", "slow", "", "veryslow"]):
            lbl = ctk.CTkLabel(
                presets_labels,
                text=label,
                font=ctk.CTkFont(family="JetBrains Mono", size=9),
                text_color=self.theme.colors['text_muted']
            )
            lbl.pack(side="left", expand=True)
            
        self.preset_label = ctk.CTkLabel(
            preset_frame,
            text="Current: medium (balanced)",
            font=ctk.CTkFont(family="JetBrains Mono", size=11),
            text_color=self.theme.colors['cyan']
        )
        self.preset_label.pack(anchor="w", pady=5)
        
    def _create_output_section(self):
        """Create the output section"""
        output_frame = ctk.CTkFrame(self, fg_color=self.theme.colors['bg_light'], corner_radius=8)
        output_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=5)
        output_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(
            output_frame,
            text="OUTPUT DIRECTORY",
            font=ctk.CTkFont(family="JetBrains Mono", size=11, weight="bold"),
            text_color=self.theme.colors['text_dim']
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=15, pady=(15, 10))
        
        self.output_entry = ctk.CTkEntry(
            output_frame,
            placeholder_text="Same as input files",
            font=ctk.CTkFont(family="JetBrains Mono", size=11),
            fg_color=self.theme.colors['bg'],
            border_color=self.theme.colors['border']
        )
        self.output_entry.grid(row=1, column=0, columnspan=2, sticky="ew", padx=15, pady=(0, 15))
        
        ctk.CTkButton(
            output_frame,
            text="Browse...",
            font=ctk.CTkFont(family="JetBrains Mono", size=11),
            width=80,
            height=28,
            fg_color=self.theme.colors['bg'],
            hover_color=self.theme.colors['bg_hover'],
            command=self.browse_output
        ).grid(row=1, column=2, padx=(0, 15), pady=(0, 15))
        
    def _create_progress_section(self):
        """Create the progress and start section"""
        progress_frame = ctk.CTkFrame(self, fg_color=self.theme.colors['bg_light'], corner_radius=8)
        progress_frame.grid(row=4, column=0, sticky="ew", padx=10, pady=(5, 10))
        progress_frame.grid_columnconfigure(0, weight=1)
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(
            progress_frame,
            height=20,
            corner_radius=5,
            fg_color=self.theme.colors['bg_hover'],
            progress_color=self.theme.colors['accent']
        )
        self.progress_bar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=15, pady=(15, 5))
        self.progress_bar.set(0)
        
        # Progress label
        self.progress_label = ctk.CTkLabel(
            progress_frame,
            text="Ready to encode",
            font=ctk.CTkFont(family="JetBrains Mono", size=11),
            text_color=self.theme.colors['text_dim']
        )
        self.progress_label.grid(row=1, column=0, sticky="w", padx=15, pady=5)
        
        # Buttons
        btn_frame = ctk.CTkFrame(progress_frame, fg_color="transparent")
        btn_frame.grid(row=2, column=0, columnspan=2, pady=15)
        
        self.cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancel",
            font=ctk.CTkFont(family="JetBrains Mono", size=12),
            width=100,
            height=40,
            fg_color=self.theme.colors['bg'],
            hover_color=self.theme.colors['bg_hover'],
            command=self.cancel_encode,
            state="disabled"
        )
        self.cancel_btn.pack(side="left", padx=10)
        
        self.start_btn = ctk.CTkButton(
            btn_frame,
            text="▶ Start Encoding",
            font=ctk.CTkFont(family="JetBrains Mono", size=12, weight="bold"),
            width=160,
            height=40,
            fg_color=self.theme.colors['accent'],
            hover_color=self.theme.colors['accent_hover'],
            text_color=self.theme.colors['bg_dark'],
            command=self.start_encode
        )
        self.start_btn.pack(side="left", padx=10)
        
    def _on_category_change(self, category: str):
        """Handle format category change"""
        formats = {
            "Video": ["MP4 (H.264)", "MKV (H.264)", "WebM (VP9)", "AVI", "MOV", "GIF"],
            "Audio": ["MP3", "AAC (M4A)", "FLAC", "WAV", "OGG (Vorbis)", "Opus"],
            "Image": ["PNG", "JPEG", "WebP", "BMP", "TIFF", "GIF"],
        }
        
        self.format_dropdown.configure(values=formats.get(category, []))
        self.format_dropdown.set(formats[category][0])
        
        # Show/hide relevant settings
        if category == "Video":
            self.video_settings.grid()
            self.audio_settings.grid()
        elif category == "Audio":
            self.video_settings.grid_remove()
            self.audio_settings.grid()
        else:
            self.video_settings.grid_remove()
            self.audio_settings.grid_remove()
            
    def _on_format_change(self, format_name: str):
        """Handle format selection change"""
        pass
        
    def _on_preset_change(self, value: float):
        """Handle preset slider change"""
        presets = ["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow"]
        descriptions = ["fastest", "very fast", "fast", "faster", "fast", "balanced", "slow", "slower", "best quality"]
        
        idx = int(value)
        self.preset_label.configure(text=f"Current: {presets[idx]} ({descriptions[idx]})")
        
    def add_files(self):
        """Add input files"""
        filetypes = [
            ("All Media", "*.mp4 *.mkv *.avi *.mov *.webm *.mp3 *.wav *.flac *.ogg *.png *.jpg *.jpeg *.gif *.bmp *.webp"),
            ("Video", "*.mp4 *.mkv *.avi *.mov *.webm *.m4v"),
            ("Audio", "*.mp3 *.wav *.flac *.ogg *.m4a *.aac"),
            ("Images", "*.png *.jpg *.jpeg *.gif *.bmp *.webp *.tiff"),
            ("All Files", "*.*"),
        ]
        
        files = ctk.filedialog.askopenfilenames(filetypes=filetypes)
        
        for f in files:
            filepath = Path(f)
            if filepath not in self.input_files:
                self.input_files.append(filepath)
                
        self._update_file_list()
        
    def clear_files(self):
        """Clear all input files"""
        self.input_files.clear()
        self._update_file_list()
        
    def _update_file_list(self):
        """Update the file list display"""
        # Clear current list
        for widget in self.file_list.winfo_children():
            widget.destroy()
            
        if not self.input_files:
            self.no_files_label = ctk.CTkLabel(
                self.file_list,
                text="No files added. Click 'Add Files' or drag and drop.",
                font=ctk.CTkFont(family="JetBrains Mono", size=11),
                text_color=self.theme.colors['text_muted']
            )
            self.no_files_label.pack(pady=30)
            return
            
        for filepath in self.input_files:
            frame = ctk.CTkFrame(self.file_list, fg_color=self.theme.colors['bg_hover'], corner_radius=5)
            frame.pack(fill="x", pady=2)
            
            # Icon based on type
            ext = filepath.suffix.lower()
            if ext in ['.mp4', '.mkv', '.avi', '.mov', '.webm']:
                icon = "🎬"
            elif ext in ['.mp3', '.wav', '.flac', '.ogg']:
                icon = "🎵"
            else:
                icon = "🖼️"
                
            ctk.CTkLabel(
                frame,
                text=f"{icon}  {filepath.name}",
                font=ctk.CTkFont(family="JetBrains Mono", size=11),
                text_color=self.theme.colors['text']
            ).pack(side="left", padx=10, pady=8)
            
            # Size
            size = filepath.stat().st_size / (1024 * 1024)
            ctk.CTkLabel(
                frame,
                text=f"{size:.1f} MB",
                font=ctk.CTkFont(family="JetBrains Mono", size=10),
                text_color=self.theme.colors['text_dim']
            ).pack(side="right", padx=10)
            
            # Remove button
            ctk.CTkButton(
                frame,
                text="✕",
                width=25,
                height=25,
                fg_color="transparent",
                hover_color=self.theme.colors['red'],
                command=lambda p=filepath: self._remove_file(p)
            ).pack(side="right", padx=5)
            
    def _remove_file(self, filepath: Path):
        """Remove a file from the list"""
        if filepath in self.input_files:
            self.input_files.remove(filepath)
            self._update_file_list()
            
    def browse_output(self):
        """Browse for output directory"""
        directory = ctk.filedialog.askdirectory()
        if directory:
            self.output_entry.delete(0, "end")
            self.output_entry.insert(0, directory)
            self.output_dir = Path(directory)
            
    def load_file(self, filepath: Path):
        """Load a file (adds to input list)"""
        if filepath not in self.input_files:
            self.input_files.append(filepath)
            self._update_file_list()
            
    def start_encode(self):
        """Start encoding process"""
        if not self.input_files:
            if self.app:
                self.app.status_bar.set_message("No input files", error=True)
            return
            
        self.is_encoding = True
        self.start_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        
        # Get settings
        category = self.format_tabs.get()
        format_name = self.format_dropdown.get()
        
        # Run encoding in thread
        threading.Thread(target=self._encode_files, args=(category, format_name), daemon=True).start()
        
    def _encode_files(self, category: str, format_name: str):
        """Encode files (runs in thread)"""
        total = len(self.input_files)
        
        for i, input_file in enumerate(self.input_files):
            if not self.is_encoding:
                break
                
            # Update progress
            progress = i / total
            self.after(0, lambda p=progress, f=input_file: self._update_progress(p, f"Encoding: {f.name}"))
            
            # Build FFmpeg command
            cmd = self._build_ffmpeg_command(input_file, category, format_name)
            
            try:
                # Run FFmpeg
                self.current_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )
                
                # Monitor progress
                for line in self.current_process.stderr:
                    if not self.is_encoding:
                        self.current_process.terminate()
                        break
                    # Parse FFmpeg progress output
                    if 'time=' in line:
                        # Extract time and calculate progress
                        pass
                        
                self.current_process.wait()
                
            except Exception as e:
                self.after(0, lambda e=e: self._encode_error(str(e)))
                
        # Complete
        self.after(0, self._encode_complete)
        
    def _build_ffmpeg_command(self, input_file: Path, category: str, format_name: str) -> List[str]:
        """Build the FFmpeg command"""
        # Determine output extension
        ext_map = {
            "MP4 (H.264)": ".mp4",
            "MKV (H.264)": ".mkv",
            "WebM (VP9)": ".webm",
            "AVI": ".avi",
            "MOV": ".mov",
            "GIF": ".gif",
            "MP3": ".mp3",
            "AAC (M4A)": ".m4a",
            "FLAC": ".flac",
            "WAV": ".wav",
            "OGG (Vorbis)": ".ogg",
            "Opus": ".opus",
            "PNG": ".png",
            "JPEG": ".jpg",
            "WebP": ".webp",
            "BMP": ".bmp",
            "TIFF": ".tiff",
        }
        
        ext = ext_map.get(format_name, ".mp4")
        
        # Output path
        if self.output_dir:
            output = self.output_dir / f"{input_file.stem}_converted{ext}"
        else:
            output = input_file.parent / f"{input_file.stem}_converted{ext}"
            
        cmd = ['ffmpeg', '-i', str(input_file), '-y']
        
        # Add codec settings based on format
        if category == "Video":
            # Resolution
            res = self.resolution_dropdown.get()
            if res != "Original" and res != "Custom":
                res_value = res.split()[0]
                cmd.extend(['-s', res_value])
                
            # Video codec
            if "H.264" in format_name:
                cmd.extend(['-c:v', 'libx264'])
            elif "VP9" in format_name:
                cmd.extend(['-c:v', 'libvpx-vp9'])
                
            # Preset
            presets = ["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow"]
            preset = presets[int(self.preset_slider.get())]
            cmd.extend(['-preset', preset])
            
            # Video bitrate
            vbr = self.video_bitrate.get()
            if vbr:
                cmd.extend(['-b:v', f'{vbr}k'])
                
            # FPS
            fps = self.fps_dropdown.get()
            if fps != "Original":
                cmd.extend(['-r', fps])
                
            # Audio codec
            acodec = self.audio_codec.get()
            if acodec == "AAC":
                cmd.extend(['-c:a', 'aac'])
            elif acodec == "MP3":
                cmd.extend(['-c:a', 'libmp3lame'])
            elif acodec == "Copy":
                cmd.extend(['-c:a', 'copy'])
                
            # Audio bitrate
            abr = self.audio_bitrate.get()
            cmd.extend(['-b:a', abr])
            
        elif category == "Audio":
            # Audio-only encoding
            cmd.extend(['-vn'])  # No video
            
            if "MP3" in format_name:
                cmd.extend(['-c:a', 'libmp3lame'])
            elif "AAC" in format_name:
                cmd.extend(['-c:a', 'aac'])
            elif "FLAC" in format_name:
                cmd.extend(['-c:a', 'flac'])
            elif "Opus" in format_name:
                cmd.extend(['-c:a', 'libopus'])
                
            abr = self.audio_bitrate.get()
            cmd.extend(['-b:a', abr])
            
            sr = self.sample_rate.get()
            if sr != "Original":
                cmd.extend(['-ar', sr])
                
        else:  # Image
            # Image conversion is simpler
            pass
            
        cmd.append(str(output))
        return cmd
        
    def _update_progress(self, progress: float, message: str):
        """Update progress display"""
        self.progress_bar.set(progress)
        self.progress_label.configure(text=message)
        
    def _encode_error(self, error: str):
        """Handle encoding error"""
        self.progress_label.configure(text=f"Error: {error}", text_color=self.theme.colors['red'])
        self.is_encoding = False
        self.start_btn.configure(state="normal")
        self.cancel_btn.configure(state="disabled")
        
    def _encode_complete(self):
        """Handle encoding completion"""
        self.progress_bar.set(1.0)
        self.progress_label.configure(text="Encoding complete!", text_color=self.theme.colors['success'])
        self.is_encoding = False
        self.start_btn.configure(state="normal")
        self.cancel_btn.configure(state="disabled")
        
        if self.app:
            self.app.status_bar.set_message("Encoding complete!")
            
    def cancel_encode(self):
        """Cancel encoding"""
        self.is_encoding = False
        if self.current_process:
            self.current_process.terminate()
        self.progress_label.configure(text="Encoding cancelled")
        self.start_btn.configure(state="normal")
        self.cancel_btn.configure(state="disabled")
