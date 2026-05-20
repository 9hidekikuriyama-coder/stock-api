from fastapi import FastAPI
import yfinance as yf

app = FastAPI()

@app.post("/stocks")
def stocks(payload: dict):
    result = {}

    for code in payload["codes"]:
        ticker = f"{code}.T"

        df = yf.download(
            ticker,
            period="5d",
            progress=False,
            threads=False,
            auto_adjust=False
        ).dropna()

        if len(df) < 2:
            continue

        today = df.iloc[-1]
        prev  = df.iloc[-2]

        result[code] = {
            "today_close":  float(today["Close"].iloc[0]),
            "today_volume": int(today["Volume"].iloc[0]),
            "prev_close":   float(prev["Close"].iloc[0]),
            "prev_volume":  int(prev["Volume"].iloc[0])
        }

    return {"data": result}

"""
既存の main.py に追加するエンドポイント
/stocks_us : 米国株・指数の日次データ取得（バックテスト用）

使い方:
  既存の from fastapi import FastAPI ... の下にこのコードを貼り付ける

取得対象:
  DJUSBK  : Dow Jones U.S. Banks Index
  ^GSPC   : S&P 500
  ^BKX    : KBW Bank Index（DJUSBKのYahoo代替、任意）
"""

@app.post("/stocks_us")
def stocks_us(payload: dict):
    """
    payload例:
      {
        "codes": ["^BKX", "^GSPC"],
        "start": "2000-01-01",   // 省略時は直近5日
        "end":   "2025-05-20"    // 省略時は今日
      }

    レスポンス例（期間指定あり）:
      {
        "data": {
          "^BKX": [
            {"date": "2000-01-03", "close": 123.45},
            ...
          ],
          "^GSPC": [...]
        }
      }

    レスポンス例（期間指定なし → 直近2日分）:
      {
        "data": {
          "^BKX": {"today_close": 123.45, "prev_close": 122.10},
          "^GSPC":  {"today_close": 5123.4, "prev_close": 5100.0}
        }
      }
    """
    import yfinance as yf
    import math

    codes  = payload.get("codes", ["^BKX", "^GSPC"])
    start  = payload.get("start")
    end    = payload.get("end")
    result = {}

    for code in codes:
        try:
            if start and end:
                # ── 期間指定：バックテスト用一括取得 ──
                df = yf.download(
                    code,
                    start=start,
                    end=end,
                    progress=False,
                    threads=False,
                    auto_adjust=False
                ).dropna()

                if df.empty:
                    result[code] = {"error": "no data"}
                    continue

                # MultiIndex対応（yfinance 0.2系）
                if hasattr(df.columns, "levels"):
                    close_col = ("Close", code)
                    closes = df[close_col] if close_col in df.columns else df["Close"].iloc[:, 0]
                else:
                    closes = df["Close"]

                records = []
                for dt, val in closes.items():
                    if not math.isnan(float(val)):
                        records.append({
                            "date":  dt.strftime("%Y-%m-%d"),
                            "close": round(float(val), 4)
                        })
                result[code] = records

            else:
                # ── 期間指定なし：直近2日分（モニタリング用） ──
                df = yf.download(
                    code,
                    period="5d",
                    progress=False,
                    threads=False,
                    auto_adjust=False
                ).dropna()

                if len(df) < 2:
                    result[code] = {"error": "not enough data"}
                    continue

                today = df.iloc[-1]
                prev  = df.iloc[-2]

                def get_val(row, col):
                    v = row[col]
                    if hasattr(v, "iloc"):
                        v = v.iloc[0]
                    return round(float(v), 4)

                result[code] = {
                    "today_close": get_val(today, "Close"),
                    "prev_close":  get_val(prev,  "Close"),
                }

        except Exception as e:
            result[code] = {"error": str(e)}

    return {"data": result}
