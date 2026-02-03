#!/usr/bin/env python3
"""
███╗   ██╗ ██████╗  ██╗██████╗       ███╗   ███╗███████╗██████╗ ██╗ █████╗ 
████╗  ██║██╔═████╗███║██╔══██╗      ████╗ ████║██╔════╝██╔══██╗██║██╔══██╗
██╔██╗ ██║██║██╔██║╚██║██║  ██║█████╗██╔████╔██║█████╗  ██║  ██║██║███████║
██║╚██╗██║████╔╝██║ ██║██║  ██║╚════╝██║╚██╔╝██║██╔══╝  ██║  ██║██║██╔══██║
██║ ╚████║╚██████╔╝ ██║██████╔╝      ██║ ╚═╝ ██║███████╗██████╔╝██║██║  ██║
╚═╝  ╚═══╝ ╚═════╝  ╚═╝╚═════╝       ╚═╝     ╚═╝╚══════╝╚═════╝ ╚═╝╚═╝  ╚═╝

N01D Media Suite - Unified Media Player, Editor & Encoder
Part of the NullSec Toolkit
"""

import sys
import os
import customtkinter as ctk
from pathlib import Path
from typing import Optional, Callable
import threading
import json

# Add modules to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.theme import N01DTheme
from core.file_browser import FileBrowser
from core.status_bar import StatusBar
from modules.video_player import VideoPlayer
from modules.audio_player import AudioPlayer
from modules.image_editor import ImageEditor
from modules.pdf_viewer import PDFViewer
from modules.encoder import MediaEncoder

VERSION = "1.0.0"
APP_NAME = "N01D Media"

class N01DMedia(ctk.CTk):
    """Main application window for N01D Media Suite"""
    
    def __init__(self):
        super().__init__()
        
        # Apply n01d theme
        self.theme = N01DTheme()
        self.theme.apply()
        
        # Window setup
        self.title(f"{APP_NAME} v{VERSION}")
        self.geometry("1400x900")
        self.minsize(1000, 700)
        
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # State
        self.current_file: Optional[Path] = None
        self.current_module: Optional[str] = None
        
        # Build UI
        self._create_sidebar()
        self._create_main_area()
        self._create_status_bar()
        
        # Key bindings
        self.bind("<Control-o>", lambda e: self.open_file())
        self.bind("<Control-s>", lambda e: self.save_file())
        self.bind("<Control-q>", lambda e: self.quit())
        self.bind("<F11>", lambda e: self.toggle_fullscreen())
        
        # Initialize with video player
        self.switch_module("video")
        
    def _create_sidebar(self):
        """Create the left sidebar with module buttons"""
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0,
                                    fg_color=self.theme.colors['bg_dark'])
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        
        # Logo/Title
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", padx=10, pady=20)
        
        title = ctk.CTkLabel(logo_frame, text="N01D", 
                            font=ctk.CTkFont(family="JetBrains Mono", size=32, weight="bold"),
                            text_color=self.theme.colors['accent'])
        title.pack()
        
        subtitle = ctk.CTkLabel(logo_frame, text="MEDIA SUITE",
                               font=ctk.CTkFont(family="JetBrains Mono", size=12),
                               text_color=self.theme.colors['text_dim'])
        subtitle.pack()
        
        # Separator
        sep = ctk.CTkFrame(self.sidebar, height=2, fg_color=self.theme.colors['border'])
        sep.pack(fill="x", padx=20, pady=10)
        
        # Module buttons
        self.module_buttons = {}
        modules = [
            ("video", "🎬 Video Player", "Play & edit video files"),
            ("audio", "🎵 Audio Player", "Play & edit audio files"),
            ("image", "🖼️ Image Editor", "View & edit images"),
            ("pdf", "📄 PDF Viewer", "Read PDF documents"),
            ("encoder", "⚙️ Encoder", "Convert media formats"),
        ]
        
        for module_id, label, tooltip in modules:
            btn = ctk.CTkButton(
                self.sidebar,
                text=label,
                font=ctk.CTkFont(family="JetBrains Mono", size=13),
                fg_color="transparent",
                hover_color=self.theme.colors['bg_light'],
                anchor="w",
                height=45,
                corner_radius=8,
                command=lambda m=module_id: self.switch_module(m)
            )
            btn.pack(fill="x", padx=10, pady=3)
            self.module_buttons[module_id] = btn
            
            # Tooltip on hover
            btn.bind("<Enter>", lambda e, t=tooltip: self.status_bar.set_message(t) if hasattr(self, 'status_bar') else None)
            btn.bind("<Leave>", lambda e: self.status_bar.clear() if hasattr(self, 'status_bar') else None)
        
        # Spacer
        spacer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        spacer.pack(fill="both", expand=True)
        
        # Bottom actions
        sep2 = ctk.CTkFrame(self.sidebar, height=2, fg_color=self.theme.colors['border'])
        sep2.pack(fill="x", padx=20, pady=10)
        
        open_btn = ctk.CTkButton(
            self.sidebar,
            text="📂 Open File",
            font=ctk.CTkFont(family="JetBrains Mono", size=12),
            fg_color=self.theme.colors['accent'],
            hover_color=self.theme.colors['accent_hover'],
            height=40,
            command=self.open_file
        )
        open_btn.pack(fill="x", padx=10, pady=5)
        
        # Version info
        version_label = ctk.CTkLabel(
            self.sidebar,
            text=f"v{VERSION}",
            font=ctk.CTkFont(family="JetBrains Mono", size=10),
            text_color=self.theme.colors['text_dim']
        )
        version_label.pack(pady=10)
        
    def _create_main_area(self):
        """Create the main content area"""
        self.main_frame = ctk.CTkFrame(self, corner_radius=0,
                                       fg_color=self.theme.colors['bg'])
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)
        
        # Module containers (lazy loaded)
        self.modules = {}
        
    def _create_status_bar(self):
        """Create the bottom status bar"""
        self.status_bar = StatusBar(self, theme=self.theme)
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        
    def switch_module(self, module_id: str):
        """Switch to a different module"""
        # Update button states
        for mid, btn in self.module_buttons.items():
            if mid == module_id:
                btn.configure(fg_color=self.theme.colors['bg_light'])
            else:
                btn.configure(fg_color="transparent")
        
        # Hide current module
        for widget in self.main_frame.winfo_children():
            widget.grid_forget()
        
        # Load/show module
        if module_id not in self.modules:
            self.modules[module_id] = self._create_module(module_id)
        
        if self.modules[module_id]:
            self.modules[module_id].grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        self.current_module = module_id
        self.status_bar.set_module(module_id.upper())
        
    def _create_module(self, module_id: str):
        """Create a module instance"""
        module_map = {
            "video": VideoPlayer,
            "audio": AudioPlayer,
            "image": ImageEditor,
            "pdf": PDFViewer,
            "encoder": MediaEncoder,
        }
        
        module_class = module_map.get(module_id)
        if module_class:
            return module_class(self.main_frame, theme=self.theme, app=self)
        return None
        
    def open_file(self, filepath: Optional[str] = None):
        """Open a file dialog or load specified file"""
        if filepath is None:
            filetypes = [
                ("All Media", "*.mp4 *.mkv *.avi *.mov *.webm *.mp3 *.wav *.flac *.ogg *.png *.jpg *.jpeg *.gif *.bmp *.webp *.pdf"),
                ("Video", "*.mp4 *.mkv *.avi *.mov *.webm *.m4v *.wmv"),
                ("Audio", "*.mp3 *.wav *.flac *.ogg *.m4a *.aac *.wma"),
                ("Images", "*.png *.jpg *.jpeg *.gif *.bmp *.webp *.tiff *.svg"),
                ("PDF", "*.pdf"),
                ("All Files", "*.*"),
            ]
            filepath = ctk.filedialog.askopenfilename(filetypes=filetypes)
        
        if filepath:
            self.load_file(Path(filepath))
            
    def load_file(self, filepath: Path):
        """Load a file into the appropriate module"""
        if not filepath.exists():
            self.status_bar.set_message(f"File not found: {filepath}", error=True)
            return
            
        self.current_file = filepath
        ext = filepath.suffix.lower()
        
        # Determine module based on extension
        video_exts = {'.mp4', '.mkv', '.avi', '.mov', '.webm', '.m4v', '.wmv', '.flv'}
        audio_exts = {'.mp3', '.wav', '.flac', '.ogg', '.m4a', '.aac', '.wma'}
        image_exts = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.tiff', '.svg'}
        pdf_exts = {'.pdf'}
        
        if ext in video_exts:
            self.switch_module("video")
        elif ext in audio_exts:
            self.switch_module("audio")
        elif ext in image_exts:
            self.switch_module("image")
        elif ext in pdf_exts:
            self.switch_module("pdf")
        else:
            self.status_bar.set_message(f"Unknown file type: {ext}", error=True)
            return
            
        # Load into current module
        if self.current_module and self.current_module in self.modules:
            self.modules[self.current_module].load_file(filepath)
            self.status_bar.set_message(f"Loaded: {filepath.name}")
            
    def save_file(self):
        """Save current file"""
        if self.current_module and self.current_module in self.modules:
            module = self.modules[self.current_module]
            if hasattr(module, 'save_file'):
                module.save_file()
                
    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        self.attributes("-fullscreen", not self.attributes("-fullscreen"))
        
    def run(self):
        """Start the application"""
        self.mainloop()


def main():
    """Entry point"""
    # Set appearance
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    # Create and run app
    app = N01DMedia()
    app.run()


if __name__ == "__main__":
    main()
