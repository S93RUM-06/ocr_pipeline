"""
簡單的 OCR 測試腳本

快速驗證 PaddleOCR 是否能正常工作
"""

import sys
from pathlib import Path
import cv2

# 加入專案路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ocr_pipeline.adapters.ocr import PaddleOCRAdapter
from ocr_pipeline.utils.image_utils import read_image

def main():
    """主函數"""
    print("=" * 60)
    print("🔍 PaddleOCR 快速測試")
    print("=" * 60)
    
    # 檢查測試影像
    sample_path = project_root / "data/samples/invoice_1.jpg"
    
    if not sample_path.exists():
        print(f"❌ 測試影像不存在: {sample_path}")
        return
    
    print(f"\n📸 載入影像: {sample_path.name}")
    
    # 讀取影像
    image = read_image(str(sample_path))
    print(f"✅ 影像載入成功: {image.shape}")
    
    # 建立 OCR 適配器
    print("\n⚙️  初始化 PaddleOCR (繁體中文)...")
    try:
        ocr_adapter = PaddleOCRAdapter(config={
            "lang": "chinese_cht",  # 繁體中文
            "use_angle_cls": True
        })
        print("✅ PaddleOCR 初始化完成 (繁體中文模式)")
    except Exception as e:
        print(f"❌ PaddleOCR 初始化失敗: {e}")
        return
    
    # 執行 OCR
    print("\n🔍 執行 OCR 識別...")
    try:
        result = ocr_adapter.recognize(image)
        print(f"✅ OCR 完成，識別到 {len(result) if result else 0} 個文字區域")
        
        # 顯示識別結果
        if result:
            print("\n📋 識別結果:")
            print("=" * 60)
            
            text_results = ocr_adapter.extract_text_with_confidence(result)
            for idx, item in enumerate(text_results, 1):
                print(f"{idx}. {item['text']}")
                print(f"   信心分數: {item['confidence']:.2%}")
                print(f"   位置: {item['bbox'][0]}")
                print()
        else:
            print("⚠️  未識別到任何文字")
        
    except Exception as e:
        print(f"❌ OCR 執行失敗: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("✅ 測試完成！")
    print("=" * 60)

if __name__ == "__main__":
    main()
