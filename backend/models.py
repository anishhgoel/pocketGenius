from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class Transaction(BaseModel):
    description: str
    amount: float
    date: datetime
    category: Optional[str] = None

class AnalysisResult(BaseModel):
    category: str
    budget_recommendation: str
    savings_potential: str

class PortfolioItem(BaseModel):
    symbol: str
    quantity: float
    purchase_price: float

class Portfolio(BaseModel):
    items: List[PortfolioItem]