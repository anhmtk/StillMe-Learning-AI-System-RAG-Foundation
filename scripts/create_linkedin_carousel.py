"""
Script to create LinkedIn Carousel PDF from markdown template

This script helps combine all 8 slides into a single PDF file for LinkedIn posting.

Requirements:
- pip install markdown pypandoc reportlab
- OR use manual method (see template instructions)
"""

import os
import sys
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import markdown
        import pypandoc
        return True
    except ImportError:
        print("❌ Missing dependencies. Install with:")
        print("   pip install markdown pypandoc reportlab")
        return False

def create_pdf_from_markdown(markdown_file: str, output_pdf: str):
    """Convert markdown to PDF using pypandoc"""
    try:
        import pypandoc
        pypandoc.convert_file(
            markdown_file,
            'pdf',
            outputfile=output_pdf,
            extra_args=['--pdf-engine=xelatex', '--variable=geometry:margin=1in']
        )
        print(f"✅ PDF created: {output_pdf}")
        return True
    except Exception as e:
        print(f"❌ Error creating PDF: {e}")
        print("\n💡 Alternative: Use manual method (Canva/Design tool)")
        return False

def main():
    """Main function"""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    template_file = project_root / "docs" / "linkedin_carousel_template.md"
    output_pdf = project_root / "linkedin_carousel.pdf"
    
    if not template_file.exists():
        print(f"❌ Template file not found: {template_file}")
        return
    
    print("📄 LinkedIn Carousel PDF Generator")
    print("=" * 50)
    print(f"Template: {template_file}")
    print(f"Output: {output_pdf}")
    print()
    
    if not check_dependencies():
        print("\n💡 Manual Method:")
        print("   1. Open template in markdown editor")
        print("   2. Export each slide as image")
        print("   3. Combine in Canva/Design tool")
        print("   4. Export as PDF")
        return
    
    print("🔄 Converting markdown to PDF...")
    if create_pdf_from_markdown(str(template_file), str(output_pdf)):
        print(f"\n✅ Success! PDF created at: {output_pdf}")
        print("\n📋 Next Steps:")
        print("   1. Review PDF")
        print("   2. Add screenshots from dashboard (Slides 2, 7)")
        print("   3. Add code snippet screenshots (Slides 3-6)")
        print("   4. Add QR code (Slide 8)")
        print("   5. Upload to LinkedIn as Carousel")
    else:
        print("\n💡 If PDF creation failed, use manual method:")
        print("   - Canva: Create 8 slides, add content from template")
        print("   - Design tool: Import template, add screenshots")
        print("   - Export as PDF")

if __name__ == "__main__":
    main()








