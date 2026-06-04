import re
import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

_PAN_RE = re.compile(r"\D+")


def _detect_brand(pan: str) -> str:
    if not pan:
        return "UNKNOWN"
    if pan.startswith("4"):
        return "VISA"
    first2 = int(pan[:2]) if pan[:2].isdigit() else 0
    if 51 <= first2 <= 55:
        return "MASTERCARD"
    first4 = int(pan[:4]) if pan[:4].isdigit() else 0
    if 2221 <= first4 <= 2720:
        return "MASTERCARD"
    if pan.startswith(("34", "37")):
        return "AMEX"
    if pan.startswith(("36", "38")):
        return "DINERS"
    if pan.startswith("62"):
        return "UNIONPAY"
    return "UNKNOWN"


class CardCreateRequest(BaseModel):
    """Тело привязки карты. CVV и полный номер используются ТОЛЬКО учебно."""

    number: str = Field(..., description="Номер карты, можно с пробелами/дефисами")
    exp_month: int = Field(..., ge=1, le=12)
    exp_year: int = Field(..., ge=2024, le=2099)
    cvv: str = Field(..., min_length=3, max_length=4)
    holder_name: str = Field(..., min_length=2, max_length=120)
    is_default: bool = False

    model_config = ConfigDict(extra="forbid")

    @field_validator("number")
    @classmethod
    def _normalize_number(cls, v: str) -> str:
        """Только цифры, без Luhn: учебные/тестовые номера допускаются."""
        digits = _PAN_RE.sub("", v or "")
        if not digits:
            raise ValueError("Card number is empty")
        if not digits.isdigit():
            raise ValueError("Card number must contain digits only (after removing spaces/dashes)")
        if len(digits) > 19:
            raise ValueError("Card number: at most 19 digits")
        return digits

    @field_validator("cvv")
    @classmethod
    def _cvv_digits(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("CVV must be digits only")
        return v

    @field_validator("holder_name")
    @classmethod
    def _name_format(cls, v: str) -> str:
        cleaned = " ".join(v.split())
        return cleaned.upper()

    @model_validator(mode="after")
    def _not_expired(self) -> "CardCreateRequest":
        today = date.today()
        if (self.exp_year, self.exp_month) < (today.year, today.month):
            raise ValueError("Card is expired")
        return self


class CardResponse(BaseModel):
    """Карта в безопасном виде (для UI)."""

    id: uuid.UUID
    brand: str
    last4: str
    exp_month: int
    exp_year: int
    holder_name: str
    is_default: bool

    @property
    def masked_number(self) -> str:
        return f"•••• •••• •••• {self.last4}"

    model_config = ConfigDict(from_attributes=True)


class CardSetDefaultRequest(BaseModel):
    is_default: bool = True
    model_config = ConfigDict(extra="forbid")


def detect_brand(pan: str) -> str:
    return _detect_brand(pan)
