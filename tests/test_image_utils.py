"""
測試 image_utils 模組

影像處理工具函數測試，包括：
- 影像讀取與儲存
- 格式轉換
- 基本影像操作
"""

import pytest
import numpy as np
from pathlib import Path
from ocr_pipeline.utils.image_utils import (
    read_image,
    save_image,
    resize_image,
    convert_to_grayscale,
    get_image_size,
    is_valid_image,
    create_blank_image
)


class TestImageUtils:
    """影像工具函數測試"""

    @pytest.fixture
    def sample_image_array(self):
        """建立範例影像陣列（RGB，100x100）"""
        return np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

    @pytest.fixture
    def sample_grayscale_array(self):
        """建立範例灰階影像陣列（100x100）"""
        return np.random.randint(0, 255, (100, 100), dtype=np.uint8)

    @pytest.fixture
    def temp_image_file(self, tmp_path, sample_image_array):
        """建立臨時影像檔案"""
        import cv2
        image_path = tmp_path / "test_image.png"
        cv2.imwrite(str(image_path), sample_image_array)
        return image_path

    # ===== 影像讀取測試 =====

    def test_read_image_from_file(self, temp_image_file):
        """測試：從檔案讀取影像"""
        img = read_image(temp_image_file)
        
        assert img is not None
        assert isinstance(img, np.ndarray)
        assert len(img.shape) in [2, 3]  # 2D 或 3D 陣列

    def test_read_image_as_grayscale(self, temp_image_file):
        """測試：以灰階模式讀取影像"""
        img = read_image(temp_image_file, grayscale=True)
        
        assert img is not None
        assert len(img.shape) == 2  # 2D 陣列（灰階）

    def test_read_nonexistent_image(self):
        """測試：讀取不存在的檔案應該拋出例外"""
        with pytest.raises(FileNotFoundError):
            read_image("nonexistent_image.png")

    def test_read_invalid_image_format(self, tmp_path):
        """測試：讀取無效的影像格式應該拋出例外"""
        invalid_file = tmp_path / "invalid.txt"
        invalid_file.write_text("not an image", encoding='utf-8')
        
        with pytest.raises(ValueError):
            read_image(invalid_file)

    # ===== 影像儲存測試 =====

    def test_save_image(self, tmp_path, sample_image_array):
        """測試：儲存影像到檔案"""
        output_path = tmp_path / "output.png"
        save_image(sample_image_array, output_path)
        
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_save_image_creates_directory(self, tmp_path, sample_image_array):
        """測試：儲存影像時自動建立目錄"""
        output_path = tmp_path / "subdir" / "output.png"
        save_image(sample_image_array, output_path)
        
        assert output_path.exists()

    def test_save_invalid_image_array(self, tmp_path):
        """測試：儲存無效的陣列應該拋出例外"""
        invalid_array = np.array([1, 2, 3])  # 1D 陣列
        
        with pytest.raises(ValueError):
            save_image(invalid_array, tmp_path / "output.png")

    # ===== 影像尺寸調整測試 =====

    def test_resize_image(self, sample_image_array):
        """測試：調整影像尺寸"""
        resized = resize_image(sample_image_array, width=50, height=50)
        
        assert resized.shape[:2] == (50, 50)

    def test_resize_image_maintain_aspect_ratio(self, sample_image_array):
        """測試：調整尺寸時保持長寬比"""
        # 只指定寬度，高度自動計算
        resized = resize_image(sample_image_array, width=50)
        
        assert resized.shape[1] == 50
        assert resized.shape[0] == 50  # 原本是正方形

    def test_resize_image_invalid_size(self, sample_image_array):
        """測試：無效的尺寸應該拋出例外"""
        with pytest.raises(ValueError):
            resize_image(sample_image_array, width=0, height=0)

    # ===== 灰階轉換測試 =====

    def test_convert_to_grayscale_from_color(self, sample_image_array):
        """測試：將彩色影像轉換為灰階"""
        gray = convert_to_grayscale(sample_image_array)
        
        assert len(gray.shape) == 2  # 2D 陣列
        assert gray.dtype == np.uint8

    def test_convert_to_grayscale_already_gray(self, sample_grayscale_array):
        """測試：灰階影像轉換應該回傳原影像"""
        gray = convert_to_grayscale(sample_grayscale_array)
        
        assert len(gray.shape) == 2
        np.testing.assert_array_equal(gray, sample_grayscale_array)

    # ===== 取得影像尺寸測試 =====

    def test_get_image_size(self, sample_image_array):
        """測試：取得影像尺寸"""
        width, height = get_image_size(sample_image_array)
        
        assert width == 100
        assert height == 100

    def test_get_image_size_from_grayscale(self, sample_grayscale_array):
        """測試：取得灰階影像尺寸"""
        width, height = get_image_size(sample_grayscale_array)
        
        assert width == 100
        assert height == 100

    # ===== 影像驗證測試 =====

    def test_is_valid_image_color(self, sample_image_array):
        """測試：驗證彩色影像"""
        assert is_valid_image(sample_image_array) is True

    def test_is_valid_image_grayscale(self, sample_grayscale_array):
        """測試：驗證灰階影像"""
        assert is_valid_image(sample_grayscale_array) is True

    def test_is_valid_image_invalid_shape(self):
        """測試：無效的影像形狀"""
        invalid_array = np.array([1, 2, 3])  # 1D
        assert is_valid_image(invalid_array) is False

    def test_is_valid_image_invalid_dtype(self):
        """測試：無效的資料型別"""
        invalid_array = np.random.rand(100, 100)  # float64
        assert is_valid_image(invalid_array) is False

    def test_is_valid_image_none(self):
        """測試：None 不是有效影像"""
        assert is_valid_image(None) is False

    # ===== 建立空白影像測試 =====

    def test_create_blank_image_color(self):
        """測試：建立彩色空白影像"""
        img = create_blank_image(100, 100, channels=3)
        
        assert img.shape == (100, 100, 3)
        assert img.dtype == np.uint8
        assert np.all(img == 0)  # 全黑

    def test_create_blank_image_grayscale(self):
        """測試：建立灰階空白影像"""
        img = create_blank_image(100, 100, channels=1)
        
        assert img.shape == (100, 100)
        assert img.dtype == np.uint8

    def test_create_blank_image_with_color(self):
        """測試：建立指定顏色的空白影像"""
        img = create_blank_image(100, 100, channels=3, color=(255, 255, 255))
        
        assert np.all(img == 255)  # 全白

    def test_create_blank_image_invalid_size(self):
        """測試：無效的尺寸"""
        with pytest.raises(ValueError):
            create_blank_image(-100, 100)
