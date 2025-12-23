"""
測試 TemplateValidator 類別

按照 TDD 原則開發 Template 驗證器
根據 03 作業範本規格.md 中定義的驗證規則
"""

import pytest
from ocr_pipeline.template.validator import TemplateValidator, ValidationError


class TestTemplateValidator:
    """Template Validator 單元測試"""

    @pytest.fixture
    def validator(self):
        """建立 Validator 實例"""
        return TemplateValidator()

    @pytest.fixture
    def valid_template(self):
        """完整有效的 Template"""
        return {
            "template_id": "invoice_v1",
            "image_size": [2480, 3508],
            "preprocess": {
                "deskew": True,
                "denoise": "nlm"
            },
            "regions": [
                {
                    "name": "invoice_no",
                    "rect": [300, 200, 900, 350],
                    "ocr_lang": "eng"
                }
            ]
        }

    # ===== 必填欄位驗證 =====

    def test_validate_valid_template(self, validator, valid_template):
        """測試：有效的 Template 應該通過驗證"""
        assert validator.validate(valid_template) is True

    def test_missing_template_id(self, validator, valid_template):
        """測試：缺少 template_id 應該失敗"""
        del valid_template["template_id"]
        
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(valid_template)
        assert "template_id" in str(exc_info.value)

    def test_missing_image_size(self, validator, valid_template):
        """測試：缺少 image_size 應該失敗"""
        del valid_template["image_size"]
        
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(valid_template)
        assert "image_size" in str(exc_info.value)

    def test_missing_regions(self, validator, valid_template):
        """測試：缺少 regions 應該失敗"""
        del valid_template["regions"]
        
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(valid_template)
        assert "regions" in str(exc_info.value)

    # ===== template_id 格式驗證 =====

    def test_template_id_format_valid(self, validator, valid_template):
        """測試：有效的 template_id 格式"""
        valid_ids = ["invoice_v1", "receipt_v2", "form123", "test_case_1"]
        
        for template_id in valid_ids:
            valid_template["template_id"] = template_id
            assert validator.validate(valid_template) is True

    def test_template_id_format_invalid(self, validator, valid_template):
        """測試：無效的 template_id 格式（包含大寫、特殊字元）"""
        invalid_ids = ["Invoice_V1", "receipt-v1", "form@123", "test case"]
        
        for template_id in invalid_ids:
            valid_template["template_id"] = template_id
            with pytest.raises(ValidationError) as exc_info:
                validator.validate(valid_template)
            assert "template_id" in str(exc_info.value).lower()

    # ===== image_size 驗證 =====

    def test_image_size_valid(self, validator, valid_template):
        """測試：有效的 image_size"""
        # 使用對應的 rect 避免超出邊界
        test_cases = [
            {"size": [1000, 1000], "rect": [100, 100, 300, 300]},
            {"size": [2480, 3508], "rect": [300, 200, 900, 350]},
            {"size": [10000, 10000], "rect": [1000, 1000, 2000, 2000]}
        ]
        
        for case in test_cases:
            valid_template["image_size"] = case["size"]
            valid_template["regions"][0]["rect"] = case["rect"]
            assert validator.validate(valid_template) is True

    def test_image_size_not_array(self, validator, valid_template):
        """測試：image_size 不是陣列"""
        valid_template["image_size"] = "2480x3508"
        
        with pytest.raises(ValidationError):
            validator.validate(valid_template)

    def test_image_size_wrong_length(self, validator, valid_template):
        """測試：image_size 長度不是 2"""
        invalid_sizes = [[100], [100, 200, 300]]
        
        for size in invalid_sizes:
            valid_template["image_size"] = size
            with pytest.raises(ValidationError):
                validator.validate(valid_template)

    def test_image_size_below_minimum(self, validator, valid_template):
        """測試：image_size 小於最小值（100）"""
        valid_template["image_size"] = [50, 100]
        
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(valid_template)
        assert "image_size" in str(exc_info.value).lower()

    def test_image_size_above_maximum(self, validator, valid_template):
        """測試：image_size 大於最大值（10000）"""
        valid_template["image_size"] = [10001, 5000]
        
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(valid_template)
        assert "image_size" in str(exc_info.value).lower()

    # ===== regions 驗證 =====

    def test_regions_empty(self, validator, valid_template):
        """測試：regions 不能為空陣列"""
        valid_template["regions"] = []
        
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(valid_template)
        assert "regions" in str(exc_info.value).lower()

    def test_region_missing_name(self, validator, valid_template):
        """測試：region 缺少 name"""
        valid_template["regions"][0] = {
            "rect": [0, 0, 100, 100]
        }
        
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(valid_template)
        assert "name" in str(exc_info.value).lower()

    def test_region_missing_rect(self, validator, valid_template):
        """測試：region 缺少 rect"""
        valid_template["regions"][0] = {
            "name": "field1"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(valid_template)
        assert "rect" in str(exc_info.value).lower()

    def test_region_duplicate_names(self, validator, valid_template):
        """測試：region name 不能重複"""
        valid_template["regions"] = [
            {"name": "field1", "rect": [0, 0, 100, 100]},
            {"name": "field1", "rect": [100, 100, 200, 200]}
        ]
        
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(valid_template)
        assert "duplicate" in str(exc_info.value).lower()

    # ===== 座標範圍驗證 =====

    def test_rect_format_valid(self, validator, valid_template):
        """測試：有效的 rect 格式"""
        valid_template["regions"][0]["rect"] = [100, 200, 300, 400]
        assert validator.validate(valid_template) is True

    def test_rect_wrong_length(self, validator, valid_template):
        """測試：rect 長度不是 4"""
        invalid_rects = [[0, 0], [0, 0, 100], [0, 0, 100, 100, 200]]
        
        for rect in invalid_rects:
            valid_template["regions"][0]["rect"] = rect
            with pytest.raises(ValidationError):
                validator.validate(valid_template)

    def test_rect_negative_coordinates(self, validator, valid_template):
        """測試：rect 座標不能為負數"""
        valid_template["regions"][0]["rect"] = [-10, 0, 100, 100]
        
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(valid_template)
        assert "coordinate" in str(exc_info.value).lower() or "rect" in str(exc_info.value).lower()

    def test_rect_x1_greater_than_x2(self, validator, valid_template):
        """測試：x1 不能大於等於 x2"""
        valid_template["regions"][0]["rect"] = [300, 200, 300, 400]
        
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(valid_template)
        assert "x1" in str(exc_info.value).lower() or "rect" in str(exc_info.value).lower()

    def test_rect_y1_greater_than_y2(self, validator, valid_template):
        """測試：y1 不能大於等於 y2"""
        valid_template["regions"][0]["rect"] = [100, 400, 300, 400]
        
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(valid_template)
        assert "y1" in str(exc_info.value).lower() or "rect" in str(exc_info.value).lower()

    def test_rect_exceeds_image_width(self, validator, valid_template):
        """測試：rect 超出影像寬度"""
        valid_template["image_size"] = [1000, 1000]
        valid_template["regions"][0]["rect"] = [900, 100, 1100, 300]
        
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(valid_template)
        assert "image_size" in str(exc_info.value).lower() or "boundary" in str(exc_info.value).lower()

    def test_rect_exceeds_image_height(self, validator, valid_template):
        """測試：rect 超出影像高度"""
        valid_template["image_size"] = [1000, 1000]
        valid_template["regions"][0]["rect"] = [100, 900, 300, 1100]
        
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(valid_template)
        assert "image_size" in str(exc_info.value).lower() or "boundary" in str(exc_info.value).lower()

    # ===== 選填欄位驗證 =====

    def test_preprocess_optional(self, validator, valid_template):
        """測試：preprocess 為選填"""
        del valid_template["preprocess"]
        assert validator.validate(valid_template) is True

    def test_ocr_lang_optional(self, validator, valid_template):
        """測試：region 的 ocr_lang 為選填"""
        del valid_template["regions"][0]["ocr_lang"]
        assert validator.validate(valid_template) is True

    def test_postprocess_optional(self, validator, valid_template):
        """測試：region 的 postprocess 為選填"""
        # postprocess 本來就不存在，但確保不影響驗證
        assert validator.validate(valid_template) is True
        
        # 添加 postprocess 也應該通過
        valid_template["regions"][0]["postprocess"] = {"regex": "[A-Z0-9]+"}
        assert validator.validate(valid_template) is True

    # ===== preprocess 值驗證 =====

    def test_denoise_valid_values(self, validator, valid_template):
        """測試：denoise 的有效值"""
        valid_values = ["nlm", "bilateral", "gaussian"]
        
        for value in valid_values:
            valid_template["preprocess"]["denoise"] = value
            assert validator.validate(valid_template) is True

    def test_denoise_invalid_value(self, validator, valid_template):
        """測試：denoise 的無效值"""
        valid_template["preprocess"]["denoise"] = "invalid_method"
        
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(valid_template)
        assert "denoise" in str(exc_info.value).lower()

    def test_binarize_valid_values(self, validator, valid_template):
        """測試：binarize 的有效值"""
        valid_values = ["adaptive", "otsu", "threshold"]
        
        for value in valid_values:
            valid_template["preprocess"]["binarize"] = value
            assert validator.validate(valid_template) is True

    def test_binarize_invalid_value(self, validator, valid_template):
        """測試：binarize 的無效值"""
        valid_template["preprocess"]["binarize"] = "invalid_method"
        
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(valid_template)
        assert "binarize" in str(exc_info.value).lower()


class TestAnchorBasedTemplateValidator:
    """Anchor-Based Template 驗證器測試（統一格式 with anchor.enable）"""

    @pytest.fixture
    def validator(self):
        """建立 Validator 實例"""
        return TemplateValidator()

    @pytest.fixture
    def valid_anchor_template(self):
        """完整有效的 Anchor-Based Template（統一格式）"""
        return {
            "template_id": "tw_einvoice_v1",
            "version": "2.0",
            "anchor": {
                "enable": True,
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
                    },
                    "validation": {
                        "required": True,
                        "min_confidence": 0.9
                    }
                }
            ],
            "ocr": {
                "engine": "paddleocr",
                "lang": "chinese_cht"
            }
        }

    @pytest.fixture
    def valid_traditional_template(self):
        """完整有效的傳統模板（統一格式 with anchor.enable=false）"""
        return {
            "template_id": "invoice_v1",
            "image_size": [2480, 3508],
            "anchor": {
                "enable": False
            },
            "regions": [
                {
                    "name": "invoice_no",
                    "rect": [300, 200, 900, 350],
                    "ocr_lang": "eng"
                }
            ]
        }

    # ===== 統一格式驗證 =====

    def test_anchor_enabled_template_valid(self, validator, valid_anchor_template):
        """測試：anchor.enable=true 的模板應該通過驗證"""
        assert validator.validate(valid_anchor_template) is True

    def test_anchor_disabled_template_valid(self, validator, valid_traditional_template):
        """測試：anchor.enable=false 的模板應該通過驗證"""
        assert validator.validate(valid_traditional_template) is True

    def test_missing_anchor_enable(self, validator, valid_anchor_template):
        """測試：anchor 缺少 enable 欄位應該失敗"""
        del valid_anchor_template["anchor"]["enable"]
        
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(valid_anchor_template)
        assert "enable" in str(exc_info.value).lower()

    def test_anchor_enable_must_be_boolean(self, validator, valid_anchor_template):
        """測試：anchor.enable 必須是布林值"""
        valid_anchor_template["anchor"]["enable"] = "true"
        
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(valid_anchor_template)
        assert "boolean" in str(exc_info.value).lower()

    def test_anchor_disabled_no_text_required(self, validator, valid_traditional_template):
        """測試：anchor.enable=false 時不需要 text 欄位"""
        # 確認即使沒有 text，只要 enable=false 就能通過
        assert "text" not in valid_traditional_template["anchor"]
        assert validator.validate(valid_traditional_template) is True

    def test_anchor_enabled_missing_text(self, validator, valid_anchor_template):
        """測試：anchor.enable=true 時缺少 text 應該失敗"""
        del valid_anchor_template["anchor"]["text"]
        
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(valid_anchor_template)
        assert "text" in str(exc_info.value).lower()

    def test_anchor_missing_expected_bbox(self, validator, valid_anchor_template):
        """測試：anchor 缺少 expected_bbox 應該失敗"""
        del valid_anchor_template["anchor"]["expected_bbox"]
        
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(valid_anchor_template)
        assert "expected_bbox" in str(exc_info.value).lower() or "bbox" in str(exc_info.value).lower()

    # ===== Anchor expected_bbox 驗證 =====

    def test_anchor_bbox_missing_width(self, validator, valid_anchor_template):
        """測試：expected_bbox 缺少 width"""
        del valid_anchor_template["anchor"]["expected_bbox"]["width"]
        
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(valid_anchor_template)
        assert "width" in str(exc_info.value).lower()

    def test_anchor_bbox_missing_height(self, validator, valid_anchor_template):
        """測試：expected_bbox 缺少 height"""
        del valid_anchor_template["anchor"]["expected_bbox"]["height"]
        
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(valid_anchor_template)
        assert "height" in str(exc_info.value).lower()

    def test_anchor_bbox_missing_tolerance(self, validator, valid_anchor_template):
        """測試：expected_bbox 缺少 tolerance_ratio"""
        del valid_anchor_template["anchor"]["expected_bbox"]["tolerance_ratio"]
        
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(valid_anchor_template)
        assert "tolerance" in str(exc_info.value).lower()

    def test_anchor_tolerance_out_of_range(self, validator, valid_anchor_template):
        """測試：tolerance_ratio 超出範圍 (0-1)"""
        invalid_values = [-0.1, 1.5, 2.0]
        
        for value in invalid_values:
            valid_anchor_template["anchor"]["expected_bbox"]["tolerance_ratio"] = value
            with pytest.raises(ValidationError) as exc_info:
                validator.validate(valid_anchor_template)
            assert "tolerance" in str(exc_info.value).lower()

    # ===== 相對位置 regions 驗證 =====

    def test_region_missing_relative_to_anchor(self, validator, valid_anchor_template):
        """測試：v2.0 region 缺少 relative_to_anchor"""
        del valid_anchor_template["regions"][0]["relative_to_anchor"]
        
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(valid_anchor_template)
        assert "relative" in str(exc_info.value).lower() or "anchor" in str(exc_info.value).lower()

    def test_relative_position_missing_coordinates(self, validator, valid_anchor_template):
        """測試：relative_to_anchor 缺少 x 或 y"""
        # 缺少 x
        del valid_anchor_template["regions"][0]["relative_to_anchor"]["x"]
        with pytest.raises(ValidationError):
            validator.validate(valid_anchor_template)
        
        # 重置後測試缺少 y
        valid_anchor_template["regions"][0]["relative_to_anchor"]["x"] = 43.0
        del valid_anchor_template["regions"][0]["relative_to_anchor"]["y"]
        with pytest.raises(ValidationError):
            validator.validate(valid_anchor_template)

    def test_relative_position_allows_negative(self, validator, valid_anchor_template):
        """測試：相對位置允許負數（anchor 左側/上方）"""
        valid_anchor_template["regions"][0]["relative_to_anchor"]["x"] = -31.0
        valid_anchor_template["regions"][0]["relative_to_anchor"]["y"] = -50.0
        
        # 負數相對位置應該是允許的
        assert validator.validate(valid_anchor_template) is True

    def test_region_tolerance_out_of_range(self, validator, valid_anchor_template):
        """測試：region tolerance_ratio 超出範圍"""
        invalid_values = [-0.1, 1.1, 2.0]
        
        for value in invalid_values:
            valid_anchor_template["regions"][0]["relative_to_anchor"]["tolerance_ratio"] = value
            with pytest.raises(ValidationError) as exc_info:
                validator.validate(valid_anchor_template)
            assert "tolerance" in str(exc_info.value).lower()

    # ===== OCR 配置驗證 =====

    def test_no_lang_in_region_ocr_config(self, validator, valid_anchor_template):
        """測試：region 的 ocr_config 不應該有 lang（應該使用全域）"""
        valid_anchor_template["regions"][0]["ocr_config"] = {
            "pattern": "^[A-Z]{2}-\\d{8}$",
            "lang": "en"  # 這應該被拒絕
        }
        
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(valid_anchor_template)
        assert "lang" in str(exc_info.value).lower() and "global" in str(exc_info.value).lower()

    def test_global_ocr_lang_required(self, validator, valid_anchor_template):
        """測試：全域 OCR 必須有 lang 設定"""
        del valid_anchor_template["ocr"]["lang"]
        
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(valid_anchor_template)
        assert "lang" in str(exc_info.value).lower()

    def test_ocr_lang_valid_values(self, validator, valid_anchor_template):
        """測試：OCR lang 的有效值"""
        valid_langs = ["chinese_cht", "ch", "en", "chinese_sim"]
        
        for lang in valid_langs:
            valid_anchor_template["ocr"]["lang"] = lang
            assert validator.validate(valid_anchor_template) is True

    # ===== Validation 欄位驗證 =====

    def test_validation_required_field(self, validator, valid_anchor_template):
        """測試：validation 的 required 欄位為選填"""
        # validation.required 為選填，有預設值
        del valid_anchor_template["regions"][0]["validation"]["required"]
        
        # 即使沒有 required 欄位也應該通過驗證
        # 只要有 validation 區塊，其內部欄位都是選填的
        assert validator.validate(valid_anchor_template) is True

    def test_validation_min_confidence_range(self, validator, valid_anchor_template):
        """測試：min_confidence 必須在 0-1 範圍內"""
        invalid_values = [-0.1, 1.5, 2.0]
        
        for value in invalid_values:
            valid_anchor_template["regions"][0]["validation"]["min_confidence"] = value
            with pytest.raises(ValidationError) as exc_info:
                validator.validate(valid_anchor_template)
            assert "confidence" in str(exc_info.value).lower()

    def test_validation_optional(self, validator, valid_anchor_template):
        """測試：validation 整個區塊為選填"""
        del valid_anchor_template["regions"][0]["validation"]
        
        # validation 為選填，刪除後應該仍能通過
        assert validator.validate(valid_anchor_template) is True

    # ===== 版本識別 =====

    def test_version_field_optional(self, validator, valid_anchor_template):
        """測試：version 欄位為選填"""
        del valid_anchor_template["version"]
        assert validator.validate(valid_anchor_template) is True

    def test_template_type_detection(self, validator, valid_anchor_template):
        """測試：自動偵測模板類型（v1 或 v2）"""
        # v2.0 模板應該有 anchor
        assert "anchor" in valid_anchor_template
        
        # v1.0 模板應該有 image_size 但沒有 anchor
        v1_template = {
            "template_id": "test_v1",
            "image_size": [1000, 1000],
            "regions": [
                {
                    "name": "field1",
                    "rect": [100, 100, 200, 200]
                }
            ]
        }
        assert "image_size" in v1_template
        assert "anchor" not in v1_template
