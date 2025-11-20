# PDF Cleaning Tool for Gemini File Search

## Project Overview

This is an advanced PDF cleaning and preparation tool specifically designed for Arabic and English documents. It prepares PDFs for use with Gemini File Search by performing OCR, removing decorative elements, and extracting clean text while **strictly protecting tables and legal content**.

## Current State

The project includes:
- ✅ Complete OCR processing with automatic chunking (handles 1300+ page files)
- ✅ Triple-algorithm header/footer detection with consistency scoring
- ✅ Intelligent image classification that **never deletes tables**
- ✅ RTL/LTR text extraction with Unicode preservation
- ✅ Mandatory preview system before any deletions
- ✅ Triple backup system (raw, ocr, cleaned versions)
- ✅ Comprehensive reporting and chunk simulation for Gemini

## Architecture

### Core Services
1. **OCR Processor** (`services/ocr_processor.py`)
   - Automatically splits large PDFs into 200-page chunks
   - Processes each chunk separately to avoid RAM issues
   - Merges back seamlessly

2. **Header/Footer Detector** (`services/header_footer_detector.py`)
   - Runs 3 parallel algorithms:
     - Text repetition analysis
     - Bounding box position matching
     - Fuzzy string matching
   - Selects best algorithm based on consistency score

3. **Image Classifier** (`services/image_classifier.py`)
   - **Critical Rule**: Images with 3+ OCR lines are never deleted
   - Detects table structures automatically
   - Only removes small decorative images (<5% page area)

4. **Text Extractor** (`services/text_extractor.py`)
   - Auto-detects RTL/LTR per page
   - No text modification (only Unicode normalization)
   - Preserves formatting and whitespace

5. **Preview Generator** (`services/preview_generator.py`)
   - Mandatory preview before final processing
   - Shows samples of detected headers/footers/images
   - Generates before/after comparisons

## User Preferences

### Critical Requirements (DO NOT VIOLATE)
1. **Never delete tables**: Any image with table structure must be protected
2. **No text modification**: No rephrasing, spell correction, or content changes
3. **Preview before deletion**: User must see what will be removed
4. **Triple backup**: Always maintain raw, ocr, and cleaned versions
5. **Chunking for large files**: Split PDFs >200 pages to avoid RAM issues

### Language Settings
- Arabic files use `ara` language code for Tesseract
- English files use `eng` language code
- Can use `ara+eng` for mixed content
- Auto-detection of RTL/LTR per page

### Safety Thresholds
- Header/footer detection: 85% consistency threshold
- Image area threshold: 5% of page (smaller = likely decorative)
- Minimum OCR lines for table: 3 lines
- OCR confidence threshold: 70% (skip aggressive cleaning below this)

## How to Use

### First Time Setup
1. Install system dependencies:
   ```bash
   # Use Replit Packager or:
   chmod +x setup.sh && ./setup.sh
   ```

2. Install Python packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure settings:
   ```bash
   cp config.yaml.example config.yaml
   # Edit config.yaml as needed
   ```

### Processing PDFs

1. **Place PDFs in `context/` directory**
   ```bash
   mkdir -p context
   cp your_files.pdf context/
   ```

2. **Run preview mode first (MANDATORY)**
   ```bash
   python3 scripts/clean_pdfs.py --preview
   ```
   - Review reports in `report/` directory
   - Check what will be deleted
   - Verify table protection

3. **Run final processing (after approval)**
   ```bash
   python3 scripts/clean_pdfs.py
   ```

### Output Structure
```
output/
├── filename_raw.pdf              # Original backup
├── filename_ocr.pdf              # After OCR (no cleaning)
├── filename_cleaned.pdf          # Final version
├── filename_cleaned.txt          # Full text UTF-8
└── filename_chunk_simulation.txt # Gemini File Search simulation

report/
├── cleaning_report.json          # Full processing report
└── filename_preview.json         # Preview analysis
```

## Recent Changes

- **2024-11-20: ENHANCED FEATURES FOR GEMINI OPTIMIZATION**
  - ✅ **Markdown Structuring:** Auto-detects headers based on font size and adds `#` and `##` for hierarchical structure
  - ✅ **Smart Quranic Noise Removal:** Removes broken font artifacts (U T S R Q) while preserving valid English terms (SUKUK, MURABAHA, SWAPS, etc.)
  - ✅ **RTL Formatting:** Proper Arabic text rendering with arabic-reshaper and python-bidi
  - ✅ New script: `process_with_markdown.py` for enhanced processing
  - ✅ Updated config with `enable_markdown`, `remove_quranic_noise` settings

- 2024-01-20: Initial project creation with all core services
- Focus on AAOIFI Arabic and English document processing
- Implemented strict table protection (3+ lines rule)
- Added triple-algorithm header/footer detection
- Created chunk simulation for Gemini File Search testing

## Configuration Reference

Key `config.yaml` settings:

```yaml
ocr:
  chunk_size: 200              # Pages per chunk (for large files)
  confidence_threshold: 0.70   # Skip cleaning below this

header_footer:
  detection_threshold: 0.85    # Repetition threshold
  use_multi_algorithm: true    # Use all 3 algorithms

images:
  keep_tables: true            # NEVER set to false
  min_lines_for_table: 3       # Minimum OCR lines to protect
  area_threshold: 0.05         # 5% of page

text:
  auto_detect_direction: true  # RTL/LTR auto-detect
  normalization: "NFC"         # Unicode normalization only
```

## Troubleshooting

### Out of Memory
- Reduce `chunk_size` in config.yaml to 100 or 50

### Tables Being Deleted
- This should NEVER happen
- Check preview report for classification
- Increase `min_lines_for_table` if needed

### Missing Dependencies
```bash
# On Replit: Use Packager tool
# On Linux:
sudo apt-get install tesseract-ocr tesseract-ocr-ara tesseract-ocr-eng poppler-utils ghostscript
```

## Enhanced Features (NEW!)

### Markdown Structuring
The new `EnhancedTextProcessor` service detects document structure based on font size:
- **H1 headers (`#`):** Font size ≥ 16pt (configurable)
- **H2 headers (`##`):** Font size ≥ 14pt (configurable)
- **Body text:** Regular paragraphs

This helps Gemini understand document hierarchy and perform intelligent chunking.

### Quranic Noise Removal
Custom fonts for Quranic verses extract as garbage Latin characters. The enhanced processor:
- Detects and removes sequences like "U T S R Q P"
- **Preserves** valid financial/Islamic terms: SUKUK, MURABAHA, SWAPS, SHARIA, etc.
- Replaces Quranic text with `[نص قرآني]` (configurable)

Protected terms list includes 40+ Islamic finance and accounting terms.

### Usage
```bash
# Method 1: Enhanced processing only
python3 scripts/process_with_markdown.py context/AAOIFI_AR.pdf

# Method 2: Full pipeline (OCR + cleaning + enhancement)
python3 scripts/clean_pdfs.py
python3 scripts/process_with_markdown.py output/AAOIFI_AR_cleaned.pdf
```

See `QUICK_START_ENHANCED.md` and `ENHANCED_FEATURES_AR.md` for details.

## Next Steps (Future Enhancements)

1. Streamlit interactive UI for page-by-page review
2. Computer vision for enhanced table detection (Hough lines)
3. Parallel processing for multiple files
4. Direct Gemini File Search API integration
5. CSV/JSON extraction from detected tables
