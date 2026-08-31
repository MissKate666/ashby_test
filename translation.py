"""Robust English -> Russian translation for material, group and subgroup names.

Tries deep_translator's Google backend, then its MyMemory backend, then falls back to
googletrans -- and finally falls back to the original English text if none of them work.
Every network attempt is time-boxed (the underlying libraries issue plain ``requests``
calls with no timeout of their own, so a stalled connection can otherwise hang forever)
and retried a small, fixed number of times. A backend that keeps failing (rate limited,
unreachable, broken response) is marked "down" for the rest of the process so later
lookups don't keep paying for a backend that has already proven unusable. Successful
translations are cached in memory and persisted to disk so repeated runs don't re-hit
the network for terms translated once already.
"""
import json
import threading
import time
from pathlib import Path

STATIC_OVERRIDES = {
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

DEFAULT_CACHE_PATH = Path(__file__).resolve().parent / ".translation_cache.json"
REQUEST_TIMEOUT_SECONDS = 3
MAX_ATTEMPTS_PER_BACKEND = 2
RETRY_BACKOFF_SECONDS = 0.6
MAX_CONSECUTIVE_FAILURES = 2


class _Backend:
    """One translator implementation plus failure tracking so it can be skipped once dead."""

    def __init__(self, name, translate_fn):
        self.name = name
        self._translate_fn = translate_fn
        self.consecutive_failures = 0
        self.disabled = False

    def translate(self, text):
        return self._translate_fn(text)

    def note_success(self):
        self.consecutive_failures = 0

    def note_failure(self):
        self.consecutive_failures += 1
        if self.consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
            self.disabled = True


def _build_deep_translator_backends():
    backends = []
    try:
        from deep_translator import GoogleTranslator, MyMemoryTranslator
    except ImportError:
        return backends
    try:
        google = GoogleTranslator(source="auto", target="ru")
        backends.append(_Backend("deep_translator.Google", lambda t: google.translate(t)))
    except Exception:
        pass
    try:
        mymemory = MyMemoryTranslator(source="en-US", target="ru-RU")
        backends.append(_Backend("deep_translator.MyMemory", lambda t: mymemory.translate(t)))
    except Exception:
        pass
    return backends


def _build_googletrans_backend():
    try:
        from googletrans import Translator as GoogleTransTranslator
    except ImportError:
        return None
    try:
        client = GoogleTransTranslator()
    except Exception:
        return None

    def _run(text):
        result = client.translate(text, dest="ru")
        translated = getattr(result, "text", None)
        if not translated:
            raise ValueError("empty translation result")
        return translated

    return _Backend("googletrans", _run)


class MaterialTranslator:
    """Translates material/group/subgroup names to Russian without ever raising or
    blocking the caller for long. Use one instance per process and reuse it -- it keeps
    an in-memory cache plus per-backend failure state across calls."""

    def __init__(self, cache_path=DEFAULT_CACHE_PATH):
        self._cache_path = Path(cache_path) if cache_path else None
        self._cache = self._load_cache()
        self._backends = None  # built lazily so import-time never touches the network

    def _ensure_backends(self):
        if self._backends is not None:
            return
        backends = _build_deep_translator_backends()
        googletrans_backend = _build_googletrans_backend()
        if googletrans_backend is not None:
            backends.append(googletrans_backend)
        self._backends = backends

    def _load_cache(self):
        if not self._cache_path or not self._cache_path.exists():
            return {}
        try:
            with self._cache_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _save_cache(self):
        if not self._cache_path:
            return
        try:
            with self._cache_path.open("w", encoding="utf-8") as f:
                json.dump(self._cache, f, ensure_ascii=False, sort_keys=True)
        except Exception:
            pass  # caching is a best-effort optimization, never fatal

    @staticmethod
    def _call_with_timeout(backend, text):
        # deep_translator / googletrans issue plain `requests` calls with no timeout of
        # their own, so a stalled connection can hang forever. Run the call in its own
        # daemon thread and bound how long we wait for it: a dedicated thread per call
        # (instead of a shared bounded pool) means one permanently-hung backend can never
        # starve later calls to a *different*, working backend out of a worker slot; the
        # daemon flag means a thread stuck on a hung call never blocks process shutdown.
        outcome = {}

        def _run():
            try:
                outcome["value"] = backend.translate(text)
            except Exception as exc:
                outcome["error"] = exc

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        thread.join(REQUEST_TIMEOUT_SECONDS)
        if thread.is_alive():
            raise TimeoutError(f"{backend.name} timed out after {REQUEST_TIMEOUT_SECONDS}s")
        if "error" in outcome:
            raise outcome["error"]
        return outcome.get("value")

    def _translate_via_backends(self, text):
        self._ensure_backends()
        for backend in self._backends:
            if backend.disabled:
                continue
            for attempt in range(MAX_ATTEMPTS_PER_BACKEND):
                try:
                    result = self._call_with_timeout(backend, text)
                    if result and result.strip():
                        backend.note_success()
                        return result.strip()
                    raise ValueError("empty translation result")
                except Exception:
                    backend.note_failure()
                    if backend.disabled or attempt == MAX_ATTEMPTS_PER_BACKEND - 1:
                        break
                    time.sleep(RETRY_BACKOFF_SECONDS * (attempt + 1))
        return None

    def translate(self, text):
        """Translate one string. Always returns a string -- falls back to the original
        text (stripped) if every backend is unavailable or fails."""
        if text is None:
            return text
        stripped = str(text).strip()
        if not stripped:
            return text
        if stripped in STATIC_OVERRIDES:
            return STATIC_OVERRIDES[stripped]
        if stripped in self._cache:
            return self._cache[stripped]
        translated = self._translate_via_backends(stripped)
        result = translated if translated else stripped
        self._cache[stripped] = result
        return result

    def translate_many(self, values):
        """Translate an iterable of strings, returning {original: translated}. Duplicate
        values are translated once. Persists the disk cache once at the end."""
        unique = {str(v).strip() for v in values if v is not None and str(v).strip()}
        result = {v: self.translate(v) for v in unique}
        self._save_cache()
        return result

    def translate_series(self, series):
        """Convenience wrapper for a pandas Series of names."""
        import pandas as pd
        mapping = self.translate_many(series.dropna().tolist())
        return series.map(lambda v: mapping.get(str(v).strip(), v) if pd.notna(v) else v)
