#!/usr/bin/env python3
"""
Paper Bulk Downloader - CLI Version
Command-line tool for downloading multiple papers with advanced options
"""

import requests
import os
import re
import sys
import argparse
import csv
import json
from urllib.parse import urljoin, urlparse
from pathlib import Path
from datetime import datetime
from typing import List, Optional
import time

# Reconfigure stdout/stderr to UTF-8 on Windows to prevent Unicode charmap encode errors
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

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

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
}

SCIHUB_MIRRORS = [
    "https://www.sci-hub.red/",
    "https://sci-hub.ru/",
    "https://sci-hub.st/",
    "https://sci-hub.se/",
    "https://sci-hub.ren/",
]
SCIHUB_URL = SCIHUB_MIRRORS[0]  # Default


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
    def __init__(self, output_dir: str, mirror: str = SCIHUB_URL, delay: float = 0, max_retries: int = 3, provider: str = 'auto'):
        self.output_dir = output_dir
        self.mirror = mirror
        self.delay = delay
        self.max_retries = max_retries
        self.provider = provider
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
    
    def extract_pdf_url(self, html: str, mirror: str = None) -> Optional[str]:
        """Extract PDF URL from HTML"""
        if mirror is None:
            mirror = self.mirror
            
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
            r = self.session.get(unpaywall_url, timeout=10)
            if r.status_code == 200:
                data = r.json()
                if data.get('is_oa'):
                    best_loc = data.get('best_oa_location') or {}
                    _add(best_loc.get('url_for_pdf'), 'Unpaywall')
                    # Also collect alternate OA locations
                    for loc in data.get('oa_locations', []):
                        _add(loc.get('url_for_pdf'), 'Unpaywall')
        except Exception:
            pass

        # Source 2: OpenAlex
        try:
            openalex_url = f"https://api.openalex.org/works/doi:{clean_doi}"
            r = self.session.get(openalex_url, timeout=10)
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
            r = self.session.get(s2_url, timeout=10)
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
            r = self.session.get(epmc_url, timeout=10)
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

    def _try_download_pdf(self, pdf_url: str) -> tuple:
        """Attempt to download a PDF from a URL. Returns (content_bytes, error_str).
        Uses Referer header matching the URL domain to bypass publisher blocks."""
        try:
            parsed = urlparse(pdf_url)
            download_headers = {
                **HEADERS,
                'Referer': f"{parsed.scheme}://{parsed.netloc}/",
                'Accept': 'application/pdf,*/*',
            }
            pdf_response = self.session.get(pdf_url, headers=download_headers, timeout=30, stream=True)
            
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

    def download_paper(self, doi: str, title: str = "") -> bool:
        """Download single paper by trying all available sources sequentially."""
        is_url = doi.startswith('http://') or doi.startswith('https://')
        last_error = "No sources available"
        
        # Build a list of all candidate URLs to try
        candidate_urls = []  # List of (url, source_name)
        
        if is_url:
            candidate_urls.append((doi, 'Direct Link'))
        else:
            # Phase 1: Collect all Open Access URLs
            if self.provider in ['auto', 'oa']:
                print(f"{ColorText.CYAN}  Querying Open Access APIs...{ColorText.ENDC}")
                oa_urls = self.resolve_all_open_access_urls(doi)
                candidate_urls.extend(oa_urls)
                if oa_urls:
                    print(f"{ColorText.GREEN}  Found {len(oa_urls)} OA source(s): {', '.join(s for _, s in oa_urls)}{ColorText.ENDC}")
            
            # Phase 2: Collect Sci-Hub URLs
            if self.provider in ['auto', 'scihub']:
                for sh_mirror in SCIHUB_MIRRORS:
                    try:
                        search_url = urljoin(sh_mirror, doi)
                        print(f"{ColorText.CYAN}  Fetching: {search_url}{ColorText.ENDC}")
                        response = self.session.get(search_url, headers=HEADERS, timeout=15)
                        if response.status_code == 200:
                            pdf_url = self.extract_pdf_url(response.text, sh_mirror)
                            if pdf_url:
                                candidate_urls.append((pdf_url, f'Sci-Hub ({sh_mirror.split("//")[1].rstrip("/")})'))
                                break  # One working Sci-Hub mirror is enough
                    except Exception:
                        continue
        
        if not candidate_urls:
            print(f"{ColorText.RED}✗ Failed{ColorText.ENDC} - PDF link not found from any source")
            self.results['failed'] += 1
            self.results['papers'].append({'doi': doi, 'title': title, 'status': 'Failed', 'error': 'PDF link not found'})
            return False
        
        # Phase 3: Try each candidate URL
        for pdf_url, source in candidate_urls:
            print(f"{ColorText.CYAN}  Trying {source}: {pdf_url[:80]}...{ColorText.ENDC}")
            content, error = self._try_download_pdf(pdf_url)
            
            if content is not None:
                # Save the valid PDF
                if is_url:
                    base_name = urlparse(pdf_url).path.split('/')[-1]
                    if not base_name.endswith('.pdf'):
                        base_name = re.sub(r'[^\w\-_\.]', '_', base_name) + '.pdf'
                    filename = base_name
                else:
                    filename = re.sub(r'[^\w\-_\.]', '_', doi) + '.pdf'
                
                filepath = os.path.join(self.output_dir, filename)
                with open(filepath, 'wb') as f:
                    f.write(content)
                
                file_size = len(content)
                print(f"{ColorText.GREEN}✓ Success via {source}{ColorText.ENDC} - {file_size / 1024:.2f} KB")
                
                self.results['success'] += 1
                self.results['papers'].append({
                    'doi': doi, 'title': title, 'status': 'Success',
                    'file_path': filepath, 'size': file_size
                })
                
                if self.delay > 0:
                    time.sleep(self.delay)
                return True
            else:
                print(f"{ColorText.YELLOW}  ✗ {source} failed: {error}{ColorText.ENDC}")
                last_error = error
        
        # All candidates exhausted
        print(f"{ColorText.RED}✗ Failed{ColorText.ENDC} - {last_error}")
        self.results['failed'] += 1
        self.results['papers'].append({'doi': doi, 'title': title, 'status': 'Failed', 'error': last_error})
        return False
    
    def download_batch(self, dois: List[str], titles: List[str] = None) -> dict:
        """Download multiple papers"""
        if titles is None:
            titles = [""] * len(dois)
        
        self.results['total'] = len(dois)
        
        print(f"\n{ColorText.BOLD}{ColorText.BLUE}{'='*70}")
        print(f"Paper Bulk Downloader")
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
        description='Paper Bulk Downloader',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download from CSV file
  python paper_bulk_cli.py -f dois.csv -o ./papers
  
  # Download from text file with delay
  python paper_bulk_cli.py -f dois.txt -o ./papers --delay 2
  
  # Use different mirror
  python paper_bulk_cli.py -f dois.csv -o ./papers -m https://sci-hub.ru/
  
  # Interactive mode
  python paper_bulk_cli.py -i -o ./papers
  
  # Filter mode: extract DOIs and links from any document
  python paper_bulk_cli.py -f document.txt --filter -o ./papers
        """
    )
    
    parser.add_argument('-f', '--file', help='Input file (CSV, TXT, DOCX or PDF with DOIs)')
    parser.add_argument('-i', '--interactive', action='store_true', help='Interactive mode (paste DOIs)')
    parser.add_argument('-o', '--output', default='./downloads', help='Output directory')
    parser.add_argument('-m', '--mirror', default=SCIHUB_URL, help='Primary Sci-Hub mirror URL (all mirrors are tried automatically as fallback)')
    parser.add_argument('-d', '--delay', type=float, default=0, help='Delay between downloads (seconds)')
    parser.add_argument('-r', '--retries', type=int, default=3, help='Max retries per paper')
    parser.add_argument('-e', '--export', help='Export results to CSV/JSON')
    parser.add_argument('-p', '--provider', default='auto', choices=['auto', 'oa', 'scihub'],
                        help="Download provider: 'auto' (tries OA APIs first, falls back to Sci-Hub), 'oa' (Open Access APIs only), 'scihub' (Sci-Hub only)")
    parser.add_argument('--filter', action='store_true', help="Filter and extract DOIs and links from the input file instead of treating it as direct list of DOIs")
    
    args = parser.parse_args()
    
    downloader = BulkDownloader(
        output_dir=args.output,
        mirror=args.mirror,
        delay=args.delay,
        max_retries=args.retries,
        provider=args.provider
    )
    
    dois = []
    titles = []
    
    if args.file:
        if not os.path.exists(args.file):
            print(f"{ColorText.RED}Error: File not found: {args.file}{ColorText.ENDC}")
            sys.exit(1)
        
        if args.filter:
            print(f"Filtering DOIs and links from {args.file}...")
            dois, urls = filter_dois_and_links_from_file(args.file)
            all_targets = dois + urls
            dois = all_targets
            titles = [""] * len(dois)
        else:
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
            else:
                titles = [""] * len(dois)
    
    elif args.interactive:
        print("Enter DOIs or direct URLs (one per line, press Ctrl+D to finish):")
        print()
        
        try:
            while True:
                line = input().strip()
                if line and not line.startswith('#'):
                    if line.startswith('http://') or line.startswith('https://'):
                        dois.append(line)
                        titles.append("")
                    else:
                        doi = downloader.validate_doi(line)
                        if doi:
                            dois.append(doi)
                            titles.append("")
        except EOFError:
            pass
    
    else:
        parser.print_help()
        sys.exit(1)
    
    # Enforce limit of 50 papers
    if len(dois) > 50:
        print(f"{ColorText.YELLOW}⚠️  Warning: Download limit is 50 papers at a time. Truncating list to the first 50 papers.{ColorText.ENDC}")
        dois = dois[:50]
        titles = titles[:50]
        
    if not dois:
        print(f"{ColorText.RED}Error: No valid DOIs or links found{ColorText.ENDC}")
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
