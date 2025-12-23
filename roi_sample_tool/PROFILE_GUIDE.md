# 欄位組 Profile 管理系統

## 📋 概述

欄位組 Profile 是預先定義的欄位配置模板，讓您可以快速開始 OCR 範本的取樣工作，無需每次都手動輸入欄位名稱。

## 🎯 使用場景

- **重複性工作**：經常處理相同類型的文件（發票、收據、證明聯等）
- **標準化流程**：確保團隊使用一致的欄位命名和配置
- **快速啟動**：新專案可直接套用現有 Profile，無需從頭設定

## 📁 Profile 存儲位置

```
roi_sample_tool/
├── profiles/                    # Profile 存儲目錄
│   ├── tw_einvoice_v1.json     # 台灣電子發票 Profile
│   ├── general_receipt_v1.json  # 一般收據 Profile
│   └── ...                      # 您的自訂 Profiles
```

## 🎨 Profile 結構

```json
{
  "profile_id": "tw_einvoice_v1",
  "profile_name": "台灣電子發票證明聯",
  "description": "統一發票證明聯（電子發票）常見欄位",
  "document_type": "invoice",
  "tags": ["台灣", "發票", "電子發票"],
  "fields": [
    {
      "field_name": "invoice_number",
      "display_name": "發票號碼",
      "data_type": "string",
      "required": true,
      "pattern": "[A-Z]{2}-\\d{8}",
      "expected_length": 10,
      "description": "格式: AB-12345678"
    },
    {
      "field_name": "total_amount",
      "display_name": "總金額",
      "data_type": "number",
      "required": true
    }
  ]
}
```

## 🚀 使用方式

### 1. 選擇 Profile

在主視窗左側面板：
1. 從「選擇 Profile」下拉選單選擇您需要的 Profile
2. 點擊「套用 Profile」按鈕
3. 欄位列表會顯示該 Profile 包含的所有欄位

### 2. 標註欄位

**方式 A：從欄位列表快速標註**
- 直接點擊欄位旁的「標註」按鈕
- 在圖片上拖曳繪製 ROI

**方式 B：手動輸入欄位名稱**
- 在「或手動輸入欄位名稱」輸入框輸入自訂欄位
- 點擊「開始繪製 ROI」
- 在圖片上拖曳繪製 ROI

### 3. 管理 Profiles

點擊工具列的「管理 Profile」按鈕開啟管理視窗：

#### 新增 Profile
1. 點擊「新增 Profile」
2. 填寫 Profile 名稱、說明、文件類型
3. 點擊「新增欄位」加入欄位定義
4. 填寫欄位名稱、顯示名稱、資料類型等
5. 點擊「儲存」

#### 複製 Profile
1. 選擇要複製的 Profile
2. 點擊「複製」按鈕
3. 修改副本的設定
4. 點擊「儲存」

#### 編輯 Profile
1. 選擇要編輯的 Profile
2. 點擊「編輯」按鈕進入編輯模式
3. 修改欄位（新增、刪除、修改屬性）
4. 點擊「儲存」或「取消」

#### 刪除 Profile
1. 選擇要刪除的 Profile
2. 點擊「刪除」按鈕
3. Profile 檔案會被永久刪除

## 📦 預設 Profiles

### 1. 台灣電子發票證明聯 (tw_einvoice_v1)

**欄位列表**：
- `invoice_number` - 發票號碼 (必填)
- `invoice_date` - 發票日期 (必填)
- `seller_name` - 賣方名稱
- `buyer_tax_id` - 買方統編
- `total_amount` - 總金額 (必填)
- `random_code` - 隨機碼 (4位數)
- `qrcode_left` - QR Code (左)
- `qrcode_right` - QR Code (右)

### 2. 一般收據 (general_receipt_v1)

**欄位列表**：
- `receipt_number` - 收據編號 (必填)
- `receipt_date` - 收據日期 (必填)
- `payer_name` - 付款人
- `total_amount` - 總金額 (必填)
- `payment_method` - 付款方式
- `description` - 項目說明

## 🔧 欄位屬性說明

| 屬性 | 說明 | 範例 |
|------|------|------|
| `field_name` | 欄位識別名稱（程式使用） | `invoice_number` |
| `display_name` | 顯示名稱（UI 顯示） | `發票號碼` |
| `data_type` | 資料類型 | `string`, `number`, `date` |
| `required` | 是否必填 | `true` / `false` |
| `pattern` | 正則表達式驗證 | `[A-Z]{2}-\\d{8}` |
| `expected_length` | 預期長度（用於評分） | `10` |
| `description` | 欄位說明 | `格式: AB-12345678` |
| `example_values` | 範例值 | `["AB-12345678", "CD-98765432"]` |

## 💡 最佳實踐

1. **命名規範**：使用小寫英文加底線（snake_case），例如 `invoice_number`
2. **顯示名稱**：使用清晰的中文描述，方便操作人員理解
3. **資料類型**：正確設定資料類型，方便後續驗證
4. **正則表達式**：為格式固定的欄位設定 pattern，提高準確度
5. **分類管理**：使用 `document_type` 和 `tags` 分類 Profiles

## 🔄 工作流程範例

### 場景：處理 10 張台灣電子發票

1. **準備階段**
   - 選擇「台灣電子發票證明聯」Profile
   - 點擊「套用 Profile」

2. **標註第一張**
   - 載入第一張圖片
   - 依序標註 8 個欄位（從欄位列表點擊「標註」）
   - 確認標註完成

3. **標註剩餘圖片**
   - 載入下一張圖片
   - 重複標註流程
   - 共處理 10 張

4. **生成範本**
   - 點擊「計算範本」
   - 檢查統計資訊
   - 匯出 JSON 範本

## 📚 進階功能

### 自訂文件類型

建立專屬於您業務的 Profile：
- 房屋租賃合約
- 醫療報告
- 物流單據
- 銀行對帳單

### 團隊協作

透過 Git 版控管理 `profiles/` 目錄：
- 團隊成員共享 Profiles
- 版本控制確保一致性
- Pull Request 審查新 Profile

## ❓ 常見問題

**Q: Profile 可以修改嗎？**  
A: 可以！點擊「管理 Profile」→ 選擇 Profile → 點擊「編輯」即可修改。

**Q: 如何備份我的 Profiles？**  
A: 直接複製 `profiles/` 目錄即可。

**Q: Profile 檔案可以手動編輯嗎？**  
A: 可以！使用任何文字編輯器編輯 JSON 檔案，但請確保 JSON 格式正確。

**Q: 可以匯入其他人的 Profile 嗎？**  
A: 可以！將 `.json` 檔案放入 `profiles/` 目錄，點擊「重新載入」即可。

## 🎓 相關文件

- [Template Schema 規格](../../docs/template_schema_specification.md)
- [ROI 取樣工具說明](README.md)
- [API 規格](../../02%20API規格.md)
