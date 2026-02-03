"""
File Browser Component for N01D Media Suite
"""

import customtkinter as ctk
from pathlib import Path
from typing import Optional, Callable, List
import os


class FileBrowser(ctk.CTkFrame):
    """File browser sidebar component"""
    
    def __init__(self, parent, theme, on_file_select: Optional[Callable] = None, **kwargs):
        super().__init__(parent, **kwargs)
        self.theme = theme
        self.on_file_select = on_file_select
        self.current_path = Path.home()
        
        self.configure(fg_color=theme.colors['bg_light'])
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Path bar
        self._create_path_bar()
        
        # File list
        self._create_file_list()
        
        # Load initial directory
        self.load_directory(self.current_path)
        
    def _create_path_bar(self):
        """Create the current path display"""
        path_frame = ctk.CTkFrame(self, fg_color="transparent")
        path_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        path_frame.grid_columnconfigure(0, weight=1)
        
        # Up button
        up_btn = ctk.CTkButton(
            path_frame,
            text="↑",
            width=30,
            height=28,
            font=ctk.CTkFont(size=14),
            fg_color=self.theme.colors['bg'],
            hover_color=self.theme.colors['bg_hover'],
            command=self.go_up
        )
        up_btn.grid(row=0, column=0, padx=(0, 5))
        
        # Path entry
        self.path_entry = ctk.CTkEntry(
            path_frame,
            height=28,
            font=ctk.CTkFont(family="JetBrains Mono", size=11),
            fg_color=self.theme.colors['bg'],
            border_color=self.theme.colors['border'],
            text_color=self.theme.colors['text_dim']
        )
        self.path_entry.grid(row=0, column=1, sticky="ew")
        self.path_entry.bind("<Return>", self._on_path_enter)
        
    def _create_file_list(self):
        """Create the scrollable file list"""
        self.file_list = ctk.CTkScrollableFrame(
            self,
            fg_color=self.theme.colors['bg'],
            corner_radius=8
        )
        self.file_list.grid(row=1, column=0, sticky="nsew", padx=10, pady=(5, 10))
        self.file_list.grid_columnconfigure(0, weight=1)
        
    def load_directory(self, path: Path):
        """Load and display directory contents"""
        if not path.is_dir():
            return
            
        self.current_path = path
        self.path_entry.delete(0, "end")
        self.path_entry.insert(0, str(path))
        
        # Clear current list
        for widget in self.file_list.winfo_children():
            widget.destroy()
            
        # Get directory contents
        try:
            items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
        except PermissionError:
            return
            
        # Filter for media files
        media_exts = {
            '.mp4', '.mkv', '.avi', '.mov', '.webm', '.m4v',
            '.mp3', '.wav', '.flac', '.ogg', '.m4a',
            '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp',
            '.pdf'
        }
        
        for item in items:
            if item.is_dir() or item.suffix.lower() in media_exts:
                self._add_file_item(item)
                
    def _add_file_item(self, path: Path):
        """Add a file/folder item to the list"""
        is_dir = path.is_dir()
        
        # Get icon
        if is_dir:
            icon = "📁"
        else:
            ext = path.suffix.lower()
            icons = {
                '.mp4': '🎬', '.mkv': '🎬', '.avi': '🎬', '.mov': '🎬',
                '.mp3': '🎵', '.wav': '🎵', '.flac': '🎵', '.ogg': '🎵',
                '.png': '🖼️', '.jpg': '🖼️', '.jpeg': '🖼️', '.gif': '🖼️',
                '.pdf': '📄',
            }
            icon = icons.get(ext, '📄')
            
        btn = ctk.CTkButton(
            self.file_list,
            text=f"{icon}  {path.name}",
            font=ctk.CTkFont(family="JetBrains Mono", size=11),
            fg_color="transparent",
            hover_color=self.theme.colors['bg_hover'],
            anchor="w",
            height=30,
            command=lambda p=path: self._on_item_click(p)
        )
        btn.pack(fill="x", pady=1)
        
    def _on_item_click(self, path: Path):
        """Handle file/folder click"""
        if path.is_dir():
            self.load_directory(path)
        elif self.on_file_select:
            self.on_file_select(path)
            
    def _on_path_enter(self, event):
        """Handle path entry submit"""
        path = Path(self.path_entry.get())
        if path.is_dir():
            self.load_directory(path)
            
    def go_up(self):
        """Navigate to parent directory"""
        parent = self.current_path.parent
        if parent != self.current_path:
            self.load_directory(parent)
