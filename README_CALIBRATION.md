# ⚠️ MUST READ: Calibration Guide

## Before Processing Your First PDF

**Stop! Don't run the processing yet!** 

You need to calibrate the font size settings first, or you'll get plain text without any headers.

---

## Quick Start (2 Minutes)

### Step 1: Analyze Your PDF

```bash
python3 scripts/analyze_fonts.py context/your_file.pdf
```

This will show you:
- What font sizes are used in your PDF
- Which sizes are headers vs body text
- Recommended config values

### Step 2: Update Config

The analyzer will give you something like:
```
Suggested settings:
h1_font_size: 14
h2_font_size: 13
```

Open `config.yaml` and update:
```yaml
text:
  h1_font_size: 14  # ← Use the recommended value
  h2_font_size: 13  # ← Use the recommended value
```

### Step 3: Process

```bash
python3 scripts/process_with_markdown.py context/your_file.pdf
```

### Step 4: Verify

Check `output/your_file_structured.md`:
- Main headers should have `#`
- Subheaders should have `##`
- Body text should have no prefix

---

## Why This Matters

**Without calibration:**
```
المعيار رقم 1
التعريف
النص...
```
→ Gemini sees this as plain text blob

**With calibration:**
```markdown
# المعيار رقم 1

## التعريف

النص...
```
→ Gemini understands structure = 50-80% better results

---

## Full Documentation

See [CALIBRATION_GUIDE.md](CALIBRATION_GUIDE.md) for complete details.

---

## Already Correct ✅

**Text Order:** The code already saves files in the correct format:
- `_structured.md` → Logical Order (for Gemini) ✅
- `_clean.txt` → Logical Order (for Gemini) ✅
- `_rtl.txt` → Visual Order (for humans) ✅

No action needed on this front!

---

## Questions?

See [CALIBRATION_GUIDE.md](CALIBRATION_GUIDE.md) for troubleshooting and detailed explanations.
