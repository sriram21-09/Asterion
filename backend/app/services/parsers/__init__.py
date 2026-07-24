"""
CDR Parsers Package
===================
"""

from app.services.parsers.airtel import AirtelCDRParser
from app.services.parsers.base import BaseCDRParser
from app.services.parsers.bsnl import BSNLCDRParser
from app.services.parsers.jio import JioCDRParser
from app.services.parsers.vi import ViCDRParser

__all__ = [
    "BaseCDRParser",
    "AirtelCDRParser",
    "BSNLCDRParser",
    "JioCDRParser",
    "ViCDRParser",
]
