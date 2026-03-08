from indicators import berechne_sma
from config import SEKTOREN, PERFORMANCE_1M, PERFORMANCE_3M


def berechne_performance(daten, tage):
    if len(daten) < tage:
        return 0

    start = float(daten["Close"].iloc[-tage])
    ende = float(daten["Close"].iloc[-1])

    return (ende - start) / start


def analysiere_sektor(daten):

    daten = berechne_sma(daten, 50)
    daten = berechne_sma(daten, 200)

    daten = daten.dropna()

    if daten.empty:
        return 0

    letzter_kurs = float(daten["Close"].iloc[-1])
    sma50 = float(daten["SMA_50"].iloc[-1])
    sma200 = float(daten["SMA_200"].iloc[-1])

    perf1m = berechne_performance(daten, PERFORMANCE_1M)
    perf3m = berechne_performance(daten, PERFORMANCE_3M)

    score = 0

    if letzter_kurs > sma50:
        score += 1

    if letzter_kurs > sma200:
        score += 1

    if perf1m > 0:
        score += 1

    if perf3m > 0:
        score += 1

    return score


def analysiere_sektoren(sektor_daten):

    ergebnisse = []

    for sektor_name, daten in sektor_daten.items():

        score = analysiere_sektor(daten)

        ergebnisse.append({
            "sektor": sektor_name,
            "score": score
        })

    ergebnisse = sorted(ergebnisse, key=lambda x: x["score"], reverse=True)

    if len(ergebnisse) > 0:
        top_sektor = ergebnisse[0]
    else:
        top_sektor = None

    return {
        "ranking": ergebnisse,
        "top_sektor": top_sektor
    }