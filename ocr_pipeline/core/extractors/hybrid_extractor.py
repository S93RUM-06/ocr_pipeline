"""
混合提取器 (Hybrid Extractor)

結合全圖 OCR 高準確率與 ROI 位置提示的混合策略
基於 docs/hybrid_extraction_strategy.md 設計

策略:
  1. 全圖 OCR（保留 PaddleOCR 的高準確率 95-100%）
  2. ROI 作為位置提示（消除同類型欄位歧義）
  3. 多重評分機制（信心 50% + 位置 30% + 格式 20%）
  4. 三層降級策略（ROI 內 → 擴展區域 → 全圖搜尋）
"""

import re
import math
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass


@dataclass
class MatchCandidate:
    """匹配候選結果"""
    text: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # (x, y, width, height)
    position_score: float
    format_score: float
    total_score: float


class HybridExtractor:
    """
    混合提取器：全圖 OCR + ROI 位置提示
    
    工作流程：
    1. 對整張圖執行 OCR（一次性獲取所有文字）
    2. 對每個欄位使用正則匹配
    3. 用 ROI 位置提示消除歧義
    4. 多重評分選擇最佳候選
    """
    
    def __init__(self, ocr_adapter):
        """
        Args:
            ocr_adapter: OCR 適配器（如 PaddleOCRAdapter）
        """
        if ocr_adapter is None:
            raise ValueError("ocr_adapter is required")
        
        self.ocr_adapter = ocr_adapter
        self._ocr_cache = None
    
    def extract_fields(
        self, 
        image, 
        template: Dict
    ) -> Dict[str, Optional[Dict]]:
        """
        提取欄位
        
        Args:
            image: 影像陣列 (H, W, 3)
            template: 範本定義（必須包含 regions）
            
        Returns:
            {
                'field_name': {
                    'text': '提取的文字',
                    'confidence': 0.985,
                    'bbox': (x, y, w, h),
                    'position_score': 0.95,
                    'total_score': 0.97
                } 或 None（未找到）
            }
        """
        # Step 1: 執行全圖 OCR（快取結果）
        ocr_results = self._get_ocr_results(image)
        
        # Step 2: 提取各欄位
        img_h, img_w = image.shape[:2]
        regions = template.get('regions', {})
        
        extracted = {}
        for field_name, field_config in regions.items():
            # 使用三層降級策略
            result = self._extract_with_fallback(
                ocr_results,
                field_config,
                (img_w, img_h)
            )
            extracted[field_name] = result
        
        return extracted
    
    def _get_ocr_results(self, image) -> List:
        """
        執行 OCR（帶快取）
        
        Returns:
            [(bbox, (text, confidence)), ...]
        """
        if self._ocr_cache is None:
            self._ocr_cache = self.ocr_adapter.recognize(image)
        return self._ocr_cache
    
    def _extract_with_fallback(
        self,
        ocr_results: List,
        field_config: Dict,
        image_size: Tuple[int, int]
    ) -> Optional[Dict]:
        """
        三層降級策略提取
        
        Layer 1: 在 ROI 區域內搜尋（tolerance_ratio）
        Layer 2: 擴大範圍搜尋（tolerance_ratio * 2）
        Layer 3: 全圖搜尋（如果 required=True）
        
        Args:
            ocr_results: OCR 結果列表
            field_config: 欄位配置
            image_size: (width, height)
            
        Returns:
            {'text': ..., 'confidence': ..., 'bbox': ..., ...} 或 None
        """
        tolerance = field_config.get('tolerance_ratio', 0.2)
        
        # Layer 1: ROI 內搜尋
        candidates = self._find_in_region(
            ocr_results,
            field_config,
            image_size,
            tolerance
        )
        
        if candidates:
            return self._select_best_match(candidates, field_config)
        
        # Layer 2: 擴大範圍
        candidates = self._find_in_region(
            ocr_results,
            field_config,
            image_size,
            tolerance * 2
        )
        
        if candidates:
            return self._select_best_match(candidates, field_config)
        
        # Layer 3: 全圖搜尋（僅必填欄位）
        if field_config.get('required', False):
            candidates = self._find_in_region(
                ocr_results,
                field_config,
                image_size,
                tolerance=None  # 無位置限制
            )
            
            if candidates:
                return self._select_best_match(candidates, field_config)
        
        return None
    
    def _find_in_region(
        self,
        ocr_results: List,
        field_config: Dict,
        image_size: Tuple[int, int],
        tolerance: Optional[float]
    ) -> List[MatchCandidate]:
        """
        在指定區域內尋找匹配結果
        
        Args:
            ocr_results: [(bbox, (text, confidence)), ...]
            field_config: 欄位配置
            image_size: (width, height)
            tolerance: 容錯範圍（None = 全圖搜尋）
            
        Returns:
            List[MatchCandidate]
        """
        # 獲取配置
        pattern = field_config.get('pattern')
        if not pattern:
            return []
        
        fallback_pattern = field_config.get('fallback_pattern')
        extract_group = field_config.get('extract_group', 0)
        expected_length = field_config.get('expected_length')
        
        # 轉換 ROI 為絕對座標
        roi_absolute = None
        if tolerance is not None and 'rect_ratio' in field_config:
            roi_absolute = self._ratio_to_pixel(
                field_config['rect_ratio'],
                image_size
            )
            # 擴展 ROI
            roi_absolute = self._expand_roi(roi_absolute, tolerance)
        
        # 編譯正則表達式
        try:
            regex = re.compile(pattern, re.UNICODE)
            fallback_regex = re.compile(fallback_pattern, re.UNICODE) if fallback_pattern else None
        except re.error as e:
            print(f"Warning: Invalid regex pattern '{pattern}': {e}")
            return []
        
        candidates = []
        
        for bbox, (text, confidence) in ocr_results:
            # 檢查位置（如果有 ROI 限制）
            if roi_absolute and not self._is_in_area(bbox, roi_absolute):
                continue
            
            # 正則匹配（主要模式）
            match = regex.search(text)
            used_fallback = False
            
            # 降級到備用模式
            if not match and fallback_regex:
                match = fallback_regex.search(text)
                used_fallback = True
            
            if not match:
                continue
            
            # 提取文字
            try:
                matched_text = match.group(extract_group)
            except IndexError:
                matched_text = match.group(0)
            
            # 計算位置分數
            position_score = 1.0
            if roi_absolute:
                position_score = self._calc_position_score(
                    bbox,
                    field_config['rect_ratio'],
                    image_size
                )
            
            # 計算格式分數
            format_score = self._calc_format_score(
                matched_text,
                expected_length,
                used_fallback
            )
            
            # 綜合評分
            position_weight = field_config.get('position_weight', 0.3)
            total_score = (
                confidence * 0.5 +
                position_score * position_weight +
                format_score * (0.5 - position_weight)
            )
            
            candidates.append(MatchCandidate(
                text=matched_text,
                confidence=confidence,
                bbox=bbox,
                position_score=position_score,
                format_score=format_score,
                total_score=total_score
            ))
        
        return sorted(candidates, key=lambda c: c.total_score, reverse=True)
    
    def _select_best_match(
        self,
        candidates: List[MatchCandidate],
        field_config: Dict
    ) -> Dict:
        """
        選擇最佳匹配
        
        Args:
            candidates: 候選列表（已排序）
            field_config: 欄位配置
            
        Returns:
            {'text': ..., 'confidence': ..., ...}
        """
        if not candidates:
            return None
        
        best = candidates[0]
        
        return {
            'text': best.text,
            'confidence': best.confidence,
            'bbox': best.bbox,
            'position_score': best.position_score,
            'format_score': best.format_score,
            'total_score': best.total_score,
            'candidates_count': len(candidates)
        }
    
    def _ratio_to_pixel(
        self,
        rect_ratio: Dict,
        image_size: Tuple[int, int]
    ) -> Dict:
        """
        將比例座標轉換為像素座標
        
        Args:
            rect_ratio: {'x': 0.1, 'y': 0.2, 'width': 0.3, 'height': 0.05}
            image_size: (width, height)
            
        Returns:
            {'x': 120, 'y': 340, 'width': 360, 'height': 85}
        """
        img_w, img_h = image_size
        
        return {
            'x': int(rect_ratio['x'] * img_w),
            'y': int(rect_ratio['y'] * img_h),
            'width': int(rect_ratio['width'] * img_w),
            'height': int(rect_ratio['height'] * img_h)
        }
    
    def _expand_roi(self, roi: Dict, tolerance: float) -> Dict:
        """
        擴展 ROI 區域（容錯範圍）
        
        Args:
            roi: {'x': 100, 'y': 200, 'width': 300, 'height': 50}
            tolerance: 0.2（擴展 20%）
            
        Returns:
            擴展後的 ROI
        """
        expand_w = int(roi['width'] * tolerance)
        expand_h = int(roi['height'] * tolerance)
        
        return {
            'x': max(0, roi['x'] - expand_w),
            'y': max(0, roi['y'] - expand_h),
            'width': roi['width'] + 2 * expand_w,
            'height': roi['height'] + 2 * expand_h
        }
    
    def _is_in_area(self, bbox: Tuple, area: Dict) -> bool:
        """
        判斷 bbox 中心是否在區域內
        
        Args:
            bbox: (x, y, width, height)
            area: {'x': 100, 'y': 200, 'width': 300, 'height': 50}
            
        Returns:
            bool
        """
        # bbox 中心點
        bbox_cx = bbox[0] + bbox[2] / 2
        bbox_cy = bbox[1] + bbox[3] / 2
        
        # area 範圍
        area_left = area['x']
        area_right = area['x'] + area['width']
        area_top = area['y']
        area_bottom = area['y'] + area['height']
        
        in_x = area_left <= bbox_cx <= area_right
        in_y = area_top <= bbox_cy <= area_bottom
        
        return in_x and in_y
    
    def _calc_position_score(
        self,
        bbox: Tuple,
        rect_ratio: Dict,
        image_size: Tuple[int, int]
    ) -> float:
        """
        計算位置匹配分數（距離越近分數越高）
        
        Args:
            bbox: OCR 檢測到的 bbox
            rect_ratio: ROI 比例座標
            image_size: 影像大小
            
        Returns:
            0.0 - 1.0 的分數
        """
        img_w, img_h = image_size
        
        # bbox 中心
        bbox_cx = bbox[0] + bbox[2] / 2
        bbox_cy = bbox[1] + bbox[3] / 2
        
        # ROI 中心（絕對座標）
        roi_cx = (rect_ratio['x'] + rect_ratio['width'] / 2) * img_w
        roi_cy = (rect_ratio['y'] + rect_ratio['height'] / 2) * img_h
        
        # 計算距離
        distance = math.sqrt(
            (bbox_cx - roi_cx) ** 2 +
            (bbox_cy - roi_cy) ** 2
        )
        
        # 正規化距離（以影像對角線長度為基準）
        diagonal = math.sqrt(img_w ** 2 + img_h ** 2)
        norm_distance = distance / diagonal
        
        # 轉換為分數
        # 距離 0 → 分數 1.0
        # 距離 0.1 → 分數 0.5
        # 距離 >= 0.2 → 分數 0.0
        if norm_distance < 0.1:
            return 1.0 - norm_distance * 5.0
        elif norm_distance < 0.2:
            return 0.5 - (norm_distance - 0.1) * 5.0
        else:
            return max(0.0, 0.1 - norm_distance * 0.5)
    
    def _calc_format_score(
        self,
        text: str,
        expected_length: Optional[int],
        used_fallback: bool
    ) -> float:
        """
        計算格式匹配分數
        
        Args:
            text: 提取的文字
            expected_length: 預期長度
            used_fallback: 是否使用了降級正則
            
        Returns:
            0.0 - 1.0 的分數
        """
        score = 1.0
        
        # 使用降級正則降分
        if used_fallback:
            score -= 0.2
        
        # 長度檢查
        if expected_length:
            length_diff = abs(len(text) - expected_length)
            # 每差 1 個字元扣 0.05 分，最多扣 0.5
            score -= min(length_diff * 0.05, 0.5)
        
        return max(score, 0.0)
    
    def clear_cache(self):
        """清除 OCR 快取"""
        self._ocr_cache = None
