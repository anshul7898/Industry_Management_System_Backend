from pydantic import BaseModel, Field, field_validator, EmailStr
from typing import Optional
import re


class Party(BaseModel):
    partyId: int
    partyName: str
    aliasOrCompanyName: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    agentId: Optional[int] = None
    contact_Person1: Optional[str] = None
    contact_Person2: Optional[str] = None
    email: Optional[str] = None
    mobile1: Optional[str] = None
    mobile2: Optional[str] = None
    orderId: Optional[str] = None


class CreateParty(BaseModel):
    partyName: str = Field(..., min_length=1, max_length=255, description="Party name")
    aliasOrCompanyName: str = Field(..., min_length=1, max_length=255, description="Alias or company name")
    contact_Person1: str = Field(..., min_length=1, max_length=255, description="First contact person name")
    contact_Person2: Optional[str] = Field(None, max_length=255, description="Second contact person name (optional)")
    mobile1: str = Field(..., description="Primary mobile number - 10 digits")
    mobile2: Optional[str] = Field(None, description="Secondary mobile number - 10 digits (optional)")
    email: Optional[str] = Field(None, description="Email address (optional)")
    address: Optional[str] = Field(None, max_length=500, description="Complete address (optional)")
    city: Optional[str] = Field(None, max_length=100, description="City (optional)")
    state: Optional[str] = Field(None, max_length=100, description="State (optional)")
    pincode: Optional[str] = Field(None, max_length=10, description="Pincode (optional)")
    agentId: Optional[int] = Field(None, description="Agent ID (optional)")
    orderId: Optional[str] = Field(None, max_length=100, description="Order ID (optional)")

    @field_validator('partyName')
    @classmethod
    def validate_party_name(cls, v):
        """Validate party name"""
        if not v or not v.strip():
            raise ValueError("Party name cannot be empty")

        if len(v.strip()) < 2:
            raise ValueError("Party name must be at least 2 characters long")

        if len(v) > 255:
            raise ValueError("Party name cannot exceed 255 characters")

        return v.strip()

    @field_validator('aliasOrCompanyName')
    @classmethod
    def validate_alias_company_name(cls, v):
        """Validate alias or company name"""
        if not v or not v.strip():
            raise ValueError("Alias or company name cannot be empty")

        if len(v.strip()) < 2:
            raise ValueError("Alias or company name must be at least 2 characters long")

        if len(v) > 255:
            raise ValueError("Alias or company name cannot exceed 255 characters")

        return v.strip()

    @field_validator('contact_Person1')
    @classmethod
    def validate_contact_person1(cls, v):
        """Validate first contact person name"""
        if not v or not v.strip():
            raise ValueError("Contact person 1 name cannot be empty")

        if len(v.strip()) < 2:
            raise ValueError("Contact person 1 name must be at least 2 characters long")

        if len(v) > 255:
            raise ValueError("Contact person 1 name cannot exceed 255 characters")

        # Allow letters, spaces, and common punctuation
        if not re.match(r"^[a-zA-Z\s\.\-\']+$", v):
            raise ValueError("Contact person name can only contain letters, spaces, dots, hyphens, and apostrophes")

        return v.strip()

    @field_validator('contact_Person2')
    @classmethod
    def validate_contact_person2(cls, v):
        """Validate second contact person name (optional)"""
        if not v:
            return v

        if not v.strip():
            return None

        if len(v.strip()) < 2:
            raise ValueError("Contact person 2 name must be at least 2 characters long")

        if len(v) > 255:
            raise ValueError("Contact person 2 name cannot exceed 255 characters")

        if not re.match(r"^[a-zA-Z\s\.\-\']+$", v):
            raise ValueError("Contact person name can only contain letters, spaces, dots, hyphens, and apostrophes")

        return v.strip()

    @field_validator('mobile1')
    @classmethod
    def validate_mobile1(cls, v):
        """Validate primary mobile number - must be exactly 10 digits"""
        if not v:
            raise ValueError("Mobile 1 is required")

        # Remove any non-digit characters
        cleaned = ''.join(c for c in v if c.isdigit())

        if len(cleaned) != 10:
            raise ValueError("Mobile 1 must be exactly 10 digits")

        if not cleaned.isdigit():
            raise ValueError("Mobile 1 must contain only digits")

        # Check if number is valid (doesn't start with 0 or 1)
        if cleaned[0] in ['0', '1']:
            raise ValueError("Mobile 1 cannot start with 0 or 1")

        return cleaned

    @field_validator('mobile2')
    @classmethod
    def validate_mobile2(cls, v):
        """Validate secondary mobile number (optional) - must be exactly 10 digits if provided"""
        if not v:
            return v

        if not v.strip():
            return None

        # Remove any non-digit characters
        cleaned = ''.join(c for c in v if c.isdigit())

        if len(cleaned) != 10:
            raise ValueError("Mobile 2 must be exactly 10 digits")

        if not cleaned.isdigit():
            raise ValueError("Mobile 2 must contain only digits")

        # Check if number is valid (doesn't start with 0 or 1)
        if cleaned[0] in ['0', '1']:
            raise ValueError("Mobile 2 cannot start with 0 or 1")

        return cleaned

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        """Validate email address (optional)"""
        if not v:
            return v

        if not v.strip():
            return None

        # Email regex pattern
        email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'

        if not re.match(email_pattern, v):
            raise ValueError("Please enter a valid email address (e.g., user@example.com)")

        if len(v) > 255:
            raise ValueError("Email cannot exceed 255 characters")

        return v.strip().lower()

    @field_validator('address')
    @classmethod
    def validate_address(cls, v):
        """Validate address (optional)"""
        if not v:
            return v

        if not v.strip():
            return None

        if len(v.strip()) < 5:
            raise ValueError("Address must be at least 5 characters long if provided")

        if len(v) > 500:
            raise ValueError("Address cannot exceed 500 characters")

        return v.strip()

    @field_validator('pincode')
    @classmethod
    def validate_pincode(cls, v):
        """Validate pincode (optional) - typically 6 digits in India"""
        if not v:
            return v

        if not v.strip():
            return None

        # Remove spaces
        cleaned = v.replace(' ', '')

        if len(cleaned) != 6:
            raise ValueError("Pincode must be exactly 6 digits")

        if not cleaned.isdigit():
            raise ValueError("Pincode must contain only digits")

        return cleaned

    @field_validator('city')
    @classmethod
    def validate_city(cls, v):
        """Validate city (optional)"""
        if not v:
            return v

        if not v.strip():
            return None

        if len(v.strip()) < 2:
            raise ValueError("City name must be at least 2 characters long if provided")

        if len(v) > 100:
            raise ValueError("City name cannot exceed 100 characters")

        return v.strip()

    @field_validator('state')
    @classmethod
    def validate_state(cls, v):
        """Validate state (optional)"""
        if not v:
            return v

        if not v.strip():
            return None

        if len(v.strip()) < 2:
            raise ValueError("State name must be at least 2 characters long if provided")

        if len(v) > 100:
            raise ValueError("State name cannot exceed 100 characters")

        return v.strip()

    @field_validator('orderId')
    @classmethod
    def validate_order_id(cls, v):
        """Validate order ID (optional)"""
        if not v:
            return v

        if not v.strip():
            return None

        if len(v) > 100:
            raise ValueError("Order ID cannot exceed 100 characters")

        return v.strip()

    @field_validator('agentId')
    @classmethod
    def validate_agent_id(cls, v):
        """Validate agent ID (optional)"""
        if v is not None and v <= 0:
            raise ValueError("Agent ID must be a positive integer")

        return v


class UpdateParty(BaseModel):
    partyName: str = Field(..., min_length=1, max_length=255, description="Party name")
    aliasOrCompanyName: str = Field(..., min_length=1, max_length=255, description="Alias or company name")
    contact_Person1: str = Field(..., min_length=1, max_length=255, description="First contact person name")
    contact_Person2: Optional[str] = Field(None, max_length=255, description="Second contact person name (optional)")
    mobile1: str = Field(..., description="Primary mobile number - 10 digits")
    mobile2: Optional[str] = Field(None, description="Secondary mobile number - 10 digits (optional)")
    email: Optional[str] = Field(None, description="Email address (optional)")
    address: Optional[str] = Field(None, max_length=500, description="Complete address (optional)")
    city: Optional[str] = Field(None, max_length=100, description="City (optional)")
    state: Optional[str] = Field(None, max_length=100, description="State (optional)")
    pincode: Optional[str] = Field(None, max_length=10, description="Pincode (optional)")
    agentId: Optional[int] = Field(None, description="Agent ID (optional)")
    orderId: Optional[str] = Field(None, max_length=100, description="Order ID (optional)")

    @field_validator('partyName')
    @classmethod
    def validate_party_name(cls, v):
        """Validate party name"""
        if not v or not v.strip():
            raise ValueError("Party name cannot be empty")

        if len(v.strip()) < 2:
            raise ValueError("Party name must be at least 2 characters long")

        if len(v) > 255:
            raise ValueError("Party name cannot exceed 255 characters")

        return v.strip()

    @field_validator('aliasOrCompanyName')
    @classmethod
    def validate_alias_company_name(cls, v):
        """Validate alias or company name"""
        if not v or not v.strip():
            raise ValueError("Alias or company name cannot be empty")

        if len(v.strip()) < 2:
            raise ValueError("Alias or company name must be at least 2 characters long")

        if len(v) > 255:
            raise ValueError("Alias or company name cannot exceed 255 characters")

        return v.strip()

    @field_validator('contact_Person1')
    @classmethod
    def validate_contact_person1(cls, v):
        """Validate first contact person name"""
        if not v or not v.strip():
            raise ValueError("Contact person 1 name cannot be empty")

        if len(v.strip()) < 2:
            raise ValueError("Contact person 1 name must be at least 2 characters long")

        if len(v) > 255:
            raise ValueError("Contact person 1 name cannot exceed 255 characters")

        if not re.match(r"^[a-zA-Z\s\.\-\']+$", v):
            raise ValueError("Contact person name can only contain letters, spaces, dots, hyphens, and apostrophes")

        return v.strip()

    @field_validator('contact_Person2')
    @classmethod
    def validate_contact_person2(cls, v):
        """Validate second contact person name (optional)"""
        if not v:
            return v

        if not v.strip():
            return None

        if len(v.strip()) < 2:
            raise ValueError("Contact person 2 name must be at least 2 characters long")

        if len(v) > 255:
            raise ValueError("Contact person 2 name cannot exceed 255 characters")

        if not re.match(r"^[a-zA-Z\s\.\-\']+$", v):
            raise ValueError("Contact person name can only contain letters, spaces, dots, hyphens, and apostrophes")

        return v.strip()

    @field_validator('mobile1')
    @classmethod
    def validate_mobile1(cls, v):
        """Validate primary mobile number - must be exactly 10 digits"""
        if not v:
            raise ValueError("Mobile 1 is required")

        cleaned = ''.join(c for c in v if c.isdigit())

        if len(cleaned) != 10:
            raise ValueError("Mobile 1 must be exactly 10 digits")

        if not cleaned.isdigit():
            raise ValueError("Mobile 1 must contain only digits")

        if cleaned[0] in ['0', '1']:
            raise ValueError("Mobile 1 cannot start with 0 or 1")

        return cleaned

    @field_validator('mobile2')
    @classmethod
    def validate_mobile2(cls, v):
        """Validate secondary mobile number (optional) - must be exactly 10 digits if provided"""
        if not v:
            return v

        if not v.strip():
            return None

        cleaned = ''.join(c for c in v if c.isdigit())

        if len(cleaned) != 10:
            raise ValueError("Mobile 2 must be exactly 10 digits")

        if not cleaned.isdigit():
            raise ValueError("Mobile 2 must contain only digits")

        if cleaned[0] in ['0', '1']:
            raise ValueError("Mobile 2 cannot start with 0 or 1")

        return cleaned

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        """Validate email address (optional)"""
        if not v:
            return v

        if not v.strip():
            return None

        email_pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'

        if not re.match(email_pattern, v):
            raise ValueError("Please enter a valid email address (e.g., user@example.com)")

        if len(v) > 255:
            raise ValueError("Email cannot exceed 255 characters")

        return v.strip().lower()

    @field_validator('address')
    @classmethod
    def validate_address(cls, v):
        """Validate address (optional)"""
        if not v:
            return v

        if not v.strip():
            return None

        if len(v.strip()) < 5:
            raise ValueError("Address must be at least 5 characters long if provided")

        if len(v) > 500:
            raise ValueError("Address cannot exceed 500 characters")

        return v.strip()

    @field_validator('pincode')
    @classmethod
    def validate_pincode(cls, v):
        """Validate pincode (optional) - typically 6 digits in India"""
        if not v:
            return v

        if not v.strip():
            return None

        cleaned = v.replace(' ', '')

        if len(cleaned) != 6:
            raise ValueError("Pincode must be exactly 6 digits")

        if not cleaned.isdigit():
            raise ValueError("Pincode must contain only digits")

        return cleaned

    @field_validator('city')
    @classmethod
    def validate_city(cls, v):
        """Validate city (optional)"""
        if not v:
            return v

        if not v.strip():
            return None

        if len(v.strip()) < 2:
            raise ValueError("City name must be at least 2 characters long if provided")

        if len(v) > 100:
            raise ValueError("City name cannot exceed 100 characters")

        return v.strip()

    @field_validator('state')
    @classmethod
    def validate_state(cls, v):
        """Validate state (optional)"""
        if not v:
            return v

        if not v.strip():
            return None

        if len(v.strip()) < 2:
            raise ValueError("State name must be at least 2 characters long if provided")

        if len(v) > 100:
            raise ValueError("State name cannot exceed 100 characters")

        return v.strip()

    @field_validator('orderId')
    @classmethod
    def validate_order_id(cls, v):
        """Validate order ID (optional)"""
        if not v:
            return v

        if not v.strip():
            return None

        if len(v) > 100:
            raise ValueError("Order ID cannot exceed 100 characters")

        return v.strip()

    @field_validator('agentId')
    @classmethod
    def validate_agent_id(cls, v):
        """Validate agent ID (optional)"""
        if v is not None and v <= 0:
            raise ValueError("Agent ID must be a positive integer")

        return v