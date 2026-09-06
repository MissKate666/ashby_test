# Ashby Web

Интерактивная диаграмма Эшби: FastAPI backend + React/Vite/D3 frontend.

## Требования

Рекомендуется Python 3.11 или 3.12. Если используется более новый Python, например 3.13/3.14, `pip` должен иметь возможность подобрать свежие binary wheels для `pandas`, `numpy` и `shapely`; поэтому backend-зависимости заданы диапазонами версий, а не жёсткими старыми pin-версиями.

Также нужен Node.js 18+ для frontend.

## Запуск backend на Windows PowerShell

```powershell
cd C:\Users\Kate\PycharmProjects\ashby_test\ashby-web\backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
python -m pip install --only-binary=:all: -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Если Python 3.12 не установлен, можно создать окружение текущим Python:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
python -m pip install --only-binary=:all: -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Важно запускать сервер через `python -m uvicorn`, а не просто `uvicorn`: так Windows точно возьмёт пакет из активного `.venv`.

Проверка backend:

```text
http://127.0.0.1:8000/health
```

## Запуск frontend

Во втором терминале:

```powershell
cd C:\Users\Kate\PycharmProjects\ashby_test\ashby-web\frontend
npm install
npm run dev
```

Открыть приложение:

```text
http://127.0.0.1:5173
```

Vite проксирует `/api` на backend `http://127.0.0.1:8000`.

## Почему могла быть ошибка с pandas

Если `pip` скачивает `pandas-2.2.0.tar.gz`, значит для вашей версии Python не нашлось готового wheel-файла. Тогда `pip` пытается собрать pandas из исходников через Meson/MSVC, что часто ломается на Windows. Решение: использовать Python 3.11/3.12 или разрешить более свежие версии pandas/numpy, для которых есть wheel под вашу версию Python.
