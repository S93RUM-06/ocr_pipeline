"""
測試 file_utils 模組

檔案操作工具函數測試，包括：
- 路徑處理
- 目錄操作
- 檔案 I/O
"""

import pytest
from pathlib import Path
from ocr_pipeline.utils.file_utils import (
    ensure_directory_exists,
    get_file_extension,
    change_file_extension,
    list_files_in_directory,
    is_image_file,
    get_relative_path,
    join_paths,
    get_project_root
)


class TestFileUtils:
    """檔案工具函數測試"""

    # ===== 目錄操作測試 =====

    def test_ensure_directory_exists_creates_dir(self, tmp_path):
        """測試：建立不存在的目錄"""
        new_dir = tmp_path / "new_directory"
        ensure_directory_exists(new_dir)
        
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_ensure_directory_exists_nested_dirs(self, tmp_path):
        """測試：建立巢狀目錄"""
        nested_dir = tmp_path / "level1" / "level2" / "level3"
        ensure_directory_exists(nested_dir)
        
        assert nested_dir.exists()
        assert nested_dir.is_dir()

    def test_ensure_directory_exists_already_exists(self, tmp_path):
        """測試：目錄已存在時不報錯"""
        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()
        
        ensure_directory_exists(existing_dir)  # 不應該報錯
        assert existing_dir.exists()

    # ===== 檔案副檔名測試 =====

    def test_get_file_extension(self):
        """測試：取得檔案副檔名"""
        assert get_file_extension("image.png") == ".png"
        assert get_file_extension("document.pdf") == ".pdf"
        assert get_file_extension("archive.tar.gz") == ".gz"

    def test_get_file_extension_no_extension(self):
        """測試：沒有副檔名"""
        assert get_file_extension("filename") == ""

    def test_get_file_extension_from_path(self):
        """測試：從路徑取得副檔名"""
        assert get_file_extension("/path/to/file.txt") == ".txt"
        assert get_file_extension(Path("/path/to/file.jpg")) == ".jpg"

    def test_change_file_extension(self):
        """測試：更改檔案副檔名"""
        assert change_file_extension("image.png", ".jpg") == Path("image.jpg")
        assert change_file_extension("doc.txt", ".pdf") == Path("doc.pdf")

    def test_change_file_extension_with_path(self):
        """測試：路徑中的檔案副檔名更改"""
        result = change_file_extension("/path/to/file.png", ".jpg")
        assert str(result) == "/path/to/file.jpg"

    def test_change_file_extension_add_extension(self):
        """測試：添加副檔名到無副檔名的檔案"""
        assert change_file_extension("filename", ".txt") == Path("filename.txt")

    # ===== 列出檔案測試 =====

    def test_list_files_in_directory(self, tmp_path):
        """測試：列出目錄中的檔案"""
        # 建立測試檔案
        (tmp_path / "file1.txt").touch()
        (tmp_path / "file2.png").touch()
        (tmp_path / "file3.jpg").touch()
        
        files = list_files_in_directory(tmp_path)
        
        assert len(files) == 3
        assert all(isinstance(f, Path) for f in files)

    def test_list_files_with_pattern(self, tmp_path):
        """測試：使用模式篩選檔案"""
        (tmp_path / "image1.png").touch()
        (tmp_path / "image2.png").touch()
        (tmp_path / "document.txt").touch()
        
        png_files = list_files_in_directory(tmp_path, pattern="*.png")
        
        assert len(png_files) == 2
        assert all(f.suffix == ".png" for f in png_files)

    def test_list_files_recursive(self, tmp_path):
        """測試：遞迴列出檔案"""
        # 建立巢狀結構
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (tmp_path / "file1.txt").touch()
        (subdir / "file2.txt").touch()
        
        files = list_files_in_directory(tmp_path, recursive=True)
        
        assert len(files) == 2

    def test_list_files_empty_directory(self, tmp_path):
        """測試：空目錄"""
        files = list_files_in_directory(tmp_path)
        assert len(files) == 0

    def test_list_files_nonexistent_directory(self):
        """測試：不存在的目錄應該拋出例外"""
        with pytest.raises(FileNotFoundError):
            list_files_in_directory("/nonexistent/directory")

    # ===== 影像檔案判斷測試 =====

    def test_is_image_file_valid_extensions(self):
        """測試：有效的影像副檔名"""
        image_files = [
            "photo.jpg",
            "image.png",
            "document.jpeg",
            "scan.tiff",
            "picture.bmp",
            Path("/path/to/image.gif")
        ]
        
        for file in image_files:
            assert is_image_file(file) is True

    def test_is_image_file_invalid_extensions(self):
        """測試：非影像副檔名"""
        non_image_files = [
            "document.pdf",
            "data.txt",
            "archive.zip",
            "script.py"
        ]
        
        for file in non_image_files:
            assert is_image_file(file) is False

    def test_is_image_file_case_insensitive(self):
        """測試：副檔名不區分大小寫"""
        assert is_image_file("IMAGE.PNG") is True
        assert is_image_file("photo.JPG") is True

    # ===== 相對路徑測試 =====

    def test_get_relative_path(self, tmp_path):
        """測試：取得相對路徑"""
        base = tmp_path / "base"
        target = tmp_path / "base" / "subdir" / "file.txt"
        
        rel_path = get_relative_path(target, base)
        
        assert str(rel_path) == "subdir/file.txt" or str(rel_path) == "subdir\\file.txt"

    def test_get_relative_path_same_directory(self, tmp_path):
        """測試：同目錄的相對路徑"""
        base = tmp_path
        target = tmp_path / "file.txt"
        
        rel_path = get_relative_path(target, base)
        
        assert str(rel_path) == "file.txt"

    # ===== 路徑連接測試 =====

    def test_join_paths(self):
        """測試：連接路徑"""
        result = join_paths("base", "subdir", "file.txt")
        
        assert isinstance(result, Path)
        assert result.parts[-3:] == ("base", "subdir", "file.txt")

    def test_join_paths_with_path_objects(self):
        """測試：使用 Path 物件連接"""
        result = join_paths(Path("base"), "subdir", "file.txt")
        
        assert isinstance(result, Path)

    # ===== 專案根目錄測試 =====

    def test_get_project_root(self):
        """測試：取得專案根目錄"""
        root = get_project_root()
        
        assert isinstance(root, Path)
        assert root.exists()
        # 專案根目錄應該包含 pyproject.toml
        assert (root / "pyproject.toml").exists()
