"""
Generate sample images for testing OCR
Run this script to create sample document images in the samples/ directory
"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path


def create_sample_document():
    """Create a sample document image"""
    width, height = 800, 1000
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)

    # Try to load a system font
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
        body_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
    except:
        title_font = ImageFont.load_default()
        body_font = ImageFont.load_default()

    # Title
    draw.text((50, 50), "SAMPLE BUSINESS DOCUMENT", fill='black', font=title_font)

    # Horizontal line
    draw.line([(50, 100), (750, 100)], fill='black', width=2)

    # Content
    content = [
        "Company Name: Tech Solutions Inc.",
        "Address: 789 Innovation Drive, Suite 100",
        "City: San Francisco, CA 94102",
        "Phone: (555) 987-6543",
        "",
        "Document Type: Technical Specification",
        "Reference: SPEC-2024-001",
        "Date: January 20, 2024",
        "",
        "INTRODUCTION",
        "This document outlines the technical specifications for",
        "the new product line. All measurements are in metric units.",
        "",
        "SPECIFICATIONS:",
        "- Dimensions: 15cm x 10cm x 5cm",
        "- Weight: 250 grams",
        "- Material: High-grade aluminum alloy",
        "- Color options: Silver, Black, Blue",
        "- Operating temperature: -10°C to 50°C",
        "",
        "QUALITY ASSURANCE",
        "All products undergo rigorous testing including:",
        "1. Stress testing",
        "2. Temperature cycling",
        "3. Quality inspection",
        "",
        "For more information, visit www.techsolutions.example",
    ]

    y = 130
    for line in content:
        draw.text((50, y), line, fill='black', font=body_font)
        y += 30

    return img


def create_sample_receipt():
    """Create a sample receipt image"""
    width, height = 600, 800
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)

    # Try to load a system font
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        body_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    except:
        title_font = ImageFont.load_default()
        body_font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    # Store name
    draw.text((200, 30), "GROCERY MART", fill='black', font=title_font)
    draw.text((180, 65), "123 Main Street", fill='black', font=small_font)
    draw.text((165, 85), "Anytown, ST 12345", fill='black', font=small_font)
    draw.text((190, 105), "Tel: 555-0123", fill='black', font=small_font)

    # Line
    draw.line([(50, 140), (550, 140)], fill='black', width=1)

    # Receipt details
    y = 160
    draw.text((50, y), "Date: 2024-01-20", fill='black', font=body_font)
    y += 25
    draw.text((50, y), "Time: 14:35:22", fill='black', font=body_font)
    y += 25
    draw.text((50, y), "Receipt #: 789456", fill='black', font=body_font)

    # Line
    y += 30
    draw.line([(50, y), (550, y)], fill='black', width=1)

    # Items
    items = [
        ("Bread                    ", "$  3.99"),
        ("Milk 2L                  ", "$  5.49"),
        ("Eggs (dozen)             ", "$  4.29"),
        ("Apples (1kg)             ", "$  6.99"),
        ("Coffee                   ", "$ 12.99"),
        ("Cereal                   ", "$  7.49"),
    ]

    y += 20
    for item, price in items:
        draw.text((50, y), item, fill='black', font=body_font)
        draw.text((450, y), price, fill='black', font=body_font)
        y += 25

    # Line
    y += 10
    draw.line([(50, y), (550, y)], fill='black', width=1)

    # Totals
    y += 20
    draw.text((350, y), "Subtotal:", fill='black', font=body_font)
    draw.text((450, y), "$ 41.24", fill='black', font=body_font)

    y += 25
    draw.text((350, y), "Tax (8%):", fill='black', font=body_font)
    draw.text((450, y), "$  3.30", fill='black', font=body_font)

    y += 30
    draw.text((350, y), "TOTAL:", fill='black', font=title_font)
    draw.text((450, y), "$ 44.54", fill='black', font=title_font)

    # Payment
    y += 50
    draw.text((50, y), "Payment Method: VISA ****1234", fill='black', font=small_font)
    y += 25
    draw.text((50, y), "Authorized: Yes", fill='black', font=small_font)

    # Footer
    y += 50
    draw.line([(50, y), (550, y)], fill='black', width=1)
    y += 20
    draw.text((150, y), "Thank you for shopping!", fill='black', font=body_font)
    y += 30
    draw.text((120, y), "Please come again soon!", fill='black', font=small_font)

    return img


if __name__ == "__main__":
    # Create samples directory if it doesn't exist
    samples_dir = Path("samples")
    samples_dir.mkdir(exist_ok=True)

    # Generate sample document
    print("Generating sample_document.png...")
    doc_img = create_sample_document()
    doc_img.save(samples_dir / "sample_document.png")
    print("✓ Created sample_document.png")

    # Generate sample receipt
    print("Generating sample_receipt.png...")
    receipt_img = create_sample_receipt()
    receipt_img.save(samples_dir / "sample_receipt.png")
    print("✓ Created sample_receipt.png")

    print("\nSample files created successfully!")
    print(f"Location: {samples_dir.absolute()}")
