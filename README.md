# PDF Cleaning Tool for Arabic & English Documents

An advanced automated tool to clean and prepare Arabic and English PDF files for use with Gemini File Search.

[النسخة العربية (Arabic Version)](README_AR.md)

## Key Features

### ✅ Strict Content Protection
- **Never Delete Tables**: Any image with 3+ lines or table structure is fully protected
- **Triple Backup**: raw.pdf (original), ocr.pdf (after OCR), cleaned.pdf (final)
- **Mandatory Preview System**: Review all changes before final execution

### 🔍 Intelligent OCR Processing
- Automatic chunking for large files (>200 pages) to avoid RAM issues
- Full support for Arabic (ara) and English (eng)
- Automatic page deskew and rotation correction

### 🎯 Advanced Header/Footer Detection
- **3 Parallel Algorithms**:
  1. Text repetition analysis
  2. Bounding box matching
  3. Fuzzy string matching
- Automatic selection of highest accuracy algorithm (consistency score)

### 🖼️ Smart Image Classification
- Protection for tables and text-containing images
- Safe removal of decorative images only
- Skip-mode for low-confidence pages

### 📝 Safe Text Extraction
- **No Content Modification**: No rephrasing or spell correction
- Automatic RTL/LTR detection per page
- Unicode normalization only (NFC)

## Installation

### On Replit

```bash
# Install system packages (use Replit Packager tool)
# Required: tesseract, poppler_utils, ghostscript

# Or use the script
chmod +x setup.sh
./setup.sh

# Install Python libraries
pip install -r requirements.txt

# Copy configuration file
cp config.yaml.example config.yaml
```

### On Standard Linux

```bash
# Run installation script (requires sudo)
chmod +x setup.sh
./setup.sh
```

## Usage

### 1. Prepare Files
```bash
# Place PDF files in context/ directory
mkdir -p context
cp AAOIFI_AR.pdf AAOIFI_EN.pdf context/
```

### 2. Configure Settings
Edit `config.yaml` according to your needs:

```yaml
# Specify language for each file
language_per_file:
  AAOIFI_AR.pdf: "ara"
  AAOIFI_EN.pdf: "eng"

# Chunk size for splitting large PDFs
ocr:
  chunk_size: 200

# Header/footer detection threshold
header_footer:
  detection_threshold: 0.85

# Table protection
images:
  keep_tables: true
  min_lines_for_table: 3
```

### 3. Run Preview Mode (Recommended)
```bash
python3 scripts/clean_pdfs.py --preview
```

This will generate:
- Detailed reports in `report/`
- Samples of detected headers/footers
- List of images to be removed
- **No final deletions will occur**

### 4. Review Reports
```bash
# Open preview report
cat report/*_preview.json

# Review samples shown in the report
```

### 5. Final Execution (After Approval)
```bash
python3 scripts/clean_pdfs.py
```

## Output Files

After full processing, you'll find in `output/`:

### PDF Files
```
output/
├── AAOIFI_AR_raw.pdf          # Original backup
├── AAOIFI_AR_ocr.pdf          # After OCR only
├── AAOIFI_AR_cleaned.pdf      # Final cleaned version
├── AAOIFI_EN_raw.pdf
├── AAOIFI_EN_ocr.pdf
└── AAOIFI_EN_cleaned.pdf
```

### Text Files
```
output/
├── AAOIFI_AR_cleaned.txt              # Full UTF-8 text
├── AAOIFI_AR_chunk_simulation.txt     # Gemini chunks simulation
├── AAOIFI_EN_cleaned.txt
└── AAOIFI_EN_chunk_simulation.txt
```

### Reports
```
report/
├── cleaning_report.json          # Comprehensive report
├── AAOIFI_AR_preview.json        # Pre-execution preview
└── AAOIFI_EN_preview.json
```

## Technical Architecture

```
.
├── context/              # Place PDF files here
├── output/               # Processed files
├── report/               # Reports and previews
├── scripts/
│   └── clean_pdfs.py    # Main script
├── services/
│   ├── ocr_processor.py           # OCR with chunking
│   ├── header_footer_detector.py  # 3 algorithms
│   ├── image_classifier.py        # Table protection
│   ├── text_extractor.py          # Safe RTL/LTR
│   ├── preview_generator.py       # Previews
│   └── pdf_utils.py               # Helper utilities
├── config.yaml          # Configuration
└── requirements.txt
```

## Advanced Options

### Process Single File Only
```bash
python3 scripts/clean_pdfs.py --file context/AAOIFI_AR.pdf
```

### Enable Verbose Logging
```bash
python3 scripts/clean_pdfs.py --verbose
```

### Disable Image Removal (Keep Everything)
In `config.yaml`:
```yaml
images:
  remove_decorative: false
```

## Safety Guarantees

### ✅ What the Tool Does:
- OCR for non-searchable text
- Remove repeated headers/footers
- Remove small decorative images (<5% of page)
- Unicode normalization only

### ❌ What the Tool Never Does:
- Modify text content or rephrase
- Delete tables or important images
- Spelling or grammar correction
- Change numbers or legal terms
- Alter paragraph structure

## Troubleshooting

### Issue: "tesseract: command not found"
```bash
# On Replit: Use packager tool to install tesseract
# On Linux:
sudo apt-get install tesseract-ocr tesseract-ocr-ara tesseract-ocr-eng
```

### Issue: Out of Memory with Large File
In `config.yaml`:
```yaml
ocr:
  chunk_size: 100  # Reduce to 100 pages
```

### Issue: Tables Deleted by Mistake
This should never happen! Check:
```bash
# Open preview report
cat report/*_preview.json

# Verify image classification
# If this occurs, report to us to improve the algorithm
```

## FAQ

**Q: How long to process a 1300-page file?**  
A: About 20-40 minutes depending on machine speed (thanks to automatic chunking).

**Q: Can I use the files directly with Gemini?**  
A: Yes! The `*_cleaned.pdf` and `*_cleaned.txt` files are ready to upload.

**Q: What if some headers/footers aren't detected?**  
A: Check `config.yaml` and reduce `detection_threshold` from 0.85 to 0.75

**Q: Does it support other languages?**  
A: Yes, edit `language_per_file` in config (e.g., fra, deu, spa)

## Contributing & Support

- For technical issues: Check `pdf_cleaning.log`
- For questions: Open an issue on GitHub
- For improvements: Pull requests welcome!

## License

MIT License - Use freely

---

**Important Note**: This tool is designed for use with AAOIFI files and similar legal/accounting documents.  
Always review outputs before official use.
