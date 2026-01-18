from PIL import Image
import numpy as np
import io
import os
if os.getenv("DISABLE_OCR") == "1":
    raise RuntimeError("OCR disabled on cloud")

_ocr = None  # 👈 模块级只放“变量”，不放 Paddle 对象


def get_ocr():
    global _ocr
    if _ocr is None:
        from paddleocr import PaddleOCR  # ✅ 延迟 import
        _ocr = PaddleOCR(
            ocr_version="PP-OCRv4",
            lang="ch",
            use_angle_cls=False,
            enable_mkldnn=False,
            use_gpu=False,
        )
    return _ocr


def extract_texts_from_uploadfiles(files):
    ocr = get_ocr()  # ✅ 真正使用延迟加载

    all_texts = []

    for file in files:
        try:
            image = Image.open(io.BytesIO(file)).convert("RGB")
            img_np = np.array(image)

            result = ocr.ocr(img_np)

        except Exception:
            continue

        for block in result:
            for line in block:
                content = line[1]
                txt = content[0] if isinstance(content, (list, tuple)) else content
                if isinstance(txt, str):
                    txt = txt.strip()
                    if txt:
                        all_texts.append(txt)

    return all_texts
