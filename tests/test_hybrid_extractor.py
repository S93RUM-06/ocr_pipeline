"""
測試 HybridExtractor（混合提取器）
"""

import pytest
import numpy as np
from ocr_pipeline.core.extractors.hybrid_extractor import HybridExtractor, MatchCandidate


class MockOCRAdapter:
    """模擬 OCR 適配器"""
    
    def __init__(self, results=None):
        self.results = results or []
    
    def recognize(self, image):
        """返回預設的模擬結果"""
        return self.results


@pytest.fixture
def mock_ocr_invoice():
    """電子發票 OCR 模擬結果"""
    return MockOCRAdapter(results=[
        ((100, 79, 999, 50), ('VJ-50215372', 0.985)),
        ((82, 30, 1040, 60), ('114年11-12月', 0.983)),
        ((1200, 950, 500, 50), ('隨機碼：3472', 0.986)),
        ((1256, 865, 330, 50), ('總計    20', 0.945)),
        ((41, 1285, 553, 50), ('賣方42552150', 0.987)),
        ((639, 1285, 365, 50), ('買方12345678', 0.982))
    ])


@pytest.fixture
def template_invoice():
    """電子發票範本（簡化版）"""
    return {
        'template_id': 'tw_einvoice_test',
        'regions': {
            'invoice_number': {
                'rect_ratio': {
                    'x': 0.046, 'y': 0.058, 'width': 0.462, 'height': 0.037
                },
                'pattern': r'[A-Z]{2}-\d{8}',
                'extract_group': 0,
                'expected_length': 11,
                'required': True,
                'position_weight': 0.3,
                'tolerance_ratio': 0.2
            },
            'random_code': {
                'rect_ratio': {
                    'x': 0.555, 'y': 0.702, 'width': 0.231, 'height': 0.037
                },
                'pattern': r'隨機碼[:：]\s*(\d{4})',
                'extract_group': 1,
                'fallback_pattern': r'\d{4}',
                'expected_length': 4,
                'required': True,
                'position_weight': 0.3,
                'tolerance_ratio': 0.2
            },
            'total_amount': {
                'rect_ratio': {
                    'x': 0.581, 'y': 0.639, 'width': 0.153, 'height': 0.037
                },
                'pattern': r'總計[:：]\s*\$?\s*([\d,]+)',
                'extract_group': 1,
                'fallback_pattern': r'\d+',
                'required': True,
                'position_weight': 0.3,
                'tolerance_ratio': 0.2
            },
            'seller_tax_id': {
                'rect_ratio': {
                    'x': 0.019, 'y': 0.949, 'width': 0.256, 'height': 0.037
                },
                'pattern': r'賣方[:：]?\s*(\d{8})',
                'extract_group': 1,
                'expected_length': 8,
                'required': False,
                'position_weight': 0.4,
                'tolerance_ratio': 0.2
            }
        }
    }


def test_hybrid_extractor_init():
    """測試初始化"""
    mock_ocr = MockOCRAdapter()
    extractor = HybridExtractor(mock_ocr)
    
    assert extractor.ocr_adapter == mock_ocr
    assert extractor._ocr_cache is None


def test_hybrid_extractor_no_ocr_adapter():
    """測試缺少 OCR 適配器"""
    with pytest.raises(ValueError, match="ocr_adapter is required"):
        HybridExtractor(None)


def test_extract_invoice_number(mock_ocr_invoice, template_invoice):
    """測試提取發票號碼"""
    extractor = HybridExtractor(mock_ocr_invoice)
    
    # 模擬影像（2163 x 1355）
    fake_image = np.zeros((1355, 2163, 3), dtype=np.uint8)
    
    result = extractor.extract_fields(fake_image, template_invoice)
    
    # 驗證發票號碼
    assert result['invoice_number'] is not None
    assert result['invoice_number']['text'] == 'VJ-50215372'
    assert result['invoice_number']['confidence'] == 0.985
    assert result['invoice_number']['position_score'] > 0.7


def test_extract_random_code(mock_ocr_invoice, template_invoice):
    """測試提取隨機碼（使用 extract_group）"""
    extractor = HybridExtractor(mock_ocr_invoice)
    fake_image = np.zeros((1355, 2163, 3), dtype=np.uint8)
    
    result = extractor.extract_fields(fake_image, template_invoice)
    
    # 驗證隨機碼（應該只提取數字部分）
    assert result['random_code'] is not None
    assert result['random_code']['text'] == '3472'
    assert result['random_code']['confidence'] == 0.986


def test_extract_total_amount(mock_ocr_invoice, template_invoice):
    """測試提取總計金額"""
    extractor = HybridExtractor(mock_ocr_invoice)
    fake_image = np.zeros((1355, 2163, 3), dtype=np.uint8)
    
    result = extractor.extract_fields(fake_image, template_invoice)
    
    # 驗證金額
    assert result['total_amount'] is not None
    assert result['total_amount']['text'] == '20'


def test_position_disambiguation(mock_ocr_invoice, template_invoice):
    """測試位置區分能力（賣方統編）"""
    extractor = HybridExtractor(mock_ocr_invoice)
    fake_image = np.zeros((1355, 2163, 3), dtype=np.uint8)
    
    result = extractor.extract_fields(fake_image, template_invoice)
    
    # 賣方統編應該提取到左側的數字
    assert result['seller_tax_id'] is not None
    assert result['seller_tax_id']['text'] == '42552150'
    assert result['seller_tax_id']['position_score'] > 0.7


def test_missing_field():
    """測試缺失欄位"""
    # 空的 OCR 結果
    mock_ocr = MockOCRAdapter(results=[])
    extractor = HybridExtractor(mock_ocr)
    
    template = {
        'regions': {
            'invoice_number': {
                'rect_ratio': {'x': 0.1, 'y': 0.1, 'width': 0.5, 'height': 0.05},
                'pattern': r'[A-Z]{2}-\d{8}',
                'required': False
            }
        }
    }
    
    fake_image = np.zeros((1000, 1000, 3), dtype=np.uint8)
    result = extractor.extract_fields(fake_image, template)
    
    # 應該返回 None
    assert result['invoice_number'] is None


def test_fallback_pattern():
    """測試降級正則表達式"""
    # 模擬只有數字沒有前綴的情況
    mock_ocr = MockOCRAdapter(results=[
        ((1200, 950, 500, 50), ('3472', 0.986))
    ])
    
    extractor = HybridExtractor(mock_ocr)
    
    template = {
        'regions': {
            'random_code': {
                'rect_ratio': {'x': 0.555, 'y': 0.702, 'width': 0.231, 'height': 0.037},
                'pattern': r'隨機碼[:：]\s*(\d{4})',
                'fallback_pattern': r'\d{4}',
                'extract_group': 1,
                'required': True
            }
        }
    }
    
    fake_image = np.zeros((1355, 2163, 3), dtype=np.uint8)
    result = extractor.extract_fields(fake_image, template)
    
    # 應該使用 fallback_pattern 匹配到
    assert result['random_code'] is not None
    assert result['random_code']['text'] == '3472'


def test_ocr_cache():
    """測試 OCR 快取機制"""
    call_count = 0
    
    class CountingOCR:
        def recognize(self, image):
            nonlocal call_count
            call_count += 1
            return [((100, 100, 200, 50), ('TEST', 0.95))]
    
    extractor = HybridExtractor(CountingOCR())
    template = {
        'regions': {
            'field1': {
                'rect_ratio': {'x': 0.1, 'y': 0.1, 'width': 0.5, 'height': 0.05},
                'pattern': r'TEST'
            },
            'field2': {
                'rect_ratio': {'x': 0.2, 'y': 0.2, 'width': 0.5, 'height': 0.05},
                'pattern': r'TEST'
            }
        }
    }
    
    fake_image = np.zeros((1000, 1000, 3), dtype=np.uint8)
    extractor.extract_fields(fake_image, template)
    
    # OCR 應該只被調用一次（快取生效）
    assert call_count == 1
    
    # 清除快取後再次提取
    extractor.clear_cache()
    extractor.extract_fields(fake_image, template)
    
    # OCR 應該被再次調用
    assert call_count == 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
