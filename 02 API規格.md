# OCR API 規格文件

## 1. 文件目的

定義 OCR 系統對外提供的 API 介面，
供前端、其他系統或批次流程整合使用。

---

## 2. API 概覽

| API | 說明 |
|----|----|
| POST /ocr/recognize | 同步 OCR |
| POST /ocr/jobs | 建立 OCR Job |
| GET /ocr/jobs/{id} | 查詢 Job 狀態 |

---

## 3. 同步 OCR API

### POST /ocr/recognize

#### Request

```json
{
  "template_id": "invoice_v1",
  "file": "<binary or base64>"
}
```

#### Response

```json
{
  "status": "SUCCESS",
  "result": {
    "invoice_no": "A12345",
    "total_amount": "1000"
  }
}
```

---

## 4. 非同步 OCR Job API

### POST /ocr/jobs

#### Request

```json
{
  "template_id": "invoice_v1",
  "file": "<binary>"
}
```

#### Response

```json
{
  "job_id": "JOB_001"
}
```

---

### GET /ocr/jobs/{job_id}

#### Response

```json
{
  "job_id": "JOB_001",
  "status": "PREPROCESSING",
  "current_step": "ROIExtraction"
}
```

---

## 5. Job 狀態定義

| 狀態               | 說明     |
| ---------------- | ------ |
| PENDING          | 等待中    |
| INPUT_PROCESSING | 檔案轉換   |
| PREPROCESSING    | 影像前處理  |
| OCR              | OCR 辨識 |
| POSTPROCESSING   | 後處理    |
| COMPLETED        | 完成     |
| FAILED           | 失敗     |

---

## 6. 錯誤處理

### HTTP 狀態碼

| 狀態碼 | 說明 |
|-------|------|
| 200 OK | 請求成功 |
| 201 Created | Job 建立成功 |
| 400 Bad Request | 請求參數錯誤 |
| 401 Unauthorized | 未授權 |
| 404 Not Found | Job 不存在 |
| 413 Payload Too Large | 檔案過大 |
| 429 Too Many Requests | 超過請求限制 |
| 500 Internal Server Error | 伺服器錯誤 |

---

### 錯誤回應格式

```json
{
  "error": {
    "code": "INVALID_TEMPLATE",
    "message": "Template 'invoice_v99' not found",
    "details": {
      "available_templates": ["invoice_v1", "receipt_v1"]
    }
  }
}
```

---

### 錯誤代碼列表

| 錯誤代碼 | 說明 |
|---------|------|
| INVALID_FILE_FORMAT | 不支援的檔案格式 |
| INVALID_TEMPLATE | Template 不存在 |
| FILE_TOO_LARGE | 檔案超過大小限制 |
| PROCESSING_TIMEOUT | 處理超時 |
| OCR_ENGINE_ERROR | OCR 引擎錯誤 |

---

## 7. 認證與授權

### API Key 認證

所有 API 請求需在 Header 中包含 API Key：

```http
Authorization: Bearer <your_api_key>
```

### Rate Limiting

- **免費版**：100 次/日
- **基礎版**：1000 次/日
- **進階版**：無限制

超過限制時回傳 `429 Too Many Requests`

---

## 8. 檔案大小限制

- **單一檔案**：最大 10 MB
- **批次處理**：最大 100 MB
- **支援格式**：PDF, DOCX, PNG, JPEG, TIFF

---
