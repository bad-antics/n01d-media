"""
Status Bar Component for N01D Media Suite
"""

import customtkinter as ctk
from datetime import datetime
from typing import Optional
import threading
import time


class StatusBar(ctk.CTkFrame):
    """Bottom status bar with module info, messages, and system status"""
    
    def __init__(self, parent, theme, **kwargs):
        super().__init__(parent, height=30, corner_radius=0, **kwargs)
        self.theme = theme
        self.configure(fg_color=theme.colors['bg_dark'])
        
        self.grid_columnconfigure(1, weight=1)
        
        # Module indicator
        self.module_label = ctk.CTkLabel(
            self,
            text="VIDEO",
            font=ctk.CTkFont(family="JetBrains Mono", size=11, weight="bold"),
            text_color=theme.colors['accent'],
            width=80
        )
        self.module_label.grid(row=0, column=0, padx=(10, 5), pady=5)
        
        # Separator
        sep = ctk.CTkLabel(self, text="│", text_color=theme.colors['border'])
        sep.grid(row=0, column=1, padx=5)
        
        # Message area
        self.message_label = ctk.CTkLabel(
            self,
            text="Ready",
            font=ctk.CTkFont(family="JetBrains Mono", size=11),
            text_color=theme.colors['text_dim'],
            anchor="w"
        )
        self.message_label.grid(row=0, column=2, sticky="w", padx=5)
        
        # Spacer
        spacer = ctk.CTkFrame(self, fg_color="transparent")
        spacer.grid(row=0, column=3, sticky="ew")
        self.grid_columnconfigure(3, weight=1)
        
        # Time
        self.time_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(family="JetBrains Mono", size=11),
            text_color=theme.colors['text_muted']
        )
        self.time_label.grid(row=0, column=4, padx=(5, 10), pady=5)
        
        # Start time update
        self._update_time()
        
        # Message timeout
        self._message_timeout = None
        
    def _update_time(self):
        """Update the time display"""
        current_time = datetime.now().strftime("%H:%M:%S")
        self.time_label.configure(text=current_time)
        self.after(1000, self._update_time)
        
    def set_module(self, module_name: str):
        """Set the current module name"""
        self.module_label.configure(text=module_name.upper())
        
    def set_message(self, message: str, error: bool = False, timeout: int = 5000):
        """Set a status message"""
        color = self.theme.colors['error'] if error else self.theme.colors['text_dim']
        self.message_label.configure(text=message, text_color=color)
        
        # Clear previous timeout
        if self._message_timeout:
            self.after_cancel(self._message_timeout)
            
        # Set timeout to clear message
        if timeout > 0:
            self._message_timeout = self.after(timeout, self.clear)
            
    def clear(self):
        """Clear the message"""
        self.message_label.configure(
            text="Ready",
            text_color=self.theme.colors['text_dim']
        )
        self._message_timeout = None
        
    def set_progress(self, value: float, text: Optional[str] = None):
        """Set progress indication"""
        if text:
            self.set_message(f"{text}: {value:.0%}", timeout=0)
        else:
            self.set_message(f"Progress: {value:.0%}", timeout=0)
