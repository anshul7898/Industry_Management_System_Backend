from pydantic import BaseModel, Field, field_validator
from typing import Optional


class Agent(BaseModel):
    agentId: int
    aadhar_Details: Optional[str] = None
    address: Optional[str] = None
    mobile: Optional[str] = None
    name: Optional[str] = None


class AgentLightweight(BaseModel):
    agentId: int
    name: Optional[str] = None


class CreateAgent(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Agent name")
    mobile: str = Field(..., description="10-digit mobile number")
    aadhar_Details: str = Field(..., description="12-digit Aadhar number")
    address: str = Field(..., min_length=1, max_length=500, description="Agent address")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate name: not empty, no leading/trailing spaces"""
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")

        if len(v.strip()) < 2:
            raise ValueError("Name must be at least 2 characters long")

        if len(v) > 255:
            raise ValueError("Name cannot exceed 255 characters")

        # Check if name contains only letters and spaces
        if not all(c.isalpha() or c.isspace() for c in v):
            raise ValueError("Name can only contain letters and spaces")

        return v.strip()

    @field_validator('mobile')
    @classmethod
    def validate_mobile(cls, v):
        """Validate mobile: must be exactly 10 digits"""
        if not v:
            raise ValueError("Mobile number is required")

        # Remove any spaces or hyphens
        cleaned = ''.join(c for c in v if c.isdigit())

        if len(cleaned) != 10:
            raise ValueError("Mobile number must be exactly 10 digits")

        if not cleaned.isdigit():
            raise ValueError("Mobile number must contain only digits")

        return cleaned

    @field_validator('aadhar_Details')
    @classmethod
    def validate_aadhar(cls, v):
        """Validate Aadhar: must be exactly 12 digits"""
        if not v:
            raise ValueError("Aadhar number is required")

        # Remove any spaces or hyphens
        cleaned = ''.join(c for c in v if c.isdigit())

        if len(cleaned) != 12:
            raise ValueError("Aadhar number must be exactly 12 digits")

        if not cleaned.isdigit():
            raise ValueError("Aadhar number must contain only digits")

        return cleaned

    @field_validator('address')
    @classmethod
    def validate_address(cls, v):
        """Validate address: not empty, reasonable length"""
        if not v or not v.strip():
            raise ValueError("Address cannot be empty")

        if len(v.strip()) < 5:
            raise ValueError("Address must be at least 5 characters long")

        if len(v) > 500:
            raise ValueError("Address cannot exceed 500 characters")

        return v.strip()


class UpdateAgent(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Agent name")
    mobile: str = Field(..., description="10-digit mobile number")
    aadhar_Details: str = Field(..., description="12-digit Aadhar number")
    address: str = Field(..., min_length=1, max_length=500, description="Agent address")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate name: not empty, no leading/trailing spaces"""
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")

        if len(v.strip()) < 2:
            raise ValueError("Name must be at least 2 characters long")

        if len(v) > 255:
            raise ValueError("Name cannot exceed 255 characters")

        if not all(c.isalpha() or c.isspace() for c in v):
            raise ValueError("Name can only contain letters and spaces")

        return v.strip()

    @field_validator('mobile')
    @classmethod
    def validate_mobile(cls, v):
        """Validate mobile: must be exactly 10 digits"""
        if not v:
            raise ValueError("Mobile number is required")

        cleaned = ''.join(c for c in v if c.isdigit())

        if len(cleaned) != 10:
            raise ValueError("Mobile number must be exactly 10 digits")

        if not cleaned.isdigit():
            raise ValueError("Mobile number must contain only digits")

        return cleaned

    @field_validator('aadhar_Details')
    @classmethod
    def validate_aadhar(cls, v):
        """Validate Aadhar: must be exactly 12 digits"""
        if not v:
            raise ValueError("Aadhar number is required")

        cleaned = ''.join(c for c in v if c.isdigit())

        if len(cleaned) != 12:
            raise ValueError("Aadhar number must be exactly 12 digits")

        if not cleaned.isdigit():
            raise ValueError("Aadhar number must contain only digits")

        return cleaned

    @field_validator('address')
    @classmethod
    def validate_address(cls, v):
        """Validate address: not empty, reasonable length"""
        if not v or not v.strip():
            raise ValueError("Address cannot be empty")

        if len(v.strip()) < 5:
            raise ValueError("Address must be at least 5 characters long")

        if len(v) > 500:
            raise ValueError("Address cannot exceed 500 characters")

        return v.strip()