"""
測試 Orchestrator - OCR 流程編排器（混合策略版本）
"""

import pytest
import numpy as np
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

from ocr_pipeline.core.orchestrator import Orchestrator
from ocr_pipeline.adapters.ocr.paddleocr_adapter import PaddleOCRAdapter


class TestOrchestrator:
    """Orchestrator 測試"""
    
    @pytest.fixture
    def mock_ocr_adapter(self):
        """建立 Mock OCR Adapter"""
        class MockOCRAdapter:
            def recognize(self, image):
                # 模擬 OCR 結果：((x, y, w, h), (text, confidence))
                return [
                    ((100, 100, 150, 30), ("AB12345678", 0.95)),
                    ((100, 200, 150, 30), ("2024-01-15", 0.92)),
                    ((100, 300, 80, 30), ("1234", 0.88)),
                    ((100, 400, 120, 30), ("NT$ 1,200", 0.90)),
                ]
        return MockOCRAdapter()
    
    @pytest.fixture
    def sample_template(self, tmp_path):
        """建立測試範本"""
        template = {
            "template_id": "test_invoice_v1",
            "template_name": "測試發票範本",
            "version": "1.0",
            "processing_strategy": "hybrid_ocr_roi",
            "regions": {
                "invoice_number": {
                    "rect_ratio": {"x": 0.1, "y": 0.1, "width": 0.3, "height": 0.05},
                    "pattern": r"[A-Z]{2}\d{8}",
                    "position_weight": 0.3
                },
                "invoice_date": {
                    "rect_ratio": {"x": 0.1, "y": 0.2, "width": 0.3, "height": 0.05},
                    "pattern": r"\d{4}-\d{2}-\d{2}",
                    "position_weight": 0.3
                }
            }
        }
        return template
    
    @pytest.fixture
    def sample_image(self, tmp_path):
        """建立測試影像檔案"""
        img = np.ones((1000, 1000, 3), dtype=np.uint8) * 255
        img_path = tmp_path / "test_invoice.png"
        import cv2
        cv2.imwrite(str(img_path), img)
        return img_path
    
    def test_init_requires_ocr_adapter(self):
        """測試：初始化需要 ocr_adapter"""
        with pytest.raises(ValueError, match="ocr_adapter is required"):
            Orchestrator(None)
    
    def test_init_with_ocr_adapter(self, mock_ocr_adapter):
        """測試：可以使用 ocr_adapter 初始化"""
        orchestrator = Orchestrator(mock_ocr_adapter)
        
        assert orchestrator.ocr_adapter == mock_ocr_adapter
        assert orchestrator.template is None
        assert orchestrator.extractor is not None
    
    def test_load_template_from_dict(self, mock_ocr_adapter, sample_template):
        """測試：從字典載入範本"""
        orchestrator = Orchestrator(mock_ocr_adapter)
        
        orchestrator.load_template(sample_template)
        
        assert orchestrator.template == sample_template
        assert orchestrator.template['template_id'] == "test_invoice_v1"
    
    def test_load_template_from_file(self, mock_ocr_adapter, tmp_path):
        """測試：從檔案載入範本"""
        orchestrator = Orchestrator(mock_ocr_adapter)
        
        # 建立範本檔案
        template_path = tmp_path / "test_template.json"
        import json
        template_data = {
            "template_id": "file_test_v1",
            "processing_strategy": "hybrid_ocr_roi",
            "image_size": {"width": 1000, "height": 1000},
            "regions": {}
        }
        template_path.write_text(json.dumps(template_data, ensure_ascii=False))
        
        orchestrator.load_template(template_path)
        
        assert orchestrator.template is not None
        assert orchestrator.template["template_id"] == "file_test_v1"
    
    def test_process_without_template_raises_error(self, mock_ocr_adapter):
        """測試：未載入範本時執行處理會拋出錯誤"""
        orchestrator = Orchestrator(mock_ocr_adapter)
        img = np.ones((1000, 1000, 3), dtype=np.uint8) * 255
        
        with pytest.raises(ValueError, match="No template loaded"):
            orchestrator.process(img)
    
    def test_process_with_image_array(self, mock_ocr_adapter, sample_template):
        """測試：使用影像陣列處理"""
        orchestrator = Orchestrator(mock_ocr_adapter)
        orchestrator.load_template(sample_template)
        
        img = np.ones((1000, 1000, 3), dtype=np.uint8) * 255
        result = orchestrator.process(img)
        
        assert result is not None
        assert 'template_id' in result
        assert result['template_id'] == "test_invoice_v1"
        assert 'fields' in result
        assert isinstance(result['fields'], dict)
    
    def test_process_with_image_path(self, mock_ocr_adapter, sample_template, sample_image):
        """測試：使用影像路徑處理"""
        orchestrator = Orchestrator(mock_ocr_adapter)
        orchestrator.load_template(sample_template)
        
        result = orchestrator.process(sample_image)
        
        assert result is not None
        assert 'template_id' in result
        assert 'fields' in result
    
    def test_process_with_nonexistent_image_raises_error(self, mock_ocr_adapter, sample_template):
        """測試：不存在的影像路徑會拋出錯誤"""
        orchestrator = Orchestrator(mock_ocr_adapter)
        orchestrator.load_template(sample_template)
        
        with pytest.raises(FileNotFoundError):
            orchestrator.process("nonexistent_image.png")
    
    def test_reset_clears_template_and_cache(self, mock_ocr_adapter, sample_template):
        """測試：reset 清除範本和快取"""
        orchestrator = Orchestrator(mock_ocr_adapter)
        orchestrator.load_template(sample_template)
        
        assert orchestrator.template is not None
        
        orchestrator.reset()
        
        assert orchestrator.template is None
    
    def test_preprocess_with_denoise(self, mock_ocr_adapter):
        """測試：前置處理 - 去噪"""
        orchestrator = Orchestrator(mock_ocr_adapter)
        
        template = {
            "template_id": "denoise_test",
            "processing_strategy": "hybrid_ocr_roi",
            "preprocess": {
                "denoise": {
                    "method": "bilateral"
                }
            },
            "regions": {
                "test_field": {
                    "rect_ratio": {"x": 0.1, "y": 0.1, "width": 0.2, "height": 0.1},
                    "pattern": r"\d+"
                }
            }
        }
        orchestrator.load_template(template)
        
        img = np.ones((1000, 1000, 3), dtype=np.uint8) * 128
        result = orchestrator.process(img)
        
        assert result is not None
        assert 'fields' in result
    
    def test_preprocess_with_binarize(self, mock_ocr_adapter):
        """測試：前置處理 - 二值化"""
        orchestrator = Orchestrator(mock_ocr_adapter)
        
        template = {
            "template_id": "binarize_test",
            "processing_strategy": "hybrid_ocr_roi",
            "preprocess": {
                "binarize": {
                    "method": "otsu"
                }
            },
            "regions": {
                "test_field": {
                    "rect_ratio": {"x": 0.1, "y": 0.1, "width": 0.2, "height": 0.1},
                    "pattern": r"\d+"
                }
            }
        }
        orchestrator.load_template(template)
        
        img = np.ones((1000, 1000, 3), dtype=np.uint8) * 200
        result = orchestrator.process(img)
        
        assert result is not None
        assert 'fields' in result
    
    def test_preprocess_with_both_denoise_and_binarize(self, mock_ocr_adapter):
        """測試：前置處理 - 去噪 + 二值化"""
        orchestrator = Orchestrator(mock_ocr_adapter)
        
        template = {
            "template_id": "both_preprocess_test",
            "processing_strategy": "hybrid_ocr_roi",
            "preprocess": {
                "denoise": {"method": "gaussian"},
                "binarize": {"method": "adaptive"}
            },
            "regions": {
                "test_field": {
                    "rect_ratio": {"x": 0.1, "y": 0.1, "width": 0.2, "height": 0.1},
                    "pattern": r"\d+"
                }
            }
        }
        orchestrator.load_template(template)
        
        img = np.ones((1000, 1000, 3), dtype=np.uint8) * 150
        result = orchestrator.process(img)
        
        assert result is not None
        assert 'fields' in result
    
    def test_preprocess_with_simple_boolean_config(self, mock_ocr_adapter):
        """測試：前置處理 - 簡單布林值設定"""
        orchestrator = Orchestrator(mock_ocr_adapter)
        
        # 使用簡化的布林值設定
        template = {
            "template_id": "simple_config_test",
            "processing_strategy": "hybrid_ocr_roi",
            "preprocess": {
                "denoise": True,  # 簡單布林值，應使用預設 bilateral
                "binarize": True  # 簡單布林值，應使用預設 adaptive
            },
            "regions": {
                "test_field": {
                    "rect_ratio": {"x": 0.1, "y": 0.1, "width": 0.2, "height": 0.1},
                    "pattern": r"\d+"
                }
            }
        }
        orchestrator.load_template(template)
        
        img = np.ones((1000, 1000, 3), dtype=np.uint8) * 180
        result = orchestrator.process(img)
        
        assert result is not None
    
    def test_process_returns_correct_structure(self, mock_ocr_adapter, sample_template):
        """測試：process 回傳正確的結構"""
        orchestrator = Orchestrator(mock_ocr_adapter)
        orchestrator.load_template(sample_template)
        
        img = np.ones((1000, 1000, 3), dtype=np.uint8) * 255
        result = orchestrator.process(img)
        
        # 驗證回傳結構
        assert isinstance(result, dict)
        assert 'template_id' in result
        assert 'fields' in result
        assert isinstance(result['fields'], dict)
        assert result['template_id'] == sample_template['template_id']
    
    def test_multiple_process_calls_clear_cache(self, mock_ocr_adapter, sample_template):
        """測試：多次 process 呼叫會清除快取"""
        orchestrator = Orchestrator(mock_ocr_adapter)
        orchestrator.load_template(sample_template)
        
        img = np.ones((1000, 1000, 3), dtype=np.uint8) * 255
        
        # 第一次處理
        result1 = orchestrator.process(img)
        
        # 第二次處理（應該清除快取）
        result2 = orchestrator.process(img)
        
        assert result1 is not None
        assert result2 is not None
        # 驗證兩次都成功處理
        assert 'fields' in result1
        assert 'fields' in result2
    
    def test_load_template_with_path_object(self, mock_ocr_adapter, tmp_path):
        """測試：使用 Path 物件載入範本"""
        orchestrator = Orchestrator(mock_ocr_adapter)
        
        # 建立範本檔案
        template_path = tmp_path / "path_test.json"
        import json
        template_data = {
            "template_id": "path_test_v1",
            "processing_strategy": "hybrid_ocr_roi",
            "image_size": {"width": 1000, "height": 1000},
            "regions": {}
        }
        template_path.write_text(json.dumps(template_data, ensure_ascii=False))
        
        # 使用 Path 物件
        orchestrator.load_template(template_path)
        
        assert orchestrator.template["template_id"] == "path_test_v1"
