
#!/usr/bin/env python3
"""
مقارنة شاملة لملفات PDF المعالجة
يحلل الفروقات ويوصي بأفضل ملف لـ Gemini File Search
"""

import sys
from pathlib import Path
import fitz  # PyMuPDF
import json
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

def analyze_pdf(pdf_path):
    """تحليل شامل لملف PDF"""
    try:
        doc = fitz.open(pdf_path)
        
        analysis = {
            'file_name': Path(pdf_path).name,
            'file_size_mb': Path(pdf_path).stat().st_size / (1024 * 1024),
            'total_pages': len(doc),
            'total_text_length': 0,
            'searchable_pages': 0,
            'empty_pages': 0,
            'pages_with_images': 0,
            'total_images': 0,
            'average_text_per_page': 0,
            'text_samples': []
        }
        
        text_lengths = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # استخراج النص
            text = page.get_text("text")
            text_length = len(text.strip())
            text_lengths.append(text_length)
            
            analysis['total_text_length'] += text_length
            
            if text_length > 50:
                analysis['searchable_pages'] += 1
            
            if text_length < 10:
                analysis['empty_pages'] += 1
            
            # عدد الصور
            images = page.get_images()
            if images:
                analysis['pages_with_images'] += 1
                analysis['total_images'] += len(images)
            
            # عينات نصية من صفحات مختلفة
            if page_num in [0, len(doc)//4, len(doc)//2, 3*len(doc)//4, len(doc)-1]:
                sample = text[:500] if text else "(صفحة فارغة)"
                analysis['text_samples'].append({
                    'page': page_num + 1,
                    'text': sample
                })
        
        if analysis['total_pages'] > 0:
            analysis['average_text_per_page'] = analysis['total_text_length'] / analysis['total_pages']
        
        # نسب مئوية
        analysis['searchable_percentage'] = (analysis['searchable_pages'] / analysis['total_pages']) * 100
        analysis['empty_percentage'] = (analysis['empty_pages'] / analysis['total_pages']) * 100
        
        doc.close()
        return analysis
        
    except Exception as e:
        print(f"❌ خطأ في تحليل {pdf_path}: {e}")
        return None

def analyze_text_file(text_path):
    """تحليل ملف نصي"""
    try:
        with open(text_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        lines = text.split('\n')
        
        analysis = {
            'file_name': Path(text_path).name,
            'file_size_mb': Path(text_path).stat().st_size / (1024 * 1024),
            'total_characters': len(text),
            'total_lines': len(lines),
            'non_empty_lines': len([l for l in lines if l.strip()]),
            'arabic_chars': sum(1 for c in text if '\u0600' <= c <= '\u06FF'),
            'english_chars': sum(1 for c in text if c.isalpha() and c.isascii()),
            'digits': sum(1 for c in text if c.isdigit()),
            'sample': text[:1000]
        }
        
        # نسبة العربية للإنجليزية
        total_letters = analysis['arabic_chars'] + analysis['english_chars']
        if total_letters > 0:
            analysis['arabic_percentage'] = (analysis['arabic_chars'] / total_letters) * 100
        else:
            analysis['arabic_percentage'] = 0
        
        return analysis
        
    except Exception as e:
        print(f"❌ خطأ في تحليل {text_path}: {e}")
        return None

def compare_pdfs(analyses):
    """مقارنة تفصيلية بين ملفات PDF"""
    print("\n" + "="*70)
    print("مقارنة تفصيلية بين ملفات PDF")
    print("="*70)
    
    for key, analysis in analyses.items():
        if analysis:
            print(f"\n📄 {analysis['file_name']}")
            print(f"   حجم الملف: {analysis['file_size_mb']:.2f} MB")
            print(f"   عدد الصفحات: {analysis['total_pages']}")
            print(f"   صفحات قابلة للبحث: {analysis['searchable_pages']} ({analysis['searchable_percentage']:.1f}%)")
            print(f"   صفحات فارغة: {analysis['empty_pages']} ({analysis['empty_percentage']:.1f}%)")
            print(f"   إجمالي النص: {analysis['total_text_length']:,} حرف")
            print(f"   متوسط النص/صفحة: {analysis['average_text_per_page']:.0f} حرف")
            print(f"   عدد الصور: {analysis['total_images']}")

def recommend_best_file(pdf_analyses, text_analyses):
    """التوصية بأفضل ملف لـ Gemini File Search"""
    print("\n" + "="*70)
    print("🎯 التوصيات لـ Gemini File Search")
    print("="*70)
    
    scores = {}
    
    # تسجيل ملفات PDF
    for key, analysis in pdf_analyses.items():
        if not analysis:
            continue
        
        score = 0
        reasons = []
        
        # نقاط للنص القابل للبحث
        if analysis['searchable_percentage'] > 95:
            score += 40
            reasons.append("✅ نص قابل للبحث بنسبة عالية")
        elif analysis['searchable_percentage'] > 80:
            score += 30
            reasons.append("✓ نص قابل للبحث بنسبة جيدة")
        else:
            score += 10
            reasons.append("⚠️ نص قابل للبحث بنسبة منخفضة")
        
        # نقاط لمتوسط النص في الصفحة
        if analysis['average_text_per_page'] > 500:
            score += 30
            reasons.append("✅ محتوى نصي غني")
        elif analysis['average_text_per_page'] > 200:
            score += 20
            reasons.append("✓ محتوى نصي معتدل")
        
        # خصم للصفحات الفارغة
        if analysis['empty_percentage'] < 5:
            score += 20
            reasons.append("✅ صفحات فارغة قليلة")
        elif analysis['empty_percentage'] < 10:
            score += 10
        else:
            score -= 10
            reasons.append("⚠️ عدد صفحات فارغة كبير")
        
        # نقاط لحجم الملف (أصغر أفضل للرفع)
        if analysis['file_size_mb'] < 50:
            score += 10
            reasons.append("✓ حجم ملف مناسب")
        
        scores[key] = {'score': score, 'reasons': reasons, 'analysis': analysis}
    
    # تسجيل ملفات النص
    for key, analysis in text_analyses.items():
        if not analysis:
            continue
        
        score = 0
        reasons = []
        
        # ملفات النص تحصل على نقاط عالية للبحث
        score += 50
        reasons.append("✅ نص خام - بحث مباشر وسريع")
        
        # نقاط للمحتوى
        if analysis['total_characters'] > 100000:
            score += 30
            reasons.append("✅ محتوى نصي شامل")
        
        # نقاط للأسطر غير الفارغة
        if analysis['non_empty_lines'] > 1000:
            score += 20
            reasons.append("✅ عدد أسطر كبير")
        
        scores[key] = {'score': score, 'reasons': reasons, 'analysis': analysis}
    
    # ترتيب حسب النقاط
    sorted_scores = sorted(scores.items(), key=lambda x: x[1]['score'], reverse=True)
    
    print("\n🏆 الترتيب حسب الملاءمة لـ Gemini File Search:")
    print()
    
    for i, (key, data) in enumerate(sorted_scores, 1):
        print(f"{i}. {data['analysis']['file_name']}")
        print(f"   النقاط: {data['score']}/100")
        for reason in data['reasons']:
            print(f"   {reason}")
        print()
    
    # التوصية النهائية
    best = sorted_scores[0]
    print("="*70)
    print("🎯 التوصية النهائية:")
    print(f"   الملف الأفضل: {best[1]['analysis']['file_name']}")
    print(f"   النقاط: {best[1]['score']}/100")
    print()
    
    # نصائح إضافية
    print("💡 ملاحظات:")
    
    if '_cleaned.txt' in best[0]:
        print("   ✅ ملفات TXT أفضل لـ Gemini File Search:")
        print("      - بحث أسرع وأكثر دقة")
        print("      - لا توجد مشاكل في استخراج النص")
        print("      - حجم أصغر")
    elif '_cleaned.pdf' in best[0]:
        print("   ✅ ملف PDF النظيف يحتفظ بالتنسيق:")
        print("      - مفيد إذا كنت تحتاج الجداول والصور")
        print("      - لكن ملف TXT قد يكون أسرع في البحث")
    elif '_ocr.pdf' in best[0]:
        print("   ⚠️ ملف OCR جيد لكن:")
        print("      - قد يحتوي على headers/footers متكررة")
        print("      - الملف النظيف (_cleaned) أفضل")
    
    return sorted_scores

def main():
    """البرنامج الرئيسي"""
    print("="*70)
    print("تحليل ومقارنة ملفات PDF المعالجة")
    print("="*70)
    
    output_dir = Path("output")
    
    if not output_dir.exists():
        print("❌ مجلد output غير موجود!")
        return
    
    # البحث عن ملفات PDF والنص
    pdf_files = list(output_dir.glob("*.pdf"))
    txt_files = list(output_dir.glob("*.txt"))
    
    if not pdf_files and not txt_files:
        print("❌ لم يتم العثور على أي ملفات في مجلد output!")
        return
    
    print(f"\n✅ تم العثور على:")
    print(f"   - {len(pdf_files)} ملف PDF")
    print(f"   - {len(txt_files)} ملف نصي")
    
    # تحليل ملفات PDF
    pdf_analyses = {}
    print(f"\n🔍 تحليل ملفات PDF...")
    for pdf_file in pdf_files:
        print(f"   معالجة {pdf_file.name}...")
        analysis = analyze_pdf(str(pdf_file))
        if analysis:
            key = pdf_file.stem
            pdf_analyses[key] = analysis
    
    # تحليل ملفات النص
    text_analyses = {}
    print(f"\n🔍 تحليل الملفات النصية...")
    for txt_file in txt_files:
        if 'chunk_simulation' not in txt_file.name:
            print(f"   معالجة {txt_file.name}...")
            analysis = analyze_text_file(str(txt_file))
            if analysis:
                key = txt_file.stem
                text_analyses[key] = analysis
    
    # المقارنة والتوصيات
    compare_pdfs(pdf_analyses)
    recommend_best_file(pdf_analyses, text_analyses)
    
    # حفظ التقرير
    report = {
        'pdf_analyses': pdf_analyses,
        'text_analyses': text_analyses,
        'timestamp': str(Path.cwd())
    }
    
    report_path = output_dir / 'comparison_report.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n📊 تم حفظ التقرير الكامل في: {report_path}")

if __name__ == '__main__':
    main()
