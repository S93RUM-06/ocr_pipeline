# OCR 作業範本 JSON Schema 規格文件

> **Template Schema Specification v1.0**  
> 創建日期：2025-12-23  
> 狀態：正式規格

---

## 📋 目錄

1. [背景與動機](#背景與動機)
2. [核心設計原則](#核心設計原則)
3. [JSON Schema 規格](#json-schema-規格)
4. [完整範例](#完整範例)
5. [欄位詳細說明](#欄位詳細說明)
6. [座標轉換公式](#座標轉換公式)
7. [驗證器實作](#驗證器實作)
8. [資料類型對照](#資料類型對照)
9. [版本演進規劃](#版本演進規劃)

---

## 背景與動機

### 核心問題

在開發 OCR Pipeline 時，我們發現了一個關鍵問題：

**取樣工具統計的圖片大小 ≠ 後置處理的實際圖片大小**

這導致：
- ❌ **絕對像素座標不可行**（不同圖片大小會失準）
- ✅ **需要抽象化的座標系統**（相對比例）
- ✅ **需要反推機制**（模板定義 → 實際像素座標）

### 設計目標

1. **適應性**：適應任意圖片大小
2. **統計性**：多張圖片統計平均值
3. **簡潔性**：反推邏輯簡單明確
4. **穩定性**：包含標準差評估模板品質

---

## 核心設計原則

### 1. 相對比例座標系統

所有 ROI 座標使用 **0-1 之間的比例值**：

```
rect_ratio.x = pixel_x / image_width
rect_ratio.y = pixel_y / image_height
rect_ratio.width = pixel_width / image_width
rect_ratio.height = pixel_height / image_height
```

### 2. 整圖統計策略

**選擇整圖統計（而非單一 ROI 統計）**的原因：

| 優勢 | 說明 |
|------|------|
| ✅ **統一基準** | 所有 ROI 共用同一個 reference_size |
| ✅ **簡化反推** | 後置處理只需一次圖片大小轉換 |
| ✅ **相對位置保持** | 各 ROI 之間的相對關係不變 |
| ✅ **標準差有意義** | 可評估整個模板的穩定性 |

### 3. 統計元數據

包含 `sampling_metadata` 記錄：
- 樣本數量
- 基準圖片大小（中位數）
- 大小範圍（min/max）
- 取樣日期、工具版本等

---

## JSON Schema 規格

### 完整 Schema (v1.0)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://ocr-pipeline.example.com/schemas/template-v1.0.json",
  "title": "OCR Template Schema",
  "description": "OCR 作業範本定義規格 - 使用相對比例座標系統",
  "type": "object",
  
  "required": [
    "template_id",
    "template_name",
    "version",
    "processing_strategy",
    "sampling_metadata",
    "regions"
  ],
  
  "properties": {
    "template_id": {
      "type": "string",
      "pattern": "^[a-z0-9_]+$",
      "minLength": 3,
      "maxLength": 50,
      "description": "模板唯一識別碼（小寫英數字+底線）",
      "examples": ["tw_einvoice_v1", "receipt_standard", "id_card_tw"]
    },
    
    "template_name": {
      "type": "string",
      "minLength": 1,
      "maxLength": 100,
      "description": "模板顯示名稱（人類可讀）",
      "examples": ["台灣電子發票證明聯", "標準收據", "台灣身分證"]
    },
    
    "version": {
      "type": "string",
      "pattern": "^\\d+\\.\\d+(\\.\\d+)?$",
      "description": "模板版本號（語義化版本）",
      "examples": ["1.0", "1.2.3", "2.0"]
    },
    
    "created_at": {
      "type": "string",
      "format": "date",
      "description": "模板創建日期（ISO 8601 格式）",
      "examples": ["2025-12-23"]
    },
    
    "updated_at": {
      "type": "string",
      "format": "date",
      "description": "模板最後更新日期",
      "examples": ["2025-12-23"]
    },
    
    "description": {
      "type": "string",
      "maxLength": 500,
      "description": "模板詳細說明"
    },
    
    "processing_strategy": {
      "type": "string",
      "enum": [
        "hybrid_ocr_roi",
        "fixed_roi",
        "full_ocr_only",
        "anchor_based"
      ],
      "description": "處理策略類型",
      "default": "hybrid_ocr_roi"
    },
    
    "sampling_metadata": {
      "type": "object",
      "required": ["sample_count", "reference_size"],
      "description": "取樣統計元數據",
      "properties": {
        "sample_count": {
          "type": "integer",
          "minimum": 1,
          "description": "參與統計的樣本圖片數量"
        },
        
        "reference_size": {
          "type": "object",
          "required": ["width", "height", "unit"],
          "description": "基準圖片大小（統計中位數或平均值）",
          "properties": {
            "width": {
              "type": "integer",
              "minimum": 1,
              "description": "基準寬度"
            },
            "height": {
              "type": "integer",
              "minimum": 1,
              "description": "基準高度"
            },
            "unit": {
              "type": "string",
              "enum": ["pixel"],
              "default": "pixel",
              "description": "單位（目前僅支援 pixel）"
            },
            "description": {
              "type": "string",
              "description": "基準大小計算方式說明"
            }
          }
        },
        
        "size_range": {
          "type": "object",
          "description": "樣本圖片大小範圍（用於評估變異性）",
          "properties": {
            "width": {
              "type": "object",
              "required": ["min", "max"],
              "properties": {
                "min": {"type": "integer", "minimum": 1},
                "max": {"type": "integer", "minimum": 1}
              }
            },
            "height": {
              "type": "object",
              "required": ["min", "max"],
              "properties": {
                "min": {"type": "integer", "minimum": 1},
                "max": {"type": "integer", "minimum": 1}
              }
            }
          }
        },
        
        "sampling_date": {
          "type": "string",
          "format": "date",
          "description": "取樣日期"
        },
        
        "sampler_version": {
          "type": "string",
          "description": "取樣工具版本"
        },
        
        "notes": {
          "type": "string",
          "description": "取樣備註"
        }
      }
    },
    
    "regions": {
      "type": "object",
      "minProperties": 1,
      "description": "欄位區域定義集合",
      "patternProperties": {
        "^[a-z_][a-z0-9_]*$": {
          "$ref": "#/definitions/region"
        }
      }
    }
  },
  
  "definitions": {
    "region": {
      "type": "object",
      "required": ["rect_ratio"],
      "description": "單一欄位區域定義",
      "properties": {
        "rect_ratio": {
          "type": "object",
          "required": ["x", "y", "width", "height"],
          "description": "ROI 相對比例座標（0-1 之間）",
          "properties": {
            "x": {
              "type": "number",
              "minimum": 0,
              "maximum": 1,
              "description": "左上角 X 座標比例 (x / image_width)"
            },
            "y": {
              "type": "number",
              "minimum": 0,
              "maximum": 1,
              "description": "左上角 Y 座標比例 (y / image_height)"
            },
            "width": {
              "type": "number",
              "minimum": 0,
              "maximum": 1,
              "description": "寬度比例 (width / image_width)"
            },
            "height": {
              "type": "number",
              "minimum": 0,
              "maximum": 1,
              "description": "高度比例 (height / image_height)"
            }
          }
        },
        
        "rect_std_dev": {
          "type": "object",
          "description": "ROI 位置標準差（評估穩定性，可選）",
          "properties": {
            "x": {"type": "number", "minimum": 0},
            "y": {"type": "number", "minimum": 0},
            "width": {"type": "number", "minimum": 0},
            "height": {"type": "number", "minimum": 0}
          }
        },
        
        "pattern": {
          "type": "string",
          "description": "正則表達式匹配模式（可選）",
          "examples": [
            "[A-Z]{2}-\\d{8}",
            "\\d{3}年\\d{1,2}-\\d{1,2}月",
            "隨機碼[:：]\\s*(\\d{4})"
          ]
        },
        
        "extract_group": {
          "type": "integer",
          "minimum": 0,
          "default": 0,
          "description": "正則捕獲組索引（0=完整匹配，1+=捕獲組）"
        },
        
        "expected_length": {
          "type": "integer",
          "minimum": 1,
          "description": "預期文字長度（用於評分）"
        },
        
        "required": {
          "type": "boolean",
          "default": false,
          "description": "是否為必填欄位"
        },
        
        "position_weight": {
          "type": "number",
          "minimum": 0,
          "maximum": 1,
          "default": 0.3,
          "description": "位置權重（評分時位置接近度的權重）"
        },
        
        "tolerance_ratio": {
          "type": "number",
          "minimum": 0,
          "maximum": 1,
          "default": 0.2,
          "description": "容錯範圍比例（ROI 擴展比例）"
        },
        
        "fallback_pattern": {
          "type": "string",
          "description": "降級策略的備用正則表達式"
        },
        
        "data_type": {
          "type": "string",
          "enum": [
            "string",
            "number",
            "date",
            "datetime",
            "phone",
            "email",
            "tax_id",
            "custom"
          ],
          "default": "string",
          "description": "數據類型提示（用於後續驗證）"
        },
        
        "validation": {
          "type": "object",
          "description": "額外驗證規則",
          "properties": {
            "min_length": {"type": "integer", "minimum": 0},
            "max_length": {"type": "integer", "minimum": 0},
            "min_value": {"type": "number"},
            "max_value": {"type": "number"},
            "allowed_values": {
              "type": "array",
              "items": {"type": "string"}
            }
          }
        },
        
        "description": {
          "type": "string",
          "description": "欄位說明"
        }
      }
    }
  }
}
```

---

## 完整範例

### 範例 1: 台灣電子發票（完整版）

```json
{
  "template_id": "tw_einvoice_v1",
  "template_name": "台灣電子發票證明聯",
  "version": "1.0.0",
  "created_at": "2025-12-23",
  "updated_at": "2025-12-23",
  "description": "適用於台灣財政部電子發票證明聯格式（2024年起通用版本）",
  
  "processing_strategy": "hybrid_ocr_roi",
  
  "sampling_metadata": {
    "sample_count": 25,
    "reference_size": {
      "width": 1169,
      "height": 1654,
      "unit": "pixel",
      "description": "25張樣本圖片的中位數大小"
    },
    "size_range": {
      "width": {"min": 1100, "max": 1250},
      "height": {"min": 1600, "max": 1700}
    },
    "sampling_date": "2025-12-23",
    "sampler_version": "1.0.0",
    "notes": "樣本來源：便利商店、超市、餐廳等多種場景"
  },
  
  "regions": {
    "invoice_number": {
      "rect_ratio": {
        "x": 0.1394,
        "y": 0.5785,
        "width": 0.8273,
        "height": 0.1161
      },
      "rect_std_dev": {
        "x": 0.0012,
        "y": 0.0015,
        "width": 0.0008,
        "height": 0.0010
      },
      "pattern": "[A-Z]{2}-\\d{8}",
      "expected_length": 11,
      "required": true,
      "position_weight": 0.3,
      "tolerance_ratio": 0.2,
      "data_type": "string",
      "validation": {
        "min_length": 11,
        "max_length": 11
      },
      "description": "發票號碼（格式：兩碼英文字母 + 連字號 + 八位數字）"
    },
    
    "invoice_date": {
      "rect_ratio": {
        "x": 0.1069,
        "y": 0.4644,
        "width": 0.8912,
        "height": 0.1415
      },
      "rect_std_dev": {
        "x": 0.0018,
        "y": 0.0022,
        "width": 0.0012,
        "height": 0.0015
      },
      "pattern": "\\d{3}年\\d{1,2}-\\d{1,2}月",
      "expected_length": 10,
      "required": true,
      "position_weight": 0.25,
      "tolerance_ratio": 0.2,
      "data_type": "string",
      "description": "開立日期（民國年月期間，如：114年11-12月）"
    },
    
    "random_code": {
      "rect_ratio": {
        "x": 0.0,
        "y": 0.7305,
        "width": 0.4738,
        "height": 0.0707
      },
      "rect_std_dev": {
        "x": 0.0,
        "y": 0.0018,
        "width": 0.0005,
        "height": 0.0012
      },
      "pattern": "隨機碼[:：]\\s*(\\d{4})",
      "extract_group": 1,
      "expected_length": 4,
      "required": true,
      "position_weight": 0.4,
      "tolerance_ratio": 0.2,
      "fallback_pattern": "\\d{4}",
      "data_type": "string",
      "validation": {
        "min_length": 4,
        "max_length": 4
      },
      "description": "隨機碼（四位數字，用於對獎）"
    },
    
    "total_amount": {
      "rect_ratio": {
        "x": 0.5467,
        "y": 0.7286,
        "width": 0.3122,
        "height": 0.0756
      },
      "rect_std_dev": {
        "x": 0.0015,
        "y": 0.0020,
        "width": 0.0010,
        "height": 0.0008
      },
      "pattern": "總計[:：]?\\s*(\\d+)",
      "extract_group": 1,
      "required": true,
      "position_weight": 0.3,
      "tolerance_ratio": 0.2,
      "fallback_pattern": "\\d+$",
      "data_type": "number",
      "validation": {
        "min_value": 0,
        "max_value": 999999
      },
      "description": "總計金額（新台幣元）"
    },
    
    "seller_tax_id": {
      "rect_ratio": {
        "x": 0.0,
        "y": 0.7771,
        "width": 0.4733,
        "height": 0.0683
      },
      "rect_std_dev": {
        "x": 0.0,
        "y": 0.0012,
        "width": 0.0008,
        "height": 0.0010
      },
      "pattern": "賣方[:：]?(\\d{8})",
      "extract_group": 1,
      "expected_length": 8,
      "required": true,
      "position_weight": 0.35,
      "tolerance_ratio": 0.2,
      "fallback_pattern": "\\d{8}",
      "data_type": "tax_id",
      "validation": {
        "min_length": 8,
        "max_length": 8
      },
      "description": "賣方統一編號（八位數字）"
    },
    
    "buyer_tax_id": {
      "rect_ratio": {
        "x": 0.5467,
        "y": 0.7771,
        "width": 0.3122,
        "height": 0.0683
      },
      "rect_std_dev": {
        "x": 0.0018,
        "y": 0.0015,
        "width": 0.0012,
        "height": 0.0010
      },
      "pattern": "買方[:：]?(\\d{8})",
      "extract_group": 1,
      "expected_length": 8,
      "required": false,
      "position_weight": 0.35,
      "tolerance_ratio": 0.2,
      "fallback_pattern": "\\d{8}",
      "data_type": "tax_id",
      "validation": {
        "min_length": 8,
        "max_length": 8
      },
      "description": "買方統一編號（選填，一般消費者可無）"
    }
  }
}
```

### 範例 2: 標準收據（簡化版）

```json
{
  "template_id": "receipt_standard",
  "template_name": "標準收據",
  "version": "1.0.0",
  "created_at": "2025-12-23",
  
  "processing_strategy": "hybrid_ocr_roi",
  
  "sampling_metadata": {
    "sample_count": 15,
    "reference_size": {
      "width": 800,
      "height": 1200,
      "unit": "pixel",
      "description": "15張樣本的平均大小"
    }
  },
  
  "regions": {
    "receipt_date": {
      "rect_ratio": {
        "x": 0.1,
        "y": 0.15,
        "width": 0.8,
        "height": 0.08
      },
      "pattern": "\\d{4}-\\d{2}-\\d{2}",
      "required": true,
      "data_type": "date",
      "description": "收據日期"
    },
    
    "total_amount": {
      "rect_ratio": {
        "x": 0.5,
        "y": 0.7,
        "width": 0.4,
        "height": 0.1
      },
      "pattern": "合計[:：]?\\s*(\\d+)",
      "extract_group": 1,
      "required": true,
      "data_type": "number",
      "description": "總金額"
    }
  }
}
```

---

## 欄位詳細說明

### 頂層欄位

| 欄位 | 類型 | 必填 | 說明 | 範例值 |
|-----|------|------|------|--------|
| `template_id` | string | ✅ | 模板唯一識別碼，只能包含小寫英數字和底線 | `tw_einvoice_v1` |
| `template_name` | string | ✅ | 模板顯示名稱 | `台灣電子發票證明聯` |
| `version` | string | ✅ | 版本號（語義化版本） | `1.0.0` |
| `created_at` | string | ⚠️ | 創建日期（ISO 8601） | `2025-12-23` |
| `updated_at` | string | ❌ | 更新日期 | `2025-12-23` |
| `description` | string | ❌ | 詳細說明 | `適用於...` |
| `processing_strategy` | enum | ✅ | 處理策略 | `hybrid_ocr_roi` |

### `sampling_metadata` 物件

| 欄位 | 類型 | 必填 | 說明 |
|-----|------|------|------|
| `sample_count` | integer | ✅ | 參與統計的樣本數量（≥1） |
| `reference_size` | object | ✅ | 基準圖片大小 |
| `reference_size.width` | integer | ✅ | 基準寬度（像素） |
| `reference_size.height` | integer | ✅ | 基準高度（像素） |
| `reference_size.unit` | enum | ✅ | 單位（目前僅 `pixel`） |
| `size_range` | object | ❌ | 樣本大小範圍（min/max） |
| `sampling_date` | string | ❌ | 取樣日期 |
| `sampler_version` | string | ❌ | 取樣工具版本 |

### `regions.<field_name>` 物件

| 欄位 | 類型 | 必填 | 預設值 | 說明 |
|-----|------|------|--------|------|
| `rect_ratio` | object | ✅ | - | **ROI 相對比例座標** |
| `rect_ratio.x` | number | ✅ | - | X 座標比例（0-1） |
| `rect_ratio.y` | number | ✅ | - | Y 座標比例（0-1） |
| `rect_ratio.width` | number | ✅ | - | 寬度比例（0-1） |
| `rect_ratio.height` | number | ✅ | - | 高度比例（0-1） |
| `rect_std_dev` | object | ❌ | - | 標準差（評估穩定性） |
| `pattern` | string | ❌ | - | 正則表達式 |
| `extract_group` | integer | ❌ | 0 | 捕獲組索引 |
| `expected_length` | integer | ❌ | - | 預期文字長度 |
| `required` | boolean | ❌ | false | 是否必填 |
| `position_weight` | number | ❌ | 0.3 | 位置權重（0-1） |
| `tolerance_ratio` | number | ❌ | 0.2 | 容錯範圍比例 |
| `fallback_pattern` | string | ❌ | - | 降級正則 |
| `data_type` | enum | ❌ | string | 數據類型提示 |
| `validation` | object | ❌ | - | 額外驗證規則 |

---

## 座標轉換公式

### 取樣工具：像素 → 比例

```python
def pixel_to_ratio(pixel_rect, image_size):
    """
    將像素座標轉換為比例座標
    
    Args:
        pixel_rect: {'x': 163, 'y': 957, 'width': 967, 'height': 192}
        image_size: (1169, 1654)  # (width, height)
    
    Returns:
        {'x': 0.1394, 'y': 0.5785, 'width': 0.8273, 'height': 0.1161}
    """
    img_w, img_h = image_size
    
    return {
        'x': round(pixel_rect['x'] / img_w, 4),
        'y': round(pixel_rect['y'] / img_h, 4),
        'width': round(pixel_rect['width'] / img_w, 4),
        'height': round(pixel_rect['height'] / img_h, 4)
    }
```

### 後置處理：比例 → 像素

```python
def ratio_to_pixel(ratio_rect, image_size):
    """
    將比例座標轉換為像素座標
    
    Args:
        ratio_rect: {'x': 0.1394, 'y': 0.5785, 'width': 0.8273, 'height': 0.1161}
        image_size: (1200, 1700)  # 實際圖片大小
    
    Returns:
        {'x': 167, 'y': 983, 'width': 993, 'height': 197}
    """
    img_w, img_h = image_size
    
    return {
        'x': int(ratio_rect['x'] * img_w),
        'y': int(ratio_rect['y'] * img_h),
        'width': int(ratio_rect['width'] * img_w),
        'height': int(ratio_rect['height'] * img_h)
    }
```

### 統計算法：多圖片平均

```python
import statistics

def calculate_template_from_samples(annotations, image_sizes):
    """
    從多張標註圖片計算模板
    
    Args:
        annotations: [
            {'image_id': 0, 'regions': {'field1': {'x': 100, 'y': 200, ...}}},
            {'image_id': 1, 'regions': {'field1': {'x': 105, 'y': 210, ...}}},
            ...
        ]
        image_sizes: [(width1, height1), (width2, height2), ...]
    
    Returns:
        Template dict with rect_ratio and rect_std_dev
    """
    # Step 1: 計算基準大小
    widths = [size[0] for size in image_sizes]
    heights = [size[1] for size in image_sizes]
    
    reference_size = {
        'width': int(statistics.median(widths)),
        'height': int(statistics.median(heights)),
        'unit': 'pixel'
    }
    
    # Step 2: 轉換所有標註為比例座標
    normalized_regions = {}
    
    for annot in annotations:
        img_w, img_h = image_sizes[annot['image_id']]
        
        for field_name, pixel_rect in annot['regions'].items():
            if field_name not in normalized_regions:
                normalized_regions[field_name] = []
            
            ratio = pixel_to_ratio(pixel_rect, (img_w, img_h))
            normalized_regions[field_name].append(ratio)
    
    # Step 3: 計算每個欄位的平均值和標準差
    template_regions = {}
    
    for field_name, ratios in normalized_regions.items():
        template_regions[field_name] = {
            'rect_ratio': {
                'x': round(statistics.mean(r['x'] for r in ratios), 4),
                'y': round(statistics.mean(r['y'] for r in ratios), 4),
                'width': round(statistics.mean(r['width'] for r in ratios), 4),
                'height': round(statistics.mean(r['height'] for r in ratios), 4)
            },
            'rect_std_dev': {
                'x': round(statistics.stdev(r['x'] for r in ratios), 4),
                'y': round(statistics.stdev(r['y'] for r in ratios), 4),
                'width': round(statistics.stdev(r['width'] for r in ratios), 4),
                'height': round(statistics.stdev(r['height'] for r in ratios), 4)
            }
        }
    
    return {
        'sampling_metadata': {
            'sample_count': len(annotations),
            'reference_size': reference_size,
            'size_range': {
                'width': {'min': min(widths), 'max': max(widths)},
                'height': {'min': min(heights), 'max': max(heights)}
            }
        },
        'regions': template_regions
    }
```

---

## 驗證器實作

### Python 驗證器

```python
"""
ocr_pipeline/template/schema_validator.py

模板 JSON Schema 驗證器
"""

import json
from pathlib import Path
from jsonschema import validate, ValidationError, Draft7Validator
from typing import Dict, List, Tuple

class TemplateSchemaValidator:
    """模板 Schema 驗證器"""
    
    def __init__(self, schema_path: str = None):
        """
        Args:
            schema_path: JSON Schema 檔案路徑（可選）
        """
        if schema_path:
            with open(schema_path, 'r', encoding='utf-8') as f:
                self.schema = json.load(f)
        else:
            # 使用內建 schema
            schema_file = Path(__file__).parent.parent.parent / 'config' / 'schemas' / 'template-v1.0.json'
            with open(schema_file, 'r', encoding='utf-8') as f:
                self.schema = json.load(f)
        
        self.validator = Draft7Validator(self.schema)
    
    def validate(self, template: Dict) -> Tuple[bool, List[str]]:
        """
        驗證模板是否符合 Schema
        
        Args:
            template: 模板字典
        
        Returns:
            (is_valid, error_messages)
        """
        errors = list(self.validator.iter_errors(template))
        
        if not errors:
            return True, []
        
        error_messages = [
            f"[{'.'.join(str(p) for p in e.path)}] {e.message}"
            for e in errors
        ]
        
        return False, error_messages
    
    def validate_file(self, template_path: str) -> Tuple[bool, List[str]]:
        """
        驗證模板檔案
        
        Args:
            template_path: 模板 JSON 檔案路徑
        
        Returns:
            (is_valid, error_messages)
        """
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template = json.load(f)
            
            return self.validate(template)
        
        except json.JSONDecodeError as e:
            return False, [f"JSON 解析錯誤: {str(e)}"]
        except FileNotFoundError:
            return False, [f"檔案不存在: {template_path}"]
        except Exception as e:
            return False, [f"未知錯誤: {str(e)}"]
    
    def validate_coordinates(self, template: Dict) -> Tuple[bool, List[str]]:
        """
        額外驗證座標邏輯（Schema 無法檢查的部分）
        
        檢查項目：
        1. rect_ratio 的 x + width <= 1.0
        2. rect_ratio 的 y + height <= 1.0
        3. std_dev 不應該過大（> 0.1 警告）
        
        Args:
            template: 模板字典
        
        Returns:
            (is_valid, warning_messages)
        """
        warnings = []
        
        for field_name, field_config in template.get('regions', {}).items():
            rect = field_config.get('rect_ratio', {})
            
            # 檢查邊界
            if rect.get('x', 0) + rect.get('width', 0) > 1.0:
                warnings.append(
                    f"{field_name}: rect_ratio.x + width = "
                    f"{rect['x'] + rect['width']:.4f} > 1.0（超出圖片範圍）"
                )
            
            if rect.get('y', 0) + rect.get('height', 0) > 1.0:
                warnings.append(
                    f"{field_name}: rect_ratio.y + height = "
                    f"{rect['y'] + rect['height']:.4f} > 1.0（超出圖片範圍）"
                )
            
            # 檢查標準差
            std_dev = field_config.get('rect_std_dev', {})
            for key in ['x', 'y', 'width', 'height']:
                if std_dev.get(key, 0) > 0.1:
                    warnings.append(
                        f"{field_name}: rect_std_dev.{key} = "
                        f"{std_dev[key]:.4f} > 0.1（位置不穩定，建議重新取樣）"
                    )
        
        return len(warnings) == 0, warnings


# 使用範例
if __name__ == '__main__':
    validator = TemplateSchemaValidator()
    
    # 驗證模板檔案
    is_valid, errors = validator.validate_file('config/templates/tw_einvoice_v1.json')
    
    if is_valid:
        print("✅ 模板格式正確")
        
        # 額外驗證座標邏輯
        with open('config/templates/tw_einvoice_v1.json') as f:
            template = json.load(f)
        
        coord_valid, warnings = validator.validate_coordinates(template)
        
        if warnings:
            print("\n⚠️ 座標警告：")
            for w in warnings:
                print(f"  - {w}")
    else:
        print("❌ 模板格式錯誤：")
        for e in errors:
            print(f"  - {e}")
```

---

## 資料類型對照

| `data_type` | 說明 | 預期格式 | 驗證範例 |
|------------|------|---------|---------|
| `string` | 一般文字 | 任意字串 | - |
| `number` | 數字 | 整數或浮點數 | `validation.min_value`, `max_value` |
| `date` | 日期 | YYYY-MM-DD 或民國年 | `2025-12-23`, `114年12月23日` |
| `datetime` | 日期時間 | ISO 8601 | `2025-12-23T14:30:00` |
| `phone` | 電話號碼 | 台灣/國際格式 | `02-12345678`, `+886-2-12345678` |
| `email` | 電子郵件 | Email 格式 | `test@example.com` |
| `tax_id` | 統一編號 | 8 位數字 | `12345678` |
| `custom` | 自訂格式 | 依 pattern 定義 | - |

---

## 版本演進規劃

### v1.0（目前）
- ✅ 相對比例座標系統
- ✅ 基本欄位定義
- ✅ 統計元數據

### v1.1（未來）
- 🔄 錨點系統（anchor_based strategy）
- 🔄 多語言支援（i18n）
- 🔄 條件欄位（conditional regions）

### v2.0（遠期）
- 🔮 AI 輔助標註建議
- 🔮 動態模板（自適應格式變化）
- 🔮 多頁文檔支援

---

## 附錄

### A. 設計決策記錄

| 決策 | 原因 | 備選方案 |
|-----|------|---------|
| **使用相對比例座標** | 適應不同圖片大小 | 絕對像素座標（已排除） |
| **整圖統計策略** | 統一基準，簡化反推 | 單一 ROI 統計（已排除） |
| **中位數作為基準** | 抗極端值干擾 | 平均值（次選） |
| **標準差記錄** | 評估模板穩定性 | - |

### B. 常見問題

#### Q1: 為什麼不用絕對像素座標？
**A**: 因為取樣工具統計的圖片大小不一定等於後置處理時的實際圖片大小，絕對座標會失準。

#### Q2: rect_std_dev 多大算不穩定？
**A**: 建議 > 0.1 時重新取樣，表示該欄位在不同樣本中位置變化超過 10%。

#### Q3: reference_size 用中位數還是平均值？
**A**: 建議用中位數，因為可以抗極端值（如掃描錯誤導致的異常大小）。

#### Q4: 如何處理非等比例縮放的圖片？
**A**: v1.0 暫不支援，建議在前處理階段統一調整為等比例。v1.1 將引入錨點系統解決此問題。

---

**文件維護者**: GitHub Copilot  
**最後更新**: 2025-12-23  
**審核狀態**: 正式規格
