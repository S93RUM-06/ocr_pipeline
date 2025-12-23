"""
PaddleOCRAdapter - PaddleOCR 引擎適配器

整合 PaddleOCR 進行文字識別
"""

import numpy as np
from typing import List, Dict, Any, Optional


class PaddleOCRAdapter:
    """
    PaddleOCR 適配器
    
    封裝 PaddleOCR 引擎，提供統一的 OCR 介面
    """
    
    def __init__(
        self, 
        config: Optional[Dict[str, Any]] = None,
        min_confidence: float = 0.6
    ):
        """
        初始化 PaddleOCR 適配器
        
        Args:
            config: PaddleOCR 設定
            min_confidence: 最小信心分數閾值
        """
        self.config = config or {}
        self.min_confidence = min_confidence
        self.lang = self.config.get("lang", "chinese_cht")  # 預設繁體中文
        self.use_angle_cls = self.config.get("use_angle_cls", True)
        
        # 延遲載入 PaddleOCR（避免測試時載入）
        self._ocr = None
        self._opencc = None
        
        # 簡繁轉換設定（當語言為繁體中文時啟用）
        self.convert_to_traditional = self.lang in ["chinese_cht", "ch"]
    
    def _init_ocr(self):
        """初始化 PaddleOCR 引擎"""
        if self._ocr is None:
            try:
                from paddleocr import PaddleOCR
                # PaddleOCR 3.x 版本簡化參數
                self._ocr = PaddleOCR(
                    lang=self.lang,
                    use_textline_orientation=self.use_angle_cls
                )
            except ImportError:
                raise ImportError(
                    "PaddleOCR not installed. "
                    "Install with: pip install paddleocr paddlepaddle"
                )
        
        # 初始化簡繁轉換器（如果需要）
        if self.convert_to_traditional and self._opencc is None:
            try:
                import opencc
                # s2t: Simplified Chinese to Traditional Chinese
                self._opencc = opencc.OpenCC('s2t.json')
            except ImportError:
                print("⚠️  OpenCC 未安裝，無法進行簡繁轉換")
                print("   安裝指令: pip install OpenCC")
                self._opencc = None
            except Exception as e:
                print(f"⚠️  OpenCC 初始化失敗: {e}")
                self._opencc = None
    
    def _convert_to_traditional(self, text: str) -> str:
        """
        將簡體中文轉換為繁體中文
        
        Args:
            text: 輸入文字
            
        Returns:
            轉換後的繁體中文
        """
        if self._opencc and self.convert_to_traditional:
            try:
                return self._opencc.convert(text)
            except Exception:
                return text
        return text
    
    def recognize(self, image: np.ndarray) -> List[Any]:
        """
        識別影像中的文字
        
        Args:
            image: 輸入影像
            
        Returns:
            PaddleOCR 識別結果列表
            
        Raises:
            ValueError: 如果影像無效
        """
        if image is None:
            raise ValueError("Image cannot be None")
        
        if not isinstance(image, np.ndarray):
            raise ValueError("Image must be a numpy array")
        
        # 檢查影像尺寸
        h, w = image.shape[:2]
        if h < 100 or w < 100:
            raise ValueError(f"Image size {w}x{h} is too small. Both width and height must be at least 100 pixels.")
        
        # 初始化 OCR 引擎
        self._init_ocr()
        
        # 執行識別（PaddleOCR 3.x API）
        result = self._ocr.predict(input=image)
        
        # result 是 list，每個元素對應一張圖
        if not result or len(result) == 0:
            return []
        
        # 取得第一張圖的結果
        page_result = result[0]
        
        # 轉換為統一格式 [[bbox, (text, confidence)], ...]
        converted_result = []
        
        # PaddleOCR 3.x 回傳的是 OCRResult 物件
        rec_polys = page_result.get("rec_polys", [])
        rec_texts = page_result.get("rec_texts", [])
        rec_scores = page_result.get("rec_scores", [])
        
        if rec_polys and rec_texts and rec_scores:
            for bbox, text, score in zip(rec_polys, rec_texts, rec_scores):
                # 將 bbox 轉換為列表格式
                if hasattr(bbox, 'tolist'):
                    bbox = bbox.tolist()
                
                # 簡繁轉換（如果啟用）
                converted_text = self._convert_to_traditional(text)
                
                converted_result.append([bbox, (converted_text, float(score))])
        
        return converted_result
    
    def extract_text(self, ocr_result: List[Any]) -> List[str]:
        """
        從 OCR 結果中提取純文字
        
        Args:
            ocr_result: PaddleOCR 識別結果
            
        Returns:
            文字列表
        """
        texts = []
        
        for item in ocr_result:
            if len(item) >= 2:
                # item[1] 是 (text, confidence) 元組
                text, confidence = item[1]
                
                # 過濾低信心分數
                if confidence >= self.min_confidence:
                    texts.append(text)
        
        return texts
    
    def extract_text_with_confidence(
        self, 
        ocr_result: List[Any]
    ) -> List[Dict[str, Any]]:
        """
        提取文字和信心分數
        
        Args:
            ocr_result: PaddleOCR 識別結果
            
        Returns:
            包含文字、信心分數和邊界框的字典列表
        """
        results = []
        
        for item in ocr_result:
            if len(item) >= 2:
                bbox = item[0]  # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                text, confidence = item[1]
                
                # 過濾低信心分數
                if confidence >= self.min_confidence:
                    results.append({
                        "text": text,
                        "confidence": confidence,
                        "bbox": bbox
                    })
        
        return results
    
    def set_language(self, lang: str) -> None:
        """
        設定識別語言
        
        Args:
            lang: 語言代碼（ch/en/...）
        """
        self.lang = lang
        # 重新初始化 OCR
        self._ocr = None
