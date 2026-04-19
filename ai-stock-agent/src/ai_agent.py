import json
import os
from textwrap import dedent

import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

TEXT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
WEB_MODEL = os.getenv("OPENAI_WEB_MODEL", "gpt-4.1-mini")
SEARCH_CONTEXT_SIZE = os.getenv("AI_SEARCH_CONTEXT_SIZE", "high")
EXTRA_INSTRUCTIONS = os.getenv("AI_ANALYST_EXTRA_INSTRUCTIONS", "").strip()
TEXT_VERBOSITY = os.getenv("AI_TEXT_VERBOSITY", "").strip()
AI_RESPONSE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "symbol": {
            "type": "string",
            "description": "The stock symbol being analyzed."
        },
        "sentiment": {
            "type": "string",
            "description": "Overall stock view such as Bullish, Neutral, Bearish, Mixed, Skipped, or Error."
        },
        "confidence": {
            "type": "string",
            "description": "Confidence as a percentage string such as 78%."
        },
        "catalysts": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Top positive or directional catalysts, ordered by near-term importance."
        },
        "risks": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Top downside risks, headwinds, or missing validations."
        },
        "summary": {
            "type": "string",
            "description": "A concise analyst summary that combines technicals, fundamentals, and catalysts."
        },
        "detailed_markdown": {
            "type": "string",
            "description": "A detailed markdown report with verdict, technicals, fundamentals, catalysts, risks, monitor items, and source notes."
        },
    },
    "required": ["symbol", "sentiment", "confidence", "catalysts", "risks", "summary", "detailed_markdown"],
}


def _env_flag(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default

    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _get_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    return OpenAI(api_key=api_key)


def _normalize_value(value):
    if isinstance(value, dict):
        normalized = {
            key: _normalize_value(item)
            for key, item in value.items()
        }
        return {key: item for key, item in normalized.items() if item is not None}

    if isinstance(value, (list, tuple)):
        normalized = [_normalize_value(item) for item in value]
        return [item for item in normalized if item is not None]

    if hasattr(value, "item"):
        try:
            value = value.item()
        except Exception:
            pass

    try:
        if pd.isna(value):
            return None
    except Exception:
        pass

    if isinstance(value, float):
        return round(value, 4)

    return value


def _pct_change(current, base):
    if current in (None, 0) or base in (None, 0):
        return None

    return round(((current - base) / base) * 100, 2)


def _build_technical_summary(df):
    latest = df.iloc[-1]

    latest_close = _normalize_value(latest.get("Close"))
    latest_volume = _normalize_value(latest.get("Volume"))

    close_20 = _normalize_value(df["Close"].iloc[-21]) if len(df) > 20 else None
    close_60 = _normalize_value(df["Close"].iloc[-61]) if len(df) > 60 else None

    avg_volume_20 = _normalize_value(df["Volume"].rolling(20).mean().iloc[-1]) if len(df) >= 20 else None
    high_52 = _normalize_value(df["High"].rolling(min(len(df), 252)).max().iloc[-1]) if len(df) else None
    recent_high_20 = _normalize_value(df["High"].iloc[-20:].max()) if len(df) >= 20 else None

    ema_50 = _normalize_value(latest.get("ema_50"))
    ema_200 = _normalize_value(latest.get("ema_200"))
    macd = _normalize_value(latest.get("macd"))
    macd_signal = _normalize_value(latest.get("macd_signal"))

    summary = {
        "close": latest_close,
        "1m_return_pct": _pct_change(latest_close, close_20),
        "3m_return_pct": _pct_change(latest_close, close_60),
        "pct_below_52w_high": round(((high_52 - latest_close) / high_52) * 100, 2)
        if high_52 not in (None, 0) and latest_close is not None
        else None,
        "pct_vs_recent_20d_high": _pct_change(latest_close, recent_high_20),
        "latest_volume": latest_volume,
        "avg_volume_20": avg_volume_20,
        "volume_vs_20d_avg": round(latest_volume / avg_volume_20, 2)
        if latest_volume not in (None, 0) and avg_volume_20 not in (None, 0)
        else None,
        "rsi": _normalize_value(latest.get("rsi")),
        "macd": macd,
        "macd_signal": macd_signal,
        "macd_trend": "bullish"
        if macd is not None and macd_signal is not None and macd > macd_signal
        else "bearish"
        if macd is not None and macd_signal is not None
        else None,
        "ema_50": ema_50,
        "ema_200": ema_200,
        "price_vs_ema_50_pct": _pct_change(latest_close, ema_50),
        "price_vs_ema_200_pct": _pct_change(latest_close, ema_200),
        "above_ema_50": bool(latest_close > ema_50) if latest_close is not None and ema_50 is not None else None,
        "above_ema_200": bool(latest_close > ema_200) if latest_close is not None and ema_200 is not None else None,
    }

    return _normalize_value(summary)


def _build_source_guidance():
    return [
        "Annual report and latest quarterly results",
        "Investor presentations and investor day decks",
        "Conference call commentary and management guidance",
        "Credit rating actions and outlook revisions",
        "Exchange filings, board updates, and corporate announcements",
        "Research reports and channel checks, only as secondary support",
        "Credible business news and promoter or management interviews",
    ]


def _build_catalyst_checklist():
    return [
        "Big order win, customer addition, tender win, or project commissioning",
        "Government policy change such as GST, tariff, subsidy, anti-dumping, or PLI",
        "RBI rate policy, liquidity changes, funding-cost impact, or credit cycle effect",
        "Industry tailwinds or headwinds such as demand, pricing, commodity, or currency",
        "Capex, capacity expansion, ramp-up timeline, and utilization inflection",
        "Debt reduction, refinancing, leverage improvement, or balance-sheet repair",
        "Merger, demerger, acquisition, divestment, or restructuring",
        "Insider trading, promoter buying or selling, pledge movement, or governance signal",
        "Credit-rating upgrade, downgrade, or outlook change",
        "Quarterly earnings surprise, margin trend, or guidance change",
    ]


def _build_system_instructions():
    instructions = dedent(
        """
        You are an Indian equities research analyst focused on swing trades and
        catalyst-driven short-term opportunities.

        Your job is to combine:
        - technical setup
        - fundamental quality
        - external catalyst research when web search is available

        Weighting rules:
        - Give extra weight to catalysts that can affect the stock in the next 30 to 90 days.
        - Prefer confirmed and recent information over old narratives.
        - Prefer primary sources over secondary commentary.
        - Distinguish facts, management guidance, sell-side opinion, and rumor.
        - Treat bearish catalysts with the same seriousness as bullish ones.
        - If evidence is weak or stale, say so clearly.

        If web search is available, prioritize sources in this order:
        1. exchange filings and company disclosures
        2. quarterly results, annual reports, presentations, and conference calls
        3. credit-rating reports
        4. credible business media
        5. research reports and interviews as supporting evidence

        The final answer must follow the configured JSON schema exactly.
        Do not return markdown, prose outside JSON, or code fences.
        Put the human-readable full report inside the `detailed_markdown` field.
        """
    ).strip()

    if EXTRA_INSTRUCTIONS:
        instructions = f"{instructions}\n\nAdditional user instructions:\n{EXTRA_INSTRUCTIONS}"

    return instructions


def _build_user_prompt(symbol, technical_summary, fundamentals, scanner_context, enable_web_research):
    source_guidance = "\n".join(f"- {item}" for item in _build_source_guidance())
    catalyst_guidance = "\n".join(f"- {item}" for item in _build_catalyst_checklist())

    research_mode = "ENABLED" if enable_web_research else "DISABLED"
    scanner_summary = scanner_context or {"note": "Scanner context not supplied"}

    return dedent(
        f"""
        Analyze the Indian stock `{symbol}`.

        External research mode: {research_mode}

        Technical summary:
        {json.dumps(_normalize_value(technical_summary), indent=2)}

        Fundamental summary:
        {json.dumps(_normalize_value(fundamentals), indent=2)}

        Scanner and trigger context:
        {json.dumps(_normalize_value(scanner_summary), indent=2)}

        When research mode is enabled, actively look for the latest relevant information from:
        {source_guidance}

        Specifically check for these short-term catalysts and headwinds:
        {catalyst_guidance}

        Analysis guidance:
        - Give more weight to confirmed, dated, near-term triggers than generic long-term stories.
        - Mention whether catalysts are already visible in price or still underappreciated.
        - Call out if recent price action does not support the narrative.
        - If research mode is disabled, state that external catalyst validation was not performed.
        - Mention dates whenever you reference results, presentations, rating actions, or news.
        - Use sentiment values like Bullish, Neutral, Bearish, or Mixed.
        - Keep catalysts and risks brief and decision-oriented.
        - Confidence should be a string like 72%.
        - `detailed_markdown` must use markdown sections in this order:
          `# {symbol}`, `## Verdict`, `## Technical View`, `## Fundamental View`,
          `## Catalyst Review`, `## Risk Review`, `## Monitor Next`, `## Source Notes`.
        """
    ).strip()


def _build_response_request(model, instructions, prompt, enable_web_research):
    request = {
        "model": model,
        "instructions": instructions,
        "input": prompt,
        "max_output_tokens": 1400,
        "text": {
            "format": {
                "type": "json_schema",
                "name": "stock_ai_analysis",
                "description": "Structured AI stock analysis payload.",
                "schema": AI_RESPONSE_SCHEMA,
                "strict": True,
            }
        },
    }

    if TEXT_VERBOSITY:
        request["text"]["verbosity"] = TEXT_VERBOSITY

    if enable_web_research:
        request["tools"] = [
            {
                "type": "web_search",
                "search_context_size": SEARCH_CONTEXT_SIZE,
                "user_location": {
                    "type": "approximate",
                    "country": "IN",
                    "timezone": "Asia/Kolkata",
                },
            }
        ]
        request["tool_choice"] = "auto"
        request["include"] = ["web_search_call.action.sources"]

    return request


def _sanitize_string(value, default):
    if value is None:
        return default

    value = str(value).strip()
    return value or default


def _sanitize_string_list(value):
    if not isinstance(value, list):
        return []

    cleaned = []
    for item in value:
        if item is None:
            continue

        item = str(item).strip()
        if item:
            cleaned.append(item)

    return cleaned[:5]


def _build_default_markdown(payload):
    symbol = payload["symbol"]
    catalysts = payload["catalysts"] or ["No major catalyst identified."]
    risks = payload["risks"] or ["No major risk identified."]

    catalyst_lines = "\n".join(f"- {item}" for item in catalysts)
    risk_lines = "\n".join(f"- {item}" for item in risks)

    return dedent(
        f"""
        # {symbol}

        ## Verdict
        - Sentiment: {payload["sentiment"]}
        - Confidence: {payload["confidence"]}

        ## Technical View
        - Refer to the technical summary and price structure used for this run.

        ## Fundamental View
        - Refer to the fundamental summary used for this run.

        ## Catalyst Review
        {catalyst_lines}

        ## Risk Review
        {risk_lines}

        ## Monitor Next
        - Track price confirmation, fresh disclosures, and any new catalyst validation.

        ## Source Notes
        - {payload["summary"]}
        """
    ).strip()


def _normalize_ai_payload(payload, symbol, extra_summary_note=None):
    if not isinstance(payload, dict):
        payload = {}

    summary = _sanitize_string(payload.get("summary"), "No AI summary generated.")
    if extra_summary_note:
        summary = f"{summary} {extra_summary_note}".strip()

    normalized = {
        "symbol": _sanitize_string(payload.get("symbol"), symbol),
        "sentiment": _sanitize_string(payload.get("sentiment"), "Neutral"),
        "confidence": _sanitize_string(payload.get("confidence"), "0%"),
        "catalysts": _sanitize_string_list(payload.get("catalysts")),
        "risks": _sanitize_string_list(payload.get("risks")),
        "summary": summary,
        "detailed_markdown": _sanitize_string(payload.get("detailed_markdown"), ""),
    }

    if not normalized["detailed_markdown"]:
        normalized["detailed_markdown"] = _build_default_markdown(normalized)

    return normalized


def _format_ai_result(payload, symbol, extra_summary_note=None):
    normalized = _normalize_ai_payload(payload, symbol, extra_summary_note=extra_summary_note)
    return {
        "payload": normalized,
        "json": json.dumps(normalized, ensure_ascii=False),
        "markdown": normalized["detailed_markdown"],
    }


def build_ai_status_output(symbol, sentiment, confidence, catalysts, risks, summary):
    return _format_ai_result(
        {
            "symbol": symbol,
            "sentiment": sentiment,
            "confidence": confidence,
            "catalysts": catalysts,
            "risks": risks,
            "summary": summary,
        },
        symbol=symbol,
    )


def ai_analysis(symbol, df, fundamentals, scanner_context=None, enable_web_research=None):
    if enable_web_research is None:
        enable_web_research = _env_flag("AI_ENABLE_WEB_RESEARCH", False)

    technical_summary = _build_technical_summary(df)
    instructions = _build_system_instructions()
    prompt = _build_user_prompt(
        symbol=symbol,
        technical_summary=technical_summary,
        fundamentals=fundamentals,
        scanner_context=scanner_context,
        enable_web_research=enable_web_research,
    )

    client = _get_client()
    model = WEB_MODEL if enable_web_research else TEXT_MODEL

    try:
        response = client.responses.create(
            **_build_response_request(
                model=model,
                instructions=instructions,
                prompt=prompt,
                enable_web_research=enable_web_research,
            )
        )
        return _format_ai_result(json.loads(response.output_text), symbol=symbol)
    except Exception as research_error:
        if not enable_web_research:
            raise

        fallback_prompt = (
            f"{prompt}\n\n"
            "Research fallback note:\n"
            f"External web research was requested but unavailable because of: {research_error}\n"
            "Complete the analysis using only the supplied technical and fundamental data, "
            "and explicitly mention that external validation is missing."
        )

        fallback_response = client.responses.create(
            **_build_response_request(
                model=TEXT_MODEL,
                instructions=instructions,
                prompt=fallback_prompt,
                enable_web_research=False,
            )
        )

        return _format_ai_result(
            json.loads(fallback_response.output_text),
            symbol=symbol,
            extra_summary_note=(
                "External web research was unavailable in this run, so the result uses only "
                "the supplied technical and fundamental data."
            ),
        )
