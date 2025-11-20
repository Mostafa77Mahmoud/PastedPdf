#!/usr/bin/env python3
"""Process first 50 pages as sample for testing"""

import sys, yaml, logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.enhanced_text_processor import EnhancedTextProcessor

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

# Load config
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

processor = EnhancedTextProcessor(config)

print('=' * 70)
print('Processing SAMPLE: First 50 pages')
print('=' * 70)
print()

# Process 50 pages in batches of 10
result = processor.extract_text_with_structure_batched(
    'context/Shariaah-Standards-ARB.pdf',
    batch_size=10,  # Small batches for faster processing
    max_pages=50    # Only process first 50 pages
)

# Save
output_dir = Path('output')
output_dir.mkdir(exist_ok=True)

md_path = output_dir / 'SAMPLE_50pages_structured.md'
txt_path = output_dir / 'SAMPLE_50pages_clean.txt'

processor.save_markdown_file(result['markdown_text'], str(md_path))

with open(txt_path, 'w', encoding='utf-8') as f:
    f.write(result['plain_text'])

print()
print('=' * 70)
print('📊 Results')
print('=' * 70)
print(f"H1 headers:      {result['structure_info']['h1_count']}")
print(f"H2 headers:      {result['structure_info']['h2_count']}")
print(f"Body paragraphs: {result['structure_info']['body_count']}")
print()
print(f"Quranic removed: {result['cleaning_stats']['quranic_sequences_removed']}")
print(f"English terms:   {result['cleaning_stats']['english_terms_preserved']}")
print()
print(f"Saved to: {md_path}")
print('=' * 70)
