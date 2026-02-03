"""
PDF Viewer Module for N01D Media Suite
Supports viewing, navigation, search, and annotations
"""

import customtkinter as ctk
from pathlib import Path
from typing import Optional, List, Dict
import subprocess
import threading
import tempfile
import os

# PDF libraries
try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


class PDFViewer(ctk.CTkFrame):
    """PDF document viewer"""
    
    def __init__(self, parent, theme, app=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.theme = theme
        self.app = app
        self.current_file: Optional[Path] = None
        
        # PDF state
        self.doc = None
        self.current_page = 0
        self.total_pages = 0
        self.zoom_level = 1.0
        self.page_images: Dict[int, ImageTk.PhotoImage] = {}
        
        # Search state
        self.search_results: List = []
        self.current_result = 0
        
        self.configure(fg_color=theme.colors['bg'])
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Build UI
        self._create_toolbar()
        self._create_viewer_area()
        self._create_sidebar()
        
    def _create_toolbar(self):
        """Create the top toolbar"""
        toolbar = ctk.CTkFrame(self, height=45, fg_color=self.theme.colors['bg_light'])
        toolbar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(10, 5))
        toolbar.grid_columnconfigure(2, weight=1)
        
        # File info
        self.file_label = ctk.CTkLabel(
            toolbar,
            text="No PDF loaded",
            font=ctk.CTkFont(family="JetBrains Mono", size=12),
            text_color=self.theme.colors['text_dim']
        )
        self.file_label.grid(row=0, column=0, padx=15, pady=10)
        
        # Navigation controls
        nav_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        nav_frame.grid(row=0, column=1, padx=20, pady=5)
        
        btn_style = {
            "width": 35,
            "height": 30,
            "font": ctk.CTkFont(size=14),
            "fg_color": self.theme.colors['bg'],
            "hover_color": self.theme.colors['bg_hover'],
        }
        
        self.first_btn = ctk.CTkButton(nav_frame, text="⏮", command=self.go_first, **btn_style)
        self.first_btn.pack(side="left", padx=2)
        
        self.prev_btn = ctk.CTkButton(nav_frame, text="◀", command=self.go_prev, **btn_style)
        self.prev_btn.pack(side="left", padx=2)
        
        # Page entry
        self.page_entry = ctk.CTkEntry(
            nav_frame,
            width=50,
            height=30,
            font=ctk.CTkFont(family="JetBrains Mono", size=12),
            fg_color=self.theme.colors['bg'],
            border_color=self.theme.colors['border'],
            justify="center"
        )
        self.page_entry.pack(side="left", padx=5)
        self.page_entry.bind("<Return>", self._on_page_entry)
        
        self.total_label = ctk.CTkLabel(
            nav_frame,
            text="/ 0",
            font=ctk.CTkFont(family="JetBrains Mono", size=12),
            text_color=self.theme.colors['text_dim']
        )
        self.total_label.pack(side="left", padx=5)
        
        self.next_btn = ctk.CTkButton(nav_frame, text="▶", command=self.go_next, **btn_style)
        self.next_btn.pack(side="left", padx=2)
        
        self.last_btn = ctk.CTkButton(nav_frame, text="⏭", command=self.go_last, **btn_style)
        self.last_btn.pack(side="left", padx=2)
        
        # Spacer
        spacer = ctk.CTkFrame(toolbar, fg_color="transparent")
        spacer.grid(row=0, column=2, sticky="ew")
        
        # Search
        search_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        search_frame.grid(row=0, column=3, padx=10, pady=5)
        
        self.search_entry = ctk.CTkEntry(
            search_frame,
            width=200,
            height=30,
            placeholder_text="Search...",
            font=ctk.CTkFont(family="JetBrains Mono", size=11),
            fg_color=self.theme.colors['bg'],
            border_color=self.theme.colors['border']
        )
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<Return>", lambda e: self.search())
        
        self.search_btn = ctk.CTkButton(
            search_frame,
            text="🔍",
            width=35,
            height=30,
            fg_color=self.theme.colors['bg'],
            hover_color=self.theme.colors['bg_hover'],
            command=self.search
        )
        self.search_btn.pack(side="left", padx=2)
        
        # Zoom controls
        zoom_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        zoom_frame.grid(row=0, column=4, padx=10, pady=5)
        
        self.zoom_out_btn = ctk.CTkButton(zoom_frame, text="-", width=30, height=30,
                                          fg_color=self.theme.colors['bg'],
                                          hover_color=self.theme.colors['bg_hover'],
                                          command=self.zoom_out)
        self.zoom_out_btn.pack(side="left", padx=2)
        
        self.zoom_label = ctk.CTkLabel(
            zoom_frame,
            text="100%",
            width=50,
            font=ctk.CTkFont(family="JetBrains Mono", size=11)
        )
        self.zoom_label.pack(side="left", padx=5)
        
        self.zoom_in_btn = ctk.CTkButton(zoom_frame, text="+", width=30, height=30,
                                         fg_color=self.theme.colors['bg'],
                                         hover_color=self.theme.colors['bg_hover'],
                                         command=self.zoom_in)
        self.zoom_in_btn.pack(side="left", padx=2)
        
    def _create_viewer_area(self):
        """Create the PDF display area"""
        self.viewer_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=self.theme.colors['bg_dark'],
            corner_radius=8
        )
        self.viewer_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.viewer_frame.grid_columnconfigure(0, weight=1)
        
        # Page canvas
        self.page_label = ctk.CTkLabel(
            self.viewer_frame,
            text="📄\n\nDrop a PDF file here\nor use Open File",
            font=ctk.CTkFont(family="JetBrains Mono", size=16),
            text_color=self.theme.colors['text_muted']
        )
        self.page_label.pack(expand=True, pady=100)
        
        # Click to open
        self.page_label.bind("<Button-1>", lambda e: self.app.open_file() if self.app else None)
        
    def _create_sidebar(self):
        """Create the thumbnails/outline sidebar"""
        self.sidebar = ctk.CTkFrame(
            self,
            width=200,
            fg_color=self.theme.colors['bg_light'],
            corner_radius=8
        )
        self.sidebar.grid(row=1, column=1, sticky="ns", padx=(0, 10), pady=5)
        self.sidebar.grid_propagate(False)
        
        # Tab buttons
        tab_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        tab_frame.pack(fill="x", padx=5, pady=5)
        
        self.thumb_tab = ctk.CTkButton(
            tab_frame,
            text="Pages",
            font=ctk.CTkFont(family="JetBrains Mono", size=11),
            height=28,
            fg_color=self.theme.colors['bg'],
            hover_color=self.theme.colors['bg_hover'],
            command=lambda: self._show_tab("thumbnails")
        )
        self.thumb_tab.pack(side="left", fill="x", expand=True, padx=2)
        
        self.outline_tab = ctk.CTkButton(
            tab_frame,
            text="Outline",
            font=ctk.CTkFont(family="JetBrains Mono", size=11),
            height=28,
            fg_color="transparent",
            hover_color=self.theme.colors['bg_hover'],
            command=lambda: self._show_tab("outline")
        )
        self.outline_tab.pack(side="left", fill="x", expand=True, padx=2)
        
        # Thumbnails list
        self.thumb_scroll = ctk.CTkScrollableFrame(
            self.sidebar,
            fg_color="transparent"
        )
        self.thumb_scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Outline list (hidden by default)
        self.outline_scroll = ctk.CTkScrollableFrame(
            self.sidebar,
            fg_color="transparent"
        )
        
        self.current_tab = "thumbnails"
        
    def _show_tab(self, tab: str):
        """Switch between tabs"""
        if tab == "thumbnails":
            self.outline_scroll.pack_forget()
            self.thumb_scroll.pack(fill="both", expand=True, padx=5, pady=5)
            self.thumb_tab.configure(fg_color=self.theme.colors['bg'])
            self.outline_tab.configure(fg_color="transparent")
        else:
            self.thumb_scroll.pack_forget()
            self.outline_scroll.pack(fill="both", expand=True, padx=5, pady=5)
            self.thumb_tab.configure(fg_color="transparent")
            self.outline_tab.configure(fg_color=self.theme.colors['bg'])
            
        self.current_tab = tab
        
    def load_file(self, filepath: Path):
        """Load a PDF file"""
        if not HAS_PYMUPDF:
            self.page_label.configure(
                text="⚠️ PyMuPDF not available\nInstall pymupdf to enable PDF viewing"
            )
            return
            
        self.current_file = filepath
        self.file_label.configure(text=filepath.name)
        
        try:
            self.doc = fitz.open(filepath)
            self.total_pages = len(self.doc)
            self.current_page = 0
            
            # Update UI
            self.total_label.configure(text=f"/ {self.total_pages}")
            self.page_entry.delete(0, "end")
            self.page_entry.insert(0, "1")
            
            # Clear cache
            self.page_images.clear()
            
            # Load thumbnails
            self._load_thumbnails()
            
            # Load outline
            self._load_outline()
            
            # Display first page
            self._display_page()
            
        except Exception as e:
            if self.app:
                self.app.status_bar.set_message(f"Error loading PDF: {e}", error=True)
                
    def _load_thumbnails(self):
        """Load page thumbnails"""
        # Clear existing
        for widget in self.thumb_scroll.winfo_children():
            widget.destroy()
            
        def load():
            for i in range(min(self.total_pages, 50)):  # Limit thumbnails
                try:
                    page = self.doc[i]
                    pix = page.get_pixmap(matrix=fitz.Matrix(0.2, 0.2))
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    
                    # Create thumbnail button
                    self.after(0, lambda idx=i, image=img: self._add_thumbnail(idx, image))
                    
                except Exception as e:
                    print(f"Thumbnail error: {e}")
                    
        threading.Thread(target=load, daemon=True).start()
        
    def _add_thumbnail(self, page_num: int, image: Image.Image):
        """Add a thumbnail to the sidebar"""
        if not HAS_PIL:
            return
            
        thumb = ImageTk.PhotoImage(image)
        
        frame = ctk.CTkFrame(
            self.thumb_scroll,
            fg_color=self.theme.colors['bg'] if page_num == self.current_page else "transparent"
        )
        frame.pack(fill="x", pady=2)
        frame.thumb_image = thumb  # Keep reference
        
        lbl = ctk.CTkLabel(frame, image=thumb, text="")
        lbl.pack(side="left", padx=5, pady=5)
        
        num = ctk.CTkLabel(
            frame,
            text=f"{page_num + 1}",
            font=ctk.CTkFont(family="JetBrains Mono", size=10),
            text_color=self.theme.colors['text_dim']
        )
        num.pack(side="left", padx=5)
        
        # Click to go to page
        for widget in [frame, lbl, num]:
            widget.bind("<Button-1>", lambda e, p=page_num: self.go_to_page(p))
            
    def _load_outline(self):
        """Load document outline/bookmarks"""
        # Clear existing
        for widget in self.outline_scroll.winfo_children():
            widget.destroy()
            
        if not self.doc:
            return
            
        toc = self.doc.get_toc()
        
        for level, title, page in toc:
            indent = "  " * (level - 1)
            btn = ctk.CTkButton(
                self.outline_scroll,
                text=f"{indent}{title}",
                font=ctk.CTkFont(family="JetBrains Mono", size=11),
                height=25,
                fg_color="transparent",
                hover_color=self.theme.colors['bg_hover'],
                anchor="w",
                command=lambda p=page-1: self.go_to_page(p)
            )
            btn.pack(fill="x", pady=1)
            
    def _display_page(self):
        """Display the current page"""
        if not self.doc or not HAS_PIL:
            return
            
        try:
            # Check cache
            cache_key = (self.current_page, self.zoom_level)
            
            page = self.doc[self.current_page]
            
            # Render page
            mat = fitz.Matrix(self.zoom_level * 1.5, self.zoom_level * 1.5)
            pix = page.get_pixmap(matrix=mat)
            
            # Convert to PIL
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            photo = ImageTk.PhotoImage(img)
            
            # Update display
            self.page_label.configure(image=photo, text="")
            self.page_label.image = photo  # Keep reference
            
            # Update page entry
            self.page_entry.delete(0, "end")
            self.page_entry.insert(0, str(self.current_page + 1))
            
        except Exception as e:
            print(f"Page display error: {e}")
            
    def _on_page_entry(self, event):
        """Handle page entry submission"""
        try:
            page = int(self.page_entry.get()) - 1
            self.go_to_page(page)
        except ValueError:
            pass
            
    def go_to_page(self, page: int):
        """Navigate to a specific page"""
        if 0 <= page < self.total_pages:
            self.current_page = page
            self._display_page()
            
    def go_first(self):
        self.go_to_page(0)
        
    def go_prev(self):
        self.go_to_page(self.current_page - 1)
        
    def go_next(self):
        self.go_to_page(self.current_page + 1)
        
    def go_last(self):
        self.go_to_page(self.total_pages - 1)
        
    def zoom_in(self):
        """Zoom in"""
        self.zoom_level = min(3.0, self.zoom_level * 1.25)
        self.zoom_label.configure(text=f"{int(self.zoom_level * 100)}%")
        self._display_page()
        
    def zoom_out(self):
        """Zoom out"""
        self.zoom_level = max(0.25, self.zoom_level / 1.25)
        self.zoom_label.configure(text=f"{int(self.zoom_level * 100)}%")
        self._display_page()
        
    def search(self):
        """Search for text in PDF"""
        query = self.search_entry.get()
        if not query or not self.doc:
            return
            
        self.search_results = []
        
        for page_num in range(self.total_pages):
            page = self.doc[page_num]
            results = page.search_for(query)
            
            for rect in results:
                self.search_results.append((page_num, rect))
                
        if self.search_results:
            self.current_result = 0
            page_num, rect = self.search_results[0]
            self.go_to_page(page_num)
            
            if self.app:
                self.app.status_bar.set_message(
                    f"Found {len(self.search_results)} results"
                )
        else:
            if self.app:
                self.app.status_bar.set_message("No results found", error=True)
                
    def destroy(self):
        """Clean up on destroy"""
        if self.doc:
            self.doc.close()
        super().destroy()
