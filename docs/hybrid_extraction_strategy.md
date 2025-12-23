# 混合提取策略設計文件

> **Hybrid Extraction Strategy: Full-Image OCR + ROI Position Hints**  
> 創建日期：2025-12-23  
> 狀態：設計提案

---

## 📋 目錄

1. [背景與動機](#背景與動機)
2. [核心概念](#核心概念)
3. [架構設計](#架構設計)
4. [實作細節](#實作細節)
5. [模板配置](#模板配置)
6. [優勢分析](#優勢分析)
7. [實作建議](#實作建議)
8. [測試驗證](#測試驗證)

---

## 背景與動機

### 問題發現

在電子發票 OCR 測試中，我們發現了兩種提取策略的差異：

#### 策略 1：ROI 裁切 + OCR
```
固定座標裁切 → 小區域 OCR → 信心分數下降
```

**問題**：
- ❌ ROI 邊界包含上下行殘缺文字
- ❌ tolerance 擴展加劇多行干擾
- ❌ OCR 引擎「失焦」混淆
- ❌ 準確率從 98% 降至 74%

**實測數據**：
```
全圖 OCR: 隨機碼：3472 (98.6%)
ROI OCR:  4 (74.66%)  ← 只辨識到一個數字
```

#### 策略 2：全圖 OCR + 正則匹配
```
全圖 OCR → 正則表達式匹配 → 高準確率
```

**優勢**：
- ✅ 保留 OCR 文字檢測階段的精確性
- ✅ 每個文字區塊都是完整單行（無殘缺）
- ✅ 準確率 95-100%

**問題**：
- ⚠️ 可能匹配到多個候選（如發票上有多個數字）
- ⚠️ 無位置資訊輔助時難以區分同類型欄位

### 核心洞察

**PaddleOCR 的兩階段工作原理**：

```
階段 1: 文字檢測 (Detection)
  ↓
  使用 DBNet++ 模型精確定位每個文字區塊
  輸出：最小外接矩形 (bbox)，不包含其他行殘缺文字
  
階段 2: 文字辨識 (Recognition)  
  ↓
  對單一完整文字區塊進行辨識
  模型訓練就是針對「乾淨單行文字」優化
```

**結論**：  
ROI 裁切跳過了文字檢測階段，破壞了 OCR 引擎的優勢。  
**我們需要的是：充分利用全圖 OCR 的高準確率，同時用 ROI 作為位置提示來消除歧義。**

---

## 核心概念

### 混合策略流程

```
Step 1: 全圖 OCR（保留高準確率）
   ↓
   獲得所有文字區塊 + bbox + confidence
   結果：[(bbox, (text, confidence)), ...]
   
Step 2: ROI 作為「搜尋區域提示」
   ↓
   在指定區域內尋找符合正則的文字
   允許一定位置偏移（tolerance）
   
Step 3: 多重驗證策略
   ↓
   - OCR 信心分數（50%）
   - 位置接近度（30%）
   - 文字格式匹配（20%）
   ↓
   選擇總分最高的候選
```

### 關鍵設計原則

1. **全圖 OCR 優先**：永遠先做完整文字檢測和辨識
2. **ROI 是提示非限制**：用於縮小搜尋範圍，非強制裁切
3. **多重評分機制**：綜合考量信心分數、位置、格式
4. **降級策略**：ROI 內找不到 → 擴大範圍 → 全圖搜尋

---

## 架構設計

### 類別結構

```
HybridExtractor (混合提取器)
├── extract_fields()          # 主入口：全圖 OCR + 位置匹配
├── _find_in_region()         # 在 ROI 區域內搜尋
├── _select_best_match()      # 多重評分選擇最佳候選
├── _expand_roi()             # 擴展 ROI 容錯範圍
├── _is_in_area()            # 判斷 bbox 是否在區域內
├── _calc_distance()          # 計算 bbox 到 ROI 中心距離
└── _extract_with_fallback()  # 三層降級策略
```

### 資料流程

```python
Input:
  - image: 原始圖片
  - template: 包含 regions 配置的模板

Processing:
  1. ocr_results = ocr_adapter.recognize(image)
     → [(bbox, (text, conf)), ...]
  
  2. For each field in template['regions']:
     candidates = find_in_region(ocr_results, roi, pattern)
     → [{'text': ..., 'confidence': ..., 'bbox': ..., 'score': ...}]
  
  3. best_match = select_best_match(candidates)
     → {'text': 'VJ-50215372', 'confidence': 0.985, ...}

Output:
  {
    'invoice_number': {'text': 'VJ-50215372', 'confidence': 0.985, ...},
    'random_code': {'text': '3472', 'confidence': 0.986, ...},
    ...
  }
```

---

## 實作細節

### 主類別實作

```python
"""
ocr_pipeline/core/extractors/hybrid_extractor.py

混合提取器：結合全圖 OCR 高準確率與 ROI 位置提示
"""

import re
import math
from typing import List, Dict, Optional, Tuple

class HybridExtractor:
    """混合提取器：全圖 OCR + ROI 位置提示"""
    
    def __init__(self, ocr_adapter):
        """
        Args:
            ocr_adapter: OCR 適配器實例
        """
        self.ocr_adapter = ocr_adapter
    
    def extract_fields(self, image, template: Dict) -> Dict:
        """
        主提取邏輯
        
        Args:
            image: 輸入圖片 (numpy array)
            template: 模板配置，包含 regions 定義
            
        Returns:
            提取結果字典 {field_name: result_dict}
        """
        # Step 1: 全圖 OCR（保留高準確率）
        ocr_results = self.ocr_adapter.recognize(image)
        # ocr_results = [(bbox, (text, confidence)), ...]
        
        # Step 2: 使用 ROI 作為位置提示進行匹配
        extracted = {}
        
        for field_name, field_config in template.get('regions', {}).items():
            # 提取欄位配置
            roi = field_config.get('rect')  # ROI 位置提示區域
            pattern = field_config.get('pattern')  # 正則表達式
            extract_group = field_config.get('extract_group', 0)  # 提取組索引
            required = field_config.get('required', False)
            position_weight = field_config.get('position_weight', 0.3)
            
            # Step 3: 在 ROI 區域內尋找符合條件的文字
            candidates = self._find_in_region(
                ocr_results, 
                roi, 
                pattern,
                tolerance=0.2  # 允許 20% 位置偏移
            )
            
            # Step 4: 多重驗證選擇最佳候選
            if candidates:
                best_match = self._select_best_match(
                    candidates, 
                    field_config,
                    position_weight=position_weight
                )
                
                # 提取指定捕獲組
                if extract_group > 0 and best_match:
                    match = re.search(pattern, best_match['text'])
                    if match and len(match.groups()) >= extract_group:
                        best_match['text'] = match.group(extract_group)
                
                extracted[field_name] = best_match
            elif required:
                # 必填欄位找不到，嘗試降級策略
                extracted[field_name] = self._extract_with_fallback(
                    ocr_results, roi, pattern, field_config
                )
            else:
                extracted[field_name] = None
        
        return extracted
    
    def _find_in_region(
        self, 
        ocr_results: List, 
        roi: Dict, 
        pattern: Optional[str], 
        tolerance: float = 0.2
    ) -> List[Dict]:
        """
        在指定區域內尋找符合正則的文字
        
        Args:
            ocr_results: OCR 結果列表 [(bbox, (text, conf)), ...]
            roi: ROI 區域定義 {'x': int, 'y': int, 'width': int, 'height': int}
            pattern: 正則表達式（可選）
            tolerance: 容錯範圍比例（0.2 = 20%）
            
        Returns:
            候選列表 [{'text': str, 'confidence': float, 'bbox': list, 'distance': float}, ...]
        """
        if not roi:
            return []
        
        candidates = []
        
        # 擴展 ROI 容錯範圍
        search_area = self._expand_roi(roi, tolerance)
        
        for bbox, (text, confidence) in ocr_results:
            # 檢查 bbox 中心點是否在搜尋區域內
            if self._is_in_area(bbox, search_area):
                # 檢查文字是否符合正則
                if pattern:
                    if re.search(pattern, text):
                        candidates.append({
                            'text': text,
                            'confidence': confidence,
                            'bbox': bbox,
                            'distance_to_roi_center': self._calc_distance(bbox, roi)
                        })
                else:
                    # 沒有正則限制，直接加入
                    candidates.append({
                        'text': text,
                        'confidence': confidence,
                        'bbox': bbox,
                        'distance_to_roi_center': self._calc_distance(bbox, roi)
                    })
        
        return candidates
    
    def _select_best_match(
        self, 
        candidates: List[Dict], 
        field_config: Dict,
        position_weight: float = 0.3
    ) -> Optional[Dict]:
        """
        多重評分策略選擇最佳匹配
        
        評分權重：
        - OCR 信心分數：50%
        - 位置接近度：30% (可調整)
        - 文字長度匹配：20%
        
        Args:
            candidates: 候選列表
            field_config: 欄位配置
            position_weight: 位置權重（預設 0.3）
            
        Returns:
            最佳匹配候選或 None
        """
        if not candidates:
            return None
        
        confidence_weight = 0.5
        length_weight = 1.0 - confidence_weight - position_weight
        
        for candidate in candidates:
            score = 0.0
            
            # 1. OCR 信心分數
            score += candidate['confidence'] * confidence_weight
            
            # 2. 位置接近度
            max_distance = 200  # 最大容許距離（像素）
            distance = candidate['distance_to_roi_center']
            distance_score = max(0, 1 - distance / max_distance)
            score += distance_score * position_weight
            
            # 3. 文字長度匹配
            expected_length = field_config.get('expected_length')
            if expected_length:
                length_diff = abs(len(candidate['text']) - expected_length)
                length_score = max(0, 1 - length_diff / expected_length)
                score += length_score * length_weight
            else:
                score += length_weight  # 沒有長度限制，給滿分
            
            candidate['total_score'] = score
        
        # 返回總分最高的候選
        best = max(candidates, key=lambda x: x['total_score'])
        return best
    
    def _expand_roi(self, roi: Dict, tolerance: float) -> Dict:
        """
        擴展 ROI 容錯範圍
        
        Args:
            roi: 原始 ROI
            tolerance: 容錯比例
            
        Returns:
            擴展後的 ROI
        """
        expand_w = int(roi['width'] * tolerance)
        expand_h = int(roi['height'] * tolerance)
        
        return {
            'x': roi['x'] - expand_w,
            'y': roi['y'] - expand_h,
            'width': roi['width'] + 2 * expand_w,
            'height': roi['height'] + 2 * expand_h
        }
    
    def _is_in_area(self, bbox: List, area: Dict) -> bool:
        """
        判斷 bbox 中心點是否在指定區域內
        
        Args:
            bbox: 4 點座標 [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            area: 區域定義 {'x', 'y', 'width', 'height'}
            
        Returns:
            True 如果在區域內
        """
        # 計算 bbox 中心點
        center_x = sum(p[0] for p in bbox) / 4
        center_y = sum(p[1] for p in bbox) / 4
        
        # 判斷是否在區域內
        in_x = area['x'] <= center_x <= area['x'] + area['width']
        in_y = area['y'] <= center_y <= area['y'] + area['height']
        
        return in_x and in_y
    
    def _calc_distance(self, bbox: List, roi: Dict) -> float:
        """
        計算 bbox 中心點到 ROI 中心點的距離
        
        Args:
            bbox: 4 點座標
            roi: ROI 定義
            
        Returns:
            歐氏距離
        """
        # bbox 中心
        bbox_center_x = sum(p[0] for p in bbox) / 4
        bbox_center_y = sum(p[1] for p in bbox) / 4
        
        # ROI 中心
        roi_center_x = roi['x'] + roi['width'] / 2
        roi_center_y = roi['y'] + roi['height'] / 2
        
        # 歐氏距離
        distance = math.sqrt(
            (bbox_center_x - roi_center_x) ** 2 + 
            (bbox_center_y - roi_center_y) ** 2
        )
        
        return distance
    
    def _extract_with_fallback(
        self, 
        ocr_results: List, 
        roi: Dict, 
        pattern: str,
        field_config: Dict
    ) -> Optional[Dict]:
        """
        三層降級策略
        
        Args:
            ocr_results: OCR 結果
            roi: ROI 定義
            pattern: 正則表達式
            field_config: 欄位配置
            
        Returns:
            提取結果或 None
        """
        # Level 1: 標準 ROI + 正則（tolerance 0.2）
        result = self._find_in_region(ocr_results, roi, pattern, tolerance=0.2)
        if result:
            return self._select_best_match(result, field_config)
        
        # Level 2: 擴大 ROI 範圍（tolerance 加倍到 0.4）
        result = self._find_in_region(ocr_results, roi, pattern, tolerance=0.4)
        if result:
            return self._select_best_match(result, field_config)
        
        # Level 3: 全圖搜尋（最後手段，無位置限制）
        fallback_pattern = field_config.get('fallback_pattern', pattern)
        candidates = []
        
        for bbox, (text, confidence) in ocr_results:
            if re.search(fallback_pattern, text):
                candidates.append({
                    'text': text,
                    'confidence': confidence,
                    'bbox': bbox,
                    'distance_to_roi_center': float('inf')  # 無位置分數
                })
        
        if candidates:
            # 全圖搜尋只依賴信心分數
            return max(candidates, key=lambda x: x['confidence'])
        
        return None
```

---

## 模板配置

### 配置 Schema

```json
{
  "template_id": "tw_einvoice_hybrid_v1",
  "description": "台灣電子發票 - 混合提取策略",
  "version": "3.0",
  "processing_strategy": "hybrid_ocr_roi",
  
  "regions": {
    "invoice_number": {
      "rect": {
        "x": 163,
        "y": 957,
        "width": 967,
        "height": 192
      },
      "pattern": "[A-Z]{2}-\\d{8}",
      "expected_length": 11,
      "required": true,
      "position_weight": 0.3,
      "description": "發票號碼 (例: VJ-50215372)"
    },
    
    "invoice_date": {
      "rect": {
        "x": 125,
        "y": 768,
        "width": 1042,
        "height": 234
      },
      "pattern": "\\d{3}年\\d{1,2}-\\d{1,2}月",
      "expected_length": 10,
      "required": true,
      "position_weight": 0.25,
      "description": "開立日期 (例: 114年11-12月)"
    },
    
    "random_code": {
      "rect": {
        "x": 0,
        "y": 1208,
        "width": 554,
        "height": 117
      },
      "pattern": "隨機碼[:：]\\s*(\\d{4})",
      "extract_group": 1,
      "expected_length": 4,
      "required": true,
      "position_weight": 0.4,
      "fallback_pattern": "\\d{4}",
      "description": "隨機碼 (例: 3472)"
    },
    
    "total_amount": {
      "rect": {
        "x": 639,
        "y": 1205,
        "width": 365,
        "height": 125
      },
      "pattern": "總計\\s*(\\d+)",
      "extract_group": 1,
      "required": true,
      "position_weight": 0.3,
      "fallback_pattern": "\\d+$",
      "description": "總計金額 (提取數字部分)"
    },
    
    "seller_tax_id": {
      "rect": {
        "x": 0,
        "y": 1285,
        "width": 553,
        "height": 113
      },
      "pattern": "賣方(\\d{8})",
      "extract_group": 1,
      "expected_length": 8,
      "required": true,
      "position_weight": 0.35,
      "fallback_pattern": "\\d{8}",
      "description": "賣方統一編號 (提取 8 位數字)"
    },
    
    "buyer_tax_id": {
      "rect": {
        "x": 639,
        "y": 1285,
        "width": 365,
        "height": 113
      },
      "pattern": "買方(\\d{8})",
      "extract_group": 1,
      "expected_length": 8,
      "required": false,
      "position_weight": 0.35,
      "fallback_pattern": "\\d{8}",
      "description": "買方統一編號 (選填)"
    }
  }
}
```

### 配置欄位說明

| 欄位 | 類型 | 必填 | 說明 |
|-----|------|------|------|
| `rect` | Object | 是 | ROI 位置提示 (x, y, width, height) |
| `pattern` | String | 否 | 正則表達式（主要匹配模式） |
| `extract_group` | Integer | 否 | 提取捕獲組索引（0=完整匹配） |
| `expected_length` | Integer | 否 | 預期文字長度（用於評分） |
| `required` | Boolean | 否 | 是否必填（影響降級策略） |
| `position_weight` | Float | 否 | 位置權重 0-1（預設 0.3） |
| `fallback_pattern` | String | 否 | 降級策略的備用正則 |

---

## 優勢分析

### 對比表

| 特性 | 純 ROI 裁切 | 純正則匹配 | 混合策略 |
|-----|------------|-----------|---------|
| **OCR 準確率** | ❌ 低 (74%) | ✅ 高 (98%) | ✅ 高 (98%) |
| **位置容錯** | ❌ 固定座標 | ⚠️ 全圖搜尋慢 | ✅ 區域搜尋快 |
| **欄位區分能力** | ✅ 明確 | ⚠️ 可能重複 | ✅ 位置輔助區分 |
| **多行文字干擾** | ❌ 嚴重 | ✅ 無影響 | ✅ 無影響 |
| **適應格式變化** | ❌ 差 | ✅ 好 | ✅ 好 |
| **處理速度** | ⚠️ 中等 | ❌ 慢（全圖） | ✅ 快（區域） |
| **實作複雜度** | ✅ 簡單 | ✅ 簡單 | ⚠️ 中等 |

### 實際應用場景

#### 場景 1：發票號碼匹配

**問題**：發票上可能有多個號碼格式文字
```python
ocr_results = [
  (bbox1, ("VJ-50215372", 0.985)),  # 發票號碼
  (bbox2, ("AB-12345678", 0.972)),  # 其他編號（如訂單號）
  (bbox3, ("NO-98765432", 0.980)),  # 另一個編號
]
```

**混合策略處理**：
```python
# ROI 位置提示：只在 invoice_number 區域 (y=957±100) 搜尋
# pattern: [A-Z]{2}-\d{8}

candidates = find_in_region(ocr_results, roi, pattern)
# → 找到 bbox1 (VJ-50215372) 在區域內
# → 位置分數高 + 信心分數高
# → 自動選擇正確的發票號碼
```

#### 場景 2：金額提取

**問題**：發票上有多個數字
```python
ocr_results = [
  (bbox1, ("114", 0.99)),        # 年份
  (bbox2, ("11-12", 0.98)),      # 月份
  (bbox3, ("總計", 0.90)),       # 標籤
  (bbox4, ("20", 1.00)),         # 金額
  (bbox5, ("42552150", 0.987)),  # 統編
  (bbox6, ("3472", 0.986))       # 隨機碼
]
```

**混合策略處理**：
```python
# ROI 位置提示：total_amount 區域
# pattern: 總計\s*(\d+)
# extract_group: 1

# Step 1: 在 ROI 區域找到 bbox3 "總計" 和 bbox4 "20"
# Step 2: pattern 匹配 → 沒有直接匹配（"總計" 和 "20" 是分開的）
# Step 3: fallback_pattern: \d+$ → 找到 "20"
# Step 4: 位置在 ROI 內 → 確認為金額
```

#### 場景 3：統一編號區分

**問題**：賣方和買方統編格式相同
```python
ocr_results = [
  (bbox1, ("賣方42552150", 0.987)),  # 賣方統編 (y=1300)
  (bbox2, ("買方12345678", 0.982)),  # 買方統編 (y=1300)
]
```

**混合策略處理**：
```python
# seller_tax_id ROI: x=0, y=1285, width=553
# → bbox1 中心在 (276, 1341) → 在 ROI 內
# → 提取 "42552150"

# buyer_tax_id ROI: x=639, y=1285, width=365
# → bbox2 中心在 (821, 1341) → 在 ROI 內
# → 提取 "12345678"

# 位置資訊成功區分了相同格式的兩個欄位
```

---

## 實作建議

### 開發順序

#### Phase 1: 核心實作（1 週）
1. ✅ 實作 `HybridExtractor` 類別
2. ✅ 實作基本搜尋邏輯 (`_find_in_region`)
3. ✅ 實作評分機制 (`_select_best_match`)
4. ✅ 單元測試（模擬 OCR 結果）

#### Phase 2: 整合測試（3-5 天）
5. ✅ 電子發票模板轉換為 hybrid 格式
6. ✅ 真實樣本測試（invoice_1.png, invoice_2.jpg）
7. ✅ 準確率對比（vs 純 ROI, vs 純正則）
8. ✅ 調整評分權重優化

#### Phase 3: 擴展與優化（1 週）
9. ✅ 降級策略實作 (`_extract_with_fallback`)
10. ✅ 多文檔類型測試（收據、合約等）
11. ✅ 效能優化（區域索引、快取）
12. ✅ 文檔與範例

### 整合到 Pipeline

```python
# ocr_pipeline/core/orchestrator.py

class PipelineOrchestrator:
    def __init__(self, config):
        self.ocr_adapter = PaddleOCRAdapter(...)
        self.hybrid_extractor = HybridExtractor(self.ocr_adapter)
        self.roi_extractor = ROIExtractor()  # 保留舊方式
    
    def process(self, image, template):
        strategy = template.get('processing_strategy', 'auto')
        
        if strategy == 'hybrid_ocr_roi':
            # 使用混合策略
            return self.hybrid_extractor.extract_fields(image, template)
        
        elif strategy == 'fixed_roi':
            # 使用傳統 ROI 方式（適用有格線文檔）
            preprocessed = self.preprocess(image, template)
            rois = self.roi_extractor.extract(preprocessed, template)
            return self.ocr_adapter.recognize_rois(rois)
        
        else:
            # 自動判斷策略
            return self._auto_strategy(image, template)
```

### 測試驗證策略

```python
# tests/test_hybrid_extractor.py

import pytest
from ocr_pipeline.core.extractors.hybrid_extractor import HybridExtractor

class TestHybridExtractor:
    
    def test_find_in_region_basic(self):
        """測試基本區域搜尋"""
        mock_ocr_results = [
            ([[100, 100], [300, 100], [300, 150], [100, 150]], 
             ("VJ-50215372", 0.985)),
            ([[100, 500], [300, 500], [300, 550], [100, 550]], 
             ("AB-12345678", 0.972))
        ]
        
        roi = {'x': 80, 'y': 80, 'width': 250, 'height': 100}
        pattern = r'[A-Z]{2}-\d{8}'
        
        extractor = HybridExtractor(None)
        candidates = extractor._find_in_region(
            mock_ocr_results, roi, pattern, tolerance=0.2
        )
        
        assert len(candidates) == 1
        assert candidates[0]['text'] == "VJ-50215372"
    
    def test_select_best_match_by_position(self):
        """測試位置優先選擇"""
        candidates = [
            {
                'text': 'VJ-50215372',
                'confidence': 0.98,
                'bbox': [[100, 100], [300, 100], [300, 150], [100, 150]],
                'distance_to_roi_center': 10.0
            },
            {
                'text': 'AB-12345678',
                'confidence': 0.99,  # 信心分數更高
                'bbox': [[100, 500], [300, 500], [300, 550], [100, 550]],
                'distance_to_roi_center': 150.0  # 但位置較遠
            }
        ]
        
        extractor = HybridExtractor(None)
        field_config = {'expected_length': 11}
        
        best = extractor._select_best_match(
            candidates, field_config, position_weight=0.4
        )
        
        # 即使信心分數略低，但位置接近應該被選中
        assert best['text'] == 'VJ-50215372'
```

---

## 測試驗證

### 電子發票驗證計畫

#### 測試案例

| 欄位 | 全圖 OCR 基準 | 預期混合策略結果 |
|-----|--------------|----------------|
| invoice_number | VJ-50215372 (98.5%) | ✅ VJ-50215372 (98.5%) |
| invoice_date | 114年11-12月 (98.3%) | ✅ 114年11-12月 (98.3%) |
| random_code | 隨機碼：3472 (98.6%) → 提取 3472 | ✅ 3472 (98.6%) |
| total_amount | 總計 (90%) + 20 (100%) → 提取 20 | ✅ 20 (95%+) |
| seller_tax_id | 賣方42552150 (98.7%) → 提取 42552150 | ✅ 42552150 (98.7%) |
| buyer_tax_id | （無） | ⚠️ None（選填） |

#### 成功標準

1. **準確率目標**：所有欄位 ≥ 95%
2. **無降級觸發**：所有欄位在第一層（tolerance 0.2）內找到
3. **位置區分**：seller_tax_id 和 buyer_tax_id 正確區分
4. **格式提取**：extract_group 正確提取數字部分

### 效能測試

```python
import time

def benchmark_extraction():
    """效能基準測試"""
    
    # 測試 100 張發票
    images = load_test_images(100)
    template = load_template('tw_einvoice_hybrid_v1')
    
    # 方法 1: 純 ROI（參考）
    start = time.time()
    for img in images:
        result = roi_extractor.extract(img, template)
    roi_time = time.time() - start
    
    # 方法 2: 混合策略
    start = time.time()
    for img in images:
        result = hybrid_extractor.extract_fields(img, template)
    hybrid_time = time.time() - start
    
    print(f"純 ROI: {roi_time:.2f}s ({roi_time/100*1000:.1f}ms/張)")
    print(f"混合策略: {hybrid_time:.2f}s ({hybrid_time/100*1000:.1f}ms/張)")
    print(f"速度比: {hybrid_time/roi_time:.2f}x")
```

**預期結果**：
- 混合策略略慢於純 ROI（因為全圖 OCR）
- 但快於純正則全圖搜尋（因為區域過濾）
- 可接受範圍：單張 < 1 秒

---

## 附錄

### A. 權重調優指南

不同文檔類型建議的權重配置：

| 文檔類型 | 信心權重 | 位置權重 | 長度權重 | 說明 |
|---------|---------|---------|---------|------|
| **電子發票** | 0.5 | 0.3 | 0.2 | 平衡策略 |
| **身分證** | 0.4 | 0.4 | 0.2 | 位置更重要 |
| **收據** | 0.6 | 0.2 | 0.2 | 格式不固定，信心優先 |
| **合約** | 0.5 | 0.2 | 0.3 | 長度特徵明顯 |

### B. 常見問題排查

#### Q1: 某欄位總是匹配錯誤
**檢查清單**：
1. ROI 區域是否正確（用視覺化工具確認）
2. 正則表達式是否過於寬鬆
3. position_weight 是否太低
4. 是否需要 extract_group 提取部分文字

#### Q2: 必填欄位返回 None
**可能原因**：
1. OCR 未檢測到該文字（檢查原圖品質）
2. ROI 位置偏移過大（增加 tolerance）
3. 正則表達式過於嚴格（檢查 fallback_pattern）

#### Q3: 性能過慢
**優化建議**：
1. 減少 tolerance 範圍（減少候選數量）
2. 使用更精確的正則（減少匹配時間）
3. 考慮區域索引（預先分組 OCR 結果）

### C. 未來擴展方向

1. **語義理解**：整合 NLP 模型輔助欄位識別
2. **學習優化**：根據歷史結果自動調整權重
3. **多頁文檔**：跨頁欄位關聯
4. **版本容錯**：自動適應不同版本的發票格式

---

## 參考資料

- [PaddleOCR 官方文檔](https://github.com/PaddlePaddle/PaddleOCR)
- [DBNet++ 文字檢測論文](https://arxiv.org/abs/2202.10304)
- 專案測試報告：[dev_report/03/VERIFICATION_REPORT.md](../dev_report/03/VERIFICATION_REPORT.md)
- 電子發票測試數據：2025-12-23 測試會話

---

**文件維護者**: GitHub Copilot  
**最後更新**: 2025-12-23  
**審核狀態**: 待實作驗證
