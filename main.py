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
