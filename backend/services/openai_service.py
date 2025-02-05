import os
import openai

from ..models import Transaction 

openai.api_key = os.getenv(OPENAI_API_KEY)

async def analyze_transaction(transaction: Transaction) -> dict:
    prompt = f"""
    You are a financial expert AI. 
    Categorize the following transaction, suggest a budget recommendation, 
    and savings potential if any.

    Transaction Description: {transaction.description}
    Amount: ${transaction.amount}
    Date: {transaction.date}

    Format your response as:
    - category: ...
    - budget_recommendation: ...
    - savings_potential: ...
    """
    response = await openai.ChatCompletion.acreate(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    message = response.choices[0].message.content

    # parsing the response structure into a dict

    lines = message.split('\n')
    parsed_response = {}
    for line in lines:
        if "category:" in line.lower():
            parsed_response["category"] = line.split(':', 1)[1].strip()
        elif "budget_recommendation:" in line.lower():
            parsed_response["budget_recommendation"] = line.split(':', 1)[1].strip()
        elif "savings_potential:" in line.lower():
            parsed_response["savings_potential"] = line.split(':', 1)[1].strip()

    return parsed_response