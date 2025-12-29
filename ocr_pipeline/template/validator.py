"""
Template Validator - 驗證 Template JSON

根據 03 作業範本規格.md 實作完整的驗證邏輯
"""

import re
from typing import Dict, Any, List


class ValidationError(Exception):
    """驗證錯誤例外"""
    pass



class TemplateValidator:
    """
    Template 驗證器 (僅支援新版 v1.0 採樣格式)
    """

    VALID_DENOISE_METHODS = ["nlm", "bilateral", "gaussian"]
    VALID_BINARIZE_METHODS = ["adaptive", "otsu", "threshold"]
    TEMPLATE_ID_PATTERN = re.compile(r'^[a-z0-9_]+$')

    def validate(self, data: Dict[str, Any]) -> bool:
        """
        驗證新版 v1.0 採樣格式範本（完整 metadata 與 regions 驗證）
        """
        # 必填欄位
        required_fields = [
            "template_id", "template_name", "version", "processing_strategy", "sampling_metadata", "regions"
        ]
        for field in required_fields:
            if field not in data:
                raise ValidationError(f"Missing required field: {field}")

        self._validate_template_id(data["template_id"])
        self._validate_template_name(data["template_name"])
        self._validate_version(data["version"])
        self._validate_processing_strategy(data["processing_strategy"])
        self._validate_sampling_metadata(data["sampling_metadata"])
        self._validate_regions(data["regions"])

        # 可選欄位
        if "preprocess" in data:
            self._validate_preprocess(data["preprocess"])

        return True

    def _validate_template_name(self, name: Any) -> None:
        if not isinstance(name, str):
            raise ValidationError("template_name must be a string")
        if not (1 <= len(name) <= 100):
            raise ValidationError("template_name length must be 1~100")

    def _validate_version(self, version: Any) -> None:
        if not isinstance(version, str):
            raise ValidationError("version must be a string")
        if not re.match(r'^\d+\.\d+(\.\d+)?$', version):
            raise ValidationError("version must match semantic version format, e.g. 1.0.0")

    def _validate_processing_strategy(self, strategy: Any) -> None:
        allowed = ["hybrid_ocr_roi", "fixed_roi", "full_ocr_only", "anchor_based"]
        if not isinstance(strategy, str):
            raise ValidationError("processing_strategy must be a string")
        if strategy not in allowed:
            raise ValidationError(f"processing_strategy must be one of: {', '.join(allowed)}")

    def _validate_sampling_metadata(self, meta: Any) -> None:
        if not isinstance(meta, dict):
            raise ValidationError("sampling_metadata must be an object")
        if "sample_count" not in meta or not isinstance(meta["sample_count"], int) or meta["sample_count"] < 1:
            raise ValidationError("sampling_metadata.sample_count must be integer >= 1")
        if "reference_size" not in meta or not isinstance(meta["reference_size"], dict):
            raise ValidationError("sampling_metadata.reference_size must be object")
        rs = meta["reference_size"]
        for k in ["width", "height", "unit"]:
            if k not in rs:
                raise ValidationError(f"reference_size missing required field: {k}")
        if not isinstance(rs["width"], int) or rs["width"] < 1:
            raise ValidationError("reference_size.width must be integer >= 1")
        if not isinstance(rs["height"], int) or rs["height"] < 1:
            raise ValidationError("reference_size.height must be integer >= 1")
        if rs["unit"] != "pixel":
            raise ValidationError("reference_size.unit must be 'pixel'")
        # size_range（可選）
        if "size_range" in meta and meta["size_range"] is not None:
            sr = meta["size_range"]
            if not isinstance(sr, dict):
                raise ValidationError("size_range must be object or null")
            for dim in ["width", "height"]:
                if dim in sr:
                    rng = sr[dim]
                    if not isinstance(rng, dict):
                        raise ValidationError(f"size_range.{dim} must be object")
                    for bound in ["min", "max"]:
                        if bound not in rng or not isinstance(rng[bound], int) or rng[bound] < 1:
                            raise ValidationError(f"size_range.{dim}.{bound} must be integer >= 1")
        # sampling_date（可選）
        if "sampling_date" in meta:
            sd = meta["sampling_date"]
            if not isinstance(sd, str) or not re.match(r'^\d{4}-\d{2}-\d{2}$', sd):
                raise ValidationError("sampling_date must be date string YYYY-MM-DD")
        # sampler_version（可選）
        if "sampler_version" in meta:
            sv = meta["sampler_version"]
            if not isinstance(sv, str):
                raise ValidationError("sampler_version must be string")
        # notes（可選）
        if "notes" in meta and meta["notes"] is not None:
            if not isinstance(meta["notes"], str):
                raise ValidationError("notes must be string or null")

    def _validate_template_id(self, template_id: Any) -> None:
        if not isinstance(template_id, str):
            raise ValidationError("template_id must be a string")
        if not self.TEMPLATE_ID_PATTERN.match(template_id):
            raise ValidationError(
                f"Invalid template_id format: '{template_id}'. "
                "Must contain only lowercase letters, numbers, and underscores."
            )

    def _validate_regions(self, regions: Any) -> None:
        # regions 必須為 dict 且至少一個欄位
        if not isinstance(regions, dict):
            raise ValidationError("regions must be an object (dict)")
        if len(regions) == 0:
            raise ValidationError("regions must contain at least one region")
        names = set()
        for name, region in regions.items():
            if name in names:
                raise ValidationError(f"Duplicate region name: '{name}'")
            names.add(name)
            self._validate_region(region)


    def _validate_region(self, region: Dict[str, Any]) -> None:
        # rect_ratio 必須存在且為 dict
        if "rect_ratio" not in region:
            raise ValidationError("Region missing required field: rect_ratio")
        self._validate_rect_ratio(region["rect_ratio"])

        # rect_std_dev（可選）
        if "rect_std_dev" in region and region["rect_std_dev"] is not None:
            self._validate_rect_std_dev(region["rect_std_dev"])

        # pattern（可選）
        if "pattern" in region and region["pattern"] is not None:
            if not isinstance(region["pattern"], str):
                raise ValidationError("pattern must be a string or null")

        # data_type（可選）
        if "data_type" in region and region["data_type"] is not None:
            if not isinstance(region["data_type"], str):
                raise ValidationError("data_type must be a string or null")

        # extract_group（可選）
        if "extract_group" in region and region["extract_group"] is not None:
            if not isinstance(region["extract_group"], int):
                raise ValidationError("extract_group must be an integer or null")
            if region["extract_group"] < 0:
                raise ValidationError("extract_group must be >= 0")

        # expected_length（可選）
        if "expected_length" in region and region["expected_length"] is not None:
            if not isinstance(region["expected_length"], int):
                raise ValidationError("expected_length must be an integer or null")
            if region["expected_length"] < 1:
                raise ValidationError("expected_length must be >= 1")

        # required（可選）
        if "required" in region and region["required"] is not None:
            if not isinstance(region["required"], bool):
                raise ValidationError("required must be a boolean or null")

        # position_weight（可選）
        if "position_weight" in region and region["position_weight"] is not None:
            pw = region["position_weight"]
            if not isinstance(pw, (int, float)):
                raise ValidationError("position_weight must be a number or null")
            if not (0 <= pw <= 1):
                raise ValidationError("position_weight must be between 0 and 1")

        # tolerance_ratio（可選）
        if "tolerance_ratio" in region and region["tolerance_ratio"] is not None:
            tr = region["tolerance_ratio"]
            if not isinstance(tr, (int, float)):
                raise ValidationError("tolerance_ratio must be a number or null")
            if not (0 <= tr <= 1):
                raise ValidationError("tolerance_ratio must be between 0 and 1")

        # fallback_pattern（可選）
        if "fallback_pattern" in region and region["fallback_pattern"] is not None:
            if not isinstance(region["fallback_pattern"], str):
                raise ValidationError("fallback_pattern must be a string or null")

        # description（可選）
        if "description" in region and region["description"] is not None:
            if not isinstance(region["description"], str):
                raise ValidationError("description must be a string or null")

        # validation（可選）
        if "validation" in region and region["validation"] is not None:
            self._validate_region_validation(region["validation"])

    def _validate_region_validation(self, validation: Dict[str, Any]) -> None:
        if not isinstance(validation, dict):
            raise ValidationError("validation must be an object")
        # min_length/max_length
        if "min_length" in validation:
            ml = validation["min_length"]
            if not isinstance(ml, int) or ml < 0:
                raise ValidationError("validation.min_length must be integer >= 0")
        if "max_length" in validation:
            ml = validation["max_length"]
            if not isinstance(ml, int) or ml < 0:
                raise ValidationError("validation.max_length must be integer >= 0")
        # min_value/max_value
        if "min_value" in validation:
            mv = validation["min_value"]
            if not isinstance(mv, (int, float)):
                raise ValidationError("validation.min_value must be number")
        if "max_value" in validation:
            mv = validation["max_value"]
            if not isinstance(mv, (int, float)):
                raise ValidationError("validation.max_value must be number")
        # allowed_values
        if "allowed_values" in validation:
            av = validation["allowed_values"]
            if not isinstance(av, list):
                raise ValidationError("validation.allowed_values must be array")
            for v in av:
                if not isinstance(v, str):
                    raise ValidationError("validation.allowed_values must be array of strings")

    def _validate_rect_ratio(self, rect: Dict[str, Any]) -> None:
        # rect_ratio 必須為 dict 且含 x, y, width, height
        required = ["x", "y", "width", "height"]
        for k in required:
            if k not in rect:
                raise ValidationError(f"rect_ratio missing required field: {k}")
            v = rect[k]
            if not isinstance(v, (int, float)):
                raise ValidationError(f"rect_ratio.{k} must be a number")
            if not (0 <= v <= 1):
                raise ValidationError(f"rect_ratio.{k} must be between 0 and 1")

    def _validate_rect_std_dev(self, rect: Dict[str, Any]) -> None:
        # rect_std_dev 必須為 dict 且含 x, y, width, height
        required = ["x", "y", "width", "height"]
        for k in required:
            if k not in rect:
                raise ValidationError(f"rect_std_dev missing required field: {k}")
            v = rect[k]
            if not isinstance(v, (int, float)):
                raise ValidationError(f"rect_std_dev.{k} must be a number")
            if v < 0:
                raise ValidationError(f"rect_std_dev.{k} must be non-negative")

    def _validate_preprocess(self, preprocess: Dict[str, Any]) -> None:
        if not isinstance(preprocess, dict):
            raise ValidationError("preprocess must be an object")
        if "denoise" in preprocess:
            denoise = preprocess["denoise"]
            if denoise not in self.VALID_DENOISE_METHODS:
                raise ValidationError(
                    f"Invalid denoise method: '{denoise}'. "
                    f"Must be one of: {', '.join(self.VALID_DENOISE_METHODS)}"
                )
        if "binarize" in preprocess:
            binarize = preprocess["binarize"]
            if binarize not in self.VALID_BINARIZE_METHODS:
                raise ValidationError(
                    f"Invalid binarize method: '{binarize}'. "
                    f"Must be one of: {', '.join(self.VALID_BINARIZE_METHODS)}"
                )
