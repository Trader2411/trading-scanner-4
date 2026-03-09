from __future__ import annotations

from typing import Dict, List
from config import UNIVERSES


ALL_UNIVERSE_NAME = "Alle"
EUROPE_UNIVERSE_NAME = "Europa Listings"
COMMODITIES_UNIVERSE_NAME = "Rohstoffe"


def get_available_universes() -> List[str]:
    """
    Liefert die Auswahl für die Sidebar.
    'Alle' steht immer an erster Stelle.
    """
    return [ALL_UNIVERSE_NAME] + list(UNIVERSES.keys())


def _dedupe_keep_order(symbols: List[str]) -> List[str]:
    seen = set()
    result: List[str] = []

    for symbol in symbols:
        if symbol not in seen:
            seen.add(symbol)
            result.append(symbol)

    return result


def load_universe(
    name: str,
    include_europe_listings: bool = True,
    include_commodities_in_all: bool = False,
) -> List[str]:
    """
    Lädt ein einzelnes Universe.

    Spezialfall 'Alle':
    - nimmt standardmäßig alle Aktien-Universen zusammen
    - europäische Listings können optional mit rein
    - Rohstoffe werden standardmäßig ausgeschlossen,
      weil sie in der App separat gescannt werden
    """

    if name != ALL_UNIVERSE_NAME:
        return UNIVERSES.get(name, []).copy()

    symbols: List[str] = []

    for universe_name, universe_symbols in UNIVERSES.items():
        # Rohstoffe standardmäßig NICHT in "Alle"
        if universe_name == COMMODITIES_UNIVERSE_NAME and not include_commodities_in_all:
            continue

        # Europa Listings optional ein-/ausschließen
        if universe_name == EUROPE_UNIVERSE_NAME and not include_europe_listings:
            continue

        symbols.extend(universe_symbols)

    return _dedupe_keep_order(symbols)


def load_all_universes() -> Dict[str, List[str]]:
    """
    Gibt alle definierten Universen 1:1 zurück.
    """
    return {k: v.copy() for k, v in UNIVERSES.items()}


def load_all_equities(
    include_europe_listings: bool = True,
) -> List[str]:
    """
    Komfortfunktion:
    Lädt alle Aktien-Universen ohne Rohstoffe.
    """
    return load_universe(
        ALL_UNIVERSE_NAME,
        include_europe_listings=include_europe_listings,
        include_commodities_in_all=False,
    )


def load_all_with_commodities(
    include_europe_listings: bool = True,
) -> List[str]:
    """
    Komfortfunktion:
    Lädt wirklich alles inklusive Rohstoffe.
    """
    return load_universe(
        ALL_UNIVERSE_NAME,
        include_europe_listings=include_europe_listings,
        include_commodities_in_all=True,
    )