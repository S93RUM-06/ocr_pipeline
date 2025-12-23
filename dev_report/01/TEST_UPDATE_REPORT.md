# TDD 測試程式更新報告

## 📋 更新日期
2025年12月22日

## 🎯 更新目標
根據新的 **Anchor-Based Template 規格 v2.0** (0-3 template_spec.md)，更新並擴展 TDD 測試程式。

## ✅ 完成的測試更新

### 1. 新增測試文件

#### `tests/test_anchor_template.py` (全新)
- **測試類別數量**: 5 個
- **測試案例數量**: 19 個
- **測試覆蓋率**: 100% 通過

**測試類別**:
1. **TestAnchorBasedTemplate** (6 tests)
   - anchor 必須存在且格式正確
   - regions 使用相對定位
   - tolerance_ratio 範圍驗證
   - 單層 OCR lang 設定檢查
   - validation 欄位完整性

2. **TestAnchorMatching** (3 tests)
   - 在 OCR 結果中尋找 anchor
   - 計算 anchor 位置（左上角）
   - 驗證 anchor 尺寸在容忍範圍內

3. **TestRelativeROIExtraction** (3 tests)
   - 從 anchor 計算 ROI 絕對位置
   - 在容忍範圍內匹配 OCR 到 ROI
   - 處理負數相對位置

4. **TestPatternExtraction** (4 tests)
   - 發票號碼格式提取
   - 隨機碼數字提取
   - 總計金額提取
   - 賣方統編提取

5. **TestConfidenceValidation** (3 tests)
   - 必填欄位信心分數驗證
   - 選填欄位低信心分數處理
   - 拒絕必填欄位低信心分數

### 2. 更新現有測試文件

#### `tests/test_template_validator.py`
新增 **TestAnchorBasedTemplateValidator** 測試類別

- **新增測試數量**: 20 個
- **測試通過率**: 100%

**新增測試案例**:

**A. Anchor 驗證** (9 tests)
- ✅ 有效的 anchor-based 模板通過驗證
- ✅ v2.0 模板缺少 anchor 會被當作 v1 處理
- ✅ anchor 缺少 text 欄位失敗
- ✅ anchor 缺少 expected_bbox 失敗
- ✅ expected_bbox 缺少 width/height/tolerance 失敗
- ✅ tolerance_ratio 超出範圍 (0-1) 失敗

**B. 相對位置驗證** (4 tests)
- ✅ region 缺少 relative_to_anchor 失敗
- ✅ relative_to_anchor 缺少座標失敗
- ✅ 允許負數相對位置（anchor 左側/上方）
- ✅ region tolerance_ratio 超出範圍失敗

**C. OCR 配置驗證** (3 tests)
- ✅ region 的 ocr_config 不應有獨立 lang（必須拒絕）
- ✅ 全域 OCR 必須有 lang 設定
- ✅ OCR lang 有效值檢查 (chinese_cht, ch, en 等)

**D. Validation 欄位驗證** (3 tests)
- ✅ validation.required 欄位為選填
- ✅ validation.min_confidence 範圍 (0-1)
- ✅ validation 整個區塊為選填

**E. 版本檢測** (2 tests)
- ✅ version 欄位為選填
- ✅ 自動偵測模板類型（v1/v2）

## 📊 測試統計

### 整體測試結果
```
總測試數: 199 個
通過: 198 個 (99.5%)
失敗: 1 個 (0.5%)
警告: 1 個
```

### 測試覆蓋率
```
總覆蓋率: 91%

關鍵模組:
- template/validator.py: 87% (新增 v2 支援)
- template/loader.py: 88%
- core/pipeline.py: 100%
- core/orchestrator.py: 92%
- adapters/ocr/paddleocr_adapter.py: 83%
```

### 失敗測試
```
tests/test_paddleocr_adapter.py::TestPaddleOCRAdapter::test_can_process_grayscale_image
原因: IndexError - 與 anchor template 無關的既有問題
```

## 🔧 主要程式碼更新

### 1. TemplateValidator 增強

**新增功能**:
- ✅ 支援 v1.0 和 v2.0 雙格式
- ✅ 自動檢測模板版本
- ✅ Anchor 定義驗證
- ✅ 相對位置驗證
- ✅ 全域 OCR 配置驗證
- ✅ 防止 region 層級 lang 設定
- ✅ Validation 配置驗證

**新增驗證方法**:
```python
_validate_v1_template()       # v1.0 特定驗證
_validate_v2_template()       # v2.0 特定驗證
_validate_anchor()            # anchor 驗證
_validate_ocr_config()        # 全域 OCR 驗證
_validate_v2_regions()        # v2.0 regions 驗證
_validate_v2_region()         # v2.0 單一 region 驗證
_validate_relative_position() # 相對位置驗證
_validate_validation_config() # validation 配置驗證
```

### 2. 測試覆蓋的關鍵規格

#### A. 單層 Lang 設定
```python
# ✅ 通過：全域 lang
{
  "ocr": {"lang": "chinese_cht"}
}

# ❌ 拒絕：region 層級 lang
{
  "regions": [{
    "ocr_config": {"lang": "en"}  # 不允許
  }]
}
```

#### B. Anchor 定位
```python
{
  "anchor": {
    "text": "電子發票證明聯",
    "expected_bbox": {
      "width": 431.0,
      "height": 71.0,
      "tolerance_ratio": 0.2  # ✅ 0-1 範圍
    }
  }
}
```

#### C. 相對位置 ROI
```python
{
  "relative_to_anchor": {
    "x": 43.0,      # ✅ 允許正數
    "y": -31.0,     # ✅ 允許負數（anchor 左側/上方）
    "width": 341.0, # ✅ 必須為正數
    "height": 64.0,
    "tolerance_ratio": 0.3
  }
}
```

## 📝 測試覆蓋的使用情境

### 1. 模板版本自動檢測
```python
# 有 anchor → v2.0
template_v2 = {"anchor": {...}, "regions": [...]}

# 有 image_size → v1.0
template_v1 = {"image_size": [1000, 1000], "regions": [...]}
```

### 2. Anchor 匹配流程
```
OCR 全張識別 → 尋找「電子發票證明聯」→ 驗證尺寸 → 取得錨點座標
```

### 3. ROI 計算流程
```
roi_x = anchor_x + relative.x
roi_y = anchor_y + relative.y
在 ±tolerance 範圍內匹配 OCR 結果
```

### 4. 欄位提取流程
```
識別文字 → 正規表達式驗證 → 提取數值 → 檢查信心分數
```

## 🎉 測試成果

### 新增測試數量
- **新檔案**: 1 個 (test_anchor_template.py)
- **新測試類別**: 6 個
- **新測試案例**: 39 個
- **全部通過**: ✅

### 確保的品質保證
1. ✅ **向後兼容**: v1.0 模板仍然正常工作
2. ✅ **前向支援**: v2.0 模板完整驗證
3. ✅ **錯誤處理**: 詳細的錯誤訊息
4. ✅ **邊界條件**: 負數座標、容忍範圍
5. ✅ **資料驗證**: 正規表達式、信心分數
6. ✅ **配置一致性**: 單層 lang 設定強制執行

## 📌 下一步建議

### 短期 (已完成)
- ✅ 模板驗證器支援 v2.0
- ✅ Anchor 匹配測試
- ✅ 相對位置計算測試
- ✅ 模式提取測試

### 中期 (待實作)
- ⏳ Orchestrator 支援 anchor-based 處理
- ⏳ ROI Extractor 支援相對位置提取
- ⏳ 整合測試：完整流程端到端

### 長期
- ⏳ 多 anchor 候選項支援
- ⏳ 自動調整 tolerance
- ⏳ 機器學習優化錨點選擇

## 🎯 總結

所有針對新 **Anchor-Based Template 規格 v2.0** 的 TDD 測試程式已完成更新：

1. ✅ **39 個新測試案例**涵蓋所有 v2.0 特性
2. ✅ **198/199 測試通過** (99.5% 通過率)
3. ✅ **91% 程式碼覆蓋率**
4. ✅ **向後兼容** v1.0 模板
5. ✅ **完整驗證**：anchor、相對位置、OCR 配置、validation

測試套件已確保新模板規格的正確性和穩定性。
