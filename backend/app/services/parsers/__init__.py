"""
CDR Parsers Package
===================
"""

from app.services.parsers.airtel import AirtelCDRParser
from app.services.parsers.base import BaseCDRParser
from app.services.parsers.bsnl import BSNLCDRParser
from app.services.parsers.jio import JioCDRParser
from app.services.parsers.vi import ViCDRParser
from app.services.parsers.generic_json import GenericJSONParser
from app.services.parsers.generic_xml import GenericXMLParser

__all__ = [
    "AirtelCDRParser",
    "BaseCDRParser",
    "BSNLCDRParser",
    "JioCDRParser",
    "ViCDRParser",
    "GenericJSONParser",
    "GenericXMLParser",
]
