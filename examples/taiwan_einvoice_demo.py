"""
台灣電子發票 OCR 驗證範例

此腳本展示如何使用 OCR Pipeline 處理台灣電子發票影像
"""

import sys
from pathlib import Path
import cv2
import numpy as np

# 加入專案路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ocr_pipeline.core import Orchestrator
from ocr_pipeline.adapters.ocr import PaddleOCRAdapter
from ocr_pipeline.utils.image_utils import read_image, save_image


def visualize_roi_extraction(result: dict, output_dir: Path):
    """
    視覺化 ROI 提取結果
    
    Args:
        result: Orchestrator 處理結果
        output_dir: 輸出目錄
    """
    if "regions" not in result:
        print("⚠️  沒有找到 ROI 區域")
        return
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n📦 提取的 ROI 區域數量: {len(result['regions'])}")
    
    for region_name, roi_image in result["regions"].items():
        # 儲存 ROI 影像
        roi_path = output_dir / f"roi_{region_name}.jpg"
        save_image(roi_image, str(roi_path))
        print(f"  ✅ {region_name}: {roi_image.shape} -> {roi_path}")


def perform_ocr_on_regions(result: dict, ocr_adapter: PaddleOCRAdapter):
    """
    對提取的 ROI 區域執行 OCR
    
    Args:
        result: Orchestrator 處理結果
        ocr_adapter: OCR 適配器
    """
    if "regions" not in result:
        print("⚠️  沒有 ROI 區域可供 OCR")
        return {}
    
    print("\n🔍 執行 OCR 識別...")
    ocr_results = {}
    
    for region_name, roi_image in result["regions"].items():
        print(f"\n  處理區域: {region_name}")
        
        try:
            # 執行 OCR
            ocr_result = ocr_adapter.recognize(roi_image)
            print(f"    📊 原始結果數量: {len(ocr_result)}")
            
            # 提取文字和信心分數
            text_results = ocr_adapter.extract_text_with_confidence(ocr_result)
            
            if text_results:
                ocr_results[region_name] = text_results
                
                # 顯示識別結果
                for item in text_results:
                    print(f"    📝 文字: {item['text']}")
                    print(f"    📊 信心分數: {item['confidence']:.2%}")
            else:
                print(f"    ⚠️  未識別到文字")
                ocr_results[region_name] = []
                
        except Exception as e:
            print(f"    ❌ OCR 處理錯誤: {e}")
            import traceback
            traceback.print_exc()
            ocr_results[region_name] = []
    
    return ocr_results


def save_visualization(
    original_image: np.ndarray,
    result: dict,
    output_path: Path
):
    """
    儲存視覺化結果
    
    在原始影像上標註 ROI 區域
    
    Args:
        original_image: 原始影像
        result: 處理結果
        output_path: 輸出路徑
    """
    if "regions" not in result:
        return
    
    # 複製影像以避免修改原始資料
    vis_image = original_image.copy()
    
    # 在影像上繪製 ROI 邊界框
    # （這裡簡化處理，實際需要從模板取得座標）
    
    save_image(vis_image, str(output_path))
    print(f"\n💾 視覺化結果已儲存: {output_path}")


def test_template_modes():
    """測試兩種範本模式的實際 OCR 效果"""
    import json
    
    print("\n" + "=" * 70)
    print("📋 範本模式測試")
    print("=" * 70)
    
    # 測試 v2 範本（相對座標模式）
    print("\n測試 tw_einvoice_v2.json (相對座標模式)")
    print("-" * 70)
    
    template_path = project_root / "config/templates/tw_einvoice_v2.json"
    with open(template_path, 'r', encoding='utf-8') as f:
        template = json.load(f)
    
    print(f"✓ 載入範本: {template['template_id']}")
    print(f"✓ anchor.enable: {template['anchor']['enable']}")
    print(f"✓ anchor.text: {template['anchor']['text']}")
    
    # 載入影像
    sample_path = project_root / "data/samples/invoice_1.jpg"
    if sample_path.exists():
        image = read_image(str(sample_path))
        print(f"✓ 載入影像: {sample_path.name}, 尺寸: {image.shape}")
        
        # 初始化 OCR
        from ocr_pipeline.adapters.ocr.paddleocr_adapter import PaddleOCRAdapter
        ocr = PaddleOCRAdapter(config={"lang": template['ocr']['lang']}, min_confidence=0.6)
        
        # 執行全張 OCR
        print(f"\n執行全張 OCR...")
        raw_results = ocr.recognize(image)
        print(f"✓ 識別到 {len(raw_results)} 個文字區域")
        
        # 尋找 anchor
        anchor_text = template['anchor']['text']
        anchor_found = None
        
        for item in raw_results:
            bbox = item[0]
            text, confidence = item[1]
            
            if anchor_text in text:
                anchor_found = {
                    'text': text,
                    'bbox': bbox,
                    'confidence': confidence
                }
                break
        
        if anchor_found:
            print(f"\n✅ 找到 Anchor: {anchor_found['text']}")
            print(f"   位置: {anchor_found['bbox'][:2]}")
            print(f"   信心分數: {anchor_found['confidence']:.2%}")
        else:
            print(f"\n❌ 未找到 Anchor: {anchor_text}")
    
    # 測試 v1 範本（絕對座標模式）
    print("\n" + "-" * 70)
    print("測試 tw_einvoice_v1.json (絕對座標模式)")
    print("-" * 70)
    
    template_path = project_root / "config/templates/tw_einvoice_v1.json"
    with open(template_path, 'r', encoding='utf-8') as f:
        template = json.load(f)
    
    print(f"✓ 載入範本: {template['template_id']}")
    print(f"✓ anchor.enable: {template['anchor']['enable']}")
    print(f"✓ image_size: {template['image_size']}")
    
    if sample_path.exists():
        image = read_image(str(sample_path))
        expected_size = template['image_size']
        actual_size = [image.shape[1], image.shape[0]]
        
        if expected_size == actual_size:
            print(f"✅ 影像尺寸符合範本")
        else:
            print(f"⚠️  影像尺寸不符: 預期 {expected_size}, 實際 {actual_size}")
        
        print(f"\n定義的 ROI 區域:")
        for region in template['regions']:
            rect = region['rect']
            print(f"  - {region['name']}: rect={rect}, lang={region.get('ocr_lang', 'N/A')}")


def main(template_version="v1"):
    """
    主函數
    
    Args:
        template_version: 範本版本，"v1" 或 "v2"
    """
    print("=" * 60)
    print("🇹🇼 台灣電子發票 OCR 驗證範例")
    print("=" * 60)
    
    # 根據版本選擇範本
    if template_version.lower() == "v2":
        template_file = "tw_einvoice_v2.json"
        version_tag = "v2"
        print(f"\n📄 使用範本: {template_file} (相對座標 + Anchor)")
    else:
        template_file = "tw_einvoice_v1.json"
        version_tag = "v1"
        print(f"\n📄 使用範本: {template_file} (絕對座標)")
    
    # 設定路徑
    template_path = project_root / "config/templates" / template_file
    sample_dir = project_root / "data/samples"
    output_dir = project_root / "data/results"
    
    # 檢查模板檔案
    if not template_path.exists():
        print(f"❌ 模板檔案不存在: {template_path}")
        return
    
    # 載入範本 JSON
    import json
    with open(template_path, 'r', encoding='utf-8') as f:
        template_json = json.load(f)
    
    # 建立 PaddleOCR 適配器
    print("\n⚙️  初始化 PaddleOCR (繁體中文)...")
    try:
        # 取得 OCR 語言設定
        ocr_lang = template_json.get("ocr", {}).get("lang", "chinese_cht")
        
        ocr_adapter = PaddleOCRAdapter(config={
            "lang": ocr_lang,
            "use_angle_cls": True,
            "use_gpu": False
        })
        print("✅ PaddleOCR 初始化完成 (繁體中文模式)")
    except ImportError as e:
        print(f"❌ PaddleOCR 未安裝: {e}")
        print("\n請執行安裝命令:")
        print("  pip install paddlepaddle paddleocr")
        return
    
    # 建立 Orchestrator（提供 OCR adapter 以支援 anchor-based 範本）
    print("\n⚙️  初始化 Orchestrator...")
    orchestrator = Orchestrator(ocr_adapter=ocr_adapter)
    orchestrator.load_template(template_json)
    print("✅ 模板載入完成")
    
    # 尋找測試影像
    image_files = list(sample_dir.glob("*.jpg")) + list(sample_dir.glob("*.png"))
    
    if not image_files:
        print(f"\n⚠️  在 {sample_dir} 中沒有找到測試影像")
        print("\n請將電子發票影像放入 data/samples/ 目錄")
        print("支援格式: .jpg, .png")
        return
    
    print(f"\n📁 找到 {len(image_files)} 張測試影像")
    
    # 處理每張影像
    for idx, image_path in enumerate(image_files, 1):
        print("\n" + "=" * 60)
        print(f"📸 處理影像 {idx}/{len(image_files)}: {image_path.name}")
        print("=" * 60)
        
        try:
            # 讀取影像
            image = read_image(str(image_path))
            print(f"✅ 影像載入成功: {image.shape}")
            
            # 執行 Pipeline 處理
            print("\n⚙️  執行影像處理 Pipeline...")
            result = orchestrator.process(image)
            print("✅ Pipeline 處理完成")
            
            # 視覺化 ROI 提取（加入版本標籤）
            image_name = image_path.stem  # 取得檔名（不含副檔名）
            roi_output_dir = output_dir / f"{version_tag}_{image_name}_rois"
            visualize_roi_extraction(result, roi_output_dir)
            
            # 執行 OCR
            ocr_results = perform_ocr_on_regions(result, ocr_adapter)
            
            # 顯示彙總結果
            if ocr_results:
                print("\n" + "=" * 60)
                print("📋 OCR 識別結果彙總")
                print("=" * 60)
                for region_name, texts in ocr_results.items():
                    print(f"\n🏷️  {region_name}:")
                    for item in texts:
                        print(f"  • {item['text']} ({item['confidence']:.1%})")
            
        except Exception as e:
            print(f"❌ 處理失敗: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("✅ 所有影像處理完成！")
    print("=" * 60)
    print(f"\n📂 結果已儲存至: {output_dir}")


if __name__ == "__main__":
    import sys
    
    # 支援命令列參數選擇範本版本
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        
        if arg == "--test-modes":
            # 執行範本比較測試
            test_template_modes()
        elif arg in ["v1", "v2", "--v1", "--v2"]:
            # 執行指定版本的範本
            version = arg.replace("--", "")
            main(template_version=version)
        elif arg in ["--help", "-h"]:
            print("使用方法:")
            print("  python taiwan_einvoice_demo.py [選項]")
            print()
            print("選項:")
            print("  v1, --v1          使用 v1 範本 (絕對座標模式)")
            print("  v2, --v2          使用 v2 範本 (相對座標 + Anchor)")
            print("  --test-modes      執行範本比較測試")
            print("  --help, -h        顯示此說明")
            print()
            print("範例:")
            print("  python taiwan_einvoice_demo.py v1")
            print("  python taiwan_einvoice_demo.py v2")
            print("  python taiwan_einvoice_demo.py --test-modes")
        else:
            print(f"❌ 未知參數: {sys.argv[1]}")
            print("使用 --help 查看可用選項")
    else:
        # 預設使用 v1 範本
        main(template_version="v1")
