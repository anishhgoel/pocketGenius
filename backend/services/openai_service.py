import os
import logging
import json
from typing import Dict
from openai import AsyncOpenAI  # Changed to AsyncOpenAI
from ..models.finance_models import Transaction
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # Using AsyncOpenAI client

async def analyze_transaction(transaction: Transaction) -> Dict[str, str]:
    """
    Analyzes a transaction with GPT to determine category, budget recommendation,
    and savings potential. Returns a dictionary with those fields.
    """
    prompt = f"""
    You are a financial expert AI. Categorize the following transaction, suggest a budget recommendation,
    and indicate any savings potential. The output format should be JSON with keys:
    "category", "budget_recommendation", and "savings_potential".

    Transaction:
      Description: {transaction.description}
      Amount: {transaction.amount}
      Date: {transaction.date}
    """
    try:
        response = await client.chat.completions.create(  # This will now work with await
            model="gpt-4",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        content = response.choices[0].message.content

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            logger.warning("OpenAI response not in valid JSON. Returning fallback.")
            parsed = {
                "category": "Uncategorized",
                "budget_recommendation": "No recommendation",
                "savings_potential": "None"
            }

        return {
            "category": parsed.get("category", "Uncategorized"),
            "budget_recommendation": parsed.get("budget_recommendation", "No recommendation"),
            "savings_potential": parsed.get("savings_potential", "None")
        }
    except Exception as e:
        logger.exception(f"Error calling OpenAI API: {e}")
        return {
            "category": "Uncategorized",
            "budget_recommendation": "No recommendation",
            "savings_potential": "None"
        }