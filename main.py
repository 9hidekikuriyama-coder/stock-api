from fastapi import FastAPI
import yfinance as yf
import pandas as pd

app = FastAPI()

@app.post("/stocks")
def stocks(payload: dict):
    codes = payload["codes"]
    result = {}

    for code in codes:
        ticker = f"{code}.T"
        df = yf.download(ticker, period="5d", progress=False)
        df = df.dropna()
        if len(df) < 2:
            continue

        today = df.iloc[-1]
        prev  = df.iloc[-2]

        result[code] = {
            "today_close":  float(today["Close"]),
            "today_volume": int(today["Volume"]),
            "prev_close":   float(prev["Close"]),
            "prev_volume":  int(prev["Volume"])
        }

    return {
        "data": result
    }
