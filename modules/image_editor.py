"""
Image Editor Module for N01D Media Suite
Supports viewing, basic editing, filters, and export
"""

import customtkinter as ctk
from pathlib import Path
from typing import Optional, Tuple
import subprocess
import threading
import io
import os

# Image libraries
try:
    from PIL import Image, ImageTk, ImageFilter, ImageEnhance, ImageOps
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


class ImageEditor(ctk.CTkFrame):
    """Image viewer and editor"""
    
    def __init__(self, parent, theme, app=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.theme = theme
        self.app = app
        self.current_file: Optional[Path] = None
        
        # Image state
        self.original_image: Optional[Image.Image] = None
        self.current_image: Optional[Image.Image] = None
        self.display_image: Optional[ImageTk.PhotoImage] = None
        self.zoom_level = 1.0
        self.pan_offset = (0, 0)
        
        # Edit history
        self.history = []
        self.history_index = -1
        
        self.configure(fg_color=theme.colors['bg'])
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Build UI
        self._create_toolbar()
        self._create_image_area()
        self._create_sidebar()
        
    def _create_toolbar(self):
        """Create the top toolbar"""
        toolbar = ctk.CTkFrame(self, height=45, fg_color=self.theme.colors['bg_light'])
        toolbar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(10, 5))
        toolbar.grid_columnconfigure(2, weight=1)
        
        # File info
        self.file_label = ctk.CTkLabel(
            toolbar,
            text="No image loaded",
            font=ctk.CTkFont(family="JetBrains Mono", size=12),
            text_color=self.theme.colors['text_dim']
        )
        self.file_label.grid(row=0, column=0, padx=15, pady=10)
        
        # Image info
        self.info_label = ctk.CTkLabel(
            toolbar,
            text="",
            font=ctk.CTkFont(family="JetBrains Mono", size=11),
            text_color=self.theme.colors['text_muted']
        )
        self.info_label.grid(row=0, column=1, padx=10, pady=10)
        
        # Spacer
        spacer = ctk.CTkFrame(toolbar, fg_color="transparent")
        spacer.grid(row=0, column=2, sticky="ew")
        
        # Action buttons
        actions_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        actions_frame.grid(row=0, column=3, padx=10, pady=5)
        
        btn_style = {
            "font": ctk.CTkFont(family="JetBrains Mono", size=11),
            "height": 30,
            "fg_color": self.theme.colors['bg'],
            "hover_color": self.theme.colors['bg_hover'],
        }
        
        self.undo_btn = ctk.CTkButton(actions_frame, text="↶ Undo", width=70, command=self.undo, **btn_style)
        self.undo_btn.pack(side="left", padx=3)
        
        self.redo_btn = ctk.CTkButton(actions_frame, text="↷ Redo", width=70, command=self.redo, **btn_style)
        self.redo_btn.pack(side="left", padx=3)
        
        self.reset_btn = ctk.CTkButton(actions_frame, text="🔄 Reset", width=70, command=self.reset, **btn_style)
        self.reset_btn.pack(side="left", padx=3)
        
        self.save_btn = ctk.CTkButton(
            actions_frame, 
            text="💾 Save", 
            width=70,
            fg_color=self.theme.colors['accent'],
            hover_color=self.theme.colors['accent_hover'],
            text_color=self.theme.colors['bg_dark'],
            command=self.save_file
        )
        self.save_btn.pack(side="left", padx=3)
        
    def _create_image_area(self):
        """Create the image display area"""
        self.image_frame = ctk.CTkFrame(
            self,
            fg_color=self.theme.colors['bg_dark'],
            corner_radius=8
        )
        self.image_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.image_frame.grid_columnconfigure(0, weight=1)
        self.image_frame.grid_rowconfigure(0, weight=1)
        
        # Canvas for image
        self.image_canvas = ctk.CTkCanvas(
            self.image_frame,
            bg=self.theme.colors['bg_dark'],
            highlightthickness=0
        )
        self.image_canvas.grid(row=0, column=0, sticky="nsew")
        
        # Placeholder
        self.placeholder = ctk.CTkLabel(
            self.image_frame,
            text="🖼️\n\nDrop an image here\nor use Open File",
            font=ctk.CTkFont(family="JetBrains Mono", size=16),
            text_color=self.theme.colors['text_muted']
        )
        self.placeholder.grid(row=0, column=0)
        
        # Click to open
        self.placeholder.bind("<Button-1>", lambda e: self.app.open_file() if self.app else None)
        
        # Zoom controls
        zoom_frame = ctk.CTkFrame(self.image_frame, fg_color=self.theme.colors['bg_light'])
        zoom_frame.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-10)
        
        zoom_out = ctk.CTkButton(
            zoom_frame, text="-", width=30, height=30,
            fg_color="transparent", hover_color=self.theme.colors['bg_hover'],
            command=self.zoom_out
        )
        zoom_out.pack(side="left")
        
        self.zoom_label = ctk.CTkLabel(
            zoom_frame, text="100%", width=50,
            font=ctk.CTkFont(family="JetBrains Mono", size=11)
        )
        self.zoom_label.pack(side="left")
        
        zoom_in = ctk.CTkButton(
            zoom_frame, text="+", width=30, height=30,
            fg_color="transparent", hover_color=self.theme.colors['bg_hover'],
            command=self.zoom_in
        )
        zoom_in.pack(side="left")
        
        fit = ctk.CTkButton(
            zoom_frame, text="⛶", width=30, height=30,
            fg_color="transparent", hover_color=self.theme.colors['bg_hover'],
            command=self.fit_to_window
        )
        fit.pack(side="left")
        
        # Bindings
        self.image_canvas.bind("<Configure>", self._on_resize)
        self.image_canvas.bind("<MouseWheel>", self._on_mouse_wheel)
        self.image_canvas.bind("<Button-4>", lambda e: self.zoom_in())
        self.image_canvas.bind("<Button-5>", lambda e: self.zoom_out())
        
    def _create_sidebar(self):
        """Create the editing sidebar"""
        self.sidebar = ctk.CTkScrollableFrame(
            self,
            width=250,
            fg_color=self.theme.colors['bg_light'],
            corner_radius=8
        )
        self.sidebar.grid(row=1, column=1, sticky="ns", padx=(0, 10), pady=5)
        
        # Adjustments section
        self._create_section("Adjustments")
        
        adjustments = [
            ("Brightness", "brightness", -100, 100, 0),
            ("Contrast", "contrast", -100, 100, 0),
            ("Saturation", "saturation", -100, 100, 0),
            ("Sharpness", "sharpness", -100, 100, 0),
        ]
        
        self.adjustment_sliders = {}
        for label, key, min_val, max_val, default in adjustments:
            frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
            frame.pack(fill="x", padx=10, pady=5)
            
            lbl = ctk.CTkLabel(
                frame, text=label,
                font=ctk.CTkFont(family="JetBrains Mono", size=11),
                text_color=self.theme.colors['text_dim']
            )
            lbl.pack(anchor="w")
            
            slider = ctk.CTkSlider(
                frame,
                from_=min_val, to=max_val,
                number_of_steps=200,
                height=16,
                fg_color=self.theme.colors['bg_hover'],
                progress_color=self.theme.colors['cyan'],
                button_color=self.theme.colors['cyan'],
                command=lambda v, k=key: self._on_adjustment(k, v)
            )
            slider.set(default)
            slider.pack(fill="x", pady=(2, 0))
            
            self.adjustment_sliders[key] = slider
            
        # Filters section
        self._create_section("Filters")
        
        filters_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        filters_frame.pack(fill="x", padx=10, pady=5)
        
        filters = [
            ("Blur", self.apply_blur),
            ("Sharpen", self.apply_sharpen),
            ("Grayscale", self.apply_grayscale),
            ("Sepia", self.apply_sepia),
            ("Invert", self.apply_invert),
            ("Edge Detect", self.apply_edge_detect),
        ]
        
        for i, (name, cmd) in enumerate(filters):
            btn = ctk.CTkButton(
                filters_frame,
                text=name,
                font=ctk.CTkFont(family="JetBrains Mono", size=11),
                height=30,
                fg_color=self.theme.colors['bg'],
                hover_color=self.theme.colors['bg_hover'],
                command=cmd
            )
            btn.grid(row=i // 2, column=i % 2, padx=3, pady=3, sticky="ew")
            
        filters_frame.grid_columnconfigure(0, weight=1)
        filters_frame.grid_columnconfigure(1, weight=1)
        
        # Transform section
        self._create_section("Transform")
        
        transform_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        transform_frame.pack(fill="x", padx=10, pady=5)
        
        transforms = [
            ("↻ Rotate 90°", self.rotate_90),
            ("↺ Rotate -90°", self.rotate_minus_90),
            ("↔ Flip H", self.flip_horizontal),
            ("↕ Flip V", self.flip_vertical),
        ]
        
        for i, (name, cmd) in enumerate(transforms):
            btn = ctk.CTkButton(
                transform_frame,
                text=name,
                font=ctk.CTkFont(family="JetBrains Mono", size=11),
                height=30,
                fg_color=self.theme.colors['bg'],
                hover_color=self.theme.colors['bg_hover'],
                command=cmd
            )
            btn.grid(row=i // 2, column=i % 2, padx=3, pady=3, sticky="ew")
            
        transform_frame.grid_columnconfigure(0, weight=1)
        transform_frame.grid_columnconfigure(1, weight=1)
        
        # Resize section
        self._create_section("Resize")
        
        resize_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        resize_frame.pack(fill="x", padx=10, pady=5)
        
        # Width/Height inputs
        size_row = ctk.CTkFrame(resize_frame, fg_color="transparent")
        size_row.pack(fill="x", pady=5)
        
        ctk.CTkLabel(size_row, text="W:", width=25).pack(side="left")
        self.width_entry = ctk.CTkEntry(
            size_row, width=70, height=28,
            fg_color=self.theme.colors['bg'],
            border_color=self.theme.colors['border']
        )
        self.width_entry.pack(side="left", padx=5)
        
        ctk.CTkLabel(size_row, text="H:", width=25).pack(side="left")
        self.height_entry = ctk.CTkEntry(
            size_row, width=70, height=28,
            fg_color=self.theme.colors['bg'],
            border_color=self.theme.colors['border']
        )
        self.height_entry.pack(side="left", padx=5)
        
        ctk.CTkButton(
            resize_frame,
            text="Apply Resize",
            font=ctk.CTkFont(family="JetBrains Mono", size=11),
            height=30,
            fg_color=self.theme.colors['purple'],
            hover_color="#8a5cf6",
            command=self.apply_resize
        ).pack(fill="x", pady=5)
        
    def _create_section(self, title: str):
        """Create a section header"""
        sep = ctk.CTkFrame(self.sidebar, height=1, fg_color=self.theme.colors['border'])
        sep.pack(fill="x", padx=10, pady=(15, 5))
        
        lbl = ctk.CTkLabel(
            self.sidebar,
            text=title.upper(),
            font=ctk.CTkFont(family="JetBrains Mono", size=11, weight="bold"),
            text_color=self.theme.colors['accent']
        )
        lbl.pack(anchor="w", padx=10, pady=5)
        
    def load_file(self, filepath: Path):
        """Load an image file"""
        if not HAS_PIL:
            self.placeholder.configure(
                text="⚠️ PIL not available\nInstall Pillow to enable image editing"
            )
            return
            
        self.current_file = filepath
        self.file_label.configure(text=filepath.name)
        self.placeholder.grid_forget()
        
        try:
            self.original_image = Image.open(filepath)
            self.current_image = self.original_image.copy()
            
            # Update info
            w, h = self.original_image.size
            mode = self.original_image.mode
            self.info_label.configure(text=f"{w} × {h} px • {mode}")
            
            # Update size entries
            self.width_entry.delete(0, "end")
            self.width_entry.insert(0, str(w))
            self.height_entry.delete(0, "end")
            self.height_entry.insert(0, str(h))
            
            # Reset history
            self.history = [self.current_image.copy()]
            self.history_index = 0
            
            # Fit to window
            self.fit_to_window()
            
        except Exception as e:
            if self.app:
                self.app.status_bar.set_message(f"Error loading image: {e}", error=True)
                
    def _display_image(self):
        """Display the current image on canvas"""
        if not self.current_image:
            return
            
        canvas_w = self.image_canvas.winfo_width()
        canvas_h = self.image_canvas.winfo_height()
        
        if canvas_w <= 1 or canvas_h <= 1:
            return
            
        # Calculate display size
        img_w, img_h = self.current_image.size
        display_w = int(img_w * self.zoom_level)
        display_h = int(img_h * self.zoom_level)
        
        # Resize for display
        if display_w > 0 and display_h > 0:
            display_img = self.current_image.resize(
                (display_w, display_h),
                Image.Resampling.LANCZOS
            )
            
            self.display_image = ImageTk.PhotoImage(display_img)
            
            # Center on canvas
            x = (canvas_w - display_w) // 2
            y = (canvas_h - display_h) // 2
            
            self.image_canvas.delete("all")
            self.image_canvas.create_image(x, y, anchor="nw", image=self.display_image)
            
        # Update zoom label
        self.zoom_label.configure(text=f"{int(self.zoom_level * 100)}%")
        
    def _on_resize(self, event):
        """Handle canvas resize"""
        self._display_image()
        
    def _on_mouse_wheel(self, event):
        """Handle mouse wheel zoom"""
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()
            
    def zoom_in(self):
        """Zoom in"""
        self.zoom_level = min(5.0, self.zoom_level * 1.2)
        self._display_image()
        
    def zoom_out(self):
        """Zoom out"""
        self.zoom_level = max(0.1, self.zoom_level / 1.2)
        self._display_image()
        
    def fit_to_window(self):
        """Fit image to window"""
        if not self.current_image:
            return
            
        canvas_w = self.image_canvas.winfo_width()
        canvas_h = self.image_canvas.winfo_height()
        img_w, img_h = self.current_image.size
        
        if canvas_w > 1 and canvas_h > 1:
            scale_w = (canvas_w - 40) / img_w
            scale_h = (canvas_h - 40) / img_h
            self.zoom_level = min(scale_w, scale_h, 1.0)
            self._display_image()
            
    def _save_state(self):
        """Save current state to history"""
        # Remove any redo states
        self.history = self.history[:self.history_index + 1]
        self.history.append(self.current_image.copy())
        self.history_index = len(self.history) - 1
        
        # Limit history size
        if len(self.history) > 50:
            self.history.pop(0)
            self.history_index -= 1
            
    def undo(self):
        """Undo last edit"""
        if self.history_index > 0:
            self.history_index -= 1
            self.current_image = self.history[self.history_index].copy()
            self._display_image()
            
    def redo(self):
        """Redo last undone edit"""
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.current_image = self.history[self.history_index].copy()
            self._display_image()
            
    def reset(self):
        """Reset to original image"""
        if self.original_image:
            self.current_image = self.original_image.copy()
            self._save_state()
            self._display_image()
            
            # Reset sliders
            for slider in self.adjustment_sliders.values():
                slider.set(0)
                
    def _on_adjustment(self, key: str, value: float):
        """Handle adjustment slider change"""
        if not self.original_image:
            return
            
        # Start from original
        img = self.original_image.copy()
        
        # Apply all adjustments
        if self.adjustment_sliders['brightness'].get() != 0:
            factor = 1 + self.adjustment_sliders['brightness'].get() / 100
            img = ImageEnhance.Brightness(img).enhance(factor)
            
        if self.adjustment_sliders['contrast'].get() != 0:
            factor = 1 + self.adjustment_sliders['contrast'].get() / 100
            img = ImageEnhance.Contrast(img).enhance(factor)
            
        if self.adjustment_sliders['saturation'].get() != 0:
            factor = 1 + self.adjustment_sliders['saturation'].get() / 100
            img = ImageEnhance.Color(img).enhance(factor)
            
        if self.adjustment_sliders['sharpness'].get() != 0:
            factor = 1 + self.adjustment_sliders['sharpness'].get() / 100
            img = ImageEnhance.Sharpness(img).enhance(factor)
            
        self.current_image = img
        self._display_image()
        
    # Filter methods
    def apply_blur(self):
        if self.current_image:
            self._save_state()
            self.current_image = self.current_image.filter(ImageFilter.GaussianBlur(2))
            self._display_image()
            
    def apply_sharpen(self):
        if self.current_image:
            self._save_state()
            self.current_image = self.current_image.filter(ImageFilter.SHARPEN)
            self._display_image()
            
    def apply_grayscale(self):
        if self.current_image:
            self._save_state()
            self.current_image = ImageOps.grayscale(self.current_image).convert('RGB')
            self._display_image()
            
    def apply_sepia(self):
        if self.current_image:
            self._save_state()
            gray = ImageOps.grayscale(self.current_image)
            sepia = ImageOps.colorize(gray, '#704214', '#C0A080')
            self.current_image = sepia.convert('RGB')
            self._display_image()
            
    def apply_invert(self):
        if self.current_image:
            self._save_state()
            if self.current_image.mode == 'RGBA':
                r, g, b, a = self.current_image.split()
                rgb = Image.merge('RGB', (r, g, b))
                inv = ImageOps.invert(rgb)
                r, g, b = inv.split()
                self.current_image = Image.merge('RGBA', (r, g, b, a))
            else:
                self.current_image = ImageOps.invert(self.current_image.convert('RGB'))
            self._display_image()
            
    def apply_edge_detect(self):
        if self.current_image:
            self._save_state()
            self.current_image = self.current_image.filter(ImageFilter.FIND_EDGES)
            self._display_image()
            
    # Transform methods
    def rotate_90(self):
        if self.current_image:
            self._save_state()
            self.current_image = self.current_image.rotate(-90, expand=True)
            self._display_image()
            
    def rotate_minus_90(self):
        if self.current_image:
            self._save_state()
            self.current_image = self.current_image.rotate(90, expand=True)
            self._display_image()
            
    def flip_horizontal(self):
        if self.current_image:
            self._save_state()
            self.current_image = ImageOps.mirror(self.current_image)
            self._display_image()
            
    def flip_vertical(self):
        if self.current_image:
            self._save_state()
            self.current_image = ImageOps.flip(self.current_image)
            self._display_image()
            
    def apply_resize(self):
        """Apply resize based on input values"""
        if not self.current_image:
            return
            
        try:
            new_w = int(self.width_entry.get())
            new_h = int(self.height_entry.get())
            
            if new_w > 0 and new_h > 0:
                self._save_state()
                self.current_image = self.current_image.resize(
                    (new_w, new_h),
                    Image.Resampling.LANCZOS
                )
                self._display_image()
                
                # Update info
                self.info_label.configure(text=f"{new_w} × {new_h} px • {self.current_image.mode}")
                
        except ValueError:
            if self.app:
                self.app.status_bar.set_message("Invalid dimensions", error=True)
                
    def save_file(self):
        """Save the edited image"""
        if not self.current_image:
            return
            
        filetypes = [
            ("PNG", "*.png"),
            ("JPEG", "*.jpg"),
            ("WebP", "*.webp"),
            ("BMP", "*.bmp"),
            ("TIFF", "*.tiff"),
        ]
        
        filepath = ctk.filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=filetypes,
            initialfile=f"{self.current_file.stem}_edited" if self.current_file else "image"
        )
        
        if filepath:
            try:
                # Convert RGBA to RGB for JPEG
                if filepath.lower().endswith(('.jpg', '.jpeg')) and self.current_image.mode == 'RGBA':
                    rgb_image = Image.new('RGB', self.current_image.size, (255, 255, 255))
                    rgb_image.paste(self.current_image, mask=self.current_image.split()[3])
                    rgb_image.save(filepath, quality=95)
                else:
                    self.current_image.save(filepath)
                    
                if self.app:
                    self.app.status_bar.set_message(f"Saved: {Path(filepath).name}")
                    
            except Exception as e:
                if self.app:
                    self.app.status_bar.set_message(f"Save failed: {e}", error=True)
