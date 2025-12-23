# OCR Pipeline 重構計劃 v3.0 (激進版 - 已修正)

> **極簡重構策略 - 根據用戶原則重新制定**  
> 日期: 2025-12-23  
> **狀態**: ✅ 已修正 HybridExtractor 誤解  
> 原則: **沒有用的都先刪除，全圖 OCR 策略，不相容 v1/v2**

---

## 🎯 用戶核心原則

1. ✂️ **沒有用的都先刪除** - 不保留未使用的代碼
2. ❌ **不相容 v1/v2** - v3 從零開始，等於新的 v1
3. 👤 **個人專案** - 無向後相容需求
4. 🎯 **全圖 OCR 策略** - 不需要的前置處理直接刪除

---

## ⚠️ 重要修正

**HybridExtractor 是核心策略，不是舊代碼！**
- ✅ HybridExtractor = 全圖 OCR + ROI 位置提示（新概念）
- ✅ 這是專案的重點，必須保留
- ❌ 我之前誤解為舊策略，現已修正

---

## 📋 全圖 OCR 策略需求分析

### ✅ 真正需要的模組（核心保留）

```
核心模組：
├── PaddleOCR 適配器 (核心 OCR 引擎)
├── HybridExtractor ⭐ (全圖 OCR + 位置提示策略 - 專案重點)
├── Orchestrator (處理編排器)
├── 基礎影像工具 (讀取、儲存、轉換)
├── 檔案工具 (路徑處理)
└── 可選前置處理：
    ├── denoise (去噪 - 提高 OCR 準確率)
    └── binarize (二值化 - 提高 OCR 準確率)
```

### ✂️ 確定刪除（舊前置工具）

```
刪除理由：全圖 OCR 策略下無用的舊前置處理工具

1. ✂️ deskew.py - 舊前置工具，PaddleOCR 內建角度檢測
2. ✂️ resize_normalize.py - 舊前置工具，全圖 OCR 不需要固定尺寸
3. ✂️ template/loader.py - 被新概念簡化，直接用 json.load
4. ✂️ 所有舊範本 (v1/v2) - 不相容，已刪除
5. ✂️ 所有舊 Schema - 不相容
```

### ⚠️ 待處理（需同步 C# 驗證器）

```
不是刪除，而是需要與 roi_sample_tool 同步：
精確刪除清單（已修正）

### Phase 1: 刪除舊範本與 Schema

```bash
# 刪除舊範本（如果還存在）
rm config/templates/invoice_v1.json 2>/dev/null || true
rm config/templates/receipt_v1.json 2>/dev/null || true
rm config/templates/tw_einvoice_v1.json 2>/dev/null || true
rm config/templates/tw_einvoice_v2.json 2>/dev/null || true

# tw_einvoice_hybrid.json - 需確認是否為新格式
# 如果是舊格式才刪除

# 刪除舊 Schema
rm -rf config/schemas/ 2>/dev/null || true
```

### Phase 2: 刪除舊前置處理工具

```bash
# ✂️ 刪除舊前置處理步驟
rm ocr_pipeline/core/steps/deskew.py
rm ocr_pipeline/core/steps/resize_normalize.py
rm tests/test_deskew.py
rm tests/test_resize_normalize.py

# ✂️ 刪除被簡化的 loader
rm ocr_pipeline/template/loader.py
rm tests/test_template_loader.py
```

### Phase 3: 同步驗證器（不刪除）

```bash
# ⚠️ 不刪除，而是同步 C# 版本
# ocr_pipeline/template/validator.py - 保留
# tests/test_template_validator.py - 保留
# 
# TODO: 與 roi_sample_tool 的 C# 驗證器同步
```

### Phase 4: 更新模組導出

```bash
# 更新 __init__.py 移除已刪除模組的導出
# 更新 ocr_pipeline/core/steps/__init__.py
# - 移除 DeskewStep
# - 移除 ResizeNormalizeStep
```

### 刪除總結（修正後）
- **檔案總數**: 約 8 個檔案（不是 15 個）
- **程式碼減少**: 約 150-200 行（不是 400-500）
- **測試減少**: 約 22 個測試（9+5+8）
- **保留核心**: HybridExtractor + Orchestrator + validator
# 更新 __init__.py 移除已刪除模組的導出
# 更新 steps/__init__.py
# 更新 extractors/__init__.py
```需要建立的檔案（可選）

### 簡化範本載入（取代 loader.py）

**選項 1: 在 Orchestrator 中直接 json.load**
```python
# 不需要單獨的 loader.py
def load_template(self, template_path):
    with open(template_path, 'r', encoding='utf-8') as f:
        self.template = json.load(f)
```

**選項 2: 簡化的 loader（如需類型檢查）**
```bash
# 可選：建立極簡 loader（使用 dataclass）
ocr_pipeline/template/simple_loader.py  # 約 30 行
```

### 新範本格式（如需要）

```bash
# 根據需要建立新範本
config/templates/tw_einvoice_v3.json  # 新格式範本
# 新增全圖 OCR 提取器
ocr_pipeline/core/extractors/full_image_extractor.py
範本格式說明

**HybridExtractor 使用的範本格式**已經在 `tw_einvoice_hybrid.json` 中定義：

```json
{
  "template_id": "tw_einvoice_hybrid",
  "version": "3.0",
  "regions": {
    "invoice_number": {
      "rect_ratio": {...},  // ROI 位置提示
      "pattern": "...",      // 正則表達式
      "position_weight": 0.3
    }
  }
}
```

**特點**:
- ✅ HybridExtractor 已支援此格式
- ✅ rect_ratio 作為位置提示（不裁切）
- ✅ pattern 用於正則匹配
- ✅ position_weight 控制位置評分權重
- ⚠️ validator.py 需與 C# 版本同步
  }
}
```

**特點**:
- ✅ 無需 Schema 驗證器 (直接用 Python dataclass)
- ✅ 無需複雜的 Loader (直接 json.load)
- ✅ 每個欄位必須有 pattern
- ✅ position_hint 可選 (用於消除歧義)

---

## 🚀 Phase 2: 實作 FullImageExtractor (2 天)

### 核心實作

**檔案**: `ocr_pipeline/core/extractors/full_image_extractor.py`

```python
"""
全圖 OCR + 正則匹配提取器
適用於無格線文檔 (發票、收據、合約等)
"""

import re
import json
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class FieldConfig:
    """欄位配置"""
    pattern: str
    extract_group: int = 0
    position_hint: Optional[Dict] = None
    required: bool = False
✅ HybridExtractor 已實作（無需新建）

**HybridExtractor 已經實作了全圖 OCR + 位置提示策略**

核心功能（已存在）:
1. ✅ 全圖 OCR（一次性獲取所有文字）
2. ✅ 正則表達式匹配
3. ✅ ROI 作為位置提示（不裁切）
4. ✅ 多重評分機制（信心 50% + 位置 30% + 格式 20%）
5. ✅ 三層降級策略（ROI 內 → 擴展區域 → 全圖搜尋）

**參考**: `ocr_pipeline/core/extractors/hybrid_extractor.py` (454 lines)

**結論**: 不需要建立 FullImageExtractor，HybridExtractor 已包含所有功能     """處理影像"""
        # 讀取影像
        image = cv2.imread(image_path)
        
        # 可選前置處理
        if preprocess:
            # 僅保留 denoise 和 binarize
            pass
        
        # 提取欄位
        return self.extractor.extract(image, self.template)
```

---

## ✅ 執行步驟與時程

### Day 1: 大掃除 (上午)

```bash
# Step 1: 刪除舊範本 (5 分鐘)
rm config/templates/invoice_v1.json
rm config/templates/receipt_v1.json
rm config/templates/tw_einvoice_v1.json
rm config/templates/tw_einvoice_v2.json
rm config/templates/tw_einvoice_hybrid.json
rm -rf config/schemas/

# Step 2: 刪除無用模組 (10 分鐘)
rm ocr_pipeline/core/extractors/hybrid_extractor.py
rm ocr_pipeline/core/steps/deskew.py
rm ocr_pipeline/core/steps/resize_normalize.py
rm -rf ocr_pipeline/template/

# Step 3: 刪除對應測試 (10 分鐘)
rm tests/test_hybrid_extractor.py
rm tests/test_deskew.py
rm tests/test_resize_normalize.py
rm tests/test_template_loader.py
rm tests/test_template_validator.py

# Step 4: 更新 __init__.py (15 分鐘)
# 移除已刪除模組的導出
```

### Day 1: 實作 FullImageExtractor (下午)

```bash
# Step 5: 建立核心模組 (2 小時)
# 實作 full_image_extractor.py

# Step 6: 建立測試 (1 小時)
# 實作 test_full_image_extractor.py
```

### Day 2: 整合與測試 (全天)

```bash
# Step 7: 建立 v3 範本 (30 分鐘)
# 建立 tw_einvoice.json

# Step 8: 更新 Orchestrator (1 小時)
# 添加 FullImageExtractor 支援

# Step 9: 端到端測試 (2 小時)
# 實作 test_e2e_einvoice.py
# 測試電子發票提取流程

# Step 10: 文檔更新 (1 小時)
# 更新 README.md
```

---

## 📊 刪除前後對比（修正版）

| 項目 | 刪除前 | 刪除後 | 變化 |
|-----|--------|--------|------|
| 核心模組檔案 | 19 個 | 17 個 | -11% |
| 測試檔案 | 15 個 | 13 個 | -13% |
| 測試數量 | 181 個 | ~159 個 | -12% |
| 程式碼行數 | ~798 stmts | ~700 stmts | -12% |
| 範本檔案 | 1 個 (hybrid) | 1 個 | 0% |
| 測試覆蓋率 | 91% | 88-90% | 略降但仍優秀 |
| **核心保留** | HybridExtractor ✅ | Orchestrator ✅ | validator ⚠️ |

---
（修正版）

**立即執行: 刪除舊前置工具（30 分鐘）**
- [ ] 刪除 deskew.py
- [ ] 刪除 resize_normalize.py
- [ ] 刪除 tests/test_deskew.py
- [ ] 刪除 tests/test_resize_normalize.py
- [ ] 刪除 template/loader.py
- [ ] 刪除 tests/test_template_loader.py
- [ ] 刪除舊範本（如存在）
- [ ] 更新 ocr_pipeline/core/steps/__init__.py
- [ ] 更新 ocr_pipeline/template/__init__.py

**執行測試驗證**
- [ ] 運行測試: pytest tests/
- [ ] 確認測試數量: ~159 個（-22）
- [ ] 確認測試覆蓋率: 88-90%
- [ ] 確認所有測試通過

**保留確認**
- [x] HybridExtractor 保留 ✅
- [x] Orchestrator 保留 ✅
- [x] validator.py 保留（待同步）⚠️
- [x] test_template_validator.py 保留 ✅

**待處理任務**
- [ ] 同步 validator.py 與 C# 版本
- [ ] 更新 README.md（如需要）
- [ ] 更新文檔（如需要）%+
- [ ] 程式碼減少 35%+

---

## 🎯 成功指標

1. ✅ **程式碼精簡**: 減少 35-40%
2. ✅ **電子發票準確率**: 95%+
3. ✅ **測試覆蓋率**: 維持 90%+
4. ✅ Orchestrator 已支援 HybridExtractor（無需修改）

**Orchestrator 已經支援 HybridExtractor**

當前實作（98% 覆蓋率）:
```python
class Orchestrator:
    def __init__(self, ocr_adapter, config=None):
        self.ocr = ocr_adapter
        self.extractor = HybridExtractor(ocr_adapter)  # 已使用
        # ...
    
    def process(self, image, preprocess_config=None):
        # 前置處理（denoise, binarize）
        # 使用 HybridExtractor 提取欄位
        return self.extractor.extract_fields(preprocessed, self.template)
```

**結論**: Orchestrator 無需修改，已完美支援（已修正）

### 立即執行: 刪除舊前置工具（30 分鐘）

```bash
# Step 1: 刪除舊前置處理步驟（確定刪除）
rm ocr_pipeline/core/steps/deskew.py
rm ocr_pipeline/core/steps/resize_normalize.py
rm tests/test_deskew.py
rm tests/test_resize_normalize.py

# Step 2: 刪除被簡化的 loader（確定刪除）
rm ocr_pipeline/template/loader.py
rm tests/test_template_loader.py

# Step 3: 刪除舊範本（如果還存在）
rm config/templates/invoice_v1.json 2>/dev/null || true
rm config/templates/receipt_v1.json 2>/dev/null || true
rm config/templates/tw_einvoice_v1.json 2>/dev/null || true
rm config/templates/tw_einvoice_v2.json 2>/dev/null || true
rm -rf config/schemas/ 2>/dev/null || true

# Step 4: 更新 __init__.py（10 分鐘）
# 移除 DeskewStep, ResizeNormalizeStep 導出
# 移除 loader 相關導出
```

### 待處理: 同步驗證器（未來工作）

```bash
# ⚠️ 不刪除，需要與 C# 版本同步
# ocr_pipeline/template/validator.py
# tests/test_template_validator.py

# TODO: 確保 Python 驗證器與 roi_sample_tool 的 C# 驗證器邏輯一致
```

### 完成: 無需新建模組

```bash
# ✅ HybridExtractor 已實作（保留）
# ✅ Orchestrator 已支援（無需修改）
# ✅ 測試覆蓋率 91%（刪除後預計 88-90%）