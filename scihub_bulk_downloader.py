#!/usr/bin/env python3
"""
Sci-Hub Bulk Paper Downloader
Professional application for downloading multiple papers from Sci-Hub
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
from urllib.parse import urljoin
from pathlib import Path
from datetime import datetime
import queue
from dataclasses import dataclass
from typing import List, Optional

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


@dataclass
class Paper:
    """Represents a paper to download"""
    doi: str
    title: str = ""
    status: str = "Pending"
    file_path: Optional[str] = None
    error: str = ""


class SciHubBulkDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("Sci-Hub Bulk Paper Downloader")
        self.root.geometry("1100x750")
        self.root.minsize(900, 600)
        
        # Configure style
        self.root.configure(bg="#0f172a")
        self.setup_styles()
        
        # Data
        self.papers: List[Paper] = []
        self.download_dir = str(Path.home() / "Downloads" / "SciHub_Papers")
        self.is_downloading = False
        self.queue = queue.Queue()
        
        # Create UI
        self.create_widgets()
        self.monitor_queue()
    
    def setup_styles(self):
        """Configure ttk styles with custom theme"""
        style = ttk.Style()
        
        # Colors
        bg_dark = "#0f172a"
        bg_card = "#1e293b"
        accent = "#3b82f6"
        accent_hover = "#60a5fa"
        success = "#10b981"
        error = "#ef4444"
        text_light = "#e2e8f0"
        text_muted = "#94a3b8"
        
        # Configure styles
        style.theme_use('clam')
        style.configure('TFrame', background=bg_dark)
        style.configure('TLabel', background=bg_dark, foreground=text_light)
        style.configure('Header.TLabel', background=bg_dark, foreground=text_light, font=('Segoe UI', 12, 'bold'))
        style.configure('Accent.TLabel', background=bg_dark, foreground=accent, font=('Segoe UI', 10, 'bold'))
        style.configure('TButton', background=accent, foreground='white')
        style.map('TButton', background=[('active', accent_hover)])
        style.configure('Success.TLabel', background=bg_dark, foreground=success)
        style.configure('Error.TLabel', background=bg_dark, foreground=error)
        style.configure('Treeview', background=bg_card, foreground=text_light, fieldbackground=bg_card)
        style.configure('Treeview.Heading', background=bg_card, foreground=text_light)
    
    def create_widgets(self):
        """Create all UI widgets"""
        # Main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        # Header
        header = self._create_header(main_container)
        header.pack(fill=tk.X, padx=0, pady=0)
        
        # Content area
        content = ttk.Frame(main_container)
        content.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Left panel - Input and controls
        left_panel = self._create_left_panel(content)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 10))
        
        # Right panel - Papers list
        right_panel = self._create_right_panel(content)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Footer
        footer = self._create_footer(main_container)
        footer.pack(fill=tk.X, padx=0, pady=0)
    
    def _create_header(self, parent):
        """Create header with title"""
        header = ttk.Frame(parent)
        header.configure(height=80)
        
        # Add background color using nested frame
        bg_frame = tk.Frame(header, bg="#1e293b", height=80)
        bg_frame.pack(fill=tk.BOTH, expand=True)
        bg_frame.pack_propagate(False)
        
        title_frame = ttk.Frame(bg_frame)
        title_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)
        
        title = tk.Label(title_frame, text="📚 Sci-Hub Bulk Downloader", font=("Segoe UI", 24, "bold"), 
                         bg="#1e293b", fg="#3b82f6")
        title.pack(side=tk.LEFT)
        
        subtitle = tk.Label(title_frame, text="Download multiple papers at once", font=("Segoe UI", 10), 
                           bg="#1e293b", fg="#94a3b8")
        subtitle.pack(side=tk.LEFT, padx=(15, 0))
        
        return header
    
    def _create_left_panel(self, parent):
        """Create left control panel"""
        panel = ttk.LabelFrame(parent, text="📋 Add Papers", padding=15)
        
        # Input method selection
        input_label = ttk.Label(panel, text="Input Method:", style='Header.TLabel')
        input_label.pack(anchor=tk.W, pady=(0, 10))
        
        button_frame = ttk.Frame(panel)
        button_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.btn_file = ttk.Button(button_frame, text="📁 Load File", command=self.load_file)
        self.btn_file.pack(fill=tk.X, pady=(0, 5))
        
        self.btn_paste = ttk.Button(button_frame, text="📝 Paste DOIs", command=self.paste_dois)
        self.btn_paste.pack(fill=tk.X, pady=(0, 5))
        
        self.btn_example = ttk.Button(button_frame, text="📌 Load Example", command=self.load_example)
        self.btn_example.pack(fill=tk.X)
        
        # Settings
        settings_label = ttk.Label(panel, text="⚙️ Settings:", style='Header.TLabel')
        settings_label.pack(anchor=tk.W, pady=(15, 10))
        
        # Save location
        save_label = ttk.Label(panel, text="Save Location:")
        save_label.pack(anchor=tk.W, pady=(0, 3))
        
        save_frame = ttk.Frame(panel)
        save_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.save_var = tk.StringVar(value=self.download_dir)
        save_entry = ttk.Entry(save_frame, textvariable=self.save_var, width=25)
        save_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        browse_btn = ttk.Button(save_frame, text="...", width=3, command=self.browse_folder)
        browse_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # Sci-Hub mirror
        mirror_label = ttk.Label(panel, text="Sci-Hub Mirror:")
        mirror_label.pack(anchor=tk.W, pady=(0, 3))
        
        self.mirror_var = tk.StringVar(value="https://www.sci-hub.red/")
        mirror_combo = ttk.Combobox(panel, textvariable=self.mirror_var, width=35, state='readonly')
        mirror_combo['values'] = (
            "https://www.sci-hub.red/",
            "https://sci-hub.ru/",
            "https://sci-hub.st/",
            "https://sci-hub.ren/",
        )
        mirror_combo.pack(fill=tk.X, pady=(0, 10))
        
        # Download controls
        control_label = ttk.Label(panel, text="🎮 Controls:", style='Header.TLabel')
        control_label.pack(anchor=tk.W, pady=(15, 10))
        
        control_frame = ttk.Frame(panel)
        control_frame.pack(fill=tk.X)
        
        self.btn_start = ttk.Button(control_frame, text="▶ Start Download", command=self.start_download)
        self.btn_start.pack(fill=tk.X, pady=(0, 5))
        
        self.btn_pause = ttk.Button(control_frame, text="⏸ Pause", command=self.pause_download, state=tk.DISABLED)
        self.btn_pause.pack(fill=tk.X, pady=(0, 5))
        
        self.btn_clear = ttk.Button(control_frame, text="🗑 Clear List", command=self.clear_list)
        self.btn_clear.pack(fill=tk.X)
        
        # Statistics
        stats_label = ttk.Label(panel, text="📊 Statistics:", style='Header.TLabel')
        stats_label.pack(anchor=tk.W, pady=(15, 10))
        
        stats_frame = ttk.Frame(panel)
        stats_frame.pack(fill=tk.X)
        
        self.stats_total = ttk.Label(stats_frame, text="Total: 0", style='Header.TLabel')
        self.stats_total.pack(anchor=tk.W, pady=2)
        
        self.stats_success = ttk.Label(stats_frame, text="✓ Success: 0", style='Success.TLabel')
        self.stats_success.pack(anchor=tk.W, pady=2)
        
        self.stats_failed = ttk.Label(stats_frame, text="✗ Failed: 0", style='Error.TLabel')
        self.stats_failed.pack(anchor=tk.W, pady=2)
        
        self.stats_pending = ttk.Label(stats_frame, text="⏳ Pending: 0", style='Accent.TLabel')
        self.stats_pending.pack(anchor=tk.W, pady=2)
        
        return panel
    
    def _create_right_panel(self, parent):
        """Create right panel with papers list"""
        panel = ttk.LabelFrame(parent, text="📄 Papers Queue", padding=10)
        
        # Treeview with scrollbar
        tree_frame = ttk.Frame(panel)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        scrollbar = ttk.Scrollbar(tree_frame)
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
        btn_frame = ttk.Frame(panel)
        btn_frame.pack(fill=tk.X)
        
        remove_btn = ttk.Button(btn_frame, text="❌ Remove Selected", command=self.remove_selected)
        remove_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        export_btn = ttk.Button(btn_frame, text="💾 Export Results", command=self.export_results)
        export_btn.pack(side=tk.LEFT)
        
        return panel
    
    def _create_footer(self, parent):
        """Create footer with progress bar"""
        footer = ttk.Frame(parent)
        
        # Progress bar
        self.progress = ttk.Progressbar(footer, mode='indeterminate')
        self.progress.pack(fill=tk.X, padx=15, pady=(10, 5))
        
        # Status text
        status_frame = ttk.Frame(footer)
        status_frame.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        self.status_label = ttk.Label(status_frame, text="Ready", foreground="#10b981")
        self.status_label.pack(anchor=tk.W)
        
        return footer
    
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
    
    def paste_dois(self):
        """Open dialog to paste DOIs"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Paste DOIs")
        dialog.geometry("500x400")
        
        label = ttk.Label(dialog, text="Paste DOIs (one per line):")
        label.pack(pady=10)
        
        text = scrolledtext.ScrolledText(dialog, height=15, width=60)
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        def process():
            content = text.get("1.0", tk.END)
            papers = []
            
            for line in content.split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    doi = self.validate_doi(line)
                    if doi:
                        papers.append(Paper(doi=doi))
            
            self.papers.extend(papers)
            self.update_tree()
            messagebox.showinfo("Success", f"Added {len(papers)} DOIs")
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
        
        self.stats_total.config(text=f"Total: {total}")
        self.stats_success.config(text=f"✓ Success: {success}")
        self.stats_failed.config(text=f"✗ Failed: {failed}")
        self.stats_pending.config(text=f"⏳ Pending: {pending}")
    
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
    
    def download_papers(self):
        """Download all papers"""
        session = requests.Session()
        mirror = self.mirror_var.get()
        
        Path(self.download_dir).mkdir(parents=True, exist_ok=True)
        
        for i, paper in enumerate(self.papers):
            if not self.is_downloading:
                break
            
            try:
                paper.status = "Downloading..."
                self.queue.put(('status', paper.status))
                
                # Extract PDF URL
                search_url = urljoin(mirror, paper.doi)
                response = session.get(search_url, headers=HEADERS, timeout=15)
                
                if response.status_code != 200:
                    raise Exception("Paper not found")
                
                # Find PDF URL
                pdf_url = self.extract_pdf_url(response.text, mirror)
                
                if not pdf_url:
                    raise Exception("PDF link not found")
                
                # Download PDF
                pdf_response = session.get(pdf_url, headers=HEADERS, timeout=30, stream=True)
                
                filename = re.sub(r'[^\w\-_\.]', '_', paper.doi) + '.pdf'
                filepath = os.path.join(self.download_dir, filename)
                
                with open(filepath, 'wb') as f:
                    for chunk in pdf_response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                # Validate PDF
                with open(filepath, 'rb') as f:
                    if f.read(4) != b'%PDF':
                        raise Exception("Invalid PDF file")
                
                paper.status = "Success"
                paper.file_path = filepath
                self.queue.put(('success', f"Downloaded {paper.doi}"))
                
            except Exception as e:
                paper.status = "Failed"
                paper.error = str(e)
                self.queue.put(('error', f"Failed {paper.doi}: {str(e)}"))
            
            self.queue.put(('update', i))
    
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
        
        return None
    
    def monitor_queue(self):
        """Monitor download progress queue"""
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
        
        except queue.Empty:
            pass
        
        if self.is_downloading:
            self.root.after(100, self.monitor_queue)
        else:
            self.progress.stop()
            self.btn_start.config(state=tk.NORMAL)
            self.btn_pause.config(state=tk.DISABLED)
            self.update_status("Ready")
    
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
    root = tk.Tk()
    app = SciHubBulkDownloader(root)
    root.mainloop()


if __name__ == "__main__":
    main()
