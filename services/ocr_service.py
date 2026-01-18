from paddleocr import PaddleOCR
from PIL import Image
import numpy as np
import io

ocr = PaddleOCR(
    ocr_version="PP-OCRv4",
    lang="ch",
    use_angle_cls=False,
    enable_mkldnn=False,
)

def extract_texts_from_uploadfiles(files):
    all_texts = []

    for file in files:
        image = Image.open(io.BytesIO(file)).convert("RGB")
        img_np = np.array(image)

        try:
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