def berechne_sma(daten, periode):
    """
    Berechnet den einfachen gleitenden Durchschnitt.
    Erwartet ein DataFrame mit einer 'Close'-Spalte.
    """
    if daten.empty or "Close" not in daten.columns:
        return daten

    daten = daten.copy()
    daten[f"SMA_{periode}"] = daten["Close"].rolling(window=periode).mean()
    return daten

def berechne_performance(daten, tage):

    if len(daten) < tage:
        return 0

    start = float(daten["Close"].iloc[-tage])
    ende = float(daten["Close"].iloc[-1])

    return (ende - start) / start

def golden_cross(daten):

    if "SMA_50" not in daten or "SMA_200" not in daten:
        return False

    if len(daten) < 2:
        return False

    heute = daten.iloc[-1]
    gestern = daten.iloc[-2]

    return (
        gestern["SMA_50"] <= gestern["SMA_200"] and
        heute["SMA_50"] > heute["SMA_200"]
    )

def golden_cross(daten):
    """
    Prüft, ob aktuell ein Golden Cross vorliegt:
    SMA50 kreuzt SMA200 von unten nach oben.
    """
    if daten.empty:
        return False

    if "SMA_50" not in daten.columns or "SMA_200" not in daten.columns:
        return False

    if len(daten) < 2:
        return False

    gestern = daten.iloc[-2]
    heute = daten.iloc[-1]

    return (
        gestern["SMA_50"] <= gestern["SMA_200"] and
        heute["SMA_50"] > heute["SMA_200"]
    )