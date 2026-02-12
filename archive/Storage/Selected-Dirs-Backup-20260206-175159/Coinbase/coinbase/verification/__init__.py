"""
Verification Layer
==================
Data verification and fact-checking for Coinbase.
"""

from .verification_scale import SourceData, SourceType, VerificationResult, VerificationScale

__all__ = ["VerificationScale", "VerificationResult", "SourceType", "SourceData"]
