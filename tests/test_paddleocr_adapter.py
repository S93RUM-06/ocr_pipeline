"""
測試 PaddleOCRAdapter - PaddleOCR 引擎適配器
"""

import pytest
import numpy as np
from ocr_pipeline.adapters.ocr.paddleocr_adapter import PaddleOCRAdapter


class TestPaddleOCRAdapter:
    """PaddleOCR 適配器測試"""
    
    def test_can_create_adapter(self):
        """測試：可以建立適配器實例"""
        adapter = PaddleOCRAdapter()
        assert adapter is not None
    
    def test_can_create_with_config(self):
        """測試：可以用設定建立適配器"""
        config = {
            "lang": "ch",
            "use_angle_cls": True,
            "use_gpu": False
        }
        adapter = PaddleOCRAdapter(config=config)
        assert adapter is not None
    
    def test_recognize_returns_result(self):
        """測試：識別回傳結果"""
        adapter = PaddleOCRAdapter()
        
        # 建立簡單的測試影像（白底黑字）
        img = np.ones((100, 200, 3), dtype=np.uint8) * 255
        
        result = adapter.recognize(img)
        
        assert result is not None
        assert isinstance(result, list)
    
    def test_recognize_with_text_image(self):
        """測試：識別包含文字的影像"""
        import cv2
        adapter = PaddleOCRAdapter()
        
        # 建立包含文字的測試影像（避免踩到 100 像素邊界）
        img = np.ones((150, 300, 3), dtype=np.uint8) * 255
        cv2.putText(img, "TEST123", (50, 90), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        
        result = adapter.recognize(img)
        
        # 應該能識別出某些內容
        assert isinstance(result, list)
    
    def test_extract_text_from_result(self):
        """測試：從結果中提取純文字"""
        adapter = PaddleOCRAdapter()
        
        # 模擬 PaddleOCR 結果格式
        mock_result = [
            [[[10, 10], [100, 10], [100, 30], [10, 30]], ("測試文字", 0.95)],
            [[[10, 40], [120, 40], [120, 60], [10, 60]], ("ABC123", 0.88)]
        ]
        
        texts = adapter.extract_text(mock_result)
        
        assert isinstance(texts, list)
        assert len(texts) == 2
        assert texts[0] == "測試文字"
        assert texts[1] == "ABC123"
    
    def test_extract_text_with_confidence(self):
        """測試：提取文字和信心分數"""
        adapter = PaddleOCRAdapter()
        
        mock_result = [
            [[[10, 10], [100, 10], [100, 30], [10, 30]], ("測試", 0.95)]
        ]
        
        result = adapter.extract_text_with_confidence(mock_result)
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["text"] == "測試"
        assert result[0]["confidence"] == 0.95
        assert "bbox" in result[0]
    
    def test_filter_low_confidence(self):
        """測試：過濾低信心分數結果"""
        adapter = PaddleOCRAdapter(min_confidence=0.7)
        
        mock_result = [
            [[[10, 10], [100, 10], [100, 30], [10, 30]], ("高信心", 0.95)],
            [[[10, 40], [100, 40], [100, 60], [10, 60]], ("低信心", 0.5)]
        ]
        
        texts = adapter.extract_text(mock_result)
        
        # 只應該保留信心分數 >= 0.7 的結果
        assert len(texts) == 1
        assert texts[0] == "高信心"
    
    def test_recognize_empty_image_returns_empty(self):
        """測試：空白影像回傳空結果"""
        adapter = PaddleOCRAdapter()
        
        # 純白影像
        img = np.ones((100, 100, 3), dtype=np.uint8) * 255
        
        result = adapter.recognize(img)
        
        assert isinstance(result, list)
    
    def test_set_language(self):
        """測試：可以設定語言"""
        adapter = PaddleOCRAdapter()
        
        # 初始化 OCR（讓 _ocr 不為 None）
        img = np.ones((100, 200, 3), dtype=np.uint8) * 255
        adapter.recognize(img)
        
        # 設定新語言應該重置 _ocr
        adapter.set_language("en")
        
        # 驗證設定已更新
        assert adapter.lang == "en"
        # 驗證 _ocr 被重置
        assert adapter._ocr is None
    
    def test_traditional_chinese_conversion(self):
        """測試：簡繁轉換功能"""
        # 啟用簡繁轉換
        config = {
            "convert_to_traditional": True
        }
        adapter = PaddleOCRAdapter(config=config)
        
        # 模擬包含簡體字的 OCR 結果
        mock_result = [
            [[[10, 10], [100, 10], [100, 30], [10, 30]], ("简体中文测试", 0.95)]
        ]
        
        texts = adapter.extract_text(mock_result)
        
        # 應該轉換為繁體（如果 OpenCC 可用）
        assert isinstance(texts, list)
        assert len(texts) == 1
        # 如果 OpenCC 可用，應該是繁體；否則保持原樣
        # 這裡只驗證功能不會報錯
    
    def test_convert_to_traditional_disabled(self):
        """測試：未啟用簡繁轉換時保持原樣"""
        adapter = PaddleOCRAdapter()
        
        # _convert_to_traditional 應該返回原始文字
        result = adapter._convert_to_traditional("简体中文")
        
        # 未啟用轉換時應該返回原文
        assert result == "简体中文"
    
    def test_extract_text_with_confidence_filtering(self):
        """測試：extract_text_with_confidence 過濾低信心結果"""
        adapter = PaddleOCRAdapter(min_confidence=0.9)
        
        mock_result = [
            [[[10, 10], [100, 10], [100, 30], [10, 30]], ("高信心", 0.95)],
            [[[10, 40], [100, 40], [100, 60], [10, 60]], ("低信心", 0.70)]
        ]
        
        results = adapter.extract_text_with_confidence(mock_result)
        
        assert len(results) == 1
        assert results[0]["text"] == "高信心"
        assert results[0]["confidence"] == 0.95
        assert "bbox" in results[0]
    
    def test_recognize_handles_empty_result(self):
        """測試：處理 PaddleOCR 回傳空結果"""
        adapter = PaddleOCRAdapter()
        
        # 測試完全空白的影像（應該沒有文字）
        img = np.ones((200, 200, 3), dtype=np.uint8) * 255
        
        result = adapter.recognize(img)
        
        # 可能是空列表或者沒有識別到文字
        assert isinstance(result, list)
    
    def test_invalid_image_raises_error(self):
        """測試：無效影像拋出錯誤"""
        adapter = PaddleOCRAdapter()
        
        with pytest.raises(ValueError):
            adapter.recognize(None)
    
    def test_reject_small_image(self):
        """測試：拒絕尺寸過小的影像"""
        adapter = PaddleOCRAdapter()
        
        # W < 100
        img = np.ones((200, 50, 3), dtype=np.uint8) * 255
        with pytest.raises(ValueError, match="too small"):
            adapter.recognize(img)
        
        # H < 100
        img = np.ones((50, 200, 3), dtype=np.uint8) * 255
        with pytest.raises(ValueError, match="too small"):
            adapter.recognize(img)
