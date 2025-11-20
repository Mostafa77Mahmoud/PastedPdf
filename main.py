#!/usr/bin/env python3
"""
Simple entry point for PDF Cleaning Tool
Shows help and instructions for users
"""

import os
import sys
from pathlib import Path

def print_banner():
    """Print welcome banner"""
    print("=" * 70)
    print("PDF CLEANING TOOL FOR GEMINI FILE SEARCH")
    print("=" * 70)
    print()
    print("Advanced PDF cleaning for Arabic and English documents")
    print()

def check_setup():
    """Check if setup is complete"""
    issues = []
    
    # Check if config exists
    if not Path("config.yaml").exists():
        issues.append("❌ config.yaml not found")
        print("Creating config.yaml from example...")
        try:
            import shutil
            shutil.copy("config.yaml.example", "config.yaml")
            print("✅ Created config.yaml")
        except Exception as e:
            print(f"Error creating config.yaml: {e}")
    else:
        print("✅ config.yaml found")
    
    # Check if context directory exists
    if not Path("context").exists():
        Path("context").mkdir(exist_ok=True)
        print("✅ Created context/ directory")
    else:
        print("✅ context/ directory exists")
    
    # Check for PDF files
    pdf_files = list(Path("context").glob("*.pdf"))
    if not pdf_files:
        issues.append("⚠️  No PDF files found in context/ directory")
    else:
        print(f"✅ Found {len(pdf_files)} PDF file(s)")
    
    # Check if dependencies are installed
    try:
        import yaml
        import fitz
        import PIL
        print("✅ Python dependencies installed")
    except ImportError as e:
        issues.append(f"❌ Missing Python dependencies: {e}")
        print(f"❌ Missing Python dependencies: {e}")
        print("   Run: pip install -r requirements.txt")
    
    return issues

def print_instructions():
    """Print usage instructions"""
    print()
    print("=" * 70)
    print("QUICK START GUIDE")
    print("=" * 70)
    print()
    print("1. SETUP (First Time Only)")
    print("   - Install system dependencies:")
    print("     chmod +x setup.sh && ./setup.sh")
    print()
    print("   - Or on Replit: Use Packager to install:")
    print("     tesseract, poppler_utils, ghostscript")
    print()
    print("   - Install Python packages:")
    print("     pip install -r requirements.txt")
    print()
    print("2. PREPARE YOUR FILES")
    print("   - Place PDF files in the 'context/' directory")
    print("   - Edit 'config.yaml' to configure language settings")
    print()
    print("3. PREVIEW MODE (Recommended First)")
    print("   python3 scripts/clean_pdfs.py --preview")
    print()
    print("   This will show you:")
    print("   - What headers/footers will be removed")
    print("   - Which images will be deleted")
    print("   - Sample pages before/after")
    print("   - NO FILES WILL BE MODIFIED")
    print()
    print("4. REVIEW PREVIEW REPORTS")
    print("   - Check files in 'report/' directory")
    print("   - Verify table protection is working")
    print("   - Confirm deletions are safe")
    print()
    print("5. FINAL PROCESSING (After Approval)")
    print("   python3 scripts/clean_pdfs.py")
    print()
    print("=" * 70)
    print("DOCUMENTATION")
    print("=" * 70)
    print("- English: README.md")
    print("- Arabic:  README_AR.md")
    print("- Project Info: replit.md")
    print()
    print("=" * 70)
    print("FEATURES")
    print("=" * 70)
    print("✅ Never deletes tables (3+ lines protection)")
    print("✅ Automatic PDF chunking for large files (>200 pages)")
    print("✅ 3-algorithm header/footer detection")
    print("✅ RTL/LTR auto-detection")
    print("✅ Triple backup (raw, ocr, cleaned)")
    print("✅ Gemini File Search chunk simulation")
    print()

def main():
    """Main entry point"""
    print_banner()
    
    print("Checking setup...")
    print()
    issues = check_setup()
    
    print()
    if issues:
        print("⚠️  SETUP ISSUES DETECTED:")
        for issue in issues:
            print(f"   {issue}")
        print()
    
    print_instructions()
    
    print("Ready to process PDFs!")
    print()
    print("Run: python3 scripts/clean_pdfs.py --preview")
    print()

if __name__ == '__main__':
    main()
