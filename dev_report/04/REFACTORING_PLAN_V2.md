# OCR Pipeline 重構計劃 v2.0 (簡化版)

> **極簡重構策略**  
> 日期: 2025-12-23  
> **狀態**: ⚠️ 需要根據當前測試覆蓋率 (91%) 重新評估刪除範圍  
> 原則: **刪除未使用的程式碼，專注全圖 OCR 策略**

---

## ⚠️ 重要提醒

**當前專案狀態** (2025-12-23):
- ✅ 測試覆蓋率: 91% (798 statements, 75 missing)
- ✅ 測試數量: 181 個測試全部通過
- ✅ Pipeline.py 已在 Phase 2 刪除
- ⚠️ 本計劃的刪除清單需要重新評估

**建議**: 在執行任何刪除操作前，請先：
1. 查看最新的 [PROJECT_STATUS_REPORT.md](../../PROJECT_STATUS_REPORT.md)
2. 檢查各模組的測試覆蓋率
3. 確認哪些模組真正未被使用

---

## 🎯 核心原則

### ✂️ 大刀闊斧刪除
1. ❌ **Template v1/v2 完全捨棄** - 不相容，從零開始
2. ❌ **錨點定位器** - 全圖 OCR 不需要
3. ❌ **ROI 提取器** - 改用位置提示，不裁切
4. ❌ **複雜前置處理** - 只保留 OCR 必要的去噪/二值化
5. ❌ **複雜的範本系統** - 簡化為單一格式

### ✅ 極簡保留
1. ✅ **PaddleOCR 適配器** - 核心引擎
2. ✅ **基礎影像工具** - 讀取/轉換
3. ✅ **簡單預處理** - 去噪、二值化（可選）
4. ✅ **全圖提取器** - 新增核心模組

---

## 📋 重構計劃

### Phase 1: 大掃除 (1 天) 🧹

#### 1.1 刪除檔案清單 ⚠️ 需要重新評估

**⚠️ 警告**: 以下清單為初步規劃，需根據當前測試覆蓋率重新評估

```bash
# 刪除舊範本 (確認)
rm config/templates/invoice_v1.json
rm config/templates/receipt_v1.json
rm config/templates/tw_einvoice_v1.json
rm config/templates/tw_einvoice_v2.json

# 刪除舊 Schema (確認)
rm config/schemas/template-v1.0.json

# ⚠️ 以下模組需要重新評估是否刪除：

# anchor_locator.py - 檢查是否有測試覆蓋
# roi_extractor.py - 檢查是否有測試覆蓋

# ❌ 不建議刪除 (有測試覆蓋)：
# resize_normalize.py - 100% 覆蓋率，9 個測試
# deskew.py - 95% 覆蓋率，5 個測試
# loader.py - 88% 覆蓋率，8 個測試
# validator.py - 86% 覆蓋率，46 個測試

# ✅ 已刪除：
# pipeline.py - 已在 Phase 2 刪除
```

**建議步驟**:
1. 先使用 `grep -r "anchor_locator\|roi_extractor" tests/` 確認是否有測試
2. 檢查這些模組是否被其他 (根據當前測試覆蓋率更新)

```
ocr_pipeline/
├── adapters/
│   └── ocr/
│       └── paddleocr_adapter.py  ✅ 保留 (84% 覆蓋率)
├── core/
│   ├── steps/
│   │   ├── base.py              ✅ 保留 (91% 覆蓋率)
│   │   ├── denoise.py           ✅ 保留 (93% 覆蓋率)
│   │   ├── binarize.py          ✅ 保留 (96% 覆蓋率)
│   │   ├── deskew.py            ✅ 保留 (95% 覆蓋率，5 個測試) ⚠️ 原計劃刪除
│   │   └── resize_normalize.py  ✅ 保留 (100% 覆蓋率，9 個測試) ⚠️ 原計劃刪除
│   ├── extractors/
│   │   └── hybrid_extractor.py  ✅ 保留 (92% 覆蓋率)
│   └── orchestrator.py          ✅ 保留 (98% 覆蓋率) ⚠️ 不需要重寫
├── extractors/                  🆕 新增 (規劃中)
│   └── full_image_extractor.py
├── template/
│   ├── loader.py                ✅ 保留 (88% 覆蓋率，8 個測試)
│   └── validator.py             ✅ 保留 (86% 覆蓋率，46 個測試)
├── utils/
│   ├── image_utils.py           ✅ 保留 (90% 覆蓋率)
│   └── file_utils.py            ✅ 保留 (97% 覆蓋率)
└── __init__.py

注意：
- ❌ pipeline.py 已在 Phase 2 刪除
- ⚠️ orchestrator.py 已有 98% 覆蓋率，無需重寫，可擴展
- ⚠️ deskew.py 和 resize_normalize.py 有完整測試，建議保留
│   ├── image_utils.py           ✅ 保留
│   └── file_utils.py            ✅ 保留
└── __init__.py
```

---

### Phase 2: 建立新核心 (2-3 天) 🚀

#### 2.1 極簡 Template Schema

**檔案**: `config/schema.json`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "OCR Template Schema",
  "description": "極簡 OCR 範本格式 - 全圖 OCR + 位置提示",
  "type": "object",
  
  "required": ["template_id", "fields"],
  
  "properties": {
    "template_id": {
      "type": "string",
      "pattern": "^[a-z0-9_]+$"
    },
    
    "description": {
      "type": "string"
    },
    
    "preprocess": {
      "type": "object",
      "description": "前置處理選項（可選）",
      "properties": {
        "denoise": {
          "type": "boolean",
          "default": false
        },
        "binarize": {
          "type": "boolean",
          "default": false
        }
      }
    },
    
    "fields": {
      "type": "object",
      "description": "欄位定義",
      "patternProperties": {
        "^[a-z_][a-z0-9_]*$": {
          "type": "object",
          "required": ["pattern"],
          "properties": {
            "pattern": {
              "type": "string",
              "description": "正則表達式"
            },
            "extract_group": {
              "type": "integer",
              "minimum": 0,
              "default": 0,
              "description": "提取群組索引"
            },
            "position_hint": {
              "type": "object",
              "description": "位置提示（可選）- 用於消除歧義",
              "required": ["x", "y", "width", "height"],
              "properties": {
                "x": {"type": "number", "minimum": 0, "maximum": 1},
                "y": {"type": "number", "minimum": 0, "maximum": 1},
                "width": {"type": "number", "minimum": 0, "maximum": 1},
                "height": {"type": "number", "minimum": 0, "maximum": 1}
              }
            },
            "required": {
              "type": "boolean",
              "default": false
            }
          }
        }
      }
    }
  }
}
```

#### 2.2 極簡電子發票範本

**檔案**: `config/templates/tw_einvoice.json`

```json
{
  "template_id": "tw_einvoice",
  "description": "台灣電子發票證明聯",
  
  "preprocess": {
    "denoise": false,
    "binarize": false
  },
  
  "fields": {
    "invoice_number": {
      "pattern": "[A-Z]{2}-\\d{8}",
      "extract_group": 0,
      "position_hint": {
        "x": 0.046, "y": 0.058, "width": 0.462, "height": 0.037
      },
      "required": true
    },
    
    "invoice_date": {
      "pattern": "(\\d{3})年(\\d{1,2})-(\\d{1,2})月",
      "extract_group": 0,
      "position_hint": {
        "x": 0.038, "y": 0.022, "width": 0.481, "height": 0.044
      },
      "required": true
    },
    
    "random_code": {
      "pattern": "隨機碼[:：]\\s*(\\d{4})",
      "extract_group": 1,
      "position_hint": {
        "x": 0.555, "y": 0.702, "width": 0.231, "height": 0.037
      },
      "required": true
    },
    
    "total_amount": {
      "pattern": "總計[:：]\\s*\\$?\\s*([\\d,]+)",
      "extract_group": 1,
      "position_hint": {
        "x": 0.581, "y": 0.639, "width": 0.153, "height": 0.037
      },
      "required": true
    },
    
    "seller_tax_id": {
      "pattern": "賣方[:：]?\\s*(\\d{8})",
      "extract_group": 1,
      "required": false
    }
  }
}
```

#### 2.3 FullImageExtractor 實作

**檔案**: `ocr_pipeline/extractors/full_image_extractor.py`

```python
"""
全圖 OCR 提取器 - 極簡版
"""

import re
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class Match:
    """匹配結果"""
    text: str
    confidence: float
    bbox: Tuple[int, int, int, int]
    score: float  # 綜合評分


class FullImageExtractor:
    """
    全圖 OCR 提取器
    
    策略: 
    1. 對整張影像執行 OCR
    2. 用正則表達式匹配欄位
    3. 用位置提示消除歧義
    """
    
    def __init__(self, ocr_adapter):
        self.ocr = ocr_adapter
        self._ocr_cache = None  # 快取 OCR 結果
    
    def extract(
        self, 
        image: np.ndarray, 
        template: Dict
    ) -> Dict[str, Optional[Dict]]:
        """
        提取欄位
        
        Args:
            image: 影像 (H, W, 3)
            template: 範本定義
            
        Returns:
            {
                'field_name': {
                    'text': '提取的文字',
                    'confidence': 0.95,
                    'bbox': (x, y, w, h)
                } 或 None
            }
        """
        # Step 1: 執行全圖 OCR
        ocr_results = self._get_ocr_results(image)
        
        # Step 2: 提取各欄位
        img_h, img_w = image.shape[:2]
        fields = template.get('fields', {})
        
        extracted = {}
        for field_name, field_def in fields.items():
            matches = self._find_matches(
                ocr_results,
                field_def,
                (img_w, img_h)
            )
            
            if matches:
                # 選擇最佳匹配
                best = max(matches, key=lambda m: m.score)
                extracted[field_name] = {
                    'text': best.text,
                    'confidence': best.confidence,
                    'bbox': best.bbox,
                    'score': best.score
                }
            else:
                extracted[field_name] = None
        
        return extracted
    
    def _get_ocr_results(self, image: np.ndarray) -> List:
        """執行 OCR（帶快取）"""
        if self._ocr_cache is None:
            self._ocr_cache = self.ocr.recognize(image)
        return self._ocr_cache
    
    def _find_matches(
        self,
        ocr_results: List,
        field_def: Dict,
        image_size: Tuple[int, int]
    ) -> List[Match]:
        """
        尋找匹配結果
        
        Args:
            ocr_results: [(bbox, (text, confidence)), ...]
            field_def: {'pattern': '...', 'position_hint': {...}}
            image_size: (width, height)
        """
        pattern = field_def.get('pattern')
        if not pattern:
            return []
        
        regex = re.compile(pattern, re.UNICODE)
        extract_group = field_def.get('extract_group', 0)
        position_hint = field_def.get('position_hint')
        
        matches = []
        
        for bbox, (text, confidence) in ocr_results:
            # 正則匹配
            match = regex.search(text)
            if not match:
                continue
            
            # 提取文字
            matched_text = match.group(extract_group)
            
            # 計算評分
            score = confidence  # 基礎分數 = OCR 信心度
            
            if position_hint:
                # 有位置提示時，加入位置評分
                pos_score = self._calc_position_score(
                    bbox, position_hint, image_size
                )
                # 綜合評分: 信心度 70% + 位置 30%
                score = confidence * 0.7 + pos_score * 0.3
            
            matches.append(Match(
                text=matched_text,
                confidence=confidence,
                bbox=bbox,
                score=score
            ))
        
        return sorted(matches, key=lambda m: m.score, reverse=True)
    
    def _calc_position_score(
        self,
        bbox: Tuple[int, int, int, int],
        hint: Dict,
        image_size: Tuple[int, int]
    ) -> float:
        """
        計算位置匹配分數
        
        方法: 計算 bbox 中心與 hint 中心的距離
        """
        img_w, img_h = image_size
        
        # bbox 中心
        bbox_cx = bbox[0] + bbox[2] / 2
        bbox_cy = bbox[1] + bbox[3] / 2
        
        # hint 中心（絕對座標）
        hint_cx = (hint['x'] + hint['width'] / 2) * img_w
        hint_cy = (hint['y'] + hint['height'] / 2) * img_h
        
        # 計算距離（正規化）
        distance = (
            ((bbox_cx - hint_cx) ** 2 + (bbox_cy - hint_cy) ** 2) ** 0.5
        )
        
        # 正規化距離（以影像對角線長度為基準）
        diagonal = (img_w ** 2 + img_h ** 2) ** 0.5
        norm_distance = distance / diagonal
        
        # 轉換為分數（距離越近分數越高）
        # 距離 0 → 分數 1.0
        # 距離 0.1 → 分數 0.5
        # 距離 >= 0.2 → 分數 0.0
        if norm_distance < 0.1:
            return 1.0 - norm_distance * 5.0
        elif norm_distance < 0.2:
            return 0.5 - (norm_distance - 0.1) * 5.0
        else:
            return 0.0
    
    def clear_cache(self):
        """清除 OCR 快取"""
        self._ocr_cache = None
```

#### 2.4 極簡 Orchestrator

**檔案**: `ocr_pipeline/orchestrator.py`

```python
"""
極簡 OCR 編排器
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, Union, Optional

from .extractors.full_image_extractor import FullImageExtractor
from .core.steps import DenoiseStep, BinarizeStep
from .utils.image_utils import read_image


class Orchestrator:
    """
    極簡 OCR 編排器
    
    流程:
    1. 載入範本
    2. 可選前置處理（去噪/二值化）
    3. 全圖 OCR 提取
    """
    
    def __init__(self, ocr_adapter):
        """
        Args:
            ocr_adapter: PaddleOCR 適配器
        """
        if ocr_adapter is None:
            raise ValueError("ocr_adapter is required")
        
        self.ocr = ocr_adapter
        self.extractor = FullImageExtractor(ocr_adapter)
        self.template: Optional[Dict] = None
    
    def load_template(self, template_path: Union[str, Path, Dict]) -> None:
        """載入範本"""
        if isinstance(template_path, dict):
            self.template = template_path
        else:
            path = Path(template_path)
            with open(path, 'r', encoding='utf-8') as f:
                self.template = json.load(f)
    
    def process(self, image_input: Union[str, Path, np.ndarray]) -> Dict:
        """
        處理影像
        
        Args:
            image_input: 影像路徑或陣列
            
        Returns:
            {
                'fields': {...},
                'template_id': '...'
            }
        """
        if self.template is None:
            raise ValueError("No template loaded")
        
        # 載入影像
        if isinstance(image_input, (str, Path)):
            image = read_image(str(image_input))
        else:
            image = image_input
        
        # 前置處理（可選）
        image = self._preprocess(image)
        
        # 提取欄位
        fields = self.extractor.extract(image, self.template)
        
        # 清除快取
        self.extractor.clear_cache()
        
        return {
            'fields': fields,
            'template_id': self.template.get('template_id')
        }
    
    def _preprocess(self, image: np.ndarray) -> np.ndarray:
        """前置處理"""
        preprocess = self.template.get('preprocess', {})
        
        if preprocess.get('denoise', False):
            step = DenoiseStep(method='bilateral')
            image = step.process(image, {})
        
        if preprocess.get('binarize', False):
            step = BinarizeStep(method='adaptive')
            image = step.process(image, {})
        
        return image
```

---

### Phase 3: 測試與文檔 (1 天) ✅

#### 3.1 端到端測試

**檔案**: `tests/test_e2e.py`

```python
"""端到端測試"""

import pytest
from pathlib import Path
from ocr_pipeline.orchestrator import Orchestrator
from ocr_pipeline.adapters.ocr.paddleocr_adapter import PaddleOCRAdapter


@pytest.fixture
def orchestrator():
    """建立編排器"""
    ocr = PaddleOCRAdapter(lang='ch', use_gpu=False)
    return Orchestrator(ocr)


def test_taiwan_einvoice_extraction(orchestrator):
    """測試台灣電子發票提取"""
    # 載入範本
    template_path = Path(__file__).parent.parent / 'config/templates/tw_einvoice.json'
    orchestrator.load_template(template_path)
    
    # 處理影像
    image_path = Path(__file__).parent.parent / 'sample_images/invoice_1.png'
    result = orchestrator.process(image_path)
    
    # 驗證結果
    fields = result['fields']
    
    assert fields['invoice_number'] is not None
    assert fields['invoice_number']['text'].startswith('VJ-')
    
    assert fields['random_code'] is not None
    assert len(fields['random_code']['text']) == 4
    
    assert fields['total_amount'] is not None
    assert fields['total_amount']['confidence'] > 0.8


def test_missing_required_field(orchestrator):
    """測試缺少必要欄位"""
    template = {
        'template_id': 'test',
        'fields': {
            'nonexistent': {
                'pattern': 'XXXXXXXX',
                'required': True
            }
        }
    }
    orchestrator.load_template(template)
    
    # 應該返回 None
    result = orchestrator.process('sample_images/invoice_1.png')
    assert result['fields']['nonexistent'] is None
```

#### 3.2 更新 README

**檔案**: `README.md`

```markdown
# OCR Pipeline - 極簡全圖 OCR 方案

> 基於 PaddleOCR 的文件欄位提取工具  
> 策略: **全圖 OCR + 正則匹配 + 位置提示**

## ✨ 特性

- ✅ 全圖 OCR（無需裁切 ROI）
- ✅ 正則表達式匹配
- ✅ 位置提示消除歧義
- ✅ 極簡範本格式
- ✅ 高準確率（測試 95-100%）

## 🚀 快速開始

### 安裝

```bash
pip install -e .
```

### 使用範例

```python
from ocr_pipeline.orchestrator import Orchestrator
from ocr_pipeline.adapters.ocr.paddleocr_adapter import PaddleOCRAdapter

# 初始化
ocr = PaddleOCRAdapter(lang='ch')
orch = Orchestrator(ocr)

# 載入範本
orch.load_template('config/templates/tw_einvoice.json')

# 處理影像
result = orch.process('invoice.png')

# 取得結果
print(result['fields']['invoice_number']['text'])  # VJ-50215372
print(result['fields']['random_code']['text'])     # 3472
```

## 📋 範本格式

```json
{
  "template_id": "tw_einvoice",
  "fields": {
    "invoice_number": {
      "pattern": "[A-Z]{2}-\\d{8}",
      "position_hint": {
        "x": 0.046, "y": 0.058, 
        "width": 0.462, "height": 0.037
      },
      "required": true
    }
  }
}
```

## 🧪 測試

```bash
pytest tests/
```

## 📊 架構

```
影像輸入
   ↓
前置處理（可選）
   ↓
全圖 OCR
   ↓需要重新評估，初步 5-7 個檔案)
**確定刪除**:
- `config/templates/*.json` (舊範本 4 個)
- `config/schemas/template-v1.0.json`

**需確認是否刪除** (檢查引用和測試):
- `ocr_pipeline/core/steps/anchor_locator.py` (如有測試則保留)
- `ocr_pipeline/core/steps/roi_extractor.py` (如有測試則保留)
- `tests/test_anchor_template.py` (如存在)
- `tests/test_roi_extractor.py` (如存在)

**建議保留** (有測試覆蓋):
- ~~`ocr_pipeline/core/steps/resize_normalize.py`~~ - 100% 覆蓋率
- ~~`ocr_pipeline/core/steps/deskew.py`~~ - 95% 覆蓋率
- ~~`ocr_pipeline/template/loader.py`~~ - 88% 覆蓋率
- ~~`ocr_pipeline/template/validator.py`~~ - 86% 覆蓋率
- ~~`tes2-3 個檔案)
- `config/schema_v3.json` (新 Schema v3) 或擴展現有 validator
- `config/templates/tw_einvoice_v3.json` (新範本格式)
- `ocr_pipeline/core/extractors/full_image_extractor.py` ⭐ (核心新增)
- ~~`ocr_pipeline/orchestrator.py` (重寫)~~ → 改為擴展現有的 (98% 覆蓋率
**已刪除** (Phase 2):
- `ocr_pipeline/core/pipeline.py`
- `tests/test_pipeliner_locator.py`
- `ocr_pipeline/core/steps/roi_extractor.py`
- `ocr_pipeline/core/steps/resize_normalize.py`
- `ocr_pipeline/core/steps/deskew.py`
- `ocr_pipeline/template/loader.py`
- `ocr_pipeline/template/validator.py`
- `tests/test_anchor_template.py`
- `tests/test_roi_extractor.py`
- `tests/test_resize_normalize.py`
- `tests/test_deskew.py`
- `tests3-4 個檔案)
- `README.md` (更新文檔)
- `ocr_pipeline/core/orchestrator.py` (擴展以支援 FullImageExtractor)
- `tests/test_full_image_extractor.py` (新測試)
- `tests/test_e2e_einvoice.py` (端到端
### 新增 (4 個檔案)
- `config/schema.json` (極簡 Schema)
- `config/templates/tw_einvoice.json` (新範本)
- `ocr_pipeline/extractors/full_image_extractor.py` ⭐
- `ocr_pipeline/orchestrator.py` (重寫)

### 修改 (2 個檔案)
- `README.md` (重寫)
- `tests/test_e2e.py` (新測試)

### 保留 (8 個檔案)
- `ocr_pip (根據當前狀態調整)

| Phase | 工作 | 原估計 | 調整後 |
|-------|------|--------|--------|
| Phase 0 | 評估刪除範圍、確認未使用模組 | - | 0.5 天 |
| Phase 1 | 刪除確定未使用的檔案 | 0.5 天 | 0.25 天 |
| Phase 2 | 實作 FullImageExtractor | 2 天 | 2 天 |
| Phase 3 | 擴展 Orchestrator (不重寫) | - | 0.5 天 |
| Phase 4 | 測試與文檔 | 0.5 天 | 0.75 天 |
| **總計** | | **3 天** | **4 天** |

**說明**: 由於當前測試覆蓋率已達 91%，許多原計劃刪除的模組實際上有完整測試，需要更謹慎的評估。

---

## ⏱️ 時程估計

| Phase | 工作 | 時間 |
|-------|------|------|
| Phase 1 | 刪除舊檔案、清理專案 | 0.5 天 |
| Phase 2 | (根據當前狀態調整)

**Phase 0: 評估**
- [ ] 檢查 anchor_locator.py 和 roi_extractor.py 是否有測試
- [ ] 確認哪些範本檔案可以刪除
- [ ] 決定是否保留 template loader/validator (目前 86-88% 覆蓋率)

**Phase 1: 刪除**
- [ ] 刪除確定未使用的舊範本檔案 (*.json)
- [ ] 刪除舊 Schema (如適用)
- [ ] 刪除確認未使用的模組 (需先評估)

**Phase 2: 實作**
- [ ] 實作 FullImageExtractor 核心類別
- [ ] 建立 Template Schema v3 (或擴展現有 validator)
- [ ] 編寫 FullImageExtractor 單元測試

**Phase 3: 整合**
- [ ] 擴展 Orchestrator 支援 FullImageExtractor (不重寫)
- [ ] 創建電子發票 v3 範本
- [ ] 端到端測試通過

**Phase 4: 品質保證**
- [ ] README 更新
- [ ] 測試覆蓋率維持 ≥ 90% (當前 91%)
- [ ] 所有 181+ 測試通過
- [ ] 實作 FullImageExtractor
- [ ] 建立極簡範本格式
- [ ] 重寫 Orchestrator
- [ ] 端到端測試通過
- [ ] README 更新
- [ ] 測試覆蓋率 ≥ 80%

---

**製作**: GitHub Copilot  
**版本**: 2.0 (極簡重構)
