import pandas as pd
import argparse
import json

# Local imports
from fetcher import fetch_stock_data, fetch_nifty_data
from indicators import apply_indicators
from fundamentals import fetch_fundamentals
from scanner import analyze_stock, scanner_signal
from relative_strength import calculate_rs
from ranker import rank_stocks
from utils import load_symbols
from ai_agent import ai_analysis, build_ai_status_output


def backtest_breakout(df):
    trades = []

    for i in range(50, len(df) - 5):
        try:
            recent_high = df['High'].iloc[i-20:i].max()
            close = df['Close'].iloc[i]
            volume = df['Volume'].iloc[i]

            avg_vol = df['Volume'].iloc[i-20:i].mean()

            # breakout condition
            if close > recent_high and volume > 1.5 * avg_vol:
                entry_price = close
                exit_price = df['Close'].iloc[i+5]

                ret = (exit_price - entry_price) / entry_price

                trades.append(ret)
        except:
            continue

    if not trades:
        return {
            "trades": 0,
            "win_rate": 0,
            "avg_return": 0
        }

    wins = [t for t in trades if t > 0]

    return {
        "trades": len(trades),
        "win_rate": round(len(wins) / len(trades) * 100, 2),
        "avg_return": round(sum(trades) / len(trades) * 100, 2)
    }


def save_ai_json_results(df):
    if "ai_analysis_json" not in df.columns or df.empty:
        return

    json_rows = []
    for value in df["ai_analysis_json"].dropna():
        try:
            json_rows.append(json.loads(value))
        except Exception:
            continue

    with open("../data/result.json", "w", encoding="utf-8") as file:
        json.dump(json_rows, file, ensure_ascii=False, indent=2)


def run(source, mode, ai_research=False):
    print("🚀 Starting AI Stock Scanner...\n")
    print(
        f"📥 Source: {source.upper()} | ⚙️ Mode: {mode.upper()} | "
        f"🌐 AI Research: {'ON' if ai_research else 'OFF'}\n"
    )

    # --- Load symbols ---
    symbols = load_symbols(source)

    # --- Fetch NIFTY only if needed ---
    nifty_df = None
    if mode == "scanner":
        print("📊 Fetching NIFTY data...")
        nifty_df = fetch_nifty_data()

    results = []

    for symbol in symbols:
        print(f"\n🔍 Processing {symbol}...")

        try:
            # --- Fetch Data ---
            df = fetch_stock_data(symbol)

            # --- Apply Indicators ---
            df = apply_indicators(df)

            # --- Fundamentals ---
            fundamentals = fetch_fundamentals(symbol)

            # =========================================================
            # 🤖 MODE 1: AI ONLY (Bypass Scanner + Ranker)
            # =========================================================
            if mode == "ai":
                try:
                    ai_result = ai_analysis(
                        symbol,
                        df,
                        fundamentals,
                        enable_web_research=ai_research
                    )
                except Exception as ai_err:
                    ai_result = build_ai_status_output(
                        symbol=symbol,
                        sentiment="Error",
                        confidence="0%",
                        catalysts=[],
                        risks=[str(ai_err)],
                        summary="AI analysis failed for this symbol."
                    )

                results.append({
                    "symbol": symbol,
                    "mode": "AI_ONLY",
                    "ai_analysis": ai_result["markdown"],
                    "ai_analysis_json": ai_result["json"]
                })

            # =========================================================
            # 📊 MODE 2: SCANNER (Default)
            # =========================================================
            else:
                # --- Scanner Flags ---
                flags = analyze_stock(df)

                # --- Relative Strength ---
                rs = calculate_rs(df, nifty_df)

                # --- Final Signal ---
                scanner_result = scanner_signal(flags, rs)

                # --- Breakout Confirmation (Trigger Layer) ---
                breakout_trigger = False
                breakout_reason = ""

                try:
                    recent_high = df['High'].iloc[-21:-1].max()
                    latest_close = df['Close'].iloc[-1]

                    avg_volume_20 = df['Volume'].rolling(20).mean().iloc[-1]
                    latest_volume = df['Volume'].iloc[-1]

                    if latest_close > recent_high and latest_volume > 1.5 * avg_volume_20:
                        breakout_trigger = True
                        breakout_reason = "Price breakout with volume"
                except Exception as be:
                    breakout_reason = f"Breakout calc error: {be}"

                if breakout_trigger:
                    print(f"🚨 BREAKOUT ALERT: {symbol} -> {breakout_reason}")

                # --- Backtest Metrics ---
                backtest_stats = backtest_breakout(df)

                # --- Optional AI (only for strong signals) ---
                ai_result = build_ai_status_output(
                    symbol=symbol,
                    sentiment="Skipped",
                    confidence="0%",
                    catalysts=[],
                    risks=["AI analysis only runs for PRE-BREAKOUT scanner signals."],
                    summary="AI analysis was skipped because this stock did not meet the AI trigger."
                )
                if scanner_result == "🎯 PRE-BREAKOUT":
                    try:
                        ai_result = ai_analysis(
                            symbol,
                            df,
                            fundamentals,
                            scanner_context={
                                "scanner_signal": scanner_result,
                                "rs_trend": rs["rs_trend"],
                                "rs_value": rs["rs_value"],
                                "near_52w_high": flags["near_52w_high"],
                                "dry_volume": flags["dry_volume"],
                                "tight_consolidation": flags["tight_consolidation"],
                                "near_resistance": flags["near_resistance"],
                                "breakout_trigger": breakout_trigger,
                                "breakout_reason": breakout_reason,
                                "backtest": backtest_stats,
                            },
                            enable_web_research=ai_research
                        )
                    except Exception as ai_err:
                        ai_result = build_ai_status_output(
                            symbol=symbol,
                            sentiment="Error",
                            confidence="0%",
                            catalysts=[],
                            risks=[str(ai_err)],
                            summary="AI analysis failed for this symbol."
                        )

                results.append({
                    "symbol": symbol,
                    "mode": "SCANNER",
                    "scanner_signal": scanner_result,
                    "rs_trend": rs["rs_trend"],
                    "rs_value": rs["rs_value"],
                    "near_52w_high": flags["near_52w_high"],
                    "dry_volume": flags["dry_volume"],
                    "tight_consolidation": flags["tight_consolidation"],
                    "near_resistance": flags["near_resistance"],
                    "structure_score": sum([
                    flags["near_52w_high"],
                    flags["tight_consolidation"],
                    flags["near_resistance"],
                    flags["dry_volume"]
                    ]),
                    "breakout_trigger": breakout_trigger,
                    "breakout_reason": breakout_reason,
                    "bt_trades": backtest_stats["trades"],
                    "bt_win_rate": backtest_stats["win_rate"],
                    "bt_avg_return": backtest_stats["avg_return"],
                    "ai_analysis": ai_result["markdown"],
                    "ai_analysis_json": ai_result["json"]
                })

        except Exception as e:
            print(f"❌ Error processing {symbol}: {e}")

    # --- Convert to DataFrame ---
    output_df = pd.DataFrame(results)

    # =========================================================
    # 📊 Ranking only in SCANNER mode
    # =========================================================
    if mode == "scanner" and not output_df.empty:
        ranked_df = rank_stocks(output_df)
        save_ai_json_results(ranked_df)

        # Save full ranked list
        ranked_df.to_csv("../data/output.csv", index=False)

        # Save Top 10
        top_df = ranked_df.head(10)
        top_df.to_csv("../data/top_stocks.csv", index=False)

        print("\n🏆 Top Stocks:")
        print(top_df[["symbol", "scanner_signal", "score"]])

    else:
        # AI-only mode output
        save_ai_json_results(output_df)
        output_df.to_csv("../data/output.csv", index=False)

    print("\n✅ Analysis complete!")
    print("📁 Check: data/output.csv")


# =========================================================
# 🚀 Entry Point
# =========================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Stock Scanner")

    parser.add_argument(
        "--source",
        type=str,
        default="txt",
        choices=["txt", "csv"],
        help="Input source: txt or csv"
    )

    parser.add_argument(
        "--mode",
        type=str,
        default="scanner",
        choices=["scanner", "ai"],
        help="Execution mode: scanner or ai"
    )

    parser.add_argument(
        "--ai-research",
        action="store_true",
        help="Allow the AI agent to use web search for results, news, ratings, and catalyst research"
    )

    args = parser.parse_args()

    run(args.source, args.mode, args.ai_research)
