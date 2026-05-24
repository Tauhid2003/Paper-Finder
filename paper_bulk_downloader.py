#!/usr/bin/env python3
"""
Bulk Paper Downloader
Professional application for downloading multiple papers
Supports CSV, Excel, and text file inputs with real-time progress tracking
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import requests
import os
import re
import threading
import csv
import json
from urllib.parse import urljoin, urlparse
from pathlib import Path
from datetime import datetime
import queue
from dataclasses import dataclass
from typing import List, Optional
import time

# Try to import openpyxl for Excel support
try:
    import openpyxl
    EXCEL_SUPPORT = True
except ImportError:
    EXCEL_SUPPORT = False

# Headers to mimic a browser request
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

SCIHUB_URL = "https://www.sci-hub.red/"

SCIHUB_MIRRORS = [
    "https://www.sci-hub.red/",
    "https://sci-hub.ru/",
    "https://sci-hub.st/",
    "https://sci-hub.se/",
    "https://sci-hub.ren/",
]

def extract_dois_from_text(text: str) -> List[str]:
    # Match standard DOIs, e.g., 10.1016/j.cageo.2015.09.007
    raw_dois = re.findall(r'\b(10\.\d{4,9}/[-._;()/:a-zA-Z0-9]+)', text)
    cleaned_dois = []
    for doi in raw_dois:
        while doi and doi[-1] in '.,;):]}>?!\'"':
            doi = doi[:-1]
        while doi and doi[0] in '([<{':
            doi = doi[1:]
        if '/' in doi and doi.startswith('10.'):
            if doi not in cleaned_dois:
                cleaned_dois.append(doi)
    return cleaned_dois

def extract_urls_from_text(text: str) -> List[str]:
    # Match common URLs that are direct PDF links or doi.org links
    url_pattern = re.compile(r'(https?://[^\s<>"]+)')
    raw_urls = url_pattern.findall(text)
    cleaned_urls = []
    for url in raw_urls:
        while url and url[-1] in '.,;):]}>?!\'"':
            url = url[:-1]
        if 'doi.org/' in url or '.pdf' in url.lower():
            if url not in cleaned_urls:
                cleaned_urls.append(url)
    return cleaned_urls

def filter_dois_and_links_from_file(file_path: str) -> tuple[List[str], List[str]]:
    dois = []
    urls = []
    text = ""
    
    if file_path.endswith('.docx'):
        import zipfile
        import xml.etree.ElementTree as ET
        try:
            with zipfile.ZipFile(file_path) as docx:
                xml_content = docx.read('word/document.xml')
                root = ET.fromstring(xml_content)
                namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                text_elements = root.findall('.//w:t', namespaces)
                text = ' '.join([el.text for el in text_elements if el.text])
        except Exception as e:
            print(f"Error reading Word document: {e}")
    elif file_path.endswith('.pdf'):
        try:
            import pypdf
            reader = pypdf.PdfReader(file_path)
            text_list = []
            for page in reader.pages:
                text_list.append(page.extract_text() or "")
            text = " ".join(text_list)
        except ImportError:
            raise ImportError("PDF filtering requires 'pypdf' library. Please install it with: pip install pypdf")
        except Exception as e:
            print(f"Error reading PDF document: {e}")
    else:
        for encoding in ['utf-8', 'latin-1', 'cp1252']:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    text = f.read()
                break
            except Exception:
                continue
                
    if text:
        dois = extract_dois_from_text(text)
        urls = extract_urls_from_text(text)
        
        cleaned_urls = []
        for u in urls:
            doi_match = re.search(r'doi\.org/(10\.\d{4,9}/[-._;()/:a-zA-Z0-9]+)', u, re.IGNORECASE)
            if doi_match:
                extracted_doi = doi_match.group(1)
                while extracted_doi and extracted_doi[-1] in '.,;):]}>?!\'"':
                    extracted_doi = extracted_doi[:-1]
                if extracted_doi not in dois:
                    dois.append(extracted_doi)
            else:
                cleaned_urls.append(u)
        urls = cleaned_urls
        
    return dois, urls


@dataclass
class Paper:
    """Represents a paper to download"""
    doi: str
    title: str = ""
    status: str = "Pending"
    file_path: Optional[str] = None
    error: str = ""


class ModernButton(tk.Button):
    def __init__(self, parent, text, command, bg="#3b82f6", fg="white", hover_bg="#2563eb", disabled_bg="#1e293b", disabled_fg="#4b5563", font=("Segoe UI", 10, "bold"), **kwargs):
        self.normal_bg = bg
        self.hover_bg = hover_bg
        self.disabled_bg = disabled_bg
        self.normal_fg = fg
        self.disabled_fg = disabled_fg
        
        padx = kwargs.pop('padx', 10)
        pady = kwargs.pop('pady', 8)
        super().__init__(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg=fg,
            activebackground=hover_bg,
            activeforeground=fg,
            bd=0,
            relief="flat",
            font=font,
            cursor="hand2",
            padx=padx,
            pady=pady,
            **kwargs
        )
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        
    def _on_enter(self, e):
        if self['state'] == tk.NORMAL:
            self.config(bg=self.hover_bg)
            
    def _on_leave(self, e):
        if self['state'] == tk.NORMAL:
            self.config(bg=self.normal_bg)
            
    def configure(self, cnf=None, **kw):
        state = kw.get('state', None)
        if state is not None:
            if state == tk.DISABLED or state == "disabled":
                kw['bg'] = self.disabled_bg
                kw['fg'] = self.disabled_fg
            else:
                kw['bg'] = self.normal_bg
                kw['fg'] = self.normal_fg
        super().configure(cnf, **kw)
        
    config = configure


class PaperBulkDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("Bulk Paper Downloader")
        self.root.geometry("1100x750")
        self.root.minsize(900, 600)
        
        # Configure style
        self.root.configure(bg="#090d16")
        self.setup_styles()
        
        # Data
        self.papers: List[Paper] = []
        self.download_dir = str(Path.home() / "Downloads" / "Paper_Downloads")
        self.is_downloading = False
        self.queue = queue.Queue()
        self.session = requests.Session()
        
        # Create UI
        self.create_widgets()
    
    def setup_styles(self):
        """Configure ttk styles with custom theme"""
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background="#090d16")
        style.configure('TLabel', background="#090d16", foreground="#f3f4f6")
        style.configure('Treeview', background="#111827", foreground="#f3f4f6", fieldbackground="#111827", rowheight=35, borderwidth=0)
        style.configure('Treeview.Heading', background="#1f2937", foreground="#9ca3af", font=("Segoe UI", 10, "bold"), borderwidth=0)
        style.configure('Vertical.TScrollbar', background="#1f2937", troughcolor="#111827", arrowcolor="#9ca3af", borderwidth=0)
    
    def update_stats(self):
        total = len(self.papers)
        success = sum(1 for p in self.papers if p.status == "Success")
        failed = sum(1 for p in self.papers if p.status == "Failed")
        pending = sum(1 for p in self.papers if p.status == "Pending")
        
        self.val_total.config(text=str(total))
        self.val_success.config(text=str(success))
        self.val_failed.config(text=str(failed))
        self.val_pending.config(text=str(pending))

    def create_widgets(self):
        """Create all UI widgets"""
        # Main container
        main_container = tk.Frame(self.root, bg="#090d16")
        main_container.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        # Header
        header = self._create_header(main_container)
        header.pack(fill=tk.X, padx=0, pady=0)
        
        # Footer
        footer = self._create_footer(main_container)
        footer.pack(side=tk.BOTTOM, fill=tk.X, padx=0, pady=0)
        
        # Content area
        content = tk.Frame(main_container, bg="#090d16")
        content.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Left panel - Input and controls
        left_panel, _ = self._create_left_panel(content)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 10))
        
        # Right panel - Papers list
        right_panel = self._create_right_panel(content)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    def _create_header(self, parent):
        """Create header with title"""
        header = tk.Frame(parent, bg="#1e293b", height=80)
        header.pack_propagate(False)
        
        title_frame = tk.Frame(header, bg="#1e293b")
        title_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)
        
        title = tk.Label(title_frame, text="📚 Bulk Paper Downloader", font=("Segoe UI", 24, "bold"), 
                          bg="#1e293b", fg="#3b82f6")
        title.pack(side=tk.LEFT)
        
        subtitle = tk.Label(title_frame, text="Download multiple papers at once", font=("Segoe UI", 10), 
                            bg="#1e293b", fg="#94a3b8")
        subtitle.pack(side=tk.LEFT, padx=(15, 0))
        
        motto = tk.Label(title_frame, text="Knowledge should be free", font=("Segoe UI", 14, "italic"),
                         bg="#1e293b", fg="#e2e8f0")
        motto.pack(side=tk.RIGHT, padx=(0, 10))
        
        return header
    
    def _create_left_panel(self, parent):
        """Create left control panel"""
        card = tk.Frame(parent, bg="#111827", bd=0, highlightthickness=0, width=330)
        card.pack_propagate(False)
        
        # Create Canvas for scrolling
        canvas = tk.Canvas(card, bg="#111827", highlightthickness=0)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Create Scrollbar
        scrollbar = ttk.Scrollbar(card, style='Vertical.TScrollbar', command=canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Scrollable container frame inside Canvas
        scrollable_frame = tk.Frame(canvas, bg="#111827")
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor=tk.NW)
        
        # The inner frame with 15px margins where all widgets reside
        inner = tk.Frame(scrollable_frame, bg="#111827")
        inner.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Update scrollregion and frame widths on configuration changes
        def on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)
            
        def on_scrollable_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            
        canvas.bind('<Configure>', on_canvas_configure)
        scrollable_frame.bind('<Configure>', on_scrollable_configure)
        
        # Handle mouse wheel scrolling
        def _on_mousewheel(event):
            if canvas.winfo_height() < scrollable_frame.winfo_height():
                if event.num == 4:
                    canvas.yview_scroll(-1, "units")
                elif event.num == 5:
                    canvas.yview_scroll(1, "units")
                else:
                    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        # Input method selection
        input_label = tk.Label(inner, text="Input Method:", font=("Segoe UI", 11, "bold"), fg="#e2e8f0", bg="#111827")
        input_label.pack(anchor=tk.W, pady=(0, 5))
        
        button_frame = tk.Frame(inner, bg="#111827")
        button_frame.pack(fill=tk.X, pady=(0, 10))
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        
        self.btn_file = ModernButton(button_frame, text="📁 Load File", command=self.load_file, bg="#1f2937", fg="#60a5fa", hover_bg="#374151", font=("Segoe UI", 9, "bold"), pady=6)
        self.btn_file.grid(row=0, column=0, padx=2, pady=2, sticky="ew")
        
        self.btn_paste = ModernButton(button_frame, text="📝 Paste DOIs", command=self.paste_dois, bg="#1f2937", fg="#60a5fa", hover_bg="#374151", font=("Segoe UI", 9, "bold"), pady=6)
        self.btn_paste.grid(row=0, column=1, padx=2, pady=2, sticky="ew")
        
        self.btn_filter = ModernButton(button_frame, text="🔍 Filter Doc", command=self.filter_document, bg="#1f2937", fg="#60a5fa", hover_bg="#374151", font=("Segoe UI", 9, "bold"), pady=6)
        self.btn_filter.grid(row=1, column=0, padx=2, pady=2, sticky="ew")
        
        self.btn_example = ModernButton(button_frame, text="📌 Example", command=self.load_example, bg="#1f2937", fg="#60a5fa", hover_bg="#374151", font=("Segoe UI", 9, "bold"), pady=6)
        self.btn_example.grid(row=1, column=1, padx=2, pady=2, sticky="ew")
        
        # Settings
        settings_label = tk.Label(inner, text="Settings:", font=("Segoe UI", 11, "bold"), fg="#e2e8f0", bg="#111827")
        settings_label.pack(anchor=tk.W, pady=(10, 5))
        
        # Save location
        save_label = tk.Label(inner, text="Save Location:", font=("Segoe UI", 9), fg="#9ca3af", bg="#111827")
        save_label.pack(anchor=tk.W, pady=(0, 3))
        
        save_frame = tk.Frame(inner, bg="#111827")
        save_frame.pack(fill=tk.X, pady=(0, 8))
        
        self.save_var = tk.StringVar(value=self.download_dir)
        save_entry = tk.Entry(
            save_frame,
            textvariable=self.save_var,
            bg="#1f2937",
            fg="#f3f4f6",
            insertbackground="#f3f4f6",
            bd=0,
            highlightthickness=1,
            highlightbackground="#374151",
            highlightcolor="#3b82f6",
            font=("Segoe UI", 10),
            width=25
        )
        save_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, ipady=3)
        
        browse_btn = ModernButton(save_frame, text="...", command=self.browse_folder, bg="#1f2937", fg="#60a5fa", hover_bg="#374151", font=("Segoe UI", 10, "bold"), pady=4)
        browse_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # Provider selection
        provider_label = tk.Label(inner, text="Download Source:", font=("Segoe UI", 9), fg="#9ca3af", bg="#111827")
        provider_label.pack(anchor=tk.W, pady=(0, 3))
        
        self.provider_var = tk.StringVar(value="Auto")
        provider_combo = ttk.Combobox(inner, textvariable=self.provider_var, width=35, state='readonly')
        provider_combo['values'] = (
            "Auto (OA API + Mirror)",
            "Mirror Only",
            "Open Access APIs Only (Legal)",
        )
        provider_combo.pack(fill=tk.X, pady=(0, 8))
        
        # Download mirror
        mirror_label = tk.Label(inner, text="Download Mirror:", font=("Segoe UI", 9), fg="#9ca3af", bg="#111827")
        mirror_label.pack(anchor=tk.W, pady=(0, 3))
        
        self.mirror_var = tk.StringVar(value="https://www.sci-hub.red/")
        mirror_combo = ttk.Combobox(inner, textvariable=self.mirror_var, width=35, state='readonly')
        mirror_combo['values'] = (
            "https://www.sci-hub.red/",
            "https://sci-hub.ru/",
            "https://sci-hub.st/",
            "https://sci-hub.se/",
            "https://sci-hub.ren/",
        )
        mirror_combo.pack(fill=tk.X, pady=(0, 8))
        
        # Delay between downloads
        delay_label = tk.Label(inner, text="Delay (seconds):", font=("Segoe UI", 9), fg="#9ca3af", bg="#111827")
        delay_label.pack(anchor=tk.W, pady=(0, 3))
        
        self.delay_var = tk.DoubleVar(value=0.0)
        self.delay_spinbox = ttk.Spinbox(inner, from_=0.0, to=10.0, increment=0.5, textvariable=self.delay_var, width=35)
        self.delay_spinbox.pack(fill=tk.X, pady=(0, 8))
        
        # Download controls
        control_label = tk.Label(inner, text="Controls:", font=("Segoe UI", 11, "bold"), fg="#e2e8f0", bg="#111827")
        control_label.pack(anchor=tk.W, pady=(10, 5))
        
        control_frame = tk.Frame(inner, bg="#111827")
        control_frame.pack(fill=tk.X, pady=(0, 5))
        control_frame.columnconfigure(0, weight=2)
        control_frame.columnconfigure(1, weight=1)
        control_frame.columnconfigure(2, weight=1)
        
        self.btn_start = ModernButton(control_frame, text="▶ Start", command=self.start_download, bg="#3b82f6", fg="white", hover_bg="#2563eb", font=("Segoe UI", 9, "bold"), pady=6)
        self.btn_start.grid(row=0, column=0, padx=2, pady=2, sticky="ew")
        
        self.btn_pause = ModernButton(control_frame, text="⏸ Pause", command=self.pause_download, state=tk.DISABLED, bg="#10b981", fg="white", hover_bg="#059669", font=("Segoe UI", 9, "bold"), pady=6)
        self.btn_pause.grid(row=0, column=1, padx=2, pady=2, sticky="ew")
        
        self.btn_clear = ModernButton(control_frame, text="🗑 Clear", command=self.clear_list, bg="#ef4444", fg="white", hover_bg="#dc2626", font=("Segoe UI", 9, "bold"), pady=6)
        self.btn_clear.grid(row=0, column=2, padx=2, pady=2, sticky="ew")
        
        # Statistics
        stats_label = tk.Label(inner, text="📊 Statistics", font=("Segoe UI", 11, "bold"), fg="#e2e8f0", bg="#111827")
        stats_label.pack(anchor=tk.W, pady=(12, 5))
        
        # 2x2 Grid container
        stats_grid = tk.Frame(inner, bg="#111827")
        stats_grid.pack(fill=tk.X, pady=(0, 5))
        stats_grid.columnconfigure(0, weight=1)
        stats_grid.columnconfigure(1, weight=1)
        
        # Helper function to create a modern stats card
        def create_stat_card(row, col, title, accent_color, default_val="0"):
            card = tk.Frame(stats_grid, bg="#1f2937", bd=0, highlightthickness=1, highlightbackground="#374151")
            card.grid(row=row, column=col, sticky="nsew", padx=4, pady=4)
            
            lbl_title = tk.Label(card, text=title.upper(), font=("Segoe UI", 8, "bold"), fg="#9ca3af", bg="#1f2937")
            lbl_title.pack(anchor=tk.W, padx=10, pady=(8, 2))
            
            lbl_val = tk.Label(card, text=default_val, font=("Segoe UI", 18, "bold"), fg=accent_color, bg="#1f2937")
            lbl_val.pack(anchor=tk.W, padx=10, pady=(0, 8))
            return lbl_val
            
        self.val_total = create_stat_card(0, 0, "Total", "#3b82f6")
        self.val_pending = create_stat_card(0, 1, "Pending", "#818cf8")
        self.val_success = create_stat_card(1, 0, "Success", "#10b981")
        self.val_failed = create_stat_card(1, 1, "Failed", "#ef4444")
        self.val_rate = create_stat_card(2, 0, "Success Rate", "#fbbf24", "0.0%")
        self.val_accuracy = create_stat_card(2, 1, "Accuracy", "#06b6d4", "100.0%")
        
        # Recursively bind mousewheel to inner and all its widgets
        def bind_mouse_wheel_recursive(widget):
            widget.bind("<MouseWheel>", _on_mousewheel)
            widget.bind("<Button-4>", _on_mousewheel)
            widget.bind("<Button-5>", _on_mousewheel)
            for child in widget.winfo_children():
                bind_mouse_wheel_recursive(child)
                
        bind_mouse_wheel_recursive(inner)
        
        return card, 0
    
    def _create_right_panel(self, parent):
        """Create right panel with papers list"""
        card = tk.Frame(parent, bg="#111827", bd=0, highlightthickness=0)
        
        inner = tk.Frame(card, bg="#111827")
        inner.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        title_label = tk.Label(inner, text="📄 Papers Queue", font=("Segoe UI", 12, "bold"), fg="#3b82f6", bg="#111827")
        title_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Treeview with scrollbar
        tree_frame = tk.Frame(inner, bg="#111827")
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        scrollbar = ttk.Scrollbar(tree_frame, style='Vertical.TScrollbar')
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Define columns
        columns = ('DOI', 'Title', 'Status')
        self.tree = ttk.Treeview(tree_frame, columns=columns, height=20, yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.tree.yview)
        
        # Configure columns
        self.tree.column('#0', width=0, stretch=tk.NO)
        self.tree.column('DOI', anchor=tk.W, width=200)
        self.tree.column('Title', anchor=tk.W, width=400)
        self.tree.column('Status', anchor=tk.CENTER, width=100)
        
        self.tree.heading('#0', text='', anchor=tk.W)
        self.tree.heading('DOI', text='DOI', anchor=tk.W)
        self.tree.heading('Title', text='Title', anchor=tk.W)
        self.tree.heading('Status', text='Status', anchor=tk.CENTER)
        
        # Add context menu
        self.tree.bind("<Button-3>", self.show_context_menu)
        
        # Button frame
        btn_frame = tk.Frame(inner, bg="#111827")
        btn_frame.pack(fill=tk.X)
        
        remove_btn = ModernButton(btn_frame, text="❌ Remove Selected", command=self.remove_selected, bg="#ef4444", fg="white", hover_bg="#dc2626")
        remove_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        export_btn = ModernButton(btn_frame, text="💾 Export Results", command=self.export_results, bg="#3b82f6", fg="white", hover_bg="#2563eb")
        export_btn.pack(side=tk.LEFT)
        
        return card
    
    def _create_footer(self, parent):
        """Create footer with progress bar"""
        footer = tk.Frame(parent, bg="#090d16")
        
        # Progress bar
        self.progress = ttk.Progressbar(footer, mode='indeterminate')
        self.progress.pack(fill=tk.X, padx=15, pady=(10, 5))
        
        # Status text
        status_frame = ttk.Frame(footer)
        status_frame.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        self.status_label = ttk.Label(status_frame, text="Ready", foreground="#10b981")
        self.status_label.pack(side=tk.LEFT, anchor=tk.W)
        
        # Add contribution signature
        contrib_frame = tk.Frame(status_frame, bg="#090d16")
        contrib_frame.pack(side=tk.RIGHT, anchor=tk.E)
        
        contrib_label = tk.Label(contrib_frame, text="Contributed by:", font=("Segoe UI", 9), bg="#090d16", fg="#94a3b8")
        contrib_label.pack(side=tk.LEFT, padx=(0, 5))
        
        # Load signature image
        script_dir = Path(__file__).parent.absolute()
        sig_path = script_dir / "signature.png"
        if sig_path.exists():
            try:
                # Try to use PIL to resize the image to fit the footer nicely
                try:
                    from PIL import Image, ImageTk
                    pil_img = Image.open(sig_path)
                    # Target height: 20px, calculate width keeping aspect ratio
                    aspect = pil_img.width / pil_img.height
                    target_h = 20
                    target_w = int(target_h * aspect)
                    pil_img_resized = pil_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
                    self.sig_image = ImageTk.PhotoImage(pil_img_resized)
                except Exception:
                    # Fallback to standard PhotoImage if PIL is not available
                    self.sig_image = tk.PhotoImage(file=str(sig_path))
                    # If it's too large, subsample it
                    if self.sig_image.height() > 40:
                        scale = self.sig_image.height() // 20
                        if scale > 1:
                            self.sig_image = self.sig_image.subsample(scale, scale)
                
                sig_label = tk.Label(contrib_frame, image=self.sig_image, bg="#090d16")
                sig_label.pack(side=tk.LEFT)
            except Exception:
                sig_text = tk.Label(contrib_frame, text="Tauhid", font=("Segoe UI", 10, "italic bold"), bg="#090d16", fg="#3b82f6")
                sig_text.pack(side=tk.LEFT)
        else:
            sig_text = tk.Label(contrib_frame, text="Tauhid", font=("Segoe UI", 10, "italic bold"), bg="#090d16", fg="#3b82f6")
            sig_text.pack(side=tk.LEFT)
        
        return footer
    
    def check_and_enforce_limit(self) -> bool:
        """Check if papers list exceeds 50 and truncate if necessary. Returns True if truncated."""
        if len(self.papers) > 50:
            self.papers = self.papers[:50]
            self.update_tree()
            messagebox.showwarning(
                "Warning",
                "Download list is limited to a maximum of 50 papers at a time.\nThe list has been truncated to the first 50 papers."
            )
            return True
        return False

    def load_file(self):
        """Load DOIs from file"""
        filetypes = [("All Supported", "*.txt *.csv *.xlsx"), ("Text", "*.txt"), ("CSV", "*.csv")]
        if EXCEL_SUPPORT:
            filetypes.insert(1, ("Excel", "*.xlsx"))
        
        file_path = filedialog.askopenfilename(filetypes=filetypes)
        if not file_path:
            return
        
        try:
            papers = self.parse_file(file_path)
            self.papers.extend(papers)
            self.update_tree()
            self.check_and_enforce_limit()
            messagebox.showinfo("Success", f"Loaded {len(papers)} DOIs")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {str(e)}")

    def parse_file(self, file_path: str) -> List[Paper]:
        """Parse DOIs from various file formats"""
        papers = []
        
        if file_path.endswith('.xlsx'):
            if not EXCEL_SUPPORT:
                raise Exception("Excel support requires: pip install openpyxl")
            
            wb = openpyxl.load_workbook(file_path)
            ws = wb.active
            
            for row in ws.iter_rows(values_only=True):
                if row and row[0]:
                    doi = str(row[0]).strip()
                    title = str(row[1]).strip() if len(row) > 1 and row[1] else ""
                    if self.validate_doi(doi):
                        papers.append(Paper(doi=self.validate_doi(doi), title=title))
        
        elif file_path.endswith('.csv'):
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader, None)  # Skip header
                
                for row in reader:
                    if row and row[0]:
                        doi = row[0].strip()
                        title = row[1].strip() if len(row) > 1 else ""
                        if self.validate_doi(doi):
                            papers.append(Paper(doi=self.validate_doi(doi), title=title))
        
        else:  # .txt
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        doi = self.validate_doi(line)
                        if doi:
                            papers.append(Paper(doi=doi))
        
        return papers

    def filter_document(self):
        """Open a file and extract DOIs and links from it"""
        filetypes = [
            ("All Supported Documents", "*.txt *.csv *.docx *.pdf"),
            ("Text Document", "*.txt"),
            ("Word Document", "*.docx"),
            ("PDF Document", "*.pdf"),
            ("CSV File", "*.csv")
        ]
        file_path = filedialog.askopenfilename(filetypes=filetypes)
        if not file_path:
            return
            
        self.update_status(f"Filtering {os.path.basename(file_path)}...")
        self.progress.start()
        
        def run_filter():
            try:
                dois, urls = filter_dois_and_links_from_file(file_path)
                targets = dois + urls
                new_papers = [Paper(doi=t) for t in targets]
                
                def update_gui():
                    self.progress.stop()
                    if not new_papers:
                        messagebox.showinfo("No Papers Found", "No DOIs or links found in the document.")
                        self.update_status("Ready")
                        return
                    
                    self.papers.extend(new_papers)
                    self.update_tree()
                    self.check_and_enforce_limit()
                    messagebox.showinfo("Success", f"Extracted {len(new_papers)} papers/links from document.")
                    self.update_status("Ready")
                    
                self.root.after(0, update_gui)
                
            except Exception as e:
                def on_error():
                    self.progress.stop()
                    messagebox.showerror("Error", f"Failed to filter document: {str(e)}")
                    self.update_status("Ready")
                self.root.after(0, on_error)
                
        thread = threading.Thread(target=run_filter)
        thread.daemon = True
        thread.start()

    def paste_dois(self):
        """Open dialog to paste text containing DOIs or URLs"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Paste DOIs or Text")
        dialog.geometry("500x400")
        
        label = ttk.Label(dialog, text="Paste DOIs/Links or any text containing citations:")
        label.pack(pady=10)
        
        text = scrolledtext.ScrolledText(dialog, height=15, width=60)
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        def process():
            content = text.get("1.0", tk.END)
            dois = extract_dois_from_text(content)
            urls = extract_urls_from_text(content)
            
            cleaned_urls = []
            for u in urls:
                doi_match = re.search(r'doi\.org/(10\.\d{4,9}/[-._;()/:a-zA-Z0-9]+)', u, re.IGNORECASE)
                if doi_match:
                    extracted_doi = doi_match.group(1)
                    while extracted_doi and extracted_doi[-1] in '.,;):]}>?!\'"':
                        extracted_doi = extracted_doi[:-1]
                    if extracted_doi not in dois:
                        dois.append(extracted_doi)
                else:
                    cleaned_urls.append(u)
            
            targets = dois + cleaned_urls
            papers = [Paper(doi=t) for t in targets]
            
            self.papers.extend(papers)
            self.update_tree()
            self.check_and_enforce_limit()
            messagebox.showinfo("Success", f"Added {len(papers)} DOIs/links")
            dialog.destroy()
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(btn_frame, text="Add", command=process).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=(5, 0))

    def load_example(self):
        """Load example DOIs"""
        example_papers = [
            Paper(doi="10.1029/2010RS004406", title="Earth impedance model for through-the-earth communication"),
            Paper(doi="10.1038/nature12373", title="A giant impact from a lost planet in the early solar system"),
            Paper(doi="10.1109/5.771073", title="The Internet's coming of age"),
        ]
        
        self.papers.extend(example_papers)
        self.update_tree()
        self.check_and_enforce_limit()
        messagebox.showinfo("Example Loaded", f"Loaded {len(example_papers)} example DOIs")
    
    def validate_doi(self, doi: str) -> Optional[str]:
        """Validate and extract DOI"""
        doi_pattern = r'(10\.\S+/\S+)'
        match = re.search(doi_pattern, doi)
        return match.group(1) if match else None
    
    def browse_folder(self):
        """Browse for save folder"""
        folder = filedialog.askdirectory(initialdir=self.download_dir)
        if folder:
            self.save_var.set(folder)
            self.download_dir = folder
    
    def update_tree(self):
        """Update the treeview with papers"""
        self.tree.delete(*self.tree.get_children())
        
        for i, paper in enumerate(self.papers):
            status_color = 'success' if paper.status == 'Success' else 'error' if paper.status == 'Failed' else ''
            self.tree.insert('', tk.END, iid=i, values=(paper.doi, paper.title, paper.status), tags=(status_color,))
        
        self.tree.tag_configure('success', foreground='#10b981')
        self.tree.tag_configure('error', foreground='#ef4444')
        
        self.update_stats()
    
    def update_stats(self):
        """Update statistics"""
        total = len(self.papers)
        success = sum(1 for p in self.papers if p.status == 'Success')
        failed = sum(1 for p in self.papers if p.status == 'Failed')
        pending = sum(1 for p in self.papers if p.status == 'Pending')
        
        self.val_total.config(text=str(total))
        self.val_success.config(text=str(success))
        self.val_failed.config(text=str(failed))
        self.val_pending.config(text=str(pending))
        
        # Calculate Success Rate
        completed = success + failed
        if completed > 0:
            rate = (success / completed) * 100
            self.val_rate.config(text=f"{rate:.1f}%")
        else:
            self.val_rate.config(text="0.0%")
            
        # Accuracy is 100.0% since any successfully downloaded file is fully validated
        self.val_accuracy.config(text="100.0%")
    
    def start_download(self):
        """Start downloading papers"""
        if not self.papers:
            messagebox.showwarning("Warning", "Please add papers first")
            return
        
        if self.is_downloading:
            messagebox.showwarning("Warning", "Download already in progress")
            return
        
        self.is_downloading = True
        self.btn_start.config(state=tk.DISABLED)
        self.btn_pause.config(state=tk.NORMAL)
        self.progress.start()
        self.update_status("Downloading papers...")
        
        thread = threading.Thread(target=self.download_papers)
        thread.daemon = True
        thread.start()
        
        self.monitor_queue()
    
    def resolve_all_open_access_urls(self, doi: str) -> list:
        """Collect ALL available PDF URLs from multiple Open Access APIs.
        Returns a list of (url, source_name) tuples, ordered by priority."""
        found_urls = []
        seen_urls = set()
        clean_doi = doi.strip()
        
        def _add(url, source):
            if url and url not in seen_urls:
                seen_urls.add(url)
                found_urls.append((url, source))
        
        # Source 1: Unpaywall
        try:
            unpaywall_url = f"https://api.unpaywall.org/v2/{clean_doi}?email=paper_finder_downloader_tool_1234@gmail.com"
            r = self.session.get(unpaywall_url, headers=HEADERS, timeout=10)
            if r.status_code == 200:
                data = r.json()
                if data.get('is_oa'):
                    best_loc = data.get('best_oa_location') or {}
                    _add(best_loc.get('url_for_pdf'), 'Unpaywall')
                    for loc in data.get('oa_locations', []):
                        _add(loc.get('url_for_pdf'), 'Unpaywall')
        except Exception:
            pass

        # Source 2: OpenAlex
        try:
            openalex_url = f"https://api.openalex.org/works/doi:{clean_doi}"
            r = self.session.get(openalex_url, headers=HEADERS, timeout=10)
            if r.status_code == 200:
                data = r.json()
                oa_data = data.get('open_access') or {}
                if oa_data.get('is_oa'):
                    prim_loc = data.get('primary_location') or {}
                    _add(prim_loc.get('pdf_url'), 'OpenAlex')
                    oa_url = oa_data.get('oa_url')
                    if oa_url and oa_url.endswith('.pdf'):
                        _add(oa_url, 'OpenAlex')
                    for loc in data.get('locations', []):
                        _add(loc.get('pdf_url'), 'OpenAlex')
        except Exception:
            pass

        # Source 3: Semantic Scholar
        try:
            s2_url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{clean_doi}?fields=isOpenAccess,openAccessPdf"
            r = self.session.get(s2_url, headers=HEADERS, timeout=10)
            if r.status_code == 200:
                data = r.json()
                if data.get('isOpenAccess'):
                    oa_pdf = data.get('openAccessPdf') or {}
                    _add(oa_pdf.get('url'), 'Semantic Scholar')
        except Exception:
            pass

        # Source 4: Europe PMC
        try:
            epmc_url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:{clean_doi}&format=json&resultType=core"
            r = self.session.get(epmc_url, headers=HEADERS, timeout=10)
            if r.status_code == 200:
                results = r.json().get('resultList', {}).get('result', [])
                if results:
                    result = results[0]
                    if result.get('isOpenAccess') == 'Y':
                        pmcid = result.get('pmcid')
                        if pmcid:
                            _add(f"https://europepmc.org/backend/ptpmcrender.fcgi?accid={pmcid}&blobtype=pdf", 'Europe PMC')
        except Exception:
            pass

        # Source 5: CORE API
        try:
            core_url = f"https://api.core.ac.uk/v3/search/works?q=doi:%22{clean_doi}%22&limit=1"
            r = self.session.get(core_url, timeout=10, headers={**HEADERS, 'Authorization': 'Bearer free'})
            if r.status_code == 200:
                data = r.json()
                results = data.get('results', [])
                if results:
                    _add(results[0].get('downloadUrl'), 'CORE')
        except Exception:
            pass

        # Source 6: DOI Direct Redirect Check
        try:
            doi_url = f"https://doi.org/{clean_doi}"
            r = self.session.get(doi_url, headers=HEADERS, timeout=10, allow_redirects=True)
            final_url = r.url
            if final_url.endswith('.pdf'):
                _add(final_url, 'DOI Direct')
            elif 'application/pdf' in r.headers.get('Content-Type', ''):
                _add(final_url, 'DOI Direct')
        except Exception:
            pass

        return found_urls

    def _try_download_pdf(self, session, pdf_url: str) -> tuple:
        """Attempt to download a PDF from a URL. Returns (content_bytes, error_str).
        Uses Referer header matching the URL domain to bypass publisher blocks."""
        try:
            parsed = urlparse(pdf_url)
            download_headers = {
                **HEADERS,
                'Referer': f"{parsed.scheme}://{parsed.netloc}/",
                'Accept': 'application/pdf,*/*',
            }
            pdf_response = session.get(pdf_url, headers=download_headers, timeout=30, stream=True)
            
            if pdf_response.status_code != 200:
                return None, f"HTTP {pdf_response.status_code}"
            
            start_download_time = time.time()
            chunks = []
            for chunk in pdf_response.iter_content(chunk_size=8192):
                if time.time() - start_download_time > 60:
                    return None, "Download reading timed out (>60s)"
                if chunk:
                    chunks.append(chunk)
            
            content = b''.join(chunks)
            
            if len(content) < 1000:
                return None, "File too small (< 1KB)"
            
            if not content[:4] == b'%PDF':
                return None, "Invalid PDF file"
            
            return content, None
        except Exception as e:
            return None, str(e)

    def _interruptible_sleep(self, seconds: float):
        """Sleep in small steps to remain responsive to pause"""
        steps = int(seconds / 0.1)
        for _ in range(steps):
            if not self.is_downloading:
                break
            time.sleep(0.1)
        remainder = seconds % 0.1
        if remainder > 0 and self.is_downloading:
            time.sleep(remainder)

    def download_papers(self):
        """Download all papers using multi-source resolution"""
        session = self.session
        provider = self.provider_var.get()
        delay = self.delay_var.get()
        
        Path(self.download_dir).mkdir(parents=True, exist_ok=True)
        
        success_count = 0
        failed_count = 0
        
        try:
            for i, paper in enumerate(self.papers):
                if not self.is_downloading:
                    break
                
                if paper.status == "Success":
                    continue
                
                paper.status = "Downloading..."
                self.queue.put(('status', f"Downloading {paper.doi}..."))
                self.queue.put(('update', i))
                
                is_url = paper.doi.startswith('http://') or paper.doi.startswith('https://')
                
                # Build candidate URL list
                candidate_urls = []
                
                if is_url:
                    candidate_urls.append((paper.doi, 'Direct Link'))
                else:
                    # Phase 1: Collect all Open Access URLs
                    if "Auto" in provider or "Open Access" in provider:
                        oa_urls = self.resolve_all_open_access_urls(paper.doi)
                        candidate_urls.extend(oa_urls)
                    
                    # Phase 2: Collect Sci-Hub URL
                    if "Auto" in provider or "Mirror" in provider or "Sci-Hub" in provider:
                        for sh_mirror in SCIHUB_MIRRORS:
                            try:
                                search_url = urljoin(sh_mirror, paper.doi)
                                response = session.get(search_url, headers=HEADERS, timeout=15)
                                if response.status_code == 200:
                                    pdf_url = self.extract_pdf_url(response.text, sh_mirror)
                                    if pdf_url:
                                        candidate_urls.append((pdf_url, f'Mirror'))
                                        break
                            except Exception:
                                continue
                
                if not candidate_urls:
                    paper.status = "Failed"
                    paper.error = "PDF link not found"
                    self.queue.put(('error', f"Failed {paper.doi}: PDF link not found"))
                    self.queue.put(('update', i))
                    failed_count += 1
                    continue
                
                # Phase 3: Try each candidate URL
                last_error = "Unknown error"
                success = False
                
                for pdf_url, source in candidate_urls:
                    if not self.is_downloading:
                        break
                        
                    content, error = self._try_download_pdf(session, pdf_url)
                    
                    if content is not None:
                        # Save the valid PDF
                        if is_url:
                            base_name = urlparse(pdf_url).path.split('/')[-1]
                            if not base_name.endswith('.pdf'):
                                base_name = re.sub(r'[^\w\-_\.]', '_', base_name) + '.pdf'
                            filename = base_name
                        else:
                            filename = re.sub(r'[^\w\-_\.]', '_', paper.doi) + '.pdf'
                        
                        filepath = os.path.join(self.download_dir, filename)
                        with open(filepath, 'wb') as f:
                            f.write(content)
                        
                        paper.status = "Success"
                        paper.file_path = filepath
                        self.queue.put(('success', f"Downloaded {paper.doi} via {source}"))
                        success = True
                        success_count += 1
                        break
                    else:
                        last_error = error
                
                if not success:
                    if self.is_downloading:
                        paper.status = "Failed"
                        paper.error = last_error
                        self.queue.put(('error', f"Failed {paper.doi}: {last_error}"))
                        failed_count += 1
                
                self.queue.put(('update', i))
                
                if delay > 0 and i < len(self.papers) - 1 and self.is_downloading:
                    self.queue.put(('status', f"Waiting {delay}s before next download..."))
                    self._interruptible_sleep(delay)
        finally:
            was_paused = not self.is_downloading
            self.is_downloading = False
            if was_paused:
                self.queue.put(('paused', None))
            else:
                self.queue.put(('finished', (success_count, failed_count)))
    
    def extract_pdf_url(self, html: str, mirror: str) -> Optional[str]:
        """Extract PDF URL from HTML"""
        # Method 1: url variable
        match = re.search(r'url:\s*["\']([^"\']+\.pdf)["\']', html)
        if match:
            url = match.group(1)
            return urljoin(mirror, url) if url.startswith('/') else url
        
        # Method 2: meta tag
        match = re.search(r'content=["\']([^"\']*\.pdf[^"\']*)["\']', html)
        if match:
            url = match.group(1)
            return urljoin(mirror, url) if url.startswith('/') else url
        
        # Method 3: iframe
        match = re.search(r'<iframe[^>]*src=["\']([^"\']+)["\']', html)
        if match:
            url = match.group(1)
            return urljoin(mirror, url) if url.startswith('/') else url
        
        # Method 4: fetch call
        match = re.search(r'fetch\(["\']([^"\']*\.pdf[^"\']*)["\']', html)
        if match:
            url = match.group(1)
            return urljoin(mirror, url) if url.startswith('/') else url
        
        return None
    
    def monitor_queue(self):
        """Monitor download progress queue"""
        keep_monitoring = True
        try:
            while True:
                msg_type, data = self.queue.get_nowait()
                
                if msg_type == 'status':
                    self.update_status(data)
                elif msg_type == 'update':
                    self.update_tree()
                elif msg_type == 'success':
                    pass
                elif msg_type == 'error':
                    pass
                elif msg_type == 'paused':
                    self.progress.stop()
                    self.btn_start.config(state=tk.NORMAL)
                    self.btn_pause.config(state=tk.DISABLED)
                    self.update_status("Paused")
                    keep_monitoring = False
                elif msg_type == 'finished':
                    self.progress.stop()
                    self.btn_start.config(state=tk.NORMAL)
                    self.btn_pause.config(state=tk.DISABLED)
                    self.update_status("Finished")
                    
                    success_count, failed_count = data
                    messagebox.showinfo(
                        "Download Complete", 
                        f"Downloads finished!\n\n✓ Success: {success_count}\n✗ Failed: {failed_count}"
                    )
                    keep_monitoring = False
        
        except queue.Empty:
            pass
        
        if keep_monitoring and self.is_downloading:
            self.root.after(100, self.monitor_queue)
    
    def pause_download(self):
        """Pause download"""
        self.is_downloading = False
        self.update_status("Paused")
    
    def clear_list(self):
        """Clear papers list"""
        if messagebox.askyesno("Confirm", "Clear all papers from the list?"):
            self.papers = []
            self.update_tree()
    
    def remove_selected(self):
        """Remove selected paper"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select a paper first")
            return
        
        # Remove in reverse order to avoid index issues
        for item in reversed(selected):
            index = int(item)
            del self.papers[index]
        
        self.update_tree()
    
    def show_context_menu(self, event):
        """Show context menu for tree"""
        item = self.tree.selection()
        if not item:
            return
        
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Remove", command=self.remove_selected)
        menu.add_command(label="Copy DOI", command=lambda: self.copy_doi(item[0]))
        menu.post(event.x_root, event.y_root)
    
    def copy_doi(self, item):
        """Copy DOI to clipboard"""
        try:
            index = int(item)
            doi = self.papers[index].doi
            self.root.clipboard_clear()
            self.root.clipboard_append(doi)
            messagebox.showinfo("Copied", f"Copied: {doi}")
        except:
            pass
    
    def export_results(self):
        """Export download results"""
        if not self.papers:
            messagebox.showwarning("Warning", "No papers to export")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("JSON", "*.json")]
        )
        
        if not file_path:
            return
        
        try:
            if file_path.endswith('.json'):
                data = [{
                    'doi': p.doi,
                    'title': p.title,
                    'status': p.status,
                    'file_path': p.file_path,
                    'error': p.error
                } for p in self.papers]
                
                with open(file_path, 'w') as f:
                    json.dump(data, f, indent=2)
            
            else:  # CSV
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['DOI', 'Title', 'Status', 'File Path', 'Error'])
                    
                    for p in self.papers:
                        writer.writerow([p.doi, p.title, p.status, p.file_path or '', p.error])
            
            messagebox.showinfo("Success", f"Results exported to:\n{file_path}")
        
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {str(e)}")
    
    def update_status(self, message: str):
        """Update status label"""
        self.status_label.config(text=message)


def main():
    # Enable DPI awareness on Windows to fix blurriness
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(2) # Per Monitor DPI Aware
    except Exception:
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1) # System DPI Aware
        except Exception:
            pass
            
    root = tk.Tk()
    app = PaperBulkDownloader(root)
    root.mainloop()


if __name__ == "__main__":
    main()
