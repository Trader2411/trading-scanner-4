from indicators import berechne_sma, berechne_performance, golden_cross
from config import MOMENTUM_TAGE


def berechne_momentum(daten):
    if len(daten) < MOMENTUM_TAGE:
        return 0

    start = float(daten["Close"].iloc[-MOMENTUM_TAGE])
    ende = float(daten["Close"].iloc[-1])

    return (ende - start) / start


def bewerte_momentum_text(momentum):
    if momentum > 0.08:
        return "Stark"
    elif momentum > 0.02:
        return "Positiv"
    elif momentum >= -0.02:
        return "Neutral"
    else:
        return "Schwach"


def berechne_signal(score_100):
    if score_100 >= 75:
        return "Kaufen"
    elif score_100 >= 55:
        return "Beobachten"
    else:
        return "Kein Einstieg"


def analysiere_aktie(daten, sektor_score, markt_daten):
    daten = berechne_sma(daten, 50)
    daten = berechne_sma(daten, 200)

    daten = daten.dropna()

    if daten.empty:
        return None

    close = float(daten["Close"].iloc[-1])
    sma50 = float(daten["SMA_50"].iloc[-1])
    sma200 = float(daten["SMA_200"].iloc[-1])
    volumen = float(daten["Volume"].iloc[-1])

    momentum = berechne_momentum(daten)

    aktien_perf = berechne_performance(daten, 20)
    markt_perf = berechne_performance(markt_daten, 20)
    relative_staerke = aktien_perf - markt_perf

    hat_golden_cross = golden_cross(daten)

    score = 0
    max_score = 7

    if close > sma50:
        score += 1

    if close > sma200:
        score += 1

    if momentum > 0:
        score += 1

    if sektor_score >= 3:
        score += 1

    if volumen > 500000:
        score += 1

    if relative_staerke > 0:
        score += 1

    if hat_golden_cross:
        score += 1

    score_100 = int((score / max_score) * 100)

    momentum_text = bewerte_momentum_text(momentum)

    kursziel = round(close * 1.10, 2)
    stop_loss = round(close * 0.94, 2)

    signal = berechne_signal(score_100)

    return {
        "score_roh": score,
        "trade_score": score_100,
        "aktueller_kurs": round(close, 2),
        "kursziel": kursziel,
        "stop_loss": stop_loss,
        "momentum_wert": round(momentum * 100, 2),
        "momentum_text": momentum_text,
        "relative_staerke": round(relative_staerke * 100, 2),
        "golden_cross": hat_golden_cross,
        "signal": signal
    }


def scanne_aktien(aktien_daten, sektor_analyse, markt_daten, aktien_liste):
    ergebnisse = []

    if "USA_SP500" not in markt_daten:
        return ergebnisse

    markt_index = markt_daten["USA_SP500"]

    for aktie in aktien_liste:
        ticker = aktie["ticker"]

        if ticker not in aktien_daten:
            continue

        daten = aktien_daten[ticker]

        sektor_score = 0
        if sektor_analyse["top_sektor"]:
            sektor_score = sektor_analyse["top_sektor"]["score"]

        analyse = analysiere_aktie(daten, sektor_score, markt_index)

        if analyse is None:
            continue

        ergebnisse.append({
            "name": aktie["name"],
            "ticker": ticker,
            "wkn": aktie["wkn"],
            "trade_score": analyse["trade_score"],
            "aktueller_kurs": analyse["aktueller_kurs"],
            "kursziel": analyse["kursziel"],
            "stop_loss": analyse["stop_loss"],
            "momentum_wert": analyse["momentum_wert"],
            "momentum_text": analyse["momentum_text"],
            "relative_staerke": analyse["relative_staerke"],
            "golden_cross": analyse["golden_cross"],
            "signal": analyse["signal"]
        })

    ergebnisse = sorted(ergebnisse, key=lambda x: x["trade_score"], reverse=True)

    return ergebnisse