#!/usr/bin/env python3
"""驗證範本檔案與規格文件的一致性"""

import json
import sys
from pathlib import Path

# 加入專案路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ocr_pipeline.template.validator import TemplateValidator

def validate_templates():
    """驗證兩個範本檔案"""
    
    validator = TemplateValidator()
    
    # 載入範本
    v1_path = project_root / "config/templates/tw_einvoice_v1.json"
    v2_path = project_root / "config/templates/tw_einvoice_v2.json"
    
    with open(v1_path, 'r', encoding='utf-8') as f:
        v1_template = json.load(f)
    
    with open(v2_path, 'r', encoding='utf-8') as f:
        v2_template = json.load(f)
    
    print("=" * 70)
    print("範本檔案驗證報告")
    print("=" * 70)
    
    # 驗證 v1
    print("\n【tw_einvoice_v1.json - 絕對座標模式】")
    print("-" * 70)
    print(f"✓ template_id: {v1_template['template_id']}")
    print(f"✓ version: {v1_template['version']}")
    print(f"✓ anchor.enable: {v1_template['anchor']['enable']}")
    print(f"✓ 有 image_size: {'是' if 'image_size' in v1_template else '否'}")
    if 'image_size' in v1_template:
        print(f"  → image_size: {v1_template['image_size']}")
    print(f"✓ regions 數量: {len(v1_template['regions'])}")
    print(f"✓ regions[0] 定位方式: {'rect (絕對座標)' if 'rect' in v1_template['regions'][0] else 'relative_to_anchor (相對座標)'}")
    if 'rect' in v1_template['regions'][0]:
        print(f"  → rect: {v1_template['regions'][0]['rect']}")
    print(f"✓ regions[0] ocr_lang: {v1_template['regions'][0].get('ocr_lang', 'N/A')}")
    print(f"✓ 有全域 ocr 設定: {'是' if 'ocr' in v1_template else '否'}")
    
    try:
        validator.validate(v1_template)
        print("\n✅ 驗證結果: 通過")
    except Exception as e:
        print(f"\n❌ 驗證失敗: {e}")
        return False
    
    # 驗證 v2
    print("\n" + "=" * 70)
    print("\n【tw_einvoice_v2.json - 相對座標模式】")
    print("-" * 70)
    print(f"✓ template_id: {v2_template['template_id']}")
    print(f"✓ version: {v2_template['version']}")
    print(f"✓ anchor.enable: {v2_template['anchor']['enable']}")
    print(f"✓ anchor.text: {v2_template['anchor']['text']}")
    print(f"✓ anchor.expected_bbox: width={v2_template['anchor']['expected_bbox']['width']}, height={v2_template['anchor']['expected_bbox']['height']}")
    print(f"✓ regions 數量: {len(v2_template['regions'])}")
    print(f"✓ regions[0] 定位方式: {'rect (絕對座標)' if 'rect' in v2_template['regions'][0] else 'relative_to_anchor (相對座標)'}")
    if 'relative_to_anchor' in v2_template['regions'][0]:
        rel = v2_template['regions'][0]['relative_to_anchor']
        print(f"  → 相對位置: x={rel['x']}, y={rel['y']}, width={rel['width']}, height={rel['height']}")
    print(f"✓ 有全域 ocr 設定: {'是' if 'ocr' in v2_template else '否'}")
    if 'ocr' in v2_template:
        print(f"  → ocr.lang: {v2_template['ocr']['lang']}")
    
    try:
        validator.validate(v2_template)
        print("\n✅ 驗證結果: 通過")
    except Exception as e:
        print(f"\n❌ 驗證失敗: {e}")
        return False
    
    # 一致性檢查
    print("\n" + "=" * 70)
    print("\n【規格一致性檢查】")
    print("-" * 70)
    
    checks = [
        ("v1 使用絕對座標模式 (enable=false)", v1_template['anchor']['enable'] == False),
        ("v1 有 image_size 欄位", 'image_size' in v1_template),
        ("v1 regions 使用 rect", 'rect' in v1_template['regions'][0]),
        ("v1 regions 有 ocr_lang", 'ocr_lang' in v1_template['regions'][0]),
        ("v1 無全域 ocr 設定", 'ocr' not in v1_template),
        ("v2 使用相對座標模式 (enable=true)", v2_template['anchor']['enable'] == True),
        ("v2 有 anchor.text", 'text' in v2_template['anchor']),
        ("v2 有 anchor.expected_bbox", 'expected_bbox' in v2_template['anchor']),
        ("v2 regions 使用 relative_to_anchor", 'relative_to_anchor' in v2_template['regions'][0]),
        ("v2 有全域 ocr 設定", 'ocr' in v2_template),
        ("v2 ocr.lang 為 chinese_cht", v2_template.get('ocr', {}).get('lang') == 'chinese_cht'),
    ]
    
    all_pass = True
    for check_name, result in checks:
        status = "✅" if result else "❌"
        print(f"{status} {check_name}")
        if not result:
            all_pass = False
    
    print("\n" + "=" * 70)
    if all_pass:
        print("\n🎉 所有檢查通過！範本檔案與規格文件完全一致。")
    else:
        print("\n⚠️  部分檢查未通過，請檢查範本檔案。")
    
    return all_pass

if __name__ == "__main__":
    success = validate_templates()
    sys.exit(0 if success else 1)
