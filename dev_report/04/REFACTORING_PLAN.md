# OCR Pipeline 重構計劃

> **Refactoring Plan v1.0**  
> 日期: 2025-12-23  
> 目標: 統一範本系統 + 實作多策略處理

---

## 🎯 重構目標

### 核心問題
1. ❌ **範本版本混亂**: v1 (絕對座標) / v2 (錨點) 並存
2. ❌ **策略單一**: 僅支援 ROI 方式，不適合無格線文檔
3. ❌ **缺少全圖 OCR 提取器**: 電子發票測試已證明必要性
4. ❌ **缺少對齊模組**: 有框文檔需要透視變換

### 重構目標
1. ✅ 統一 Template Schema v3 (支援多種策略)
2. ✅ 實作 FullImageExtractor (全圖 OCR + 正則匹配)
3. ✅ 實作 ProcessingStrategyRouter (自動選擇策略)
4. ✅ 向後相容 v1/v2 範本

---

## 📋 Phase 1: 核心重構 (2-3 週)

### Week 1: 全圖 OCR 提取器 ⭐⭐⭐

#### 1.1 建立 FullImageExtractor
**檔案**: `ocr_pipeline/core/extractors/full_image_extractor.py`

```python
"""
全圖 OCR + 正則匹配提取器
適用於無格線文檔 (發票、收據、合約等)
"""

from typing import Dict, List, Tuple, Optional
import re
from dataclasses import dataclass

@dataclass
class ExtractionCandidate:
    """提取候選結果"""
    text: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # (x, y, width, height)
    position_score: float  # 位置匹配分數
    total_score: float  # 綜合評分


class FullImageExtractor:
    """
    全圖 OCR + 正則匹配提取器
    
    工作流程:
    1. 全圖 OCR 獲取所有文字區塊
    2. 對每個欄位使用正則表達式匹配
    3. 使用 ROI 作為「搜尋提示」消除歧義
    4. 多重評分機制選擇最佳候選
    """
    
    def __init__(self, ocr_adapter, config: Optional[Dict] = None):
        self.ocr = ocr_adapter
        self.config = config or {
            'confidence_weight': 0.5,
            'position_weight': 0.3,
            'format_weight': 0.2,
            'position_tolerance': 0.3  # ROI 位置容錯範圍
        }
    
    def extract_fields(
        self, 
        image, 
        template: Dict,
        ocr_results: Optional[List] = None
    ) -> Dict[str, Dict]:
        """
        從全圖 OCR 結果中提取欄位
        
        Args:
            image: 影像 (ndarray)
            template: 範本定義 (必須包含 patterns 欄位)
            ocr_results: 預先執行的 OCR 結果 (可選)
        
        Returns:
            {
                'field_name': {
                    'text': '提取的文字',
                    'confidence': 0.95,
                    'bbox': (x, y, w, h),
                    'candidates': [...]  # 所有候選
                }
            }
        """
        # Step 1: 獲取全圖 OCR 結果
        if ocr_results is None:
            ocr_results = self.ocr.recognize(image)
        
        # Step 2: 轉換為絕對座標 (如果範本使用比例座標)
        img_h, img_w = image.shape[:2]
        absolute_regions = self._convert_template_to_absolute(
            template, (img_w, img_h)
        )
        
        # Step 3: 對每個欄位提取
        extracted = {}
        patterns = template.get('patterns', {})
        
        for field_name, field_config in patterns.items():
            candidates = self._find_candidates(
                ocr_results, 
                field_config,
                absolute_regions.get(field_name)
            )
            
            if candidates:
                best = max(candidates, key=lambda c: c.total_score)
                extracted[field_name] = {
                    'text': best.text,
                    'confidence': best.confidence,
                    'bbox': best.bbox,
                    'position_score': best.position_score,
                    'total_score': best.total_score,
                    'candidates': candidates
                }
            else:
                extracted[field_name] = None
        
        return extracted
    
    def _find_candidates(
        self, 
        ocr_results: List,
        field_config: Dict,
        roi_hint: Optional[Dict] = None
    ) -> List[ExtractionCandidate]:
        """
        尋找符合條件的候選結果
        
        Args:
            ocr_results: OCR 結果 [(bbox, (text, confidence)), ...]
            field_config: 欄位配置 {'pattern': r'...', 'required': True}
            roi_hint: ROI 位置提示 {'x': 100, 'y': 200, 'width': 300, 'height': 50}
        """
        pattern = field_config.get('pattern')
        if not pattern:
            return []
        
        regex = re.compile(pattern, re.UNICODE | re.IGNORECASE)
        candidates = []
        
        for bbox, (text, confidence) in ocr_results:
            # 正則匹配
            match = regex.search(text)
            if not match:
                continue
            
            # 提取匹配組
            extract_group = field_config.get('extract_group', 0)
            matched_text = match.group(extract_group) if extract_group > 0 else match.group(0)
            
            # 計算位置分數
            position_score = 1.0  # 預設滿分
            if roi_hint:
                position_score = self._calculate_position_score(bbox, roi_hint)
            
            # 計算格式分數
            format_score = self._calculate_format_score(
                matched_text, field_config
            )
            
            # 綜合評分
            total_score = (
                confidence * self.config['confidence_weight'] +
                position_score * self.config['position_weight'] +
                format_score * self.config['format_weight']
            )
            
            candidates.append(ExtractionCandidate(
                text=matched_text,
                confidence=confidence,
                bbox=bbox,
                position_score=position_score,
                total_score=total_score
            ))
        
        return sorted(candidates, key=lambda c: c.total_score, reverse=True)
    
    def _calculate_position_score(self, bbox, roi_hint) -> float:
        """
        計算位置匹配分數
        使用 IoU (Intersection over Union) 或中心點距離
        """
        # 計算 bbox 中心點
        bbox_center_x = bbox[0] + bbox[2] / 2
        bbox_center_y = bbox[1] + bbox[3] / 2
        
        # 計算 ROI 中心點
        roi_center_x = roi_hint['x'] + roi_hint['width'] / 2
        roi_center_y = roi_hint['y'] + roi_hint['height'] / 2
        
        # 計算正規化距離
        roi_size = max(roi_hint['width'], roi_hint['height'])
        distance = (
            ((bbox_center_x - roi_center_x) ** 2 +
             (bbox_center_y - roi_center_y) ** 2) ** 0.5
        )
        
        normalized_distance = distance / roi_size
        tolerance = self.config['position_tolerance']
        
        # 距離越近分數越高
        if normalized_distance <= tolerance:
            return 1.0 - (normalized_distance / tolerance) * 0.5
        else:
            return 0.5 * (1.0 / (1.0 + normalized_distance))
    
    def _calculate_format_score(self, text: str, field_config: Dict) -> float:
        """計算格式匹配分數"""
        score = 1.0
        
        # 檢查預期長度
        expected_length = field_config.get('expected_length')
        if expected_length:
            length_diff = abs(len(text) - expected_length)
            score -= min(length_diff * 0.1, 0.5)
        
        # 檢查數據類型
        data_type = field_config.get('data_type', 'string')
        if data_type == 'number' and not text.replace(',', '').replace('.', '').isdigit():
            score -= 0.3
        
        return max(score, 0.0)
    
    def _convert_template_to_absolute(
        self, 
        template: Dict, 
        image_size: Tuple[int, int]
    ) -> Dict:
        """
        將範本比例座標轉換為絕對像素座標
        
        Args:
            template: 範本定義
            image_size: (width, height)
        
        Returns:
            {'field_name': {'x': 100, 'y': 200, 'width': 300, 'height': 50}}
        """
        img_w, img_h = image_size
        absolute_regions = {}
        
        regions = template.get('regions', {})
        for field_name, field_def in regions.items():
            rect_ratio = field_def.get('rect_ratio')
            if not rect_ratio:
                continue
            
            absolute_regions[field_name] = {
                'x': int(rect_ratio['x'] * img_w),
                'y': int(rect_ratio['y'] * img_h),
                'width': int(rect_ratio['width'] * img_w),
                'height': int(rect_ratio['height'] * img_h)
            }
        
        return absolute_regions
```

#### 1.2 建立單元測試
**檔案**: `tests/test_full_image_extractor.py`

```python
import pytest
from ocr_pipeline.core.extractors.full_image_extractor import (
    FullImageExtractor, ExtractionCandidate
)

class MockOCRAdapter:
    """Mock OCR 適配器用於測試"""
    def recognize(self, image):
        # 模擬電子發票 OCR 結果
        return [
            ((100, 50, 200, 30), ('VJ-50215372', 0.985)),
            ((100, 100, 150, 25), ('114年12-23', 0.920)),
            ((250, 200, 100, 25), ('隨機碼: 3472', 0.986)),
            ((100, 300, 120, 25), ('總計: $1,250', 0.945))
        ]

def test_extract_invoice_fields():
    """測試電子發票欄位提取"""
    ocr = MockOCRAdapter()
    extractor = FullImageExtractor(ocr)
    
    template = {
        'patterns': {
            'invoice_number': {
                'pattern': r'[A-Z]{2}-\d{8}',
                'extract_group': 0,
                'data_type': 'string',
                'expected_length': 11
            },
            'random_code': {
                'pattern': r'隨機碼[:：]\s*(\d{4})',
                'extract_group': 1,
                'data_type': 'number',
                'expected_length': 4
            },
            'total_amount': {
                'pattern': r'總計[:：]\s*\$?\s*([\d,]+)',
                'extract_group': 1,
                'data_type': 'number'
            }
        },
        'regions': {}  # 不使用 ROI 提示
    }
    
    import numpy as np
    fake_image = np.zeros((600, 400, 3), dtype=np.uint8)
    
    results = extractor.extract_fields(fake_image, template)
    
    # 驗證結果
    assert results['invoice_number']['text'] == 'VJ-50215372'
    assert results['invoice_number']['confidence'] == 0.985
    
    assert results['random_code']['text'] == '3472'
    assert results['random_code']['confidence'] == 0.986
    
    assert results['total_amount']['text'] == '1,250'
    assert results['total_amount']['confidence'] == 0.945

def test_position_hint_scoring():
    """測試位置提示評分機制"""
    ocr = MockOCRAdapter()
    extractor = FullImageExtractor(ocr)
    
    template = {
        'patterns': {
            'invoice_number': {
                'pattern': r'[A-Z]{2}-\d{8}'
            }
        },
        'regions': {
            'invoice_number': {
                'rect_ratio': {
                    'x': 0.25, 'y': 0.083, 'width': 0.5, 'height': 0.05
                }
            }
        }
    }
    
    fake_image = np.zeros((600, 400, 3), dtype=np.uint8)
    results = extractor.extract_fields(fake_image, template)
    
    # 位置接近 ROI 提示應該有更高分數
    assert results['invoice_number']['position_score'] > 0.7
```

---

### Week 2: Template Schema v3 + 策略路由器 ⭐⭐

#### 2.1 更新 Template Schema
**檔案**: `config/schemas/template-v3.0.json`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "OCR Template Schema v3.0",
  "description": "統一支援多種處理策略的範本格式",
  
  "required": [
    "template_id",
    "version",
    "processing_strategy",
    "extraction_method"
  ],
  
  "properties": {
    "processing_strategy": {
      "type": "string",
      "enum": [
        "full_ocr_matching",      // 全圖 OCR + 正則匹配 (無格線文檔)
        "grid_correction_roi",    // 對齊矯正 + 固定 ROI (有格線文檔)
        "hybrid"                  // 混合策略
      ],
      "description": "處理策略類型"
    },
    
    "extraction_method": {
      "type": "string",
      "enum": ["regex_pattern", "fixed_roi", "hybrid"],
      "description": "提取方法"
    },
    
    "patterns": {
      "type": "object",
      "description": "正則表達式模式 (extraction_method=regex_pattern 時必需)",
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
              "default": 0
            },
            "data_type": {
              "type": "string",
              "enum": ["string", "number", "date"]
            },
            "expected_length": {
              "type": "integer",
              "minimum": 1
            }
          }
        }
      }
    }
  }
}
```

#### 2.2 實作策略路由器
**檔案**: `ocr_pipeline/core/strategy_router.py`

```python
"""
處理策略路由器
根據範本配置自動選擇適當的處理流程
"""

from typing import Dict, Type
from abc import ABC, abstractmethod

class ProcessingStrategy(ABC):
    """處理策略抽象基類"""
    
    @abstractmethod
    def process(self, image, template: Dict, ocr_adapter) -> Dict:
        """執行處理流程"""
        pass


class FullOCRMatchingStrategy(ProcessingStrategy):
    """全圖 OCR + 正則匹配策略 (無格線文檔)"""
    
    def process(self, image, template: Dict, ocr_adapter) -> Dict:
        from ocr_pipeline.core.extractors.full_image_extractor import FullImageExtractor
        
        extractor = FullImageExtractor(ocr_adapter)
        return extractor.extract_fields(image, template)


class GridCorrectionROIStrategy(ProcessingStrategy):
    """對齊矯正 + 固定 ROI 策略 (有格線文檔)"""
    
    def process(self, image, template: Dict, ocr_adapter) -> Dict:
        # TODO: 實作對齊矯正流程
        # 1. ImageAligner.align_to_standard()
        # 2. ROIExtractor.extract_regions()
        # 3. OCR 處理每個 ROI
        raise NotImplementedError("GridCorrectionROI strategy not implemented yet")


class HybridStrategy(ProcessingStrategy):
    """混合策略"""
    
    def process(self, image, template: Dict, ocr_adapter) -> Dict:
        # TODO: 實作混合策略
        # 1. 先嘗試 full_ocr_matching
        # 2. 低信心欄位降級到 ROI 方式
        raise NotImplementedError("Hybrid strategy not implemented yet")


class ProcessingStrategyRouter:
    """處理策略路由器"""
    
    STRATEGIES: Dict[str, Type[ProcessingStrategy]] = {
        'full_ocr_matching': FullOCRMatchingStrategy,
        'grid_correction_roi': GridCorrectionROIStrategy,
        'hybrid': HybridStrategy
    }
    
    def route(self, template: Dict) -> ProcessingStrategy:
        """
        根據範本選擇處理策略
        
        Args:
            template: 範本定義
        
        Returns:
            ProcessingStrategy 實例
        """
        strategy_name = template.get('processing_strategy', 'auto')
        
        if strategy_name == 'auto':
            strategy_name = self._auto_detect(template)
        
        strategy_class = self.STRATEGIES.get(strategy_name)
        if not strategy_class:
            raise ValueError(f"Unknown strategy: {strategy_name}")
        
        return strategy_class()
    
    def _auto_detect(self, template: Dict) -> str:
        """
        自動檢測適合的策略
        
        規則:
        - 有 patterns 欄位 → full_ocr_matching
        - 有 standard_sample → grid_correction_roi
        - 都有 → hybrid
        """
        has_patterns = bool(template.get('patterns'))
        has_standard_sample = bool(template.get('standard_sample'))
        
        if has_patterns and not has_standard_sample:
            return 'full_ocr_matching'
        elif has_standard_sample and not has_patterns:
            return 'grid_correction_roi'
        elif has_patterns and has_standard_sample:
            return 'hybrid'
        else:
            # 降級到舊版 ROI 方式
            return 'grid_correction_roi'
```

---

### Week 3: 整合測試與範本遷移 ⭐

#### 3.1 更新 Orchestrator
**檔案**: `ocr_pipeline/core/orchestrator.py`

```python
# 在 Orchestrator 中整合策略路由器

from ocr_pipeline.core.strategy_router import ProcessingStrategyRouter

class Orchestrator:
    def __init__(self, config=None):
        self.config = config or {}
        self.strategy_router = ProcessingStrategyRouter()
        # ... 其他初始化
    
    def process(self, image, template_id: str):
        """
        處理流程
        1. 載入範本
        2. 選擇策略
        3. 執行處理
        """
        # 載入範本
        template = self.template_loader.load(template_id)
        
        # 選擇策略
        strategy = self.strategy_router.route(template)
        
        # 執行處理
        results = strategy.process(image, template, self.ocr_adapter)
        
        return results
```

#### 3.2 電子發票範本遷移
**檔案**: `config/templates/tw_einvoice_v3.json`

```json
{
  "template_id": "tw_einvoice_v3",
  "template_name": "台灣電子發票證明聯 v3.0",
  "version": "3.0.0",
  "created_at": "2025-12-23",
  
  "processing_strategy": "full_ocr_matching",
  "extraction_method": "regex_pattern",
  
  "sampling_metadata": {
    "sample_count": 2,
    "reference_size": {
      "width": 2163,
      "height": 1355,
      "unit": "pixel"
    }
  },
  
  "patterns": {
    "invoice_number": {
      "pattern": "[A-Z]{2}-\\d{8}",
      "extract_group": 0,
      "data_type": "string",
      "expected_length": 11,
      "required": true
    },
    "invoice_date": {
      "pattern": "(\\d{3})年(\\d{1,2})-(\\d{1,2})月",
      "extract_group": 0,
      "data_type": "date",
      "required": true
    },
    "seller_name": {
      "pattern": "賣方[:：]?\\s*(.+?)\\s+買方",
      "extract_group": 1,
      "data_type": "string",
      "required": false
    },
    "random_code": {
      "pattern": "隨機碼[:：]\\s*(\\d{4})",
      "extract_group": 1,
      "data_type": "number",
      "expected_length": 4,
      "required": true
    },
    "total_amount": {
      "pattern": "總計[:：]\\s*\\$?\\s*([\\d,]+)",
      "extract_group": 1,
      "data_type": "number",
      "required": true
    }
  },
  
  "regions": {
    "invoice_number": {
      "rect_ratio": {
        "x": 0.046, "y": 0.058, "width": 0.462, "height": 0.037
      }
    },
    "random_code": {
      "rect_ratio": {
        "x": 0.555, "y": 0.702, "width": 0.231, "height": 0.037
      }
    }
  }
}
```

---

## 📊 重構完成檢查清單

### Week 1
- [ ] FullImageExtractor 核心實作
- [ ] 單元測試 (≥90% 覆蓋率)
- [ ] 電子發票測試案例通過

### Week 2
- [ ] Template Schema v3.0 定義
- [ ] ProcessingStrategyRouter 實作
- [ ] 策略單元測試

### Week 3
- [ ] Orchestrator 整合策略路由器
- [ ] tw_einvoice_v3.json 範本遷移
- [ ] 端到端測試通過

---

## 🎯 成功指標

1. ✅ 電子發票提取準確率 ≥ 95%
2. ✅ 支援 v3 範本格式
3. ✅ 向後相容 v1/v2 範本
4. ✅ 測試覆蓋率 ≥ 85%
5. ✅ 文檔更新完整

---

## 📝 Phase 2 規劃 (後續)

- ImageAligner 模組 (有框文檔對齊)
- GridDetector 模組 (格線檢測)
- Python Validator 重建
- API 服務化

---

**製作人**: GitHub Copilot  
**審核狀態**: 待審核
