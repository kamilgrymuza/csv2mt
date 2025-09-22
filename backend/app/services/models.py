from typing import List, Optional
from datetime import date
from decimal import Decimal
from pydantic import BaseModel


class BankTransaction(BaseModel):
    registered_date: date
    initiated_date: date
    title: str
    other_party_info: Optional[str] = None
    other_party_account: Optional[str] = None
    amount: Decimal
    resulting_balance: Decimal
    entry_number: int


class BankStatementHeader(BaseModel):
    generation_date: date
    start_date: date
    end_date: date
    account_holder: str
    account_number: str
    currency: str
    initial_balance: Decimal
    end_balance: Decimal
    number_of_entries: int


class BankStatement(BaseModel):
    header: BankStatementHeader
    transactions: List[BankTransaction]