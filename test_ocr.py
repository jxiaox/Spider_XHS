from paddleocr import PaddleOCR
import logging

# Suppress heavy logging
logging.getLogger("ppocr").setLevel(logging.ERROR)

try:
    ocr = PaddleOCR(use_angle_cls=True, lang="ch")
    print("Init successful")
    # Create a dummy image or use existing one?
    # I'll just try to call ocr with a non-existent path to check argument validation, or create a dummy image.
    # actually argument validation happens before file reading usually?
    # Let's use an existing image if possible, or just catch the error.
    
    # We need a real image path to pass `ocr`.
    # I'll check if there is any image in `datas/media_datas`
    import os
    img_path = ""
    # traverse to find an image
    for root, dirs, files in os.walk("datas/media_datas"):
        for file in files:
            if file.endswith(".jpg"):
                img_path = os.path.join(root, file)
                break
        if img_path: break
    
    if img_path:
        print(f"Testing with image: {img_path}")
        try:
            res = ocr.ocr(img_path, cls=True)
            print("OCR with cls=True successful")
        except Exception as e:
            print(f"OCR with cls=True failed: {e}")
            
        try:
            res = ocr.ocr(img_path, cls=False)
            print("OCR with cls=False successful")
        except Exception as e:
            print(f"OCR with cls=False failed: {e}")
            
        try:
            res = ocr.ocr(img_path)
            print("OCR without cls arg successful")
        except Exception as e:
            print(f"OCR without cls arg failed: {e}")

    else:
        print("No image found to test")

except Exception as e:
    print(f"Init failed: {e}")
