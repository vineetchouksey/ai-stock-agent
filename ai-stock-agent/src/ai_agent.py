import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def ai_analysis(symbol, df, fundamentals):
    latest = df.iloc[-1].to_dict()

    prompt = f"""
    Analyze stock {symbol}.

    Technical data:
    {latest}

    Fundamentals:
    {fundamentals}

    Provide:
    - Recommendation (Buy/Sell/Hold)
    - Confidence %
    - Reason
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content