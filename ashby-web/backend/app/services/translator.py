import pandas as pd

TRANSLATION_OVERRIDES = {
    # Groups
    "Metals": "Металлы", "Polymers": "Полимеры", "Ceramics": "Керамика",
    "Composites": "Композиты", "Natural": "Природные", "Glasses": "Стекло",
    "Foams": "Пены", "Elastomers": "Эластомеры",
    # Subgroups
    "Steels": "Стали",
    "Aluminum Alloys": "Алюминиевые сплавы", "Titanium Alloys": "Титановые сплавы",
    "Copper Alloys": "Медные сплавы", "Thermoplastics": "Термопласты",
    "Thermosets": "Реактопласты", "Technical Ceramics": "Техническая керамика",
    "Natural Fibers": "Натуральные волокна", "Woods": "Древесина",
    "Oxides": "Оксиды", "Carbides": "Карбиды", "Fiber Reinforced": "Волокнистые композиты",
    "Polymer Foams": "Полимерные пены", "Metal Foams": "Металлические пены",
    "Rubbers": "Каучуки", "Technical Glasses": "Технические стёкла",
    # Materials
    "Low Carbon Steel": "Низкоуглеродистая сталь", "Stainless Steel": "Нержавеющая сталь",
    "Al 6061": "Al 6061", "Al 7075": "Al 7075", "Ti-6Al-4V": "Ti-6Al-4V",
    "Copper": "Медь",
    "Polyethylene (PE)": "Полиэтилен (ПЭ)", "Polypropylene (PP)": "Полипропилен (ПП)",
    "Polycarbonate (PC)": "Поликарбонат (ПК)", "Epoxy": "Эпоксидная смола",
    "Alumina": "Оксид алюминия", "Silica Glass": "Кварцевое стекло",
    "Silicon Carbide": "Карбид кремния", "CFRP": "Углепластик", "GFRP": "Стеклопластик",
    "Wood (Pine)": "Древесина (сосна)", "Bamboo": "Бамбук",
    "PU Foam": "Пенополиуретан", "Al Foam": "Алюминиевая пена",
    "Natural Rubber": "Натуральный каучук", "Silicone Rubber": "Силиконовый каучук",
    "Borosilicate Glass": "Боросиликатное стекло", "Soda-lime Glass": "Натриево-известковое стекло",
}


def translate_series_to_russian(series: pd.Series) -> pd.Series:
    """Deterministic offline translation used instead of runtime network translators."""
    return series.map(lambda v: TRANSLATION_OVERRIDES.get(str(v).strip(), v) if pd.notna(v) else v)
