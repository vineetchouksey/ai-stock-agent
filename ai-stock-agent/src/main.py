import pandas as pd
import argparse

# Local imports
from fetcher import fetch_stock_data, fetch_nifty_data
from indicators import apply_indicators
from fundamentals import fetch_fundamentals
from scanner import analyze_stock, scanner_signal
from relative_strength import calculate_rs
from ranker import rank_stocks
from utils import load_symbols
from ai_agent import ai_analysis


def run(source, mode):
    print("🚀 Starting AI Stock Scanner...\n")
    print(f"📥 Source: {source.upper()} | ⚙️ Mode: {mode.upper()}\n")

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
                    ai_result = ai_analysis(symbol, df, fundamentals)
                except Exception as ai_err:
                    ai_result = f"AI Error: {ai_err}"

                results.append({
                    "symbol": symbol,
                    "mode": "AI_ONLY",
                    "ai_analysis": ai_result
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

                # --- Optional AI (only for strong signals) ---
                ai_result = "Skipped"
                if scanner_result in ["🚀 ELITE BUY", "⚡ STRONG BREAKOUT"]:
                    try:
                        ai_result = ai_analysis(symbol, df, fundamentals)
                    except Exception as ai_err:
                        ai_result = f"AI Error: {ai_err}"

                results.append({
                    "symbol": symbol,
                    "mode": "SCANNER",
                    "scanner_signal": scanner_result,
                    "rs_trend": rs["rs_trend"],
                    "rs_value": rs["rs_value"],
                    "near_52w_high": flags["near_52w_high"],
                    "dry_volume": flags["dry_volume"],
                    "volume_spike": flags["volume_spike"],
                    "breakout": flags["breakout"],
                    "ai_analysis": ai_result
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

        # Save full ranked list
        ranked_df.to_csv("../data/output.csv", index=False)

        # Save Top 10
        top_df = ranked_df.head(10)
        top_df.to_csv("../data/top_stocks.csv", index=False)

        print("\n🏆 Top Stocks:")
        print(top_df[["symbol", "scanner_signal", "score"]])

    else:
        # AI-only mode output
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

    args = parser.parse_args()

    run(args.source, args.mode)