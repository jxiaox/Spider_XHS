"""Standalone OCR subprocess script.
Called by data_util.py via subprocess.run() to perform OCR on a single image.
This allows the parent process to truly kill OCR if it hangs, unlike threading
where PaddleOCR's C++ inference cannot be interrupted.

Usage: python ocr_subprocess.py <image_path>
Output: JSON string with OCR results to stdout.
"""
import sys
import json
import warnings
import logging
import os

# Suppress noisy PaddleOCR logs
warnings.filterwarnings("ignore")
logging.getLogger("ppocr").setLevel(logging.ERROR)
os.environ["DISABLE_MODEL_SOURCE_CHECK"] = "True"

def main():
    """Run OCR on the given image and print results as JSON to stdout."""
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No image path provided"}))
        sys.exit(1)
    
    img_path = sys.argv[1]
    if not os.path.exists(img_path):
        print(json.dumps({"error": f"File not found: {img_path}"}))
        sys.exit(1)
    
    try:
        from paddleocr import PaddleOCR
        ocr = PaddleOCR(use_angle_cls=True, lang="ch")
        res = ocr.ocr(img_path)
        
        if res and res[0]:
            ocr_item = res[0]
            # PaddleOCR v5: OCRResult with rec_texts key
            if hasattr(ocr_item, 'get') and 'rec_texts' in ocr_item:
                text_lines = [t for t in ocr_item['rec_texts'] if t.strip()]
            else:
                # Legacy format: list of [box, (text, score)]
                text_lines = []
                for line in ocr_item:
                    if line and len(line) >= 2:
                        text_lines.append(line[1][0])
            print(json.dumps({"texts": text_lines}, ensure_ascii=False))
        else:
            print(json.dumps({"texts": []}))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

if __name__ == "__main__":
    main()
