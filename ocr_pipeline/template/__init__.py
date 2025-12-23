"""
Template 模組：負責載入和驗證 OCR Template JSON
"""

from .validator import TemplateValidator, ValidationError

__all__ = [
    "TemplateValidator", 
    "ValidationError",
]
