"""
Enumerations for the mortgage processing system.

Contains all enum definitions used throughout the system for type safety
and consistent value handling.
"""

from enum import Enum


class DocumentType(Enum):
    """Types of documents that can be processed in the mortgage workflow."""
    IDENTITY = "identity"
    INCOME = "income"
    EMPLOYMENT = "employment"
    CREDIT = "credit"
    PROPERTY = "property"
    ADDRESS_PROOF = "address_proof"
    TAX_DOCUMENT = "tax_document"
    BANK_STATEMENT = "bank_statement"
    PAY_STUB = "pay_stub"
    EMPLOYMENT_LETTER = "employment_letter"
    UTILITY_BILL = "utility_bill"
    INVOICE = "invoice"
    RECEIPT = "receipt"
    CONTRACT = "contract"
    PASSPORT = "passport"
    DRIVERS_LICENSE = "drivers_license"
    NATIONAL_ID = "national_id"


class ProcessingStatus(Enum):
    """Status of document or application processing."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    REQUIRES_REVIEW = "requires_review"
    CANCELLED = "cancelled"


class DecisionType(Enum):
    """Types of loan decisions that can be made."""
    APPROVE = "approve"
    CONDITIONAL = "conditional"
    DENY = "deny"
    PENDING = "pending"


class ValidationStatus(Enum):
    """Status of document validation."""
    VALID = "valid"
    INVALID = "invalid"
    PENDING = "pending"
    REQUIRES_MANUAL_REVIEW = "requires_manual_review"


class RiskLevel(Enum):
    """Risk levels for various assessments."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class LoanType(Enum):
    """Types of mortgage loans."""
    CONVENTIONAL = "conventional"
    FHA = "fha"
    VA = "va"
    USDA = "usda"
    JUMBO = "jumbo"