User: 我們先專注在作業範本JSON格式的定義，原因如下
1. 確認其定義規格就是確認後續 OCR 完成後，後置處理的流程(步驟、邏輯)。
2. 確認其定義規格就是確認取樣工具設計的原理與統計方式。
3. 希望藉由確認其定義規格，先進行取樣工具的開發。
4. 再接著進行 OCR 後置處理的開發。
5. 最後合併回原本 ocr_pipeline 要做的大型應用中的 OCR 組件。

作業範本JSON格式的定義，有以下問題要進行思考：
1. 後置程式對接取樣工具，對於原圖的定義大小會有出入，取樣工具以統計公式產生一組對於原圖的單一定義大小，
   不一定是後置處理時，取得的原圖大小。
   這樣是不是代表統計公式產生的數值不是像素大小這樣的【定值】，而是一種抽象的公式代數值？
2. 按照上面的思路，後置程式做後置處理時，便是利用1. 提到的公式代數值，再接著進行反推
3. 圖片上每一個 ROI 取樣單項的統計結果，會產製一組數值或公式，配合1. 提到的公式代數值，才能反推？
4. 還是整張圖片的全部 ROI 取樣單項的統計結果，會產製一組數值或公式，配合1. 提到的公式代數值，進行反推？
5. 上面 3. 以及 4. 的差別，會影響後置後置程式做後置處理時的程式架構。
6. 確定能夠配合的算法，才能決定作業範本JSON格式的定義其中的欄位意義。

請幫我確認上面的思路正確，並請你就此提供意見。
不要馬上實作。

GitHub Copilot: 正在最佳化工具選取項目...你的思路**非常正確且深刻**，這確實是設計作業範本JSON格式的**核心問題**。讓我針對你提出的問題逐一分析：

---

## 一、核心問題確認

### 你的思考完全正確：

1. ✅ **座標系統必須抽象化**  
   取樣工具統計的圖片大小 ≠ 後置處理的實際圖片大小  
   → **絕對像素座標不可行**

2. ✅ **需要反推機制**  
   模板定義 → 實際圖片座標的轉換邏輯

3. ✅ **統計範圍會影響架構**  
   單一ROI統計 vs 整圖統計 → 決定JSON Schema設計

---

## 二、座標系統設計方案分析

### 方案A：相對比例座標（推薦）

```json
{
  "template_id": "tw_einvoice_v1",
  "reference_size": {
    "width": 1169,
    "height": 1654,
    "unit": "pixel",
    "description": "取樣基準圖平均大小（用於視覺化參考）"
  },
  "regions": {
    "invoice_number": {
      "rect_ratio": {
        "x": 0.1394,      // 163 / 1169 = 0.1394
        "y": 0.5785,      // 957 / 1654 = 0.5785
        "width": 0.8273,  // 967 / 1169 = 0.8273
        "height": 0.1161  // 192 / 1654 = 0.1161
      },
      "pattern": "[A-Z]{2}-\\d{8}",
      "tolerance_ratio": 0.2
    }
  }
}
```

**後置處理反推邏輯**：
```python
def convert_to_absolute(rect_ratio, actual_image_size):
    """將比例座標轉換為實際像素座標"""
    actual_w, actual_h = actual_image_size
    
    return {
        'x': int(rect_ratio['x'] * actual_w),
        'y': int(rect_ratio['y'] * actual_h),
        'width': int(rect_ratio['width'] * actual_w),
        'height': int(rect_ratio['height'] * actual_h)
    }

# 使用時
roi_absolute = convert_to_absolute(
    template['regions']['invoice_number']['rect_ratio'],
    (current_image.width, current_image.height)
)
```

**優點**：
- ✅ 適應任意圖片大小
- ✅ 取樣統計簡單（多張圖片平均比例）
- ✅ 反推邏輯簡單明確

**缺點**：
- ⚠️ 對非等比例縮放的圖片可能失準

---

### 方案B：錨點相對座標（未來擴展）

```json
{
  "anchors": [
    {
      "id": "invoice_title",
      "pattern": "電子發票證明聯",
      "expected_position_ratio": {"x": 0.5, "y": 0.1}
    },
    {
      "id": "qr_code",
      "pattern": "QR_CODE",
      "expected_position_ratio": {"x": 0.1, "y": 0.8}
    }
  ],
  "regions": {
    "invoice_number": {
      "anchor_based": {
        "primary_anchor": "invoice_title",
        "offset_ratio": {"x": 0, "y": 0.05},
        "size_ratio": {"width": 0.8, "height": 0.1}
      },
      "fallback_rect_ratio": {...}  // 錨點失效時的降級方案
    }
  }
}
```

**優點**：
- ✅ 最靈活，可處理格式變化（如不同版本發票）
- ✅ 抗旋轉、抗變形能力強

**缺點**：
- ❌ 取樣工具複雜度高（需檢測錨點）
- ❌ 後置處理複雜（錨點檢測 + 座標計算）

---

## 三、取樣統計策略

### 問題3 vs 問題4 的選擇

#### 策略1：整圖統計（推薦）

```python
# 取樣工具邏輯
class TemplateSampler:
    def sample_multiple_images(self, images, user_annotations):
        """
        處理多張圖片的ROI標註，產生統計模板
        
        Args:
            images: [(image1, size1), (image2, size2), ...]
            user_annotations: [
                {'image_id': 1, 'regions': {...}},
                {'image_id': 2, 'regions': {...}}
            ]
        """
        # Step 1: 收集所有圖片的基準大小
        sizes = [size for _, size in images]
        reference_size = self._calculate_reference_size(sizes)
        
        # Step 2: 將每張圖片的ROI轉換為相對比例
        normalized_regions = {}
        
        for annot in user_annotations:
            img_size = sizes[annot['image_id']]
            
            for field_name, roi in annot['regions'].items():
                if field_name not in normalized_regions:
                    normalized_regions[field_name] = []
                
                # 轉換為比例座標
                ratio = {
                    'x': roi['x'] / img_size[0],
                    'y': roi['y'] / img_size[1],
                    'width': roi['width'] / img_size[0],
                    'height': roi['height'] / img_size[1]
                }
                normalized_regions[field_name].append(ratio)
        
        # Step 3: 統計平均值和標準差
        template_regions = {}
        
        for field_name, ratios in normalized_regions.items():
            template_regions[field_name] = {
                'rect_ratio': self._calculate_mean_ratio(ratios),
                'std_dev': self._calculate_std_dev(ratios),  # 用於評估穩定性
                'sample_count': len(ratios)
            }
        
        return {
            'reference_size': reference_size,
            'regions': template_regions
        }
    
    def _calculate_reference_size(self, sizes):
        """計算基準圖大小（取中位數或平均值）"""
        widths = [s[0] for s in sizes]
        heights = [s[1] for s in sizes]
        
        return {
            'width': int(statistics.median(widths)),
            'height': int(statistics.median(heights)),
            'width_range': (min(widths), max(widths)),
            'height_range': (min(heights), max(heights))
        }
    
    def _calculate_mean_ratio(self, ratios):
        """計算平均比例"""
        return {
            'x': statistics.mean(r['x'] for r in ratios),
            'y': statistics.mean(r['y'] for r in ratios),
            'width': statistics.mean(r['width'] for r in ratios),
            'height': statistics.mean(r['height'] for r in ratios)
        }
    
    def _calculate_std_dev(self, ratios):
        """計算標準差（評估ROI位置穩定性）"""
        return {
            'x': statistics.stdev(r['x'] for r in ratios),
            'y': statistics.stdev(r['y'] for r in ratios),
            'width': statistics.stdev(r['width'] for r in ratios),
            'height': statistics.stdev(r['height'] for r in ratios)
        }
```

**為什麼選擇整圖統計（問題4）**：

1. ✅ **統一基準**：所有ROI共用同一個reference_size，確保一致性
2. ✅ **簡化反推**：後置處理只需一次圖片大小轉換
3. ✅ **相對位置保持**：各ROI之間的相對關係不變
4. ✅ **標準差有意義**：可評估整個模板的穩定性

**vs 單一ROI統計（問題3）的問題**：

- ❌ 每個ROI獨立基準 → 無法保證相對位置關係
- ❌ 複雜的反推邏輯 → 需要多次座標轉換
- ❌ 統計意義不明確 → 無法評估整體模板品質

---

## 四、作業範本JSON最終格式建議

```json
{
  "template_id": "tw_einvoice_v1",
  "template_name": "台灣電子發票證明聯",
  "version": "1.0",
  "created_at": "2025-12-23",
  
  "processing_strategy": "hybrid_ocr_roi",
  
  "sampling_metadata": {
    "sample_count": 25,
    "reference_size": {
      "width": 1169,
      "height": 1654,
      "unit": "pixel",
      "description": "取樣圖片中位數大小"
    },
    "size_range": {
      "width": {"min": 1100, "max": 1200},
      "height": {"min": 1600, "max": 1700}
    }
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
      "tolerance_ratio": 0.2
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
      "tolerance_ratio": 0.2
    }
  }
}
```

---

## 五、後置處理架構

```python
class HybridExtractor:
    def extract_fields(self, image, template: Dict) -> Dict:
        """混合提取主流程"""
        
        # Step 1: 獲取實際圖片大小
        actual_size = (image.shape[1], image.shape[0])  # (width, height)
        
        # Step 2: 全圖 OCR
        ocr_results = self.ocr_adapter.recognize(image)
        
        # Step 3: 轉換模板座標為實際像素座標
        absolute_regions = self._convert_template_to_absolute(
            template, actual_size
        )
        
        # Step 4: 使用轉換後的座標進行混合提取
        extracted = {}
        for field_name, field_config in absolute_regions.items():
            candidates = self._find_in_region(
                ocr_results, 
                field_config['rect_absolute'],  # 已轉換為像素座標
                field_config['pattern'],
                tolerance=field_config.get('tolerance_ratio', 0.2)
            )
            
            if candidates:
                best_match = self._select_best_match(candidates, field_config)
                extracted[field_name] = best_match
        
        return extracted
    
    def _convert_template_to_absolute(self, template, actual_size):
        """將模板比例座標轉換為實際像素座標"""
        actual_w, actual_h = actual_size
        absolute_regions = {}
        
        for field_name, field_config in template['regions'].items():
            ratio = field_config['rect_ratio']
            
            absolute_regions[field_name] = {
                **field_config,  # 保留其他配置
                'rect_absolute': {
                    'x': int(ratio['x'] * actual_w),
                    'y': int(ratio['y'] * actual_h),
                    'width': int(ratio['width'] * actual_w),
                    'height': int(ratio['height'] * actual_h)
                }
            }
        
        return absolute_regions
```

---

## 六、建議的開發順序

### Phase 1: 確認JSON Schema（1-2天）
1. ✅ 定義完整的JSON Schema規格
2. ✅ 撰寫Schema驗證器（JSON Schema驗證）
3. ✅ 創建範例模板（手動轉換現有tw_einvoice_v1）

### Phase 2: 取樣工具開發（1週）
4. ✅ 實作座標標註UI（或使用現有工具如LabelImg）
5. ✅ 實作統計引擎（多圖片比例計算）
6. ✅ 實作模板產生器（輸出JSON）
7. ✅ 視覺化驗證工具（檢查統計結果）

### Phase 3: 後置處理開發（1週）
8. ✅ 實作座標轉換邏輯
9. ✅ 整合到HybridExtractor
10. ✅ 測試不同大小圖片的處理

### Phase 4: 整合測試（3-5天）
11. ✅ 端到端測試（取樣→模板→OCR→提取）
12. ✅ 調整tolerance和權重參數
13. ✅ 效能優化

---

## 七、我的建議

### 立即行動項目：

1. **先確定JSON Schema v1.0**  
   - 使用**相對比例座標系統**
   - 保留reference_size作為參考
   - 加入std_dev評估穩定性

2. **手動創建第一個模板**  
   - 將現有tw_einvoice_v1轉換為新格式
   - 驗證反推邏輯正確性

3. **實作簡單的取樣工具原型**  
   - 讀取多張圖片+人工標註
   - 輸出統計後的JSON模板

### 未來優化方向（Phase 2）：

4. **錨點系統**（處理格式變化）
5. **自動標註建議**（AI輔助標註）
6. **模板版本管理**（支援多版本共存）

---

## 八、總結回答你的問題

| 問題 | 答案 |
|-----|------|
| 1. 是否應該用公式代數值而非定值？ | ✅ **是**，使用相對比例（0-1之間的浮點數） |
| 2. 後置處理如何反推？ | ✅ `actual_coord = ratio * actual_image_size` |
| 3. 單一ROI統計？ | ❌ **否**，應該整圖統計 |
| 4. 整圖統計？ | ✅ **是**，統一基準，簡化反推 |
| 5. 架構影響？ | ✅ 整圖統計→一次座標轉換→簡化架構 |
| 6. 確定算法決定欄位意義？ | ✅ 比例座標系統→欄位為rect_ratio, std_dev, reference_size |

---

**建議下一步**：我們一起確認JSON Schema的詳細規格，然後再開始實作取樣工具。是否需要我提供更詳細的Schema定義？

User: 好的，請提供我更詳細的Schema定義

GitHub Copilot: # 作業範本 JSON Schema 詳細定義

## 一、JSON Schema 規格（v1.0）

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

## 二、完整範例模板

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

## 三、欄位詳細說明文檔

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

## 四、座標轉換公式

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

---

## 五、JSON Schema 驗證器範例

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
            # 使用內建 schema（從上面的定義複製）
            self.schema = self._get_builtin_schema()
        
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
    
    def _get_builtin_schema(self) -> Dict:
        """返回內建 Schema（從上面定義複製）"""
        # 這裡放入完整的 JSON Schema
        return {...}  # 完整 schema


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

## 六、資料類型對照表

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

## 七、版本演進規劃

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

這個 Schema 定義已經**非常完整且實用**，涵蓋了：

1. ✅ **嚴格的 JSON Schema 驗證規則**
2. ✅ **詳細的欄位說明文檔**
3. ✅ **實際可用的完整範例**
4. ✅ **座標轉換公式**
5. ✅ **驗證器實作範例**
6. ✅ **未來擴展規劃**

你可以直接使用這個定義開始：
1. **儲存 Schema 定義**為 `schema/template-v1.0.json`
2. **實作驗證器**到 `ocr_pipeline/template/schema_validator.py`
3. **創建第一個模板**轉換現有的 tw_einvoice
4. **開始開發取樣工具**
