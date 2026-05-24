# 📚 Sci-Hub Bulk Downloader - Complete Guide

## 🎯 Overview

Two powerful tools for downloading multiple papers at once:

1. **GUI Version** (`paper_bulk_downloader.py`) - Visual interface with progress tracking
2. **CLI Version** (`paper_bulk_cli.py`) - Command-line for automation and scripting

Choose based on your preference:
- **GUI**: User-friendly, visual feedback, point-and-click
- **CLI**: Powerful, scriptable, batch automation, perfect for servers

---

## 🚀 Getting Started

### Installation

First, install required packages:

```bash
pip install requests
```

Optional (for Excel support):

```bash
pip install openpyxl
```

---

## 📊 GUI Version

### Running the Application

```bash
python paper_bulk_downloader.py
```

### Features

✅ **Multiple Input Methods:**
- Load from CSV file
- Load from Excel file (.xlsx)
- Load from Text file (.txt)
- Paste DOIs directly
- Load example papers

✅ **Real-Time Progress:**
- Live paper queue display
- Status updates per paper
- Overall statistics (Total, Success, Failed, Pending)
- Progress bar animation

✅ **Flexible Settings:**
- Custom save location
- Multiple Sci-Hub mirrors
- Resume/pause downloads
- Remove individual papers

✅ **Export Results:**
- Save as CSV
- Save as JSON
- Includes file paths and error messages

### Step-by-Step Usage

#### Step 1: Load Papers

**Option A - Load from File:**
1. Click "📁 Load File"
2. Select CSV, Excel, or TXT file
3. Papers appear in the list

**Option B - Paste DOIs:**
1. Click "📝 Paste DOIs"
2. Paste one DOI per line
3. Click "Add"

**Option C - Load Example:**
1. Click "📌 Load Example"
2. 3 example papers are added

#### Step 2: Configure Settings

- **Save Location**: Click "..." to choose folder
- **Sci-Hub Mirror**: Select from dropdown (or use default)

#### Step 3: Download

1. Click "▶ Start Download"
2. Watch progress in real-time
3. View status updates

#### Step 4: Review & Export

- Papers show green (Success) or red (Failed)
- Click "💾 Export Results" to save summary

### Input File Formats

#### CSV Format

```csv
DOI,Title,Category
10.1029/2010RS004406,Earth impedance model,Geophysics
10.1038/nature12373,A giant impact,Astronomy
```

First row is header (skipped). Columns:
- **Column 1** (required): DOI
- **Column 2** (optional): Paper title
- **Column 3+** (optional): Any metadata

#### Excel Format (.xlsx)

Same structure as CSV:
- Row 1: Headers
- Column A: DOI
- Column B: Title (optional)

#### Text Format (.txt)

One DOI per line, comments start with `#`:

```
# My papers to download
10.1029/2010RS004406
10.1038/nature12373

# Skip blank lines and comments
10.1109/5.771073
```

### GUI Statistics

Real-time updates showing:
- **Total**: Papers in queue
- **✓ Success**: Papers downloaded successfully
- **✗ Failed**: Papers that couldn't be found
- **⏳ Pending**: Papers waiting to be downloaded

### Keyboard Shortcuts

- **Ctrl+V** in DOI field: Paste from clipboard
- **Right-click** on paper: Show context menu
- **Delete**: Remove selected paper (in context menu)

---

## 💻 CLI Version

### Running the CLI

#### Basic Usage

```bash
# Download from CSV file
python paper_bulk_cli.py -f dois.csv -o ./papers

# Download from text file
python paper_bulk_cli.py -f dois.txt -o ./papers

# Interactive mode (paste DOIs)
python paper_bulk_cli.py -i -o ./papers
```

#### Advanced Options

```bash
# With delay between downloads (avoid being blocked)
python paper_bulk_cli.py -f dois.csv -o ./papers --delay 2

# Use different Sci-Hub mirror
python paper_bulk_cli.py -f dois.csv -o ./papers -m https://sci-hub.ru/

# Custom retries per paper
python paper_bulk_cli.py -f dois.csv -o ./papers --retries 5

# Export results
python paper_bulk_cli.py -f dois.csv -o ./papers -e results.csv

# Combine options
python paper_bulk_cli.py -f dois.csv -o ./papers -m https://sci-hub.st/ -d 1 -r 3 -e results.json
```

### CLI Arguments

```
-f, --file FILE           Input file (CSV or TXT with DOIs)
-i, --interactive         Interactive mode (paste DOIs)
-o, --output DIR          Output directory (default: ./downloads)
-m, --mirror URL          Sci-Hub mirror URL
-d, --delay SECONDS       Delay between downloads (default: 0)
-r, --retries NUMBER      Max retries per paper (default: 3)
-e, --export FILE         Export results to CSV or JSON
-h, --help                Show help message
```

### Interactive Mode

```bash
$ python paper_bulk_cli.py -i -o ./papers

Enter DOIs (one per line, press Ctrl+D to finish):

10.1029/2010RS004406
10.1038/nature12373
10.1109/5.771073
^D

[1/3] 10.1029/2010RS004406
✓ Success - 2291.09 KB
[2/3] 10.1038/nature12373
✓ Success - 3456.78 KB
[3/3] 10.1109/5.771073
✗ Failed - PDF link not found
```

### Output & Results

#### Console Output

```
======================================================================
Sci-Hub Bulk Downloader
======================================================================

📊 Papers to download: 5
💾 Save location: ./papers
🌐 Mirror: https://www.sci-hub.red/

[1/5] 10.1029/2010RS004406
✓ Success - 2291.09 KB
[2/5] 10.1038/nature12373
✓ Success - 3456.78 KB
[3/5] 10.1109/5.771073
✓ Success - 1234.56 KB
[4/5] 10.1145/3025453.3025815
✗ Failed - HTTP 404
[5/5] 10.1016/j.cageo.2015.09.007
✓ Success - 4567.89 KB

======================================================================
Download Summary
======================================================================

Total:        5
Success:      4
Failed:       1
Success Rate: 80.0%
Time Elapsed: 45.3 seconds
```

#### Export Formats

**CSV Export** (`-e results.csv`):
```csv
DOI,Title,Status,File Path / Error
10.1029/2010RS004406,Earth impedance model,Success,./papers/10_1029_2010RS004406.pdf
10.1038/nature12373,A giant impact,Success,./papers/10_1038_nature12373.pdf
10.1109/5.771073,The Internet's coming of age,Failed,HTTP 404
```

**JSON Export** (`-e results.json`):
```json
{
  "total": 3,
  "success": 2,
  "failed": 1,
  "papers": [
    {
      "doi": "10.1029/2010RS004406",
      "title": "Earth impedance model",
      "status": "Success",
      "file_path": "./papers/10_1029_2010RS004406.pdf",
      "size": 2347643
    },
    {
      "doi": "10.1038/nature12373",
      "status": "Failed",
      "error": "PDF link not found"
    }
  ]
}
```

---

## 📁 Input File Examples

### CSV Example

```csv
DOI,Title,Category
10.1029/2010RS004406,Earth impedance model,Geophysics
10.1038/nature12373,A giant impact,Astronomy
10.1109/5.771073,The Internet's coming of age,Technology
```

See `example_dois.csv` included in the package.

### Text Example

```
# Geophysics Papers
10.1029/2010RS004406
10.1016/j.cageo.2015.09.007

# Astronomy Papers
10.1038/nature12373
10.1051/0004-6361/201833051
```

See `example_dois.txt` included in the package.

---

## ⚙️ Advanced Features

### Retry Logic

Papers that fail to download are retried automatically:

```bash
# Use 5 retries per paper (default is 3)
python paper_bulk_cli.py -f dois.csv -r 5
```

Each retry waits 2 seconds before attempting again.

### Rate Limiting

Add delay between downloads to avoid being rate-limited:

```bash
# Wait 2 seconds between each download
python paper_bulk_cli.py -f dois.csv -d 2

# Wait 5 seconds
python paper_bulk_cli.py -f dois.csv -d 5
```

### Multiple Mirrors

If the default mirror is slow or blocked:

```bash
# Try different mirror
python paper_bulk_cli.py -f dois.csv -m https://sci-hub.ru/

# Test which mirror is faster
for mirror in "https://sci-hub.red/" "https://sci-hub.ru/" "https://sci-hub.st/"; do
  echo "Testing $mirror"
  python paper_bulk_cli.py -f dois.csv -m $mirror -e "results_${mirror##*/}.json"
done
```

---

## 🐛 Troubleshooting

### Papers Still Failing?

1. **Check DOI Format**
   - Valid: `10.1029/2010RS004406`
   - Invalid: `doi: 10.1029/2010RS004406` or `DOI10.1029/...`

2. **Try Different Mirror**
   ```bash
   python paper_bulk_cli.py -f dois.csv -m https://sci-hub.st/
   ```

3. **Increase Retries**
   ```bash
   python paper_bulk_cli.py -f dois.csv -r 5
   ```

4. **Add Delay**
   ```bash
   python paper_bulk_cli.py -f dois.csv -d 3
   ```

### Connection Issues?

- Use VPN if Sci-Hub is blocked in your region
- Check internet connection: `ping google.com`
- Try later if mirrors are overloaded

### File Validation

The script checks:
1. ✓ File size > 1KB (not an error page)
2. ✓ PDF header `%PDF` (valid PDF file)
3. ✓ HTTP status 200 (successful download)

### No Papers Downloaded?

Check that:
1. DOI format is valid
2. DOI exists on Sci-Hub
3. Save location is writable
4. Internet connection is working

---

## 📊 Batch Processing

### Process Multiple Batches

```bash
# Download from different sources
for file in papers_*.csv; do
  python paper_bulk_cli.py -f $file -o "./results/$file" -e "results/$file.json"
done
```

### Create Custom Input Files

```bash
# Generate DOI list from database/API
# Then feed to downloader

python paper_bulk_cli.py -i -o ./papers << EOF
10.1029/2010RS004406
10.1038/nature12373
EOF
```

### Combine Results

```bash
# Merge multiple result files
python -c "
import json
results = []
for f in glob.glob('results_*.json'):
    with open(f) as file:
        results.extend(json.load(file)['papers'])
with open('combined.json', 'w') as f:
    json.dump({'papers': results}, f)
"
```

---

## 🎓 Use Cases

### Case 1: Researcher Downloading Literature Review

```bash
# Create CSV with papers found on Google Scholar
# Run bulk downloader
python paper_bulk_downloader.py
# Load CSV → Download → Export results
```

### Case 2: Batch Process from API

```python
# Python script to get DOIs from an API, then download

import subprocess
import json

# Get DOIs from your source
dois = ["10.1029/2010RS004406", "10.1038/nature12373"]

# Create temp file
with open('temp_dois.txt', 'w') as f:
    f.write('\n'.join(dois))

# Run downloader
result = subprocess.run([
    'python', 'paper_bulk_cli.py',
    '-f', 'temp_dois.txt',
    '-o', './papers',
    '-e', 'results.json'
])

# Parse results
with open('results.json') as f:
    results = json.load(f)
    print(f"Downloaded {results['success']} papers")
```

### Case 3: Monitor Large Download

```bash
# Download many papers with progress tracking
python paper_bulk_cli.py -f all_dois.csv -o ./papers -d 2 -e results.csv

# Monitor in real-time
watch -n 1 'tail -20 results.csv'
```

---

## 📈 Performance Tips

1. **Use CLI for large batches** (1000+ papers)
   - Faster than GUI
   - Can run in background
   - Scriptable

2. **Add appropriate delay**
   - 0-1 seconds: Fast (risk of rate limiting)
   - 1-3 seconds: Balanced
   - 3+ seconds: Very safe (slower)

3. **Increase retries for unstable connection**
   - Default 3 is usually fine
   - Use 5+ for poor connections

4. **Choose mirror wisely**
   - Test with small batch first
   - Different mirrors have different speeds

5. **Run during off-peak hours**
   - Sci-Hub is faster at night
   - Lower chance of rate limiting

---

## 📋 FAQ

**Q: How many papers can I download?**
A: No hard limit, but be respectful. Large batches (1000+) should use delays.

**Q: Will I get blocked?**
A: Unlikely if you use reasonable delays (1-2 seconds). VPN helps if you're blocked.

**Q: Can I pause and resume?**
A: GUI: Yes (pause button). CLI: Use Ctrl+C and rerun with same file.

**Q: What if a paper fails?**
A: Script shows error and continues. Check results file for details.

**Q: Can I automate this?**
A: Yes! Use CLI version in cron jobs or scripts.

**Q: Which version is faster?**
A: CLI is slightly faster. GUI is easier to use.

---

## 🔧 Configuration

### Custom Download Script

```python
from paper_bulk_cli import BulkDownloader

downloader = BulkDownloader(
    output_dir='./papers',
    mirror='https://sci-hub.red/',
    delay=1,
    max_retries=3
)

dois = ['10.1029/2010RS004406', '10.1038/nature12373']
results = downloader.download_batch(dois)

print(f"Downloaded: {results['success']}/{results['total']}")
```

---

## 📚 Resources

- **Sci-Hub Mirrors**: Check working mirrors at sci-hub mirrors list
- **DOI Lookup**: Find DOIs at CrossRef, Google Scholar, ResearchGate
- **Python**: https://python.org
- **Requests Library**: https://requests.readthedocs.io

---

## 📝 Version Info

- **Version**: 2.0
- **Date**: 2026
- **Python**: 3.6+
- **Status**: Production Ready

---

## 🎉 Success Examples

### Example 1: Geophysics Research

```
Downloaded 47 papers
Success Rate: 93.6% (44/47)
Total Size: 1.2 GB
Time: 3 minutes 45 seconds
Failed: 3 papers not found
```

### Example 2: Literature Review

```
Downloaded 125 papers
Success Rate: 97.6% (122/125)
Total Size: 2.8 GB
Time: 8 minutes 20 seconds
Failed: 3 papers (try different mirror)
```

---

## 📞 Support

If you encounter issues:

1. Check DOI format is valid
2. Try different Sci-Hub mirror
3. Use debug mode (--verbose flag if available)
4. Check internet connection
5. Try with smaller batch first

---

**Happy researching!** 🎓📚
