#!/usr/bin/env python3
"""
Sci-Hub Bulk Downloader - CLI Version
Command-line tool for downloading multiple papers with advanced options
"""

import requests
import os
import re
import sys
import argparse
import csv
import json
from urllib.parse import urljoin
from pathlib import Path
from datetime import datetime
from typing import List, Optional
import time

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
}

SCIHUB_URL = "https://www.sci-hub.red/"


class ColorText:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class BulkDownloader:
    def __init__(self, output_dir: str, mirror: str = SCIHUB_URL, delay: float = 0, max_retries: int = 3):
        self.output_dir = output_dir
        self.mirror = mirror
        self.delay = delay
        self.max_retries = max_retries
        self.session = requests.Session()
        
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        
        self.results = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'papers': []
        }
    
    def validate_doi(self, doi: str) -> Optional[str]:
        """Validate and extract DOI"""
        doi_pattern = r'(10\.\S+/\S+)'
        match = re.search(doi_pattern, doi)
        return match.group(1) if match else None
    
    def load_dois(self, file_path: str) -> List[str]:
        """Load DOIs from file"""
        dois = []
        
        if file_path.endswith('.csv'):
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader, None)  # Skip header
                
                for row in reader:
                    if row:
                        doi = self.validate_doi(row[0])
                        if doi:
                            dois.append(doi)
        
        else:  # .txt
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        doi = self.validate_doi(line)
                        if doi:
                            dois.append(doi)
        
        return dois
    
    def extract_pdf_url(self, html: str) -> Optional[str]:
        """Extract PDF URL from HTML"""
        # Method 1: url variable
        match = re.search(r'url:\s*["\']([^"\']+\.pdf)["\']', html)
        if match:
            url = match.group(1)
            return urljoin(self.mirror, url) if url.startswith('/') else url
        
        # Method 2: meta tag
        match = re.search(r'content=["\']([^"\']*\.pdf[^"\']*)["\']', html)
        if match:
            url = match.group(1)
            return urljoin(self.mirror, url) if url.startswith('/') else url
        
        # Method 3: iframe
        match = re.search(r'<iframe[^>]*src=["\']([^"\']+)["\']', html)
        if match:
            url = match.group(1)
            return urljoin(self.mirror, url) if url.startswith('/') else url
        
        # Method 4: fetch call
        match = re.search(r'fetch\(["\']([^"\']*\.pdf[^"\']*)["\']', html)
        if match:
            url = match.group(1)
            return urljoin(self.mirror, url) if url.startswith('/') else url
        
        return None
    
    def download_paper(self, doi: str, title: str = "") -> bool:
        """Download single paper with retries"""
        for attempt in range(self.max_retries):
            try:
                if attempt > 0:
                    print(f"{ColorText.YELLOW}  Retry {attempt}/{self.max_retries}...{ColorText.ENDC}")
                    time.sleep(2)
                
                # Fetch paper page
                search_url = urljoin(self.mirror, doi)
                print(f"{ColorText.CYAN}  Fetching: {search_url}{ColorText.ENDC}")
                
                response = self.session.get(search_url, headers=HEADERS, timeout=15)
                
                if response.status_code != 200:
                    if attempt == self.max_retries - 1:
                        raise Exception(f"HTTP {response.status_code}")
                    continue
                
                # Extract PDF URL
                pdf_url = self.extract_pdf_url(response.text)
                
                if not pdf_url:
                    if attempt == self.max_retries - 1:
                        raise Exception("PDF link not found")
                    continue
                
                print(f"{ColorText.CYAN}  PDF URL: {pdf_url[:80]}...{ColorText.ENDC}")
                
                # Download PDF
                pdf_response = self.session.get(pdf_url, headers=HEADERS, timeout=30, stream=True)
                
                if pdf_response.status_code != 200:
                    if attempt == self.max_retries - 1:
                        raise Exception(f"Download HTTP {pdf_response.status_code}")
                    continue
                
                # Save file
                filename = re.sub(r'[^\w\-_\.]', '_', doi) + '.pdf'
                filepath = os.path.join(self.output_dir, filename)
                
                bytes_downloaded = 0
                with open(filepath, 'wb') as f:
                    for chunk in pdf_response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            bytes_downloaded += len(chunk)
                
                # Validate PDF
                file_size = os.path.getsize(filepath)
                
                if file_size < 1000:
                    os.remove(filepath)
                    if attempt == self.max_retries - 1:
                        raise Exception("File too small (< 1KB)")
                    continue
                
                with open(filepath, 'rb') as f:
                    if f.read(4) != b'%PDF':
                        os.remove(filepath)
                        if attempt == self.max_retries - 1:
                            raise Exception("Invalid PDF file")
                        continue
                
                print(f"{ColorText.GREEN}✓ Success{ColorText.ENDC} - {file_size / 1024:.2f} KB")
                
                self.results['success'] += 1
                self.results['papers'].append({
                    'doi': doi,
                    'title': title,
                    'status': 'Success',
                    'file_path': filepath,
                    'size': file_size
                })
                
                if self.delay > 0:
                    time.sleep(self.delay)
                
                return True
                
            except Exception as e:
                if attempt == self.max_retries - 1:
                    print(f"{ColorText.RED}✗ Failed{ColorText.ENDC} - {str(e)}")
                    
                    self.results['failed'] += 1
                    self.results['papers'].append({
                        'doi': doi,
                        'title': title,
                        'status': 'Failed',
                        'error': str(e)
                    })
                    
                    return False
        
        return False
    
    def download_batch(self, dois: List[str], titles: List[str] = None) -> dict:
        """Download multiple papers"""
        if titles is None:
            titles = [""] * len(dois)
        
        self.results['total'] = len(dois)
        
        print(f"\n{ColorText.BOLD}{ColorText.BLUE}{'='*70}")
        print(f"Sci-Hub Bulk Downloader")
        print(f"{'='*70}{ColorText.ENDC}\n")
        
        print(f"📊 Papers to download: {ColorText.BOLD}{len(dois)}{ColorText.ENDC}")
        print(f"💾 Save location: {ColorText.BOLD}{self.output_dir}{ColorText.ENDC}")
        print(f"🌐 Mirror: {ColorText.BOLD}{self.mirror}{ColorText.ENDC}\n")
        
        start_time = time.time()
        
        for i, (doi, title) in enumerate(zip(dois, titles), 1):
            print(f"{ColorText.BOLD}[{i}/{len(dois)}]{ColorText.ENDC} {doi}")
            if title:
                print(f"        {title}")
            
            self.download_paper(doi, title)
        
        elapsed = time.time() - start_time
        
        # Print summary
        self._print_summary(elapsed)
        
        return self.results
    
    def _print_summary(self, elapsed: float):
        """Print download summary"""
        print(f"\n{ColorText.BOLD}{ColorText.BLUE}{'='*70}")
        print(f"Download Summary")
        print(f"{'='*70}{ColorText.ENDC}\n")
        
        print(f"Total:    {self.results['total']}")
        print(f"{ColorText.GREEN}Success:  {self.results['success']}{ColorText.ENDC}")
        print(f"{ColorText.RED}Failed:   {self.results['failed']}{ColorText.ENDC}")
        print(f"Success Rate: {(self.results['success'] / max(self.results['total'], 1) * 100):.1f}%")
        print(f"Time Elapsed: {elapsed:.1f} seconds")
        print()


def main():
    parser = argparse.ArgumentParser(
        description='Sci-Hub Bulk Paper Downloader',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download from CSV file
  python scihub_bulk_cli.py -f dois.csv -o ./papers
  
  # Download from text file with delay
  python scihub_bulk_cli.py -f dois.txt -o ./papers --delay 2
  
  # Use different mirror
  python scihub_bulk_cli.py -f dois.csv -o ./papers -m https://sci-hub.ru/
  
  # Interactive mode
  python scihub_bulk_cli.py -i -o ./papers
        """
    )
    
    parser.add_argument('-f', '--file', help='Input file (CSV or TXT with DOIs)')
    parser.add_argument('-i', '--interactive', action='store_true', help='Interactive mode (paste DOIs)')
    parser.add_argument('-o', '--output', default='./downloads', help='Output directory')
    parser.add_argument('-m', '--mirror', default=SCIHUB_URL, help='Sci-Hub mirror URL')
    parser.add_argument('-d', '--delay', type=float, default=0, help='Delay between downloads (seconds)')
    parser.add_argument('-r', '--retries', type=int, default=3, help='Max retries per paper')
    parser.add_argument('-e', '--export', help='Export results to CSV/JSON')
    
    args = parser.parse_args()
    
    downloader = BulkDownloader(
        output_dir=args.output,
        mirror=args.mirror,
        delay=args.delay,
        max_retries=args.retries
    )
    
    dois = []
    titles = []
    
    if args.file:
        if not os.path.exists(args.file):
            print(f"{ColorText.RED}Error: File not found: {args.file}{ColorText.ENDC}")
            sys.exit(1)
        
        print(f"Loading DOIs from {args.file}...")
        dois = downloader.load_dois(args.file)
        
        # Try to load titles from CSV
        if args.file.endswith('.csv'):
            with open(args.file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader, None)  # Skip header
                
                for row in reader:
                    if len(row) > 1:
                        titles.append(row[1])
                    else:
                        titles.append("")
    
    elif args.interactive:
        print("Enter DOIs (one per line, press Ctrl+D to finish):")
        print()
        
        try:
            while True:
                line = input().strip()
                if line and not line.startswith('#'):
                    doi = downloader.validate_doi(line)
                    if doi:
                        dois.append(doi)
                        titles.append("")
        except EOFError:
            pass
    
    else:
        parser.print_help()
        sys.exit(1)
    
    if not dois:
        print(f"{ColorText.RED}Error: No valid DOIs found{ColorText.ENDC}")
        sys.exit(1)
    
    results = downloader.download_batch(dois, titles)
    
    # Export results if requested
    if args.export:
        print(f"Exporting results to {args.export}...")
        
        try:
            if args.export.endswith('.json'):
                with open(args.export, 'w') as f:
                    json.dump(results, f, indent=2)
            else:  # CSV
                with open(args.export, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['DOI', 'Title', 'Status', 'File Path / Error'])
                    
                    for paper in results['papers']:
                        writer.writerow([
                            paper['doi'],
                            paper.get('title', ''),
                            paper['status'],
                            paper.get('file_path', '') or paper.get('error', '')
                        ])
            
            print(f"{ColorText.GREEN}Results exported successfully{ColorText.ENDC}")
        
        except Exception as e:
            print(f"{ColorText.RED}Export failed: {str(e)}{ColorText.ENDC}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{ColorText.YELLOW}Cancelled by user{ColorText.ENDC}")
        sys.exit(0)
    except Exception as e:
        print(f"{ColorText.RED}Error: {str(e)}{ColorText.ENDC}")
        sys.exit(1)
