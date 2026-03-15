from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class SalesRecord(BaseModel):
    order_id: int
    customer_id: str
    product_name: str
    quantity: int
    unit_price: Decimal
    order_date: date


class CustomerRecord(BaseModel):
    customer_id: str
    name: str
    email: str
    country: str
    joined_date: date


class SalesReport(BaseModel):
    customer_id: str
    customer_name: str
    month: str
    total_revenue: Decimal
