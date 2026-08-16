import pandas as pd

TRANSLATION_OVERRIDES = {
    "Metals": "Металлы", "Polymers": "Полимеры", "Ceramics": "Керамика",
    "Composites": "Композиты", "Natural": "Природные", "Glasses": "Стекло",
    "Foams": "Пены", "Elastomers": "Эластомеры", "Steels": "Стали",
    "Aluminum Alloys": "Алюминиевые сплавы", "Titanium Alloys": "Титановые сплавы",
    "Copper Alloys": "Медные сплавы", "Thermoplastics": "Термопласты",
    "Thermosets": "Реактопласты", "Technical Ceramics": "Техническая керамика",
    "Natural Fibers": "Натуральные волокна", "Woods": "Древесина",
}


def translate_series_to_russian(series: pd.Series) -> pd.Series:
    """Deterministic offline translation used instead of runtime network translators."""
    return series.map(lambda v: TRANSLATION_OVERRIDES.get(str(v).strip(), v) if pd.notna(v) else v)
