from pydantic import BaseModel
from enum import Enum as PyEnum

class VendorScale(PyEnum):
    Retail = "Retail"
    Wholesale = "Wholesale"
