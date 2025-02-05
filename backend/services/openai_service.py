import os
import logging
import openai
from typing import Dict
from ..models.finance_models import Transaction

logger = logging.getLogger(__name__)


openai.api_key = os.getenv(OPENAI_API_KEY)

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
        response = await openai.ChatCompletion.acreate(
            model="gpt-4",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        content = response.choices[0].message.content

        # attempt to parse JSON from the content
        # For production, i think parsing should have more robust approach
        import json
        parsed = {}
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            # fallback if not a valid JSON
            logger.warning("OpenAI response not in valid JSON. Returning fallback.")
            parsed = {
                "category": "Uncategorized",
                "budget_recommendation": "No recommendation",
                "savings_potential": "None"
            }

        # ensuring that the keys exist
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