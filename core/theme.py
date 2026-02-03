"""
N01D Theme - Cyberpunk/Hacker aesthetic for the media suite
"""

import customtkinter as ctk
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class N01DColors:
    """N01D color palette"""
    # Backgrounds
    bg_dark: str = "#0a0a0f"      # Darkest background
    bg: str = "#0d1117"           # Main background
    bg_light: str = "#161b22"     # Elevated elements
    bg_hover: str = "#21262d"     # Hover states
    
    # Borders
    border: str = "#30363d"
    border_light: str = "#484f58"
    
    # Text
    text: str = "#e6edf3"         # Primary text
    text_dim: str = "#8b949e"     # Secondary text
    text_muted: str = "#6e7681"   # Muted text
    
    # Accent colors
    accent: str = "#00ff9f"       # Neon green (primary)
    accent_hover: str = "#00cc7f"
    accent_dim: str = "#00994f"
    
    cyan: str = "#00d4ff"         # Neon cyan
    purple: str = "#a371f7"       # Purple
    pink: str = "#ff6ec7"         # Neon pink
    yellow: str = "#ffd700"       # Gold/yellow
    red: str = "#ff4757"          # Error/danger
    orange: str = "#ff8c00"       # Warning
    
    # Semantic
    success: str = "#3fb950"
    warning: str = "#d29922"
    error: str = "#f85149"
    info: str = "#58a6ff"


class N01DTheme:
    """Theme manager for N01D Media Suite"""
    
    def __init__(self):
        self.colors = N01DColors()
        self._colors_dict = None
        
    @property
    def colors(self) -> Dict[str, str]:
        """Get colors as dictionary"""
        if self._colors_dict is None:
            self._colors_dict = {
                'bg_dark': self._colors.bg_dark,
                'bg': self._colors.bg,
                'bg_light': self._colors.bg_light,
                'bg_hover': self._colors.bg_hover,
                'border': self._colors.border,
                'border_light': self._colors.border_light,
                'text': self._colors.text,
                'text_dim': self._colors.text_dim,
                'text_muted': self._colors.text_muted,
                'accent': self._colors.accent,
                'accent_hover': self._colors.accent_hover,
                'accent_dim': self._colors.accent_dim,
                'cyan': self._colors.cyan,
                'purple': self._colors.purple,
                'pink': self._colors.pink,
                'yellow': self._colors.yellow,
                'red': self._colors.red,
                'orange': self._colors.orange,
                'success': self._colors.success,
                'warning': self._colors.warning,
                'error': self._colors.error,
                'info': self._colors.info,
            }
        return self._colors_dict
        
    @colors.setter
    def colors(self, value: N01DColors):
        self._colors = value
        self._colors_dict = None
        
    def apply(self):
        """Apply theme to customtkinter"""
        ctk.set_appearance_mode("dark")
        
    def get_button_style(self, variant: str = "default") -> Dict[str, Any]:
        """Get button style configuration"""
        styles = {
            "default": {
                "fg_color": self.colors['bg_light'],
                "hover_color": self.colors['bg_hover'],
                "text_color": self.colors['text'],
                "border_width": 1,
                "border_color": self.colors['border'],
            },
            "primary": {
                "fg_color": self.colors['accent'],
                "hover_color": self.colors['accent_hover'],
                "text_color": self.colors['bg_dark'],
            },
            "danger": {
                "fg_color": self.colors['red'],
                "hover_color": "#cc3944",
                "text_color": self.colors['text'],
            },
            "ghost": {
                "fg_color": "transparent",
                "hover_color": self.colors['bg_hover'],
                "text_color": self.colors['text_dim'],
            },
        }
        return styles.get(variant, styles["default"])
        
    def get_entry_style(self) -> Dict[str, Any]:
        """Get entry/input style configuration"""
        return {
            "fg_color": self.colors['bg_dark'],
            "border_color": self.colors['border'],
            "text_color": self.colors['text'],
            "placeholder_text_color": self.colors['text_muted'],
        }
        
    def get_slider_style(self) -> Dict[str, Any]:
        """Get slider style configuration"""
        return {
            "fg_color": self.colors['bg_hover'],
            "progress_color": self.colors['accent'],
            "button_color": self.colors['accent'],
            "button_hover_color": self.colors['accent_hover'],
        }
        
    def style_frame(self, frame: ctk.CTkFrame, elevated: bool = False):
        """Apply theme to a frame"""
        frame.configure(
            fg_color=self.colors['bg_light'] if elevated else self.colors['bg'],
            border_color=self.colors['border'],
            border_width=1 if elevated else 0,
        )
        
    def style_label(self, label: ctk.CTkLabel, variant: str = "default"):
        """Apply theme to a label"""
        text_colors = {
            "default": self.colors['text'],
            "dim": self.colors['text_dim'],
            "muted": self.colors['text_muted'],
            "accent": self.colors['accent'],
            "error": self.colors['error'],
        }
        label.configure(text_color=text_colors.get(variant, self.colors['text']))


# Fonts
FONTS = {
    "mono": "JetBrains Mono",
    "mono_fallback": "Consolas",
    "sans": "Inter",
    "sans_fallback": "Segoe UI",
}

def get_font(family: str = "mono", size: int = 12, weight: str = "normal") -> ctk.CTkFont:
    """Get a themed font"""
    font_family = FONTS.get(family, FONTS["mono"])
    return ctk.CTkFont(family=font_family, size=size, weight=weight)
