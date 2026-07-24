"""
Base CDR Parser Interface
=========================
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseCDRParser(ABC):
    """Base interface for operator-specific CDR CSV parsers."""

    @abstractmethod
    def detect(self, content_sample: str) -> bool:
        """Return True if the content matches this operator's format."""

    @abstractmethod
    def parse(self, content: str) -> tuple[list[dict[str, Any]], int]:
        """
        Parse CSV content string.
        Returns a tuple of (parsed_records_dicts, failed_count).
        """
