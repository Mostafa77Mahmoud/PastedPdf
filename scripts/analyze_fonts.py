#!/usr/bin/env python3
"""
Font Analysis Utility - تحليل أحجام الخطوط في PDF
Analyzes font sizes in PDF to help calibrate Markdown header detection

This tool helps you find the correct h1_font_size and h2_font_size values
for your specific PDF before running the full processing.
"""

import sys
import logging
from pathlib import Path
from collections import Counter, defaultdict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import pdfplumber
except ImportError:
    print("Error: pdfplumber not installed")
    print("Run: pip install pdfplumber")
    sys.exit(1)


def setup_logging():
    """Setup basic logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)


def analyze_fonts(pdf_path: str, sample_pages: int = 5):
    """
    Analyze font sizes in PDF
    
    Args:
        pdf_path: Path to PDF file
        sample_pages: Number of pages to analyze (default: 5)
    
    Returns:
        dict: Font size statistics
    """
    logger = logging.getLogger(__name__)
    
    font_sizes = []
    font_size_text_samples = defaultdict(list)
    total_chars = 0
    
    with pdfplumber.open(pdf_path) as pdf:
        pages_to_analyze = min(sample_pages, len(pdf.pages))
        
        logger.info(f"Analyzing first {pages_to_analyze} pages...")
        
        for page_num in range(pages_to_analyze):
            page = pdf.pages[page_num]
            
            # Extract characters with font information
            chars = page.chars
            
            for char in chars:
                # Get font size (height)
                size = char.get('size', char.get('height', 12))
                text = char.get('text', '')
                
                if text.strip():  # Only count non-whitespace
                    font_sizes.append(size)
                    total_chars += 1
                    
                    # Collect text samples for each font size
                    if len(font_size_text_samples[size]) < 3:
                        font_size_text_samples[size].append(text)
    
    # Count font size frequency
    size_counter = Counter(font_sizes)
    
    # Calculate statistics
    total = len(font_sizes)
    
    # Sort by size descending
    sorted_sizes = sorted(size_counter.items(), key=lambda x: x[0], reverse=True)
    
    return {
        'total_chars': total_chars,
        'total_measurements': total,
        'size_distribution': sorted_sizes,
        'samples': dict(font_size_text_samples),
        'unique_sizes': len(size_counter)
    }


def recommend_thresholds(stats: dict):
    """
    Recommend h1 and h2 font size thresholds based on statistics
    
    Args:
        stats: Font size statistics from analyze_fonts()
    
    Returns:
        dict: Recommended thresholds
    """
    distribution = stats['size_distribution']
    total = stats['total_measurements']
    
    # Calculate percentage for each size
    size_percentages = [(size, count, (count / total) * 100) 
                        for size, count in distribution]
    
    # Find body text size (most common size)
    body_size = max(size_percentages, key=lambda x: x[1])[0]
    
    # Find sizes that are larger than body text and represent < 20% of text
    header_candidates = [
        (size, count, pct) 
        for size, count, pct in size_percentages 
        if size > body_size and pct < 20
    ]
    
    # Sort header candidates by size descending
    header_candidates.sort(reverse=True)
    
    recommendations = {
        'body_text_size': body_size,
        'h1_size': None,
        'h2_size': None,
        'confidence': 'low'
    }
    
    if len(header_candidates) >= 2:
        # We have at least 2 header levels
        recommendations['h1_size'] = header_candidates[0][0]
        recommendations['h2_size'] = header_candidates[1][0]
        recommendations['confidence'] = 'high'
    elif len(header_candidates) == 1:
        # Only one header level detected
        recommendations['h2_size'] = header_candidates[0][0]
        recommendations['h1_size'] = header_candidates[0][0] + 2
        recommendations['confidence'] = 'medium'
    else:
        # No clear headers detected, use body + offset
        recommendations['h2_size'] = body_size + 2
        recommendations['h1_size'] = body_size + 4
        recommendations['confidence'] = 'low'
    
    return recommendations


def print_report(stats: dict, recommendations: dict):
    """Print analysis report"""
    
    print("=" * 80)
    print("📊 FONT SIZE ANALYSIS REPORT")
    print("=" * 80)
    print()
    
    print(f"Total characters analyzed: {stats['total_chars']:,}")
    print(f"Unique font sizes found: {stats['unique_sizes']}")
    print()
    
    print("=" * 80)
    print("FONT SIZE DISTRIBUTION")
    print("=" * 80)
    print(f"{'Size (pt)':<12} {'Count':<12} {'Percentage':<12} {'Sample Text'}")
    print("-" * 80)
    
    total = stats['total_measurements']
    samples = stats['samples']
    
    for size, count in stats['size_distribution'][:10]:  # Show top 10
        percentage = (count / total) * 100
        sample = ''.join(samples.get(size, [''])[:3])[:40]
        
        # Add indicator for likely text type
        indicator = ""
        if size == recommendations['body_text_size']:
            indicator = " ← BODY TEXT"
        elif size == recommendations['h1_size']:
            indicator = " ← Recommended H1"
        elif size == recommendations['h2_size']:
            indicator = " ← Recommended H2"
        
        print(f"{size:<12.1f} {count:<12,} {percentage:<11.1f}% {sample}{indicator}")
    
    if stats['unique_sizes'] > 10:
        print(f"... and {stats['unique_sizes'] - 10} more sizes")
    
    print()
    print("=" * 80)
    print("RECOMMENDATIONS FOR config.yaml")
    print("=" * 80)
    print()
    
    print(f"Confidence Level: {recommendations['confidence'].upper()}")
    print()
    
    print("Suggested settings:")
    print("-" * 40)
    print(f"h1_font_size: {recommendations['h1_size']:.0f}  # Main headers")
    print(f"h2_font_size: {recommendations['h2_size']:.0f}  # Subheaders")
    print(f"# Body text size: {recommendations['body_text_size']:.1f}pt")
    print()
    
    if recommendations['confidence'] == 'high':
        print("✅ High confidence: Clear header hierarchy detected!")
    elif recommendations['confidence'] == 'medium':
        print("⚠️  Medium confidence: Only one header level found.")
        print("   You may need to adjust h1_font_size manually.")
    else:
        print("⚠️  Low confidence: No clear headers detected.")
        print("   These are estimated values. Please review your PDF manually.")
    
    print()
    print("=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print()
    print("1. Update config.yaml with the recommended values above")
    print()
    print("2. Verify by running:")
    print("   python3 scripts/process_with_markdown.py <your_pdf>")
    print()
    print("3. Check the output _structured.md file:")
    print("   - Main headers should have # prefix")
    print("   - Subheaders should have ## prefix")
    print()
    print("4. If headers are missing or incorrect, adjust the font size values")
    print("   in config.yaml and try again")
    print()


def main():
    """Main function"""
    
    logger = setup_logging()
    
    print()
    print("=" * 80)
    print("🔍 PDF FONT ANALYZER")
    print("=" * 80)
    print()
    
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/analyze_fonts.py <pdf_file> [sample_pages]")
        print()
        print("Example:")
        print("  python3 scripts/analyze_fonts.py context/AAOIFI_AR.pdf")
        print("  python3 scripts/analyze_fonts.py context/AAOIFI_AR.pdf 10")
        print()
        print("This will analyze font sizes in your PDF and recommend")
        print("the correct h1_font_size and h2_font_size values for config.yaml")
        return 1
    
    pdf_path = Path(sys.argv[1])
    
    if not pdf_path.exists():
        print(f"❌ File not found: {pdf_path}")
        return 1
    
    # Get sample pages from argument or use default
    sample_pages = 5
    if len(sys.argv) >= 3:
        try:
            sample_pages = int(sys.argv[2])
        except ValueError:
            print(f"⚠️  Invalid sample_pages value, using default: 5")
    
    print(f"📖 Analyzing: {pdf_path.name}")
    print(f"📄 Sample pages: {sample_pages}")
    print()
    
    # Analyze fonts
    stats = analyze_fonts(str(pdf_path), sample_pages)
    
    # Get recommendations
    recommendations = recommend_thresholds(stats)
    
    # Print report
    print_report(stats, recommendations)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
