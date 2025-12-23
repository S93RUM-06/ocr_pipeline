"""檢查圖片中是否包含錨點文字"""

import cv2
from ocr_pipeline.adapters.ocr.paddleocr_adapter import PaddleOCRAdapter

# 初始化 OCR
ocr_config = {
    "lang": "chinese_cht",
    "use_angle_cls": True
}
adapter = PaddleOCRAdapter(config=ocr_config, min_confidence=0.5)

# 讀取圖片
image_paths = [
    "data/samples/invoice_1.png",
    "data/samples/invoice_2.jpg"
]

for img_path in image_paths:
    print(f"\n{'='*60}")
    print(f"檢查圖片: {img_path}")
    print('='*60)
    
    image = cv2.imread(img_path)
    if image is None:
        print(f"❌ 無法載入圖片")
        continue
    
    print(f"✅ 圖片尺寸: {image.shape}")
    
    # 執行 OCR
    results = adapter.recognize(image)
    print(f"📊 識別到 {len(results)} 個文字區域\n")
    
    # 顯示所有文字及其完整座標
    anchor_found = False
    for i, item in enumerate(results, 1):
        text, confidence = item[1]
        bbox = item[0]
        
        # 計算矩形範圍
        x_coords = [p[0] for p in bbox]
        y_coords = [p[1] for p in bbox]
        x_min, x_max = int(min(x_coords)), int(max(x_coords))
        y_min, y_max = int(min(y_coords)), int(max(y_coords))
        width = x_max - x_min
        height = y_max - y_min
        
        # 檢查是否包含錨點文字
        marker = ""
        if "電子發票" in text or "證明聯" in text:
            marker = "🎯 "
            anchor_found = True
        
        print(f"{marker}[{i:2d}] {text} ({confidence*100:.1f}%)")
        print(f"     bbox: {bbox}")
        print(f"     rect: x={x_min}, y={y_min}, width={width}, height={height}")
        print()
    
    if not anchor_found:
        print("\n⚠️  未找到包含「電子發票」或「證明聯」的文字")
