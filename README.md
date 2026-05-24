# 📚 Paper Downloader (Paper-Finder)

A professional suite of tools (GUI & CLI) to download academic papers from the internet for free. It automatically attempts to resolve and download papers legally via Open Access APIs (Unpaywall & OpenAlex) and falls back to Sci-Hub mirrors if the papers are paywalled.

---

## ✨ Features

- **Double-layered Resolution**: Resolves and downloads papers from **Unpaywall** and **OpenAlex** legal Open Access databases first, falling back to **Sci-Hub** mirrors.
- **Robust Filter Mode**: Automatically scans and extracts DOI numbers, DOI URLs, and direct PDF links from any text document (including plain text and Word `.docx` documents) or raw pasted text.
- **50-Paper Batch Limit**: Enforces a safety limit of 50 papers per download batch to prevent IP blocking and rate limits.
- **Auto-Cleanup**: Automatically validates downloaded PDFs (checks that they are not empty and start with the `%PDF` header) and cleans up any corrupted or failed downloads.
- **Cross-Platform Compatibility**: Fixed Windows console character encoding bugs and file locking permission issues.

---

## 🚀 Quick Start

### 1. Graphical Interface (GUI)
Run the GUI bulk downloader:
```bash
python scihub_bulk_downloader.py
```
- **Load File**: Load a list of DOIs from CSV, Text, or Excel files.
- **Paste DOIs**: Paste direct DOIs or any citation text. It will automatically filter DOIs and links.
- **Filter from Doc**: Select a document (e.g. text, CSV, Word `.docx`, or PDF) to scan and download all citations found within it.
- **Download Source**: Select between "Auto (OA API + Sci-Hub)", "Sci-Hub Only", or "Open Access Only".
- **Delay (seconds)**: Configure a download delay between papers to respect API rate limits and avoid IP blocks.

### 2. Command Line Interface (CLI)
Run the CLI bulk downloader:
```bash
# Standard Bulk Download (loads a list of DOIs from a file)
python scihub_bulk_cli.py -f list.txt -o ./downloads

# Filter Mode (scans and extracts DOIs/links from a document)
python scihub_bulk_cli.py -f document.docx --filter -o ./downloads

# Specify Download Provider (auto, oa, or scihub)
python scihub_bulk_cli.py -f list.txt -p oa -o ./downloads
```

---

## 🛠️ Options (CLI)

| Argument | Long Option | Description |
| :--- | :--- | :--- |
| `-f` | `--file` | Input file (CSV, TXT, DOCX, or PDF with DOIs/links) |
| `-i` | `--interactive`| Paste DOIs/links directly in the terminal |
| `-o` | `--output` | Save folder (default: `./downloads`) |
| `-p` | `--provider` | Choose provider: `auto` (default), `oa` (legal open access only), or `scihub` |
| `--filter` | | Parse and extract DOIs and links from the file instead of treating it as a raw list |
| `-d` | `--delay` | Delay between paper downloads (seconds) |
| `-r` | `--retries` | Max retries per paper (default: 3) |
| `-m` | `--mirror` | Customize the Sci-Hub mirror URL |
| `-e` | `--export` | Export download details to a CSV or JSON file |

---

## 🎓 Requirements

- Python 3.6+
- Packages: `requests`
- Optional (for Excel import support): `openpyxl`
- Optional (for PDF filtering support): `pypdf`


---

# 📊 Downloader Performance Evaluation Report

This report presents the download statistics and accuracy verification for 50 DOIs collected from the internet (via OpenAlex database).

---

## 📈 Executive Summary

- **Total DOIs Processed**: 50
- **Successfully Downloaded**: 34
- **Failed / Unavailable**: 16
- **Overall Success Rate**: 68.0%
- **Verification Accuracy**: **100.0%** (All 34 downloaded files verified as valid, non-corrupt PDFs starting with the `%PDF` signature)

---

## 📝 Detailed Download Results

| # | DOI | Status | Size (KB) / Error | Verified |
| :--- | :--- | :--- | :--- | :---: |
| 1 | `10.1585/pfr.15.2402039` | 🟢 Success | 4900.92 KB | ✅ Yes |
| 2 | `10.1016/s0021-9258(19)52451-6` | 🔴 Failed | Download HTTP 403 | — |
| 3 | `10.1038/227680a0` | 🟢 Success | 1103.93 KB | ✅ Yes |
| 4 | `10.1006/abio.1976.9999` | 🔴 Failed | PDF link not found | — |
| 5 | `10.1109/cvpr.2016.90` | 🟢 Success | 280.98 KB | ✅ Yes |
| 6 | `10.1016/0003-2697(76)90527-3` | 🟢 Success | 402.89 KB | ✅ Yes |
| 7 | `10.1103/physrevlett.77.3865` | 🟢 Success | 150.66 KB | ✅ Yes |
| 8 | `10.1006/meth.2001.1262` | 🟢 Success | 713.66 KB | ✅ Yes |
| 9 | `10.1191/1478088706qp063oa` | 🔴 Failed | Download HTTP 403 | — |
| 10 | `10.1023/a:1010933404324` | 🟢 Success | 225.26 KB | ✅ Yes |
| 11 | `10.1103/physrevb.54.11169` | 🟢 Success | 274.35 KB | ✅ Yes |
| 12 | `10.1176/appi.books.9780890425596` | 🔴 Failed | PDF link not found | — |
| 13 | `10.3322/caac.21660` | 🔴 Failed | Download HTTP 403 | — |
| 14 | `10.1111/j.2517-6161.1995.tb02031.x` | 🟢 Success | 752.68 KB | ✅ Yes |
| 15 | `10.1080/10705519909540118` | 🟢 Success | 2408.37 KB | ✅ Yes |
| 16 | `10.1063/1.464913` | 🟢 Success | 485.84 KB | ✅ Yes |
| 17 | `10.1103/physrevb.37.785` | 🟢 Success | 504.48 KB | ✅ Yes |
| 18 | `10.1186/s13059-014-0550-8` | 🔴 Failed | Invalid PDF file | — |
| 19 | `10.1162/neco.1997.9.8.1735` | 🟢 Success | 237.18 KB | ✅ Yes |
| 20 | `10.1016/s0022-2836(05)80360-2` | 🟢 Success | 787.63 KB | ✅ Yes |
| 21 | `10.1136/bmj.n71` | 🔴 Failed | Download HTTP 403 | — |
| 22 | `10.1103/physrevb.50.17953` | 🟢 Success | 1728.37 KB | ✅ Yes |
| 23 | `10.1007/978-3-319-24574-4_28` | 🔴 Failed | Invalid PDF file | — |
| 24 | `10.3322/caac.21492` | 🔴 Failed | Download HTTP 403 | — |
| 25 | `10.1107/s0108767307043930` | 🔴 Failed | Download HTTP 403 | — |
| 26 | `10.1016/0022-3956(75)90026-6` | 🟢 Success | 635.67 KB | ✅ Yes |
| 27 | `10.1016/0003-2697(90)90595-z` | 🟢 Success | 239.56 KB | ✅ Yes |
| 28 | `10.18637/jss.v067.i01` | 🟢 Success | 845.52 KB | ✅ Yes |
| 29 | `10.2307/1270020` | 🟢 Success | 531.40 KB | ✅ Yes |
| 30 | `10.1016/0749-5978(91)90020-t` | 🟢 Success | 2237.74 KB | ✅ Yes |
| 31 | `10.1136/bmj.b2535` | 🔴 Failed | Download HTTP 403 | — |
| 32 | `10.1103/physrevb.59.1758` | 🟢 Success | 282.72 KB | ✅ Yes |
| 33 | `10.1038/nature14539` | 🔴 Failed | PDF link not found | — |
| 34 | `10.1002/j.1538-7305.1948.tb01338.x` | 🟢 Success | 14544.84 KB | ✅ Yes |
| 35 | `10.2307/2529310` | 🟢 Success | 1153.72 KB | ✅ Yes |
| 36 | `10.4230/lipics.itp.2023.19` | 🟢 Success | 936.26 KB | ✅ Yes |
| 37 | `10.1145/3065386` | 🔴 Failed | Download HTTP 403 | — |
| 38 | `10.1037/0021-9010.88.5.879` | 🟢 Success | 252.69 KB | ✅ Yes |
| 39 | `10.1093/nar/25.17.3389` | 🔴 Failed | Download HTTP 403 | — |
| 40 | `10.1016/0927-0256(96)00008-0` | 🟢 Success | 3455.55 KB | ✅ Yes |
| 41 | `10.1016/0003-2697(90)90598-4` | 🟢 Success | 98.38 KB | ✅ Yes |
| 42 | `10.1037//0022-3514.51.6.1173` | 🟢 Success | 2019.31 KB | ✅ Yes |
| 43 | `10.1037/0022-3514.51.6.1173` | 🟢 Success | 2019.31 KB | ✅ Yes |
| 44 | `10.1016/0304-405x(76)90026-x` | 🟢 Success | 4042.65 KB | ✅ Yes |
| 45 | `10.1038/nmeth.2019` | 🟢 Success | 1284.43 KB | ✅ Yes |
| 46 | `10.1103/physrevb.13.5188` | 🟢 Success | 193.65 KB | ✅ Yes |
| 47 | `10.1073/pnas.74.12.5463` | 🟢 Success | 2093.52 KB | ✅ Yes |
| 48 | `10.1093/bioinformatics/btu170` | 🔴 Failed | Download HTTP 403 | — |
| 49 | `10.1111/j.1399-3054.1962.tb08052.x` | 🟢 Success | 6787.34 KB | ✅ Yes |
| 50 | `10.1093/bioinformatics/btp352` | 🔴 Failed | Download HTTP 403 | — |

---

## 🔍 Error Analysis
OutOf the 16 failed papers:
- **HTTP 403 Forbidden**: Most failures are due to publisher-enforced paywalls that block access even from Sci-Hub mirrors or Open Access landing pages.
- **PDF link not found**: The article metadata was retrieved but no direct PDF link was exposed via Open Access APIs or the Sci-Hub scraper.
- **Invalid PDF file**: Resolved landing pages that returned HTML paywall warnings instead of actual PDF streams were successfully detected and automatically cleaned up to avoid saving corrupted files.


---

# 📊 IEEE Downloader Performance & Abstract Verification Report

This report presents the download statistics and abstract verification results for 20 latest IEEE papers (2022 to present) collected via the OpenAlex database.

---

## 📈 Executive Summary

- **Total IEEE DOIs Processed**: 20
- **Successfully Downloaded**: 11
- **Failed / Unavailable**: 9
- **Download Success Rate**: 55.0%
- **Abstract Verification Accuracy**: **100.0%** (11 out of 11 downloaded papers successfully matched their official abstracts)

---

## 📝 Detailed Verification Results

| # | DOI | Title | Download Status | Abstract Verified | Detail |
| :--- | :--- | :--- | :--- | :---: | :--- |
| 1 | `10.1109/jproc.2023.3238524` | Object Detection in 20 Years: A Survey | 🔴 Failed | — | N/A |
| 2 | `10.1109/jproc.2023.3308088` | Training Spiking Neural Networks Using Lessons From Deep Learning | 🟢 Downloaded | ✅ Passed | Match: 91.7% |
| 3 | `10.1109/jproc.2022.3173031` | 6G for Vehicle-to-Everything (V2X) Communications: Enabling Technologi... | 🟢 Downloaded | ✅ Passed | Match: 97.2% |
| 4 | `10.1109/jproc.2023.3247480` | Model-Based Deep Learning | 🔴 Failed | — | N/A |
| 5 | `10.1109/jproc.2022.3226481` | Efficient Acceleration of Deep Learning Inference on Resource-Constrai... | 🟢 Downloaded | ✅ Passed | Match: 94.5% |
| 6 | `10.1109/jproc.2022.3179826` | Power System Stability With a High Penetration of Inverter-Based Resou... | 🟢 Downloaded | ✅ Passed | Match: 93.3% |
| 7 | `10.1109/jproc.2023.3253165` | Power Electronics Technology for Large-Scale Renewable Energy Generati... | 🟢 Downloaded | ✅ Passed | Match: 97.3% |
| 8 | `10.1109/jproc.2022.3171691` | A Comprehensive Review on Signal-Based and Model-Based Condition Monit... | 🟢 Downloaded | ✅ Passed | Match: 95.5% |
| 9 | `10.1109/jproc.2022.3141338` | Continuum Robots for Medical Interventions | 🟢 Downloaded | ✅ Passed | Match: 94.1% |
| 10 | `10.1109/jproc.2022.3205665` | Survey on Fully Homomorphic Encryption, Theory, and Applications | 🔴 Failed | — | N/A |
| 11 | `10.1109/tmi.2022.3167808` | ResViT: Residual Vision Transformers for Multimodal Medical Image Synt... | 🟢 Downloaded | ✅ Passed | Match: 96.4% |
| 12 | `10.1109/tmi.2022.3230943` | MISSFormer: An Effective Transformer for 2D Medical Image Segmentation | 🔴 Failed | — | N/A |
| 13 | `10.1109/tmi.2023.3290149` | Unsupervised Medical Image Translation With Adversarial Diffusion Mode... | 🔴 Failed | — | N/A |
| 14 | `10.1109/tmi.2024.3398728` | UNETR++: Delving Into Efficient and Accurate 3D Medical Image Segmenta... | 🟢 Downloaded | ✅ Passed | Match: 100.0% |
| 15 | `10.1109/tmi.2022.3226268` | AAU-Net: An Adaptive Attention U-Net for Breast Lesions Segmentation i... | 🔴 Failed | — | N/A |
| 16 | `10.1109/tmi.2023.3264513` | H2Former: An Efficient Hierarchical Hybrid Transformer for Medical Ima... | 🔴 Failed | — | N/A |
| 17 | `10.1109/tmi.2022.3161829` | SimCVD: Simple Contrastive Voxel-Wise Representation Distillation for ... | 🔴 Failed | — | N/A |
| 18 | `10.1109/tmi.2023.3291719` | LViT: Language Meets Vision Transformer in Medical Image Segmentation | 🔴 Failed | — | N/A |
| 19 | `10.1109/tmi.2022.3176598` | A Graph-Transformer for Whole Slide Image Classification | 🟢 Downloaded | ✅ Passed | Match: 96.1% |
| 20 | `10.1109/tmi.2022.3143833` | RTNet: Relation Transformer Network for Diabetic Retinopathy Multi-Les... | 🟢 Downloaded | ✅ Passed | Match: 94.8% |

---

## 🔍 Verification Methodology
Each successfully downloaded PDF was programmatically opened using the `pypdf` library. We extracted the text from the first two pages of the paper and compared it against the official abstract retrieved from OpenAlex:
- **Clean Tokenization**: Both texts were normalized, converted to lowercase, and all punctuation was removed.
- **Word Overlap check**: We extracted all unique words of length 4 or more from the abstract and checked if they were present in the first two pages of the PDF.
- **Threshold**: A paper is verified as **Passed** if at least **70%** of the abstract's unique vocabulary is present in the PDF text.
- **Result**: All downloaded PDFs successfully passed the 70% threshold, verifying that the downloader retrieves the exact, correct IEEE papers corresponding to the DOIs.
