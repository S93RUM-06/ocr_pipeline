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
    Template 驗證器
    
    負責驗證 Template JSON 是否符合規格。
    """

    # 允許的值定義
    VALID_DENOISE_METHODS = ["nlm", "bilateral", "gaussian"]
    VALID_BINARIZE_METHODS = ["adaptive", "otsu", "threshold"]
    VALID_OCR_LANGS = ["chinese_cht", "ch", "en", "chinese_sim", "chinese_tra"]
    
    # template_id 格式：只允許小寫字母、數字、底線
    TEMPLATE_ID_PATTERN = re.compile(r'^[a-z0-9_]+$')
    
    # 影像尺寸限制
    MIN_IMAGE_SIZE = 100
    MAX_IMAGE_SIZE = 10000

    def validate(self, data: Dict[str, Any]) -> bool:
        """
        驗證 Template 資料
        
        支援統一的模板格式：
        - anchor.enable = true: 使用 anchor 和 relative_to_anchor (相對座標)
        - anchor.enable = false 或無 anchor: 使用 image_size 和 rect (絕對座標)
        
        Args:
            data: Template 資料字典
            
        Returns:
            驗證是否通過
            
        Raises:
            ValidationError: 驗證失敗時拋出，包含錯誤訊息
        """
        # 驗證 template_id（兩種格式都需要）
        if "template_id" not in data:
            raise ValidationError("Missing required field: template_id")
        self._validate_template_id(data["template_id"])
        
        # 檢查是否有 anchor 欄位
        if "anchor" not in data:
            # 沒有 anchor 欄位 → 傳統模式
            anchor_enabled = False
        else:
            # 有 anchor 欄位 → 檢查 enable
            anchor_obj = data["anchor"]
            if not isinstance(anchor_obj, dict):
                raise ValidationError("Anchor must be an object")
            
            if "enable" not in anchor_obj:
                raise ValidationError("Anchor missing required field: enable")
            
            if not isinstance(anchor_obj["enable"], bool):
                raise ValidationError("Anchor 'enable' must be a boolean value")
            
            anchor_enabled = anchor_obj["enable"]
        
        if anchor_enabled:
            # Anchor-based mode: 需要 anchor 定義
            self._validate_v2_template(data)
        else:
            # Traditional mode: 需要 image_size
            self._validate_v1_template(data)
        
        # 驗證 regions（兩種格式都需要）
        if "regions" not in data:
            raise ValidationError("Missing required field: regions")
        
        if anchor_enabled:
            self._validate_v2_regions(data["regions"])
        else:
            self._validate_regions(data["regions"], data["image_size"])
        
        # 驗證 preprocess（選填）
        if "preprocess" in data:
            self._validate_preprocess(data["preprocess"])
        
        # 驗證 OCR 設定（anchor mode 要求全域設定）
        if anchor_enabled and "ocr" in data:
            self._validate_ocr_config(data["ocr"])
        
        return True

    def _validate_v1_template(self, data: Dict[str, Any]) -> None:
        """驗證傳統模板特定欄位（絕對座標模式）"""
        # 傳統模式需要 image_size
        if "image_size" not in data:
            raise ValidationError("Missing required field: image_size")
        self._validate_image_size(data["image_size"])

    def _validate_v2_template(self, data: Dict[str, Any]) -> None:
        """驗證 Anchor-based 模板特定欄位（相對座標模式）"""
        # Anchor mode 需要 anchor 定義
        if "anchor" not in data:
            raise ValidationError("Missing required field: anchor")
        self._validate_anchor(data["anchor"])
        
        # v2.0 建議有 ocr 全域設定
        if "ocr" not in data:
            raise ValidationError("Missing required field: ocr (global OCR configuration)")

    def _validate_anchor(self, anchor: Dict[str, Any]) -> None:
        """驗證 anchor 定義"""
        # 檢查 enable 欄位
        if "enable" not in anchor:
            raise ValidationError("Anchor missing required field: enable")
        
        if not isinstance(anchor["enable"], bool):
            raise ValidationError("Anchor 'enable' must be a boolean value")
        
        # 如果 anchor 未啟用，不需要驗證其他欄位
        if not anchor["enable"]:
            return
        
        # Anchor 啟用時，檢查必填欄位
        if "text" not in anchor:
            raise ValidationError("Anchor missing required field: text")
        
        if "expected_bbox" not in anchor:
            raise ValidationError("Anchor missing required field: expected_bbox")
        
        # 驗證 expected_bbox
        bbox = anchor["expected_bbox"]
        
        if "width" not in bbox:
            raise ValidationError("Anchor expected_bbox missing required field: width")
        
        if "height" not in bbox:
            raise ValidationError("Anchor expected_bbox missing required field: height")
        
        if "tolerance_ratio" not in bbox:
            raise ValidationError("Anchor expected_bbox missing required field: tolerance_ratio")
        
        # 驗證 tolerance_ratio 範圍
        tolerance = bbox["tolerance_ratio"]
        if not isinstance(tolerance, (int, float)):
            raise ValidationError("tolerance_ratio must be a number")
        
        if not (0 <= tolerance <= 1):
            raise ValidationError(
                f"tolerance_ratio must be between 0 and 1, got {tolerance}"
            )

    def _validate_ocr_config(self, ocr_config: Dict[str, Any]) -> None:
        """驗證全域 OCR 配置"""
        # 檢查必填欄位
        if "lang" not in ocr_config:
            raise ValidationError("OCR config missing required field: lang")
        
        # 驗證 lang 值
        lang = ocr_config["lang"]
        if lang not in self.VALID_OCR_LANGS:
            raise ValidationError(
                f"Invalid OCR lang: '{lang}'. "
                f"Must be one of: {', '.join(self.VALID_OCR_LANGS)}"
            )

    def _validate_required_fields(self, data: Dict[str, Any]) -> None:
        """驗證必填欄位"""
        required_fields = ["template_id", "image_size", "regions"]
        
        for field in required_fields:
            if field not in data:
                raise ValidationError(f"Missing required field: {field}")

    def _validate_template_id(self, template_id: Any) -> None:
        """驗證 template_id 格式"""
        if not isinstance(template_id, str):
            raise ValidationError("template_id must be a string")
        
        if not self.TEMPLATE_ID_PATTERN.match(template_id):
            raise ValidationError(
                f"Invalid template_id format: '{template_id}'. "
                "Must contain only lowercase letters, numbers, and underscores."
            )

    def _validate_image_size(self, image_size: Any) -> None:
        """驗證 image_size"""
        # 檢查是否為陣列
        if not isinstance(image_size, list):
            raise ValidationError("image_size must be an array")
        
        # 檢查長度
        if len(image_size) != 2:
            raise ValidationError(
                f"image_size must have exactly 2 elements, got {len(image_size)}"
            )
        
        # 檢查數值類型和範圍
        for i, size in enumerate(image_size):
            if not isinstance(size, int):
                raise ValidationError(f"image_size[{i}] must be an integer")
            
            if size < self.MIN_IMAGE_SIZE:
                raise ValidationError(
                    f"image_size[{i}] is {size}, must be at least {self.MIN_IMAGE_SIZE}"
                )
            
            if size > self.MAX_IMAGE_SIZE:
                raise ValidationError(
                    f"image_size[{i}] is {size}, must not exceed {self.MAX_IMAGE_SIZE}"
                )

    def _validate_regions(self, regions: Any, image_size: List[int]) -> None:
        """驗證 v1.0 regions"""
        # 檢查是否為陣列
        if not isinstance(regions, list):
            raise ValidationError("regions must be an array")
        
        # 檢查至少有一個 region
        if len(regions) == 0:
            raise ValidationError("regions must contain at least one region")
        
        # 檢查 name 是否重複
        names = []
        for region in regions:
            self._validate_region(region, image_size)
            
            name = region.get("name")
            if name in names:
                raise ValidationError(f"Duplicate region name: '{name}'")
            names.append(name)

    def _validate_v2_regions(self, regions: Any) -> None:
        """驗證 v2.0 regions (anchor-based)"""
        # 檢查是否為陣列
        if not isinstance(regions, list):
            raise ValidationError("regions must be an array")
        
        # 檢查至少有一個 region
        if len(regions) == 0:
            raise ValidationError("regions must contain at least one region")
        
        # 檢查 name 是否重複
        names = []
        for region in regions:
            self._validate_v2_region(region)
            
            name = region.get("name")
            if name in names:
                raise ValidationError(f"Duplicate region name: '{name}'")
            names.append(name)

    def _validate_v2_region(self, region: Dict[str, Any]) -> None:
        """驗證單一 v2.0 region"""
        # 檢查必填欄位
        if "name" not in region:
            raise ValidationError("Region missing required field: name")
        
        if "relative_to_anchor" not in region:
            raise ValidationError("Region missing required field: relative_to_anchor")
        
        # 驗證 relative_to_anchor
        self._validate_relative_position(region["relative_to_anchor"])
        
        # 驗證 ocr_config 不應該有 lang（應該使用全域設定）
        if "ocr_config" in region and "lang" in region["ocr_config"]:
            raise ValidationError(
                "Region ocr_config should not contain 'lang'. "
                "Use global OCR lang configuration instead."
            )
        
        # 驗證 validation 欄位（選填）
        if "validation" in region:
            self._validate_validation_config(region["validation"])

    def _validate_relative_position(self, relative: Dict[str, Any]) -> None:
        """驗證相對位置定義"""
        # 檢查必填欄位
        required_fields = ["x", "y", "width", "height", "tolerance_ratio"]
        for field in required_fields:
            if field not in relative:
                raise ValidationError(f"relative_to_anchor missing required field: {field}")
        
        # 驗證數值類型（允許負數，因為可能在 anchor 左側/上方）
        for field in ["x", "y", "width", "height"]:
            value = relative[field]
            if not isinstance(value, (int, float)):
                raise ValidationError(f"relative_to_anchor.{field} must be a number")
        
        # width 和 height 必須為正數
        if relative["width"] <= 0:
            raise ValidationError("relative_to_anchor.width must be positive")
        
        if relative["height"] <= 0:
            raise ValidationError("relative_to_anchor.height must be positive")
        
        # 驗證 tolerance_ratio
        tolerance = relative["tolerance_ratio"]
        if not isinstance(tolerance, (int, float)):
            raise ValidationError("relative_to_anchor.tolerance_ratio must be a number")
        
        if not (0 <= tolerance <= 1):
            raise ValidationError(
                f"relative_to_anchor.tolerance_ratio must be between 0 and 1, got {tolerance}"
            )

    def _validate_validation_config(self, validation: Dict[str, Any]) -> None:
        """驗證 validation 配置"""
        # 檢查 required 欄位
        if "required" in validation:
            required = validation["required"]
            if not isinstance(required, bool):
                raise ValidationError("validation.required must be a boolean")
        
        # 檢查 min_confidence 欄位
        if "min_confidence" in validation:
            min_conf = validation["min_confidence"]
            if not isinstance(min_conf, (int, float)):
                raise ValidationError("validation.min_confidence must be a number")
            
            if not (0 <= min_conf <= 1):
                raise ValidationError(
                    f"validation.min_confidence must be between 0 and 1, got {min_conf}"
                )

    def _validate_region(self, region: Dict[str, Any], image_size: List[int]) -> None:
        """驗證單一 region"""
        # 檢查必填欄位
        if "name" not in region:
            raise ValidationError("Region missing required field: name")
        
        if "rect" not in region:
            raise ValidationError("Region missing required field: rect")
        
        # 驗證 rect
        self._validate_rect(region["rect"], image_size)

    def _validate_rect(self, rect: Any, image_size: List[int]) -> None:
        """驗證 rect 座標"""
        # 檢查是否為陣列
        if not isinstance(rect, list):
            raise ValidationError("rect must be an array")
        
        # 檢查長度
        if len(rect) != 4:
            raise ValidationError(
                f"rect must have exactly 4 elements [x1, y1, x2, y2], got {len(rect)}"
            )
        
        x1, y1, x2, y2 = rect
        
        # 檢查數值類型
        for i, coord in enumerate(rect):
            if not isinstance(coord, int):
                raise ValidationError(f"rect[{i}] must be an integer")
        
        # 檢查座標不能為負數
        if any(coord < 0 for coord in rect):
            raise ValidationError("rect coordinates cannot be negative")
        
        # 檢查 x1 < x2
        if x1 >= x2:
            raise ValidationError(
                f"Invalid rect: x1 ({x1}) must be less than x2 ({x2})"
            )
        
        # 檢查 y1 < y2
        if y1 >= y2:
            raise ValidationError(
                f"Invalid rect: y1 ({y1}) must be less than y2 ({y2})"
            )
        
        # 檢查不超出影像邊界
        width, height = image_size
        
        if x2 > width:
            raise ValidationError(
                f"rect x2 ({x2}) exceeds image_size width ({width})"
            )
        
        if y2 > height:
            raise ValidationError(
                f"rect y2 ({y2}) exceeds image_size height ({height})"
            )

    def _validate_preprocess(self, preprocess: Dict[str, Any]) -> None:
        """驗證 preprocess 設定"""
        if not isinstance(preprocess, dict):
            raise ValidationError("preprocess must be an object")
        
        # 驗證 denoise 值（如果存在）
        if "denoise" in preprocess:
            denoise = preprocess["denoise"]
            if denoise not in self.VALID_DENOISE_METHODS:
                raise ValidationError(
                    f"Invalid denoise method: '{denoise}'. "
                    f"Must be one of: {', '.join(self.VALID_DENOISE_METHODS)}"
                )
        
        # 驗證 binarize 值（如果存在）
        if "binarize" in preprocess:
            binarize = preprocess["binarize"]
            if binarize not in self.VALID_BINARIZE_METHODS:
                raise ValidationError(
                    f"Invalid binarize method: '{binarize}'. "
                    f"Must be one of: {', '.join(self.VALID_BINARIZE_METHODS)}"
                )
