# Quick Start Guide - PDF Cleaning Tool

## 🚀 5-Minute Setup

### Step 1: Install (Done automatically on Replit)
```bash
# System dependencies already installed via Replit Packager:
# ✅ tesseract (with Arabic & English)
# ✅ poppler
# ✅ ghostscript

# Python packages already installed
```

### Step 2: Place Your PDFs
```bash
# Put your PDF files in the context/ directory
cp your_file.pdf context/
```

### Step 3: Run Preview (Safe Mode)
```bash
python3 scripts/clean_pdfs.py --preview
```

This will:
- Show what will be removed (NO actual changes)
- Generate reports in `report/` directory
- Display sample pages before/after

### Step 4: Review Results
```bash
# Check the preview report
cat report/cleaning_report.json

# Look for:
# - Headers/footers detected
# - Images classified (tables vs decorative)
# - Recommendations
```

### Step 5: Run Final Processing
```bash
# If satisfied with preview:
python3 scripts/clean_pdfs.py
```

## 📁 Output Files

After processing, find in `output/`:

```
output/
├── filename_raw.pdf         # Original (backup)
├── filename_ocr.pdf         # After OCR only  
├── filename_cleaned.pdf     # Final cleaned version
├── filename_cleaned.txt     # Full text UTF-8
└── filename_chunk_simulation.txt  # For Gemini testing
```

## ⚙️ Configuration

Edit `config.yaml` to customize:

```yaml
# Set language for each file
language_per_file:
  AAOIFI_AR.pdf: "ara"
  AAOIFI_EN.pdf: "eng"

# Adjust detection sensitivity
header_footer:
  detection_threshold: 0.85  # Lower = more aggressive

# Table protection (DON'T CHANGE)
images:
  keep_tables: true
  min_lines_for_table: 3
```

## 🛡️ Safety Features

✅ **Triple Backup**: Always keeps raw, ocr, and cleaned versions  
✅ **Table Protection**: Never deletes images with 3+ text lines  
✅ **Preview Mode**: See changes before applying  
✅ **Skip on Low Confidence**: Skips cleaning if OCR quality is poor  

## 🔧 Advanced Usage

### Process Single File
```bash
python3 scripts/clean_pdfs.py --file context/myfile.pdf
```

### Verbose Logging
```bash
python3 scripts/clean_pdfs.py --verbose
```

### Custom Config
```bash
python3 scripts/clean_pdfs.py --config my_config.yaml
```

## ❓ Troubleshooting

### "No PDF files found"
```bash
# Make sure PDFs are in context/ directory
ls context/
```

### Out of Memory (large files)
```yaml
# Edit config.yaml
ocr:
  chunk_size: 100  # Reduce from 200 to 100
```

### Tables Being Deleted
```bash
# This should NEVER happen
# Check preview report first:
cat report/*_preview.json

# If it happens, increase protection:
# Edit config.yaml
images:
  min_lines_for_table: 2  # From 3 to 2
```

## 📚 Full Documentation

- English: `README.md`
- Arabic: `README_AR.md`
- Project Details: `replit.md`

## 🎯 Example Workflow

```bash
# 1. Add your files
cp AAOIFI_AR.pdf context/

# 2. Preview
python3 scripts/clean_pdfs.py --preview

# 3. Review
cat report/AAOIFI_AR_preview.json

# 4. Process
python3 scripts/clean_pdfs.py

# 5. Use outputs
ls output/AAOIFI_AR_*
```

## ✨ Features Summary

| Feature | Description |
|---------|-------------|
| OCR Chunking | Handles 1300+ page files by splitting into 200-page chunks |
| 3 Algorithms | Triple header/footer detection for accuracy |
| Table Protection | **Never** deletes tables (3+ lines rule) |
| RTL/LTR Support | Auto-detection per page |
| Preview System | Mandatory review before changes |
| Chunk Simulation | Test output with Gemini File Search |

---

**Ready to start?** Run: `python3 main.py`
