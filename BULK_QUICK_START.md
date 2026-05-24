# 🚀 Bulk Mode - Quick Start

## 📦 What You Got

```
paper_bulk_downloader.py     ← GUI Version (easiest)
paper_bulk_cli.py             ← CLI Version (most powerful)
BULK_MODE_GUIDE.md             ← Full documentation
example_dois.csv               ← Example CSV file
example_dois.txt               ← Example text file
```

---

## ⚡ 30-Second Start

### GUI Version (Recommended for Beginners)

```bash
python paper_bulk_downloader.py
```

Then:
1. Click "📌 Load Example" (to test)
2. Click "▶ Start Download"
3. Watch papers download
4. Click "💾 Export Results"

Done! ✓

### CLI Version (Recommended for Power Users)

```bash
# Download from example file
python paper_bulk_cli.py -f example_dois.csv -o ./my_papers

# That's it!
```

---

## 📊 Input Formats

### Option 1: CSV File

```csv
DOI,Title
10.1029/2010RS004406,Earth impedance model
10.1038/nature12373,A giant impact
```

### Option 2: Text File

```
10.1029/2010RS004406
10.1038/nature12373
10.1109/5.771073
```

### Option 3: Paste DOIs

In GUI: Click "📝 Paste DOIs" and paste your list

---

## 🎮 Common Commands

```bash
# GUI - visual, interactive
python paper_bulk_downloader.py

# CLI - from CSV file
python paper_bulk_cli.py -f papers.csv -o ./downloads

# CLI - from text file
python paper_bulk_cli.py -f papers.txt -o ./downloads

# CLI - interactive (paste DOIs)
python paper_bulk_cli.py -i -o ./downloads

# CLI - with slow download (safer)
python paper_bulk_cli.py -f papers.csv -o ./downloads -d 2

# CLI - export results
python paper_bulk_cli.py -f papers.csv -o ./downloads -e results.csv

# CLI - use different mirror
python paper_bulk_cli.py -f papers.csv -o ./downloads -m https://sci-hub.ru/
```

---

## 📋 Features

### GUI Highlights

✓ Load from CSV, Excel, or Text  
✓ Paste DOIs directly  
✓ Real-time progress  
✓ Statistics (Success/Failed/Pending)  
✓ Pause/Resume  
✓ Remove individual papers  
✓ Export results as CSV or JSON  

### CLI Highlights

✓ Command-line automation  
✓ Batch processing  
✓ Multiple input formats  
✓ Rate limiting (--delay)  
✓ Retry logic (--retries)  
✓ Multiple mirrors  
✓ Export results  
✓ Perfect for scripting  

---

## 📁 File Formats

### CSV Example

```csv
DOI,Title,Category
10.1029/2010RS004406,Earth impedance model,Geophysics
10.1038/nature12373,A giant impact,Astronomy
```

First row = headers. Columns 2+ optional.

### Text Example

```
# Comments start with #
10.1029/2010RS004406
10.1038/nature12373

# Blank lines ignored
10.1109/5.771073
```

---

## ✅ Quick Checklist

- [ ] Python 3.6+ installed
- [ ] Run: `pip install requests`
- [ ] Create CSV or TXT file with DOIs
- [ ] Run GUI or CLI version
- [ ] Download completes
- [ ] Export results (optional)

---

## 🎯 Example Workflow

### Using GUI

```
1. python paper_bulk_downloader.py
2. Click "📁 Load File"
3. Select papers.csv
4. Verify papers in list
5. Click "▶ Start Download"
6. Wait for completion
7. Click "💾 Export Results"
8. Open results_*.csv to see summary
```

### Using CLI

```bash
# Create paper list
cat > papers.txt << EOF
10.1029/2010RS004406
10.1038/nature12373
10.1109/5.771073
EOF

# Download all
python paper_bulk_cli.py -f papers.txt -o ./papers -e results.csv

# View results
cat results.csv
```

---

## 🔧 Configuration

### Change Save Location

**GUI**: Click "..." button next to "Save to:"

**CLI**: Use `-o` flag
```bash
python paper_bulk_cli.py -f papers.csv -o /path/to/save
```

### Use Different Mirror

**GUI**: Select from "Sci-Hub Mirror:" dropdown

**CLI**: Use `-m` flag
```bash
python paper_bulk_cli.py -f papers.csv -m https://sci-hub.ru/
```

Available mirrors:
- `https://www.sci-hub.red/` (default)
- `https://sci-hub.ru/`
- `https://sci-hub.st/`
- `https://sci-hub.ren/`

### Add Delay Between Downloads

**GUI**: Not directly available (downloads fast)

**CLI**: Use `-d` flag
```bash
python paper_bulk_cli.py -f papers.csv -d 2
# Wait 2 seconds between downloads
```

---

## 📊 Output Examples

### CLI Output

```
======================================================================
Sci-Hub Bulk Downloader
======================================================================

📊 Papers to download: 3
💾 Save location: ./papers
🌐 Mirror: https://www.sci-hub.red/

[1/3] 10.1029/2010RS004406
  Fetching: https://www.sci-hub.red/10.1029/2010RS004406
  PDF URL: /storage/moscow/2035/...
✓ Success - 2291.09 KB

[2/3] 10.1038/nature12373
✓ Success - 3456.78 KB

[3/3] 10.1109/5.771073
✗ Failed - PDF link not found

======================================================================
Download Summary
======================================================================

Total:        3
Success:      2
Failed:       1
Success Rate: 66.7%
Time Elapsed: 15.3 seconds
```

### GUI Statistics

```
Total: 3
✓ Success: 2
✗ Failed: 1
⏳ Pending: 0
```

---

## 🐛 Troubleshooting

### Papers not downloading?

1. **Check DOI format** - Should be like: `10.1029/2010RS004406`
2. **Try different mirror** - Some papers on different mirrors
3. **Add delay** - `python paper_bulk_cli.py -f papers.csv -d 2`
4. **Check internet** - Make sure you're online

### File not found?

Make sure file exists in current directory:
```bash
ls papers.csv    # Check if file exists
```

### Need Excel support?

```bash
pip install openpyxl
```

Then you can use `.xlsx` files.

---

## 📞 Common Questions

**Q: How many papers can I download?**  
A: Unlimited! Test with 10-20 first.

**Q: Will I get blocked?**  
A: No if you use delay (--delay 2). Very safe.

**Q: Which is faster - GUI or CLI?**  
A: Both similar speed. CLI slightly faster.

**Q: Can I stop and resume?**  
A: GUI has pause button. CLI: Ctrl+C stops, rerun to continue.

**Q: How do I know which papers failed?**  
A: Check the exported results.csv or results.json

---

## 🎁 Included Files

### Scripts

- **paper_bulk_downloader.py** - Full GUI application
- **paper_bulk_cli.py** - Command-line tool

### Examples

- **example_dois.csv** - Sample CSV format
- **example_dois.txt** - Sample text format

### Documentation

- **BULK_MODE_GUIDE.md** - Complete reference
- **This file** - Quick start guide

---

## 🚀 Ready to Go!

### For Beginners:
```bash
python paper_bulk_downloader.py
```

### For Power Users:
```bash
python paper_bulk_cli.py -f papers.csv -o ./downloads
```

---

## 📚 Next Steps

1. **Read BULK_MODE_GUIDE.md** for full documentation
2. **Try with example files** first
3. **Create your own CSV/TXT** with your DOIs
4. **Download and enjoy!**

---

## ✨ Pro Tips

1. **Test with 3-5 papers first** - Make sure it works
2. **Use delays for large batches** - `--delay 1` or `--delay 2`
3. **Export results** - Keeps track of what downloaded
4. **Try different mirrors if fails** - Some mirrors have different papers
5. **Use CLI for automation** - Perfect for cron jobs, scripts

---

**Happy downloading!** 📚🎓

For detailed help: See **BULK_MODE_GUIDE.md**
