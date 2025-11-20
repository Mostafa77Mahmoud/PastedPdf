#!/usr/bin/env python3
"""
Fix Lam-Alif ligature issues in Arabic text
============================================

This script fixes common Lam-Alif decomposition errors that occur when 
extracting Arabic text from PDFs:

- األ -> الأ (fixes: األمين -> الأمين, األمر -> الأمر)
- اإل -> الإ (fixes: اإلجارة -> الإجارة, اإلسلامية -> الإسلامية)
- اآل -> الآ (fixes: اآلن -> الآن, اآلية -> الآية)

These errors happen when PDF stores Lam-Alif ligatures in a way that 
causes incorrect character ordering during extraction.
"""

import re
import sys
from pathlib import Path


def fix_lam_alif(text: str) -> dict:
    """
    Fix Lam-Alif ligature issues in Arabic text
    
    Args:
        text: Input text with Lam-Alif errors
        
    Returns:
        Dictionary with 'text' (fixed text) and 'stats' (replacement counts)
    """
    stats = {
        'األ -> الأ': 0,
        'اإل -> الإ': 0,
        'اآل -> الآ': 0,
        'total_fixes': 0
    }
    
    # Pattern 1: األ -> الأ (most common - affects الأمين, الأمر, الأول, etc.)
    # This fixes the case where Lam and Hamza are reversed
    fixed_text = text
    pattern1_count = len(re.findall(r'أل', fixed_text))
    fixed_text = re.sub(r'أل', 'لأ', fixed_text)
    stats['األ -> الأ'] = pattern1_count
    
    # Pattern 2: اإل -> الإ (affects الإجارة, الإسلامية, الإيمان, etc.)
    # This fixes the case where Lam and Alif with Hamza below are reversed
    pattern2_count = len(re.findall(r'إل', fixed_text))
    fixed_text = re.sub(r'إل', 'لإ', fixed_text)
    stats['اإل -> الإ'] = pattern2_count
    
    # Pattern 3: اآل -> الآ (affects الآخرة, الآن, الآية, etc.)
    # This fixes the case where Lam and Alif with Madda are reversed
    pattern3_count = len(re.findall(r'آل', fixed_text))
    fixed_text = re.sub(r'آل', 'لآ', fixed_text)
    stats['اآل -> الآ'] = pattern3_count
    
    stats['total_fixes'] = pattern1_count + pattern2_count + pattern3_count
    
    return {
        'text': fixed_text,
        'stats': stats
    }


def main():
    """Main function to fix Lam-Alif issues in the output file"""
    
    input_file = Path('output/Shariaah-Standards-ARB_structured.md')
    output_file = input_file  # Overwrite the same file
    backup_file = Path('output/Shariaah-Standards-ARB_structured.md.backup')
    
    print('=' * 80)
    print('🔧 FIXING LAM-ALIF LIGATURE ISSUES')
    print('=' * 80)
    print()
    
    # Check if file exists
    if not input_file.exists():
        print(f'❌ Error: File not found: {input_file}')
        sys.exit(1)
    
    # Create backup
    print(f'📁 Input file: {input_file}')
    print(f'💾 Creating backup: {backup_file}')
    
    with open(input_file, 'r', encoding='utf-8') as f:
        original_text = f.read()
    
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.write(original_text)
    
    print()
    print('🔍 Scanning for Lam-Alif errors...')
    
    # Apply fixes
    result = fix_lam_alif(original_text)
    fixed_text = result['text']
    stats = result['stats']
    
    print()
    print('📊 Replacement Statistics:')
    print('=' * 80)
    print(f"   األ -> الأ : {stats['األ -> الأ']:,} replacements")
    print(f"   اإل -> الإ : {stats['اإل -> الإ']:,} replacements")
    print(f"   اآل -> الآ : {stats['اآل -> الآ']:,} replacements")
    print(f"   TOTAL:    {stats['total_fixes']:,} fixes applied")
    print('=' * 80)
    print()
    
    # Save fixed text
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(fixed_text)
    
    print(f'✅ Fixed file saved: {output_file}')
    print()
    
    # Verify fixes by showing first few TOC lines
    print('🔍 VERIFICATION - First TOC entries (after fix):')
    print('=' * 80)
    
    lines = fixed_text.split('\n')
    toc_lines = []
    for line in lines:
        if ('كلمة' in line or 'الإجارة' in line or 'الأمين' in line or 
            'الآ' in line) and len(line.strip()) > 15:
            if '.' * 3 in line:  # Table of contents line
                toc_lines.append(line.strip())
                if len(toc_lines) >= 10:
                    break
    
    for i, line in enumerate(toc_lines, 1):
        print(f'{i:2}. {line}')
    
    print('=' * 80)
    print()
    
    # Verify no more errors exist
    remaining_errors = []
    if 'اأ' in fixed_text:
        remaining_errors.append('اأ still found')
    if 'اإ' in fixed_text:
        remaining_errors.append('اإ still found')
    if 'اآ' in fixed_text:
        remaining_errors.append('اآ still found')
    
    if remaining_errors:
        print('⚠️  WARNING: Some patterns still exist:')
        for error in remaining_errors:
            print(f'   - {error}')
        print()
    else:
        print('✅ ALL LAM-ALIF ERRORS FIXED!')
        print()
    
    print('=' * 80)
    print('🎉 FILE READY FOR GEMINI!')
    print('=' * 80)
    print()
    print(f'Original backup saved at: {backup_file}')
    print()


if __name__ == '__main__':
    main()
