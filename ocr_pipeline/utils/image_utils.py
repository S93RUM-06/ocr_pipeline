"""
影像處理工具函數

提供基本的影像讀取、儲存、轉換等功能
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, Union


def read_image(
    file_path: Union[str, Path], 
    grayscale: bool = False
) -> np.ndarray:
    """
    從檔案讀取影像
    
    Args:
        file_path: 影像檔案路徑
        grayscale: 是否以灰階模式讀取
        
    Returns:
        影像陣列（numpy.ndarray）
        
    Raises:
        FileNotFoundError: 檔案不存在
        ValueError: 無法讀取影像
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Image file not found: {file_path}")
    
    # 讀取影像
    if grayscale:
        img = cv2.imread(str(file_path), cv2.IMREAD_GRAYSCALE)
    else:
        img = cv2.imread(str(file_path))
    
    if img is None:
        raise ValueError(f"Failed to read image: {file_path}")
    
    return img


def save_image(
    image: np.ndarray, 
    file_path: Union[str, Path]
) -> None:
    """
    儲存影像到檔案
    
    Args:
        image: 影像陣列
        file_path: 輸出檔案路徑
        
    Raises:
        ValueError: 無效的影像陣列
    """
    if not is_valid_image(image):
        raise ValueError("Invalid image array")
    
    file_path = Path(file_path)
    
    # 自動建立目錄
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 儲存影像
    success = cv2.imwrite(str(file_path), image)
    
    if not success:
        raise ValueError(f"Failed to save image: {file_path}")


def resize_image(
    image: np.ndarray,
    width: Optional[int] = None,
    height: Optional[int] = None,
    maintain_aspect_ratio: bool = True
) -> np.ndarray:
    """
    調整影像尺寸
    
    Args:
        image: 輸入影像
        width: 目標寬度
        height: 目標高度
        maintain_aspect_ratio: 是否保持長寬比
        
    Returns:
        調整後的影像
        
    Raises:
        ValueError: 無效的尺寸參數
    """
    if width is not None and width <= 0:
        raise ValueError("Width must be positive")
    if height is not None and height <= 0:
        raise ValueError("Height must be positive")
    
    h, w = image.shape[:2]
    
    # 如果只指定一個維度，計算另一個維度
    if maintain_aspect_ratio:
        if width is not None and height is None:
            height = int(h * width / w)
        elif height is not None and width is None:
            width = int(w * height / h)
    
    if width is None or height is None:
        raise ValueError("Must specify at least width or height")
    
    resized = cv2.resize(image, (width, height), interpolation=cv2.INTER_LINEAR)
    return resized


def convert_to_grayscale(image: np.ndarray) -> np.ndarray:
    """
    將影像轉換為灰階
    
    Args:
        image: 輸入影像
        
    Returns:
        灰階影像
    """
    # 如果已經是灰階，直接回傳
    if len(image.shape) == 2:
        return image
    
    # 轉換為灰階
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return gray


def get_image_size(image: np.ndarray) -> Tuple[int, int]:
    """
    取得影像尺寸
    
    Args:
        image: 輸入影像
        
    Returns:
        (width, height) 寬度和高度
    """
    h, w = image.shape[:2]
    return (w, h)


def is_valid_image(image: any) -> bool:
    """
    驗證是否為有效的影像陣列
    
    Args:
        image: 待驗證的物件
        
    Returns:
        是否為有效影像
    """
    if image is None:
        return False
    
    if not isinstance(image, np.ndarray):
        return False
    
    # 檢查維度（2D 或 3D）
    if len(image.shape) not in [2, 3]:
        return False
    
    # 檢查資料型別
    if image.dtype != np.uint8:
        return False
    
    return True


def create_blank_image(
    width: int,
    height: int,
    channels: int = 3,
    color: Optional[Tuple[int, ...]] = None
) -> np.ndarray:
    """
    建立空白影像
    
    Args:
        width: 寬度
        height: 高度
        channels: 通道數（1=灰階，3=彩色）
        color: 填充顏色（預設為黑色）
        
    Returns:
        空白影像陣列
        
    Raises:
        ValueError: 無效的尺寸參數
    """
    if width <= 0 or height <= 0:
        raise ValueError("Width and height must be positive")
    
    if channels == 1:
        # 灰階影像
        img = np.zeros((height, width), dtype=np.uint8)
        if color is not None:
            img.fill(color[0])
    elif channels == 3:
        # 彩色影像
        img = np.zeros((height, width, 3), dtype=np.uint8)
        if color is not None:
            img[:] = color
    else:
        raise ValueError("Channels must be 1 or 3")
    
    return img
