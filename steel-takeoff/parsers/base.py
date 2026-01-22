"""
Base Parser
Abstract base class for all parsers
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from domain import ParseResult


class BaseParser(ABC):
    """Abstract base class for file parsers"""
    
    def __init__(self, file_path: Path):
        self.file_path = Path(file_path)
        self._validate_file()
    
    def _validate_file(self) -> None:
        """Validate that the file exists and is readable"""
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")
        if not self.file_path.is_file():
            raise ValueError(f"Path is not a file: {self.file_path}")
    
    @abstractmethod
    def parse(self) -> ParseResult:
        """Parse the file and return results"""
        pass
    
    @property
    @abstractmethod
    def supported_extensions(self) -> tuple:
        """Return tuple of supported file extensions"""
        pass
    
    def supports_file(self, file_path: Path) -> bool:
        """Check if this parser supports the given file"""
        return file_path.suffix.lower() in self.supported_extensions
