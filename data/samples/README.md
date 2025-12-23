"""
測試資料目錄說明

## 資料夾結構
data/
├── samples/           # 測試樣本影像
│   ├── invoice_1.jpg  # 唯統科技電子發票
│   ├── invoice_2.jpg  # 三敏公司電子發票
│   └── README.md      # 本檔案
└── results/           # 處理結果輸出

## 使用說明

### 放置測試影像
1. 將電子發票影像放入 `samples/` 目錄
2. 建議命名格式: `invoice_*.jpg` 或 `receipt_*.jpg`

### 執行測試
```bash
# 在 WSL 中執行
cd /mnt/d/source/ocr_pipeline
conda activate ocr_pipeline
python examples/taiwan_einvoice_demo.py
```

## 當前測試樣本

### invoice_1.jpg
- 公司：唯統科技有限公司
- 發票號碼：PC-72923474
- 日期：2019-03-13
- 總計：3,360

### invoice_2.jpg
- 公司：三敏公司
- 發票號碼：AA-12340007
- 日期：2017-5-30
- 總計：1,100

## 注意事項
- 影像解析度建議至少 600x900 以上
- 支援格式：JPG, PNG, BMP
- 確保文字清晰可讀
