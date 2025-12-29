"""
測試 TemplateValidator 類別

按照 TDD 原則開發 Template 驗證器
根據 03 作業範本規格.md 中定義的驗證規則
"""

import pytest
from ocr_pipeline.template.validator import TemplateValidator, ValidationError





class TestTemplateValidator:
    def test_missing_required_fields_exception(self, validator, valid_template):
        for field in ["template_id", "template_name", "version", "processing_strategy", "sampling_metadata", "regions"]:
            t = dict(valid_template)
            t.pop(field)
            with pytest.raises(ValidationError):
                validator.validate(t)

    def test_template_id_type_and_format_exception(self, validator, valid_template):
        t = dict(valid_template)
        t["template_id"] = 123
        with pytest.raises(ValidationError):
            validator.validate(t)
        t["template_id"] = "Invalid-ID"
        with pytest.raises(ValidationError):
            validator.validate(t)

    def test_version_type_and_format_exception(self, validator, valid_template):
        t = dict(valid_template)
        t["version"] = 1.0
        with pytest.raises(ValidationError):
            validator.validate(t)
        t["version"] = "v1.0"
        with pytest.raises(ValidationError):
            validator.validate(t)

    def test_processing_strategy_type_and_enum_exception(self, validator, valid_template):
        t = dict(valid_template)
        t["processing_strategy"] = 123
        with pytest.raises(ValidationError):
            validator.validate(t)
        t["processing_strategy"] = "not_exist"
        with pytest.raises(ValidationError):
            validator.validate(t)

    def test_sampling_metadata_type_and_required_fields_exception(self, validator, valid_template):
        t = dict(valid_template)
        t["sampling_metadata"] = "not_a_dict"
        with pytest.raises(ValidationError):
            validator.validate(t)
        meta = dict(valid_template["sampling_metadata"])
        meta.pop("sample_count")
        t["sampling_metadata"] = meta
        with pytest.raises(ValidationError):
            validator.validate(t)

    def test_regions_type_and_empty_exception(self, validator, valid_template):
        t = dict(valid_template)
        t["regions"] = []
        with pytest.raises(ValidationError):
            validator.validate(t)
        t["regions"] = {}
        with pytest.raises(ValidationError):
            validator.validate(t)

    def test_region_rect_ratio_missing_and_type_exception(self, validator, valid_template):
        region = dict(valid_template["regions"]["invoice_number"])
        region.pop("rect_ratio")
        valid_template["regions"]["invoice_number"] = region
        with pytest.raises(ValidationError):
            validator.validate(valid_template)
        region["rect_ratio"] = "not_a_dict"
        valid_template["regions"]["invoice_number"] = region
        with pytest.raises(ValidationError):
            validator.validate(valid_template)

    def test_rect_ratio_value_range_exception(self, validator, valid_template):
        region = dict(valid_template["regions"]["invoice_number"])
        region["rect_ratio"] = {"x": 1.1, "y": 0.5, "width": 0.5, "height": 0.5}
        valid_template["regions"]["invoice_number"] = region
        with pytest.raises(ValidationError):
            validator.validate(valid_template)
    def test_region_all_optional_fields_none(self, validator, valid_template):
        region = dict(valid_template["regions"]["invoice_number"])
        region.update({
            "pattern": None,
            "data_type": None,
            "extract_group": None,
            "expected_length": None,
            "required": None,
            "position_weight": None,
            "tolerance_ratio": None,
            "fallback_pattern": None,
            "description": None,
            "validation": None,
            "rect_std_dev": None
        })
        valid_template["regions"]["invoice_number"] = region
        valid_template["sampling_metadata"]["notes"] = None
        assert validator.validate(valid_template) is True

    def test_rect_std_dev_valid(self, validator, valid_template):
        region = dict(valid_template["regions"]["invoice_number"])
        region["rect_std_dev"] = {"x": 0.01, "y": 0.02, "width": 0.03, "height": 0.04}
        valid_template["regions"]["invoice_number"] = region
        assert validator.validate(valid_template) is True

    def test_preprocess_valid(self, validator, valid_template):
        valid_template["preprocess"] = {"denoise": "nlm", "binarize": "otsu"}
        assert validator.validate(valid_template) is True

    def test_region_validation_object(self, validator, valid_template):
        region = dict(valid_template["regions"]["invoice_number"])
        region["validation"] = {
            "min_length": 1,
            "max_length": 10,
            "min_value": 0,
            "max_value": 100,
            "allowed_values": ["A", "B"]
        }
        valid_template["regions"]["invoice_number"] = region
        assert validator.validate(valid_template) is True

    def test_region_all_optional_fields(self, validator, valid_template):
        region = dict(valid_template["regions"]["invoice_number"])
        region.update({
            "pattern": r"\\d+",
            "extract_group": 1,
            "expected_length": 8,
            "required": True,
            "position_weight": 0.5,
            "tolerance_ratio": 0.1,
            "fallback_pattern": r"[A-Z]+",
            "data_type": "string",
            "description": "測試欄位"
        })
        valid_template["regions"]["invoice_number"] = region
        assert validator.validate(valid_template) is True

    """新版 Template Validator 單元測試 (v1.0 採樣格式)"""

    @pytest.fixture
    def validator(self):
        return TemplateValidator()

    @pytest.fixture
    def valid_template(self):
        return {
            "template_id": "invoice_v1",
            "template_name": "台灣電子發票證明聯",
            "version": "1.0.0",
            "processing_strategy": "hybrid_ocr_roi",
            "sampling_metadata": {
                "sample_count": 2,
                "reference_size": {
                    "width": 1200,
                    "height": 1915,
                    "unit": "pixel"
                },
                "size_range": {
                    "width": {"min": 1200, "max": 1200},
                    "height": {"min": 1904, "max": 1927}
                },
                "sampling_date": "2025-12-27",
                "sampler_version": "1.0.0",
                "notes": None
            },
            "regions": {
                "invoice_number": {
                    "rect_ratio": {"x": 0.18, "y": 0.4487, "width": 0.625, "height": 0.0715},
                    "rect_std_dev": {"x": 0.0047, "y": 0.0057, "width": 0.0378, "height": 0.0028},
                    "pattern": None,
                    "extract_group": 0,
                    "expected_length": None,
                    "required": False,
                    "position_weight": 0.3,
                    "tolerance_ratio": 0.2,
                    "fallback_pattern": None,
                    "data_type": "string",
                    "description": None,
                    "validation": {
                        "min_length": 8,
                        "max_length": 10,
                        "allowed_values": ["AA-12345678", "BB-87654321"]
                    }
                }
            },
            "preprocess": {
                "denoise": "nlm",
                "binarize": "adaptive"
            }
        }

    def test_validate_valid_template(self, validator, valid_template):
        assert validator.validate(valid_template) is True

    def test_missing_required_fields(self, validator, valid_template):
        for field in ["template_id", "template_name", "version", "processing_strategy", "sampling_metadata", "regions"]:
            t = dict(valid_template)
            t.pop(field)
            with pytest.raises(ValidationError) as exc_info:
                validator.validate(t)
            assert field in str(exc_info.value)

    def test_template_id_format(self, validator, valid_template):
        valid_template["template_id"] = "valid_id_123"
        assert validator.validate(valid_template) is True
        valid_template["template_id"] = "InvalidID"
        with pytest.raises(ValidationError):
            validator.validate(valid_template)

    def test_template_name_length(self, validator, valid_template):
        valid_template["template_name"] = "A"
        assert validator.validate(valid_template) is True
        valid_template["template_name"] = ""
        with pytest.raises(ValidationError):
            validator.validate(valid_template)

    def test_version_format(self, validator, valid_template):
        valid_template["version"] = "1.2.3"
        assert validator.validate(valid_template) is True
        valid_template["version"] = "v1.0"
        with pytest.raises(ValidationError):
            validator.validate(valid_template)

    def test_processing_strategy_enum(self, validator, valid_template):
        valid_template["processing_strategy"] = "fixed_roi"
        assert validator.validate(valid_template) is True
        valid_template["processing_strategy"] = "unknown"
        with pytest.raises(ValidationError):
            validator.validate(valid_template)

    def test_sampling_metadata_required(self, validator, valid_template):
        meta = dict(valid_template["sampling_metadata"])
        meta.pop("sample_count")
        t = dict(valid_template)
        t["sampling_metadata"] = meta
        with pytest.raises(ValidationError):
            validator.validate(t)

    def test_regions_dict_and_duplicate(self, validator, valid_template):
        valid_template["regions"] = {
            "field1": valid_template["regions"]["invoice_number"],
            "field2": valid_template["regions"]["invoice_number"]
        }
        assert validator.validate(valid_template) is True
        # regions 應為 dict，key 唯一，value 為 region 設定
        region1 = {
            "rect_ratio": {"x": 0.1, "y": 0.2, "width": 0.3, "height": 0.4},
            "data_type": "string"
        }
        region2 = {
            "rect_ratio": {"x": 0.5, "y": 0.6, "width": 0.2, "height": 0.1},
            "data_type": "string"
        }
        valid_template["regions"] = {
            "field1": region1,
            "field2": region2
        }
        assert validator.validate(valid_template) is True

    def test_rect_ratio_required_and_range(self, validator, valid_template):
        region = dict(valid_template["regions"]["invoice_number"])
        region["rect_ratio"] = {"x": 1.1, "y": 0.5, "width": 0.5, "height": 0.5}
        valid_template["regions"]["invoice_number"] = region
        with pytest.raises(ValidationError):
            validator.validate(valid_template)

    def test_rect_std_dev_optional(self, validator, valid_template):
        region = dict(valid_template["regions"]["invoice_number"])
        region["rect_std_dev"] = {"x": 0.1, "y": 0.1, "width": 0.1, "height": 0.1}
        valid_template["regions"]["invoice_number"] = region
        assert validator.validate(valid_template) is True
        region["rect_std_dev"] = {"x": -0.1, "y": 0.1, "width": 0.1, "height": 0.1}
        valid_template["regions"]["invoice_number"] = region
        with pytest.raises(ValidationError):
            validator.validate(valid_template)

    def test_validation_fields(self, validator, valid_template):
        region = dict(valid_template["regions"]["invoice_number"])
        region["validation"] = {
            "min_length": 1,
            "max_length": 10,
            "min_value": 0,
            "max_value": 100,
            "allowed_values": ["A", "B"]
        }
        valid_template["regions"]["invoice_number"] = region
        assert validator.validate(valid_template) is True
        region["validation"]["min_length"] = -1
        valid_template["regions"]["invoice_number"] = region
        with pytest.raises(ValidationError):
            validator.validate(valid_template)

    def test_preprocess_optional_and_values(self, validator, valid_template):
        t = dict(valid_template)
        t.pop("preprocess")
        assert validator.validate(t) is True
        valid_template["preprocess"]["denoise"] = "invalid"
        with pytest.raises(ValidationError):
            validator.validate(valid_template)
        valid_template["preprocess"]["denoise"] = "nlm"
        valid_template["preprocess"]["binarize"] = "invalid"
        with pytest.raises(ValidationError):
            validator.validate(valid_template)


