from indicators import berechne_sma
from config import TEXTBAUSTEINE


def analysiere_einzelmarkt(daten):
    """
    Analysiert einen einzelnen Markt anhand von:
    - Kurs über SMA50
    - Kurs über SMA200
    - SMA50 über SMA200

    Rückgabe:
    {
        "score": 0 bis 3,
        "kurs_ueber_sma50": True/False,
        "kurs_ueber_sma200": True/False,
        "sma50_ueber_sma200": True/False
    }
    """
    if daten.empty:
        return {
            "score": 0,
            "kurs_ueber_sma50": False,
            "kurs_ueber_sma200": False,
            "sma50_ueber_sma200": False
        }

    daten = berechne_sma(daten, 50)
    daten = berechne_sma(daten, 200)

    daten = daten.dropna()

    if daten.empty:
        return {
            "score": 0,
            "kurs_ueber_sma50": False,
            "kurs_ueber_sma200": False,
            "sma50_ueber_sma200": False
        }

    letzter_close = float(daten["Close"].iloc[-1])
    sma50 = float(daten["SMA_50"].iloc[-1])
    sma200 = float(daten["SMA_200"].iloc[-1])

    kurs_ueber_sma50 = letzter_close > sma50
    kurs_ueber_sma200 = letzter_close > sma200
    sma50_ueber_sma200 = sma50 > sma200

    score = 0
    if kurs_ueber_sma50:
        score += 1
    if kurs_ueber_sma200:
        score += 1
    if sma50_ueber_sma200:
        score += 1

    return {
        "score": score,
        "kurs_ueber_sma50": kurs_ueber_sma50,
        "kurs_ueber_sma200": kurs_ueber_sma200,
        "sma50_ueber_sma200": sma50_ueber_sma200
    }


def analysiere_gesamtmarkt(markt_daten):
    """
    Erwartet ein Dictionary:
    {
        "USA_SP500": DataFrame,
        "USA_NASDAQ100": DataFrame,
        ...
    }

    Rückgabe:
    {
        "marktstatus": "Bullish",
        "crashrisiko": "Niedrig",
        "gesamt_score": ...,
        "max_score": ...,
        "details": {...}
    }
    """
    details = {}
    gesamt_score = 0
    max_score = 0
    anzahl_unter_sma200 = 0

    for markt_name, daten in markt_daten.items():
        ergebnis = analysiere_einzelmarkt(daten)
        details[markt_name] = ergebnis

        gesamt_score += ergebnis["score"]
        max_score += 3

        if not ergebnis["kurs_ueber_sma200"]:
            anzahl_unter_sma200 += 1

    if max_score == 0:
        marktstatus = TEXTBAUSTEINE["markt_neutral"]
    else:
        score_quote = gesamt_score / max_score

        if score_quote >= 0.7:
            marktstatus = TEXTBAUSTEINE["markt_bullish"]
        elif score_quote >= 0.4:
            marktstatus = TEXTBAUSTEINE["markt_neutral"]
        else:
            marktstatus = TEXTBAUSTEINE["markt_bearish"]

    anzahl_maerkte = len(markt_daten)

    if anzahl_maerkte == 0:
        crashrisiko = TEXTBAUSTEINE["crash_mittel"]
    else:
        quote_unter_sma200 = anzahl_unter_sma200 / anzahl_maerkte

        if quote_unter_sma200 >= 0.6:
            crashrisiko = TEXTBAUSTEINE["crash_hoch"]
        elif quote_unter_sma200 >= 0.3:
            crashrisiko = TEXTBAUSTEINE["crash_mittel"]
        else:
            crashrisiko = TEXTBAUSTEINE["crash_niedrig"]

    ausstieg = bestimme_ausstieg(crashrisiko)

    return {
        "marktstatus": marktstatus,
        "crashrisiko": crashrisiko,
        "ausstieg": ausstieg,
        "gesamt_score": gesamt_score,
        "max_score": max_score,
        "details": details
    }

def bestimme_ausstieg(crashrisiko):

    if crashrisiko == "Niedrig":
        return "Halten"

    elif crashrisiko == "Mittel":
        return "Gewinne sichern"

    else:
        return "Ausstieg prüfen"