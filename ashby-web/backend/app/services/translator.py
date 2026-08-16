TRANSLATIONS = {
    "Metals": "Металлы", "Polymers": "Полимеры", "Ceramics": "Керамика", "Composites": "Композиты",
    "Natural Materials": "Природные материалы", "Foams": "Пены", "Elastomers": "Эластомеры",
    "Steels": "Стали", "Aluminum Alloys": "Алюминиевые сплавы", "Titanium Alloys": "Титановые сплавы",
    "Copper Alloys": "Медные сплавы", "Thermoplastics": "Термопласты", "Thermosets": "Реактопласты",
    "Technical Ceramics": "Техническая керамика", "Glass": "Стекло",
}

def translate_series_to_russian(value: str | None) -> str:
    if not value:
        return "Не указано"
    return TRANSLATIONS.get(str(value), str(value))
