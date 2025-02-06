import pandas as pd
from typing import List
from ..models.finance_models import Transaction


def parse_csv_file(file_path: str) -> List[Transaction]:
    df = pd.read_csv(file_path)
    transactions = []
    for _, row in df.iterrows():
        transaction = Transaction(
            description=row["description"],
            amount=row["amount"],
            date=(row["date"]) 
        )
        transactions.append(transaction)
    return transactions