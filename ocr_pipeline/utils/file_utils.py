"""
檔案操作工具函數

提供路徑處理、目錄操作、檔案 I/O 等功能
"""

from pathlib import Path
from typing import List, Union, Optional


def ensure_directory_exists(directory: Union[str, Path]) -> Path:
    """
    確保目錄存在，若不存在則建立
    
    Args:
        directory: 目錄路徑
        
    Returns:
        Path 物件
    """
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def get_file_extension(file_path: Union[str, Path]) -> str:
    """
    取得檔案副檔名
    
    Args:
        file_path: 檔案路徑
        
    Returns:
        副檔名（包含點號，如 ".png"）
    """
    return Path(file_path).suffix


def change_file_extension(
    file_path: Union[str, Path], 
    new_extension: str
) -> Path:
    """
    更改檔案副檔名
    
    Args:
        file_path: 原檔案路徑
        new_extension: 新副檔名（需包含點號，如 ".jpg"）
        
    Returns:
        新的 Path 物件
    """
    file_path = Path(file_path)
    return file_path.with_suffix(new_extension)


def list_files_in_directory(
    directory: Union[str, Path],
    pattern: str = "*",
    recursive: bool = False
) -> List[Path]:
    """
    列出目錄中的檔案
    
    Args:
        directory: 目錄路徑
        pattern: 檔案模式（如 "*.png"）
        recursive: 是否遞迴搜尋子目錄
        
    Returns:
        檔案路徑列表
        
    Raises:
        FileNotFoundError: 目錄不存在
    """
    directory = Path(directory)
    
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    
    if recursive:
        files = list(directory.rglob(pattern))
    else:
        files = list(directory.glob(pattern))
    
    # 只回傳檔案，排除目錄
    return [f for f in files if f.is_file()]


def is_image_file(file_path: Union[str, Path]) -> bool:
    """
    判斷是否為影像檔案
    
    Args:
        file_path: 檔案路徑
        
    Returns:
        是否為影像檔案
    """
    image_extensions = {
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', 
        '.tiff', '.tif', '.webp', '.svg'
    }
    
    extension = get_file_extension(file_path).lower()
    return extension in image_extensions


def get_relative_path(
    target: Union[str, Path],
    base: Union[str, Path]
) -> Path:
    """
    取得相對路徑
    
    Args:
        target: 目標路徑
        base: 基準路徑
        
    Returns:
        相對路徑
    """
    target = Path(target)
    base = Path(base)
    
    return target.relative_to(base)


def join_paths(*paths: Union[str, Path]) -> Path:
    """
    連接多個路徑
    
    Args:
        *paths: 要連接的路徑
        
    Returns:
        連接後的 Path 物件
    """
    result = Path(paths[0])
    
    for path in paths[1:]:
        result = result / path
    
    return result


def get_project_root() -> Path:
    """
    取得專案根目錄
    
    Returns:
        專案根目錄的 Path 物件
    """
    # 從當前檔案往上找，直到找到包含 pyproject.toml 的目錄
    current = Path(__file__).resolve()
    
    for parent in current.parents:
        if (parent / "pyproject.toml").exists():
            return parent
    
    # 如果找不到，回傳當前檔案所在目錄的父目錄的父目錄
    # (utils -> ocr_pipeline -> project_root)
    return Path(__file__).resolve().parent.parent.parent
