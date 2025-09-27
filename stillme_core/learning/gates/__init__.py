"""
StillMe Learning Gates
Content validation gates (license, quality, etc.).
"""

from .license_gate import validate_content_licenses, validate_content_license, LicenseGate

__all__ = ['validate_content_licenses', 'validate_content_license', 'LicenseGate']
