"""
Orchestrator - OCR 流程編排器（混合策略版本）
"""

import json
import numpy as np
from typing import Dict, Any, Union, Optional
from pathlib import Path

from ..utils.image_utils import read_image
from .extractors import HybridExtractor


class Orchestrator:
    """
    OCR 流程編排器（混合策略版本）
    
    工作流程：
    1. 載入範本（Template Schema v3.0）
    2. 混合提取（全圖 OCR + 位置提示）
    """
    
    def __init__(self, ocr_adapter):
        """初始化編排器"""
        if ocr_adapter is None:
            raise ValueError("ocr_adapter is required for hybrid extraction")
        
        self.ocr_adapter = ocr_adapter
        self.extractor = HybridExtractor(ocr_adapter)
        self.template: Optional[Dict] = None
    
    def load_template(self, template_input: Union[str, Path, Dict[str, Any]]) -> None:
        """
        載入範本
        
        Args:
            template_input: 範本 dict 或 JSON 檔案路徑
        """
        if isinstance(template_input, dict):
            self.template = template_input
        else:
            # 直接使用 json.load
            with open(template_input, 'r', encoding='utf-8') as f:
                self.template = json.load(f)
    
    def process(self, image_input: Union[str, Path, np.ndarray]) -> Dict[str, Any]:
        """處理影像"""
        if self.template is None:
            raise ValueError("No template loaded. Call load_template() first.")
        
        # 載入影像
        if isinstance(image_input, (str, Path)):
            image_path = Path(image_input)
            if not image_path.exists():
                raise FileNotFoundError(f"Image file not found: {image_input}")
            image = read_image(str(image_input))
        else:
            image = image_input
        
        # 混合提取（全圖 OCR + 位置提示）
        fields = self.extractor.extract_fields(image, self.template)
        self.extractor.clear_cache()
        
        return {
            'template_id': self.template.get('template_id', 'unknown'),
            'fields': fields
        }
    
    def reset(self) -> None:
        """重置狀態"""
        self.template = None
        self.extractor.clear_cache()
