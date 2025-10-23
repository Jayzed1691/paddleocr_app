"""Quick test of OCR functionality"""
import sys
from pathlib import Path
from ocr_engine import OCREngine
from document_processor import DocumentProcessor

def test_basic_ocr():
    print("Testing PaddleOCR functionality...")
    
    # Initialize components
    print("1. Initializing OCR engine...")
    config = {'lang': 'en'}
    ocr_engine = OCREngine(config)
    print("   ✓ OCR engine initialized")
    
    # Test document processor
    print("2. Testing document processor...")
    doc_processor = DocumentProcessor()
    
    # Process sample text file
    sample_file = Path("samples/sample.txt")
    if sample_file.exists():
        print(f"   Processing {sample_file}...")
        images = doc_processor.process_file(sample_file)
        print(f"   ✓ Generated {len(images)} image(s)")
        
        # Run OCR
        print("3. Running OCR...")
        results = ocr_engine.process_images(images)
        print(f"   ✓ Processed {len(results)} page(s)")
        
        # Extract text
        print("4. Extracting text...")
        for i, result in enumerate(results, 1):
            text = ocr_engine.extract_text(result)
            print(f"   Page {i}: {len(text)} characters extracted")
            if text:
                print(f"   First 100 chars: {text[:100]}...")
        
        # Get statistics
        print("5. Getting statistics...")
        stats = ocr_engine.get_statistics(results)
        print(f"   Total pages: {stats['total_pages']}")
        print(f"   Total text blocks: {stats['total_text_blocks']}")
        print(f"   Total characters: {stats['total_characters']}")
        print(f"   Average confidence: {stats['average_confidence']:.2%}")
        
        print("\n✓ All tests passed successfully!")
        return True
    else:
        print(f"   ✗ Sample file not found: {sample_file}")
        return False

if __name__ == "__main__":
    try:
        success = test_basic_ocr()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
