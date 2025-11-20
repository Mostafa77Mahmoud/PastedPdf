
#!/usr/bin/env python3
"""
Deep Text Cleaner - تنظيف عميق للنصوص العربية
يحل مشاكل: التكرار، أرقام الصفحات المكررة، الفهارس، الحواشي المدمجة، الترويسات والتذييلات
"""

import re
import sys
from pathlib import Path
from difflib import SequenceMatcher
from collections import Counter


class DeepTextCleaner:
    """منظف متقدم للنصوص العربية"""
    
    def __init__(self):
        self.similarity_threshold = 0.90  # نسبة التشابه لاعتبار السطر مكرر
        self.min_line_length = 10  # زيادة الحد الأدنى لطول السطر
        self.common_headers_footers = [
            r'ﺍﻟﻤﻌﺎﻳﻴﺮ\s*ﺍﻟﺸﺮﻋﻴﺔ',
            r'ﺭﻗﻢ\s*ﺍﻟﺼﻔﺤﺔ',
            r'www\.aaoifi\.com',
            r'info@aaoifi\.com',
            r'©.*aaoifi',
            r'المعايير\s*الشرعية',
            r'رقم\s*الصفحة',
        ]
        
    def clean_text(self, text: str) -> str:
        """تنظيف شامل للنص"""
        
        lines = text.split('\n')
        print(f"📊 عدد الأسطر الأصلي: {len(lines)}")
        
        # المرحلة 1: إزالة الترويسات والتذييلات المتكررة
        lines = self._remove_headers_footers(lines)
        print(f"✅ بعد إزالة الترويسات والتذييلات: {len(lines)} سطر")
        
        # المرحلة 2: إزالة التكرار المباشر
        lines = self._remove_exact_duplicates(lines)
        print(f"✅ بعد إزالة التكرار المباشر: {len(lines)} سطر")
        
        # المرحلة 3: إزالة التكرار الضبابي (Fuzzy)
        lines = self._remove_fuzzy_duplicates(lines)
        print(f"✅ بعد إزالة التكرار الضبابي: {len(lines)} سطر")
        
        # المرحلة 4: تنظيف أرقام الصفحات المكررة
        lines = self._clean_page_numbers(lines)
        print(f"✅ بعد تنظيف أرقام الصفحات: {len(lines)} سطر")
        
        # المرحلة 5: إزالة الفهارس (النقاط المتعددة)
        lines = self._remove_toc_lines(lines)
        print(f"✅ بعد إزالة الفهارس: {len(lines)} سطر")
        
        # المرحلة 6: تنظيف الحواشي المدمجة
        lines = self._clean_footnotes(lines)
        print(f"✅ بعد تنظيف الحواشي: {len(lines)} سطر")
        
        # المرحلة 7: إزالة الأسطر القصيرة جداً أو الفارغة
        lines = self._remove_short_lines(lines)
        print(f"✅ بعد إزالة الأسطر القصيرة: {len(lines)} سطر")
        
        # المرحلة 8: إصلاح المسافات والتنسيق
        lines = self._fix_spacing(lines)
        print(f"✅ بعد إصلاح المسافات: {len(lines)} سطر")
        
        # المرحلة 9: دمج الفقرات المكسورة
        text = '\n'.join(lines)
        text = self._merge_broken_paragraphs(text)
        lines = text.split('\n')
        print(f"✅ بعد دمج الفقرات: {len(lines)} سطر")
        
        # المرحلة 10: تنظيف نهائي للأسطر الفارغة الزائدة
        lines = self._clean_empty_lines(lines)
        print(f"✅ التنظيف النهائي: {len(lines)} سطر")
        
        return '\n'.join(lines)
    
    def _remove_headers_footers(self, lines: list) -> list:
        """إزالة الترويسات والتذييلات المتكررة"""
        
        cleaned = []
        
        for line in lines:
            line_stripped = line.strip()
            
            # تحقق من الأنماط الشائعة
            is_header_footer = False
            for pattern in self.common_headers_footers:
                if re.search(pattern, line_stripped, re.IGNORECASE):
                    is_header_footer = True
                    break
            
            # احتفظ بالسطر فقط إذا لم يكن ترويسة أو تذييل
            if not is_header_footer:
                cleaned.append(line)
        
        return cleaned
    
    def _remove_exact_duplicates(self, lines: list) -> list:
        """إزالة الأسطر المكررة بشكل مباشر متتالية"""
        
        cleaned = []
        prev_line = None
        
        for line in lines:
            line = line.strip()
            
            # لا تضيف السطر إذا كان مطابق تماماً للسطر السابق
            if line != prev_line:
                cleaned.append(line)
                prev_line = line
        
        return cleaned
    
    def _remove_fuzzy_duplicates(self, lines: list) -> list:
        """إزالة الأسطر المتشابهة جداً (>90%)"""
        
        cleaned = []
        prev_line = None
        
        for line in lines:
            if not line.strip():
                continue
            
            # قارن مع السطر السابق
            if prev_line:
                similarity = SequenceMatcher(None, line, prev_line).ratio()
                
                # إذا كان التشابه أكثر من 90%، تجاهل السطر
                if similarity >= self.similarity_threshold:
                    continue
            
            cleaned.append(line)
            prev_line = line
        
        return cleaned
    
    def _clean_page_numbers(self, lines: list) -> list:
        """إزالة أرقام الصفحات المكررة والمشوهة"""
        
        cleaned = []
        
        # Patterns لأرقام الصفحات المشوهة
        page_number_patterns = [
            r'^[\u0660-\u0669]{2,4}\s+[\u0660-\u0669]{2,4}$',  # ٥١٥١ ٥١٥١
            r'^[\u0660-\u0669]{3,}$',  # ٣٠٢٣٠٢
            r'^\d{3,}$',  # 302302
            r'^[\u0660-\u0669]{1,3}$',  # أرقام عربية منفردة قصيرة
            r'^\d+-\d+$',  # أرقام مثل 1-85
            r'^\d+$',  # أرقام منفردة
            r'^[\u0660-\u0669]+\s*-\s*[\u0660-\u0669]+$',  # ١-٨٥
        ]
        
        for line in lines:
            line_stripped = line.strip()
            
            # تحقق من جميع الـ patterns
            is_page_number = False
            for pattern in page_number_patterns:
                if re.match(pattern, line_stripped):
                    is_page_number = True
                    break
            
            # احتفظ بالسطر فقط إذا لم يكن رقم صفحة
            if not is_page_number:
                cleaned.append(line)
        
        return cleaned
    
    def _remove_toc_lines(self, lines: list) -> list:
        """إزالة أسطر الفهرس (التي تحتوي على نقاط متعددة)"""
        
        cleaned = []
        
        for line in lines:
            # إذا كان السطر يحتوي على 5 نقاط متتالية أو أكثر، احذفه
            if not re.search(r'\.{5,}', line):
                cleaned.append(line)
        
        return cleaned
    
    def _clean_footnotes(self, lines: list) -> list:
        """تنظيف الحواشي السفلية المدمجة"""
        
        cleaned = []
        
        # Pattern للحواشي: (1) أو .(١) أو مراجع مكررة
        footnote_pattern = r'\(\s*[\u0660-\u0669\d]+\s*\)|\.\(\s*[\u0660-\u0669\d]+\s*\)'
        
        for line in lines:
            # إزالة الحواشي المكررة من منتصف السطر
            line_cleaned = re.sub(footnote_pattern + r'\s*' + footnote_pattern, '', line)
            
            # إزالة أسطر تحتوي فقط على مراجع (مثل: .(٢٨٢ ٢٨٢) :ﺍﻵﻳﺔ)
            if re.match(r'^\s*[\.\(\)\s\u0660-\u0669\d:]+\s*$', line_cleaned):
                continue
            
            cleaned.append(line_cleaned)
        
        return cleaned
    
    def _remove_short_lines(self, lines: list) -> list:
        """إزالة الأسطر القصيرة جداً (أقل من 10 أحرف)"""
        
        cleaned = []
        
        for line in lines:
            # احتفظ فقط بالأسطر التي تحتوي على محتوى حقيقي
            if len(line.strip()) >= self.min_line_length:
                cleaned.append(line)
        
        return cleaned
    
    def _fix_spacing(self, lines: list) -> list:
        """إصلاح المسافات الزائدة"""
        
        cleaned = []
        
        for line in lines:
            # إزالة المسافات المتعددة
            line = re.sub(r'\s+', ' ', line)
            
            # إزالة المسافات من بداية ونهاية السطر
            line = line.strip()
            
            if line:
                cleaned.append(line)
        
        return cleaned
    
    def _merge_broken_paragraphs(self, text: str) -> str:
        """دمج الفقرات المكسورة - الأسطر التي لا تنتهي بعلامات ترقيم"""
        
        # دمج الأسطر إذا لم تنتهِ بنقطة أو فاصلة أو علامة استفهام أو تعجب أو نقطتين
        # ولكن احتفظ بالأسطر التي تنتهي بهذه العلامات كفواصل فقرات
        text = re.sub(r'([^\.\:\؛\!\?\n])\n', r'\1 ', text)
        
        # إصلاح المسافات المتعددة الناتجة عن الدمج
        text = re.sub(r' +', ' ', text)
        
        return text
    
    def _clean_empty_lines(self, lines: list) -> list:
        """تنظيف الأسطر الفارغة الزائدة - احتفظ بسطر فارغ واحد فقط بين الفقرات"""
        
        cleaned = []
        prev_empty = False
        
        for line in lines:
            is_empty = not line.strip()
            
            if is_empty:
                # أضف سطر فارغ واحد فقط
                if not prev_empty:
                    cleaned.append('')
                prev_empty = True
            else:
                cleaned.append(line)
                prev_empty = False
        
        return cleaned


def main():
    """نقطة الدخول الرئيسية"""
    
    if len(sys.argv) < 2:
        print("الاستخدام: python3 scripts/deep_text_cleaner.py <input_file.txt>")
        print("مثال: python3 scripts/deep_text_cleaner.py output/Shariaah-Standards-ARB_cleaned.txt")
        return 1
    
    input_path = Path(sys.argv[1])
    
    if not input_path.exists():
        print(f"❌ الملف غير موجود: {input_path}")
        return 1
    
    print("=" * 70)
    print("🧹 منظف النصوص المتقدم - Deep Text Cleaner v2.0")
    print("=" * 70)
    print()
    
    # قراءة الملف
    print(f"📖 قراءة الملف: {input_path}")
    with open(input_path, 'r', encoding='utf-8') as f:
        original_text = f.read()
    
    print(f"📊 حجم النص الأصلي: {len(original_text):,} حرف")
    print()
    
    # التنظيف
    cleaner = DeepTextCleaner()
    cleaned_text = cleaner.clean_text(original_text)
    
    print()
    print(f"📊 حجم النص النظيف: {len(cleaned_text):,} حرف")
    print(f"🎯 نسبة الضغط: {(1 - len(cleaned_text)/len(original_text)) * 100:.1f}%")
    print()
    
    # حفظ النتيجة
    output_path = input_path.parent / f"{input_path.stem}_ultra_clean.txt"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(cleaned_text)
    
    print(f"✅ تم الحفظ في: {output_path}")
    print()
    
    # إحصائيات إضافية
    print("=" * 70)
    print("📊 الإحصائيات النهائية")
    print("=" * 70)
    print(f"عدد الأحرف الأصلي: {len(original_text):,}")
    print(f"عدد الأحرف النظيف: {len(cleaned_text):,}")
    print(f"تم إزالة: {len(original_text) - len(cleaned_text):,} حرف")
    print(f"عدد الأسطر النهائية: {len(cleaned_text.split(chr(10))):,}")
    print()
    print("💡 الملف جاهز الآن للاستخدام مع Gemini File Search")
    print()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
