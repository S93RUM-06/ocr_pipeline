# 6️⃣ README.md 建議內容


# OCR Pipeline

> 模組化、可配置、可擴充的 OCR 辨識生產流程系統

## 📖 專案簡介

OCR Pipeline 是一個工程級的 OCR（光學字元識別）系統，提供完整的文件處理流程：

- **多格式支援**：處理 PDF、DOCX、TIFF、PNG、JPEG 等格式
- **模組化設計**：前處理、OCR 引擎、後處理完全解耦
- **統一範本系統**：支援兩種定位模式（絕對座標/相對座標），靈活適應不同文件類型
- **可插拔引擎**：支援 PaddleOCR、Tesseract 等多種 OCR 引擎
- **完整測試覆蓋**：91% 測試覆蓋率，201+ 單元測試
- **完整追溯**：所有中間結果可保存，便於除錯與優化

## 🎯 設計目標

1. **Pipeline 與 OCR Engine 解耦**
2. **Config-driven（設定驅動）**
3. **模組可插拔**
4. **統一範本格式**：新版 v1.0 schema，regions 為 dict，欄位皆用 rect_ratio 相對座標描述
5. **所有中間結果可追蹤**
6. **可因應多文件版型**

## 📋 系統需求

- Python 3.10+
- OpenCV 4.5+
- PaddleOCR 3.3+ (CPU 版本)

## ⚙️ 安裝

```bash
# 建立 conda 環境
conda create -n ocr_pipeline python=3.10
conda activate ocr_pipeline

# 安裝依賴套件
pip install -r requirements.txt

# 安裝 PaddleOCR (CPU 版本)
pip install paddlepaddle==3.2.2
pip install paddleocr==3.3.2
```

## 🚀 快速開始

### 範例程式

```bash
# 快速 OCR 測試
wsl -e bash -c "cd /mnt/d/source/ocr_pipeline && ~/miniconda3/envs/ocr_pipeline/bin/python examples/quick_ocr_test.py"

# 台灣電子發票完整示範
wsl -e bash -c "cd /mnt/d/source/ocr_pipeline && ~/miniconda3/envs/ocr_pipeline/bin/python examples/taiwan_einvoice_demo.py"
```

### Python API 使用

```python
from ocr_pipeline.adapters.ocr import PaddleOCRAdapter
from ocr_pipeline.utils.image_utils import read_image

# 初始化 OCR 引擎
ocr = PaddleOCRAdapter(
    config={"lang": "chinese_cht"},
    min_confidence=0.7
)

# 載入影像
image = read_image("invoice.jpg")

# 執行 OCR
results = ocr.recognize(image)

# 顯示結果
for item in results:
    print(f"文字: {item['text']}, 信心分數: {item['confidence']:.2%}")
```

## 📚 範本系統

本專案採用**統一新版 v1.0 範本格式**，所有欄位皆以 metadata + regions dict 結構描述，完全符合 template-v1.0.json schema：

### 🎯 相對座標模式（推薦）

適用於格式有變化的文件（如不同來源的發票）：

```json
{
  "template_id": "tw_einvoice_v1",
  "anchor": {
    "enable": true,
    "text": "電子發票證明聯",
    "expected_bbox": {
      "width": 431.0,
      "height": 71.0,
      "tolerance_ratio": 0.2
    }
  },
  "regions": [
    {
      "name": "invoice_number",
      "relative_to_anchor": {
        "x": 43.0,
        "y": 147.0,
        "width": 341.0,
        "height": 64.0,
        "tolerance_ratio": 0.3
      }
    }
  ],
  "ocr": {
    "lang": "chinese_cht"
  }
}
```

### 📍 絕對座標模式

適用於格式完全統一的文件：

```json
{
  "template_id": "invoice_v1",
  "anchor": {
    "enable": false
  },
  "image_size": [2480, 3508],
  "regions": [
    {
      "name": "invoice_no",
      "rect": [300, 200, 900, 350]
    }
  ]
}
```

詳細規格請參閱 [03 作業範本規格.md](03 作業範本規格.md)

## 📚 文件索引

- [00 初步構想.md](00 初步構想.md) - 構想設計
- [01 設計架構.md](01 設計架構.md) - 系統架構說明
- [02 API規格.md](02 API規格.md) - API 規格定義
- [03 作業範本規格.md](03 作業範本規格.md) - **統一範本規格說明**
- [04 專案規格.md](04 專案規格.md) - Python 專案結構規劃
- [TEST_UPDATE_REPORT.md](TEST_UPDATE_REPORT.md) - 測試更新報告

## 🏗️ 專案狀態

**目前階段：核心開發與驗證 ✅**

- ✅ 架構設計完成
- ✅ PaddleOCR 3.3.2 CPU 版本整合
- ✅ 新版 v1.0 schema 範本格式設計與實作
- ✅ Template Validator（支援雙模式）
- ✅ 台灣電子發票範本（Anchor-based）
- ✅ 測試覆蓋率 91%（201/202 測試通過）
- ⏳ Orchestrator 整合（進行中）
- ⏳ REST API 開發（待開始）

## 🔧 測試

```bash
# 執行所有測試
# 執行所有測試
wsl -e bash -c "cd /mnt/d/source/ocr_pipeline && ~/miniconda3/envs/ocr_pipeline/bin/python -m pytest tests/ -v"

# 執行特定測試
pytest tests/test_template_validator.py -v

# 顯示覆蓋率
pytest tests/ --cov=ocr_pipeline --cov-report=html
# 顯示覆蓋率
wsl -e bash -c "cd /mnt/d/source/ocr_pipeline && ~/miniconda3/envs/ocr_pipeline/bin/python -m pytest tests/ --cov=ocr_pipeline --cov-report=html"
```

**測試統計**：

## 🎯 範例程式


## 📄 授權

(待補充)

## 🤝 貢獻

(待補充)