from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel

T = TypeVar("T")

class StandardResponse(BaseModel, Generic[T]):
    """
    Standard API response format.
    """
    success: bool
    data: Optional[T] = None
    error: Optional[Any] = None
    message: Optional[str] = None
