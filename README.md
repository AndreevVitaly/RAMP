# RAMP — конструктор пандусов для собак

Backend рассчитывает реальный боковой профиль пандуса: рабочую поверхность, основание с отступом 5 см, внутреннюю складную стойку 105°, независимые точки верхнего шарнира D и нижней опоры S, контакт с упором и координаты реек. React-интерфейс отправляет параметры в API и отображает готовую геометрию в масштабируемом SVG. Конфигурации пока не сохраняются, цена и 3D-модель не рассчитываются.

## Структура

- `backend/` — Django 4.2 + Django REST Framework, доменный сервис расчёта и тесты.
- `frontend/` — React 18 + Vite, форма конфигуратора и SVG-схема.
- `docs/` — описание модели и список открытых производственных вопросов.

## Запуск backend

Требуется Python 3.11+ и PostgreSQL. Для быстрого локального запуска без PostgreSQL можно явно выбрать SQLite.

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item ..\.env.example .env
$env:USE_SQLITE = "true"  # убрать строку для PostgreSQL
python manage.py migrate
python manage.py runserver
```

Переменные из `.env` нужно загрузить в окружение выбранным способом; Django не читает этот файл автоматически. По умолчанию используются параметры PostgreSQL из переменных `POSTGRES_*`.

Проверки backend:

```powershell
cd backend
$env:USE_SQLITE = "true"
python manage.py test
python manage.py check
python manage.py makemigrations --check --dry-run
```

## Запуск frontend

Требуется Node.js 20+.

```powershell
cd frontend
npm install
npm run dev
```

Vite откроет интерфейс на `http://localhost:5173` и проксирует `/api` в Django на `http://127.0.0.1:8000`. Сборка: `npm run build`.

## API

`POST /api/ramp/calculate/`

```json
{
  "height_cm": 50,
  "width_cm": 40,
  "color": "beige",
  "side_rails": false
}
```

`ramp_length_cm` необязателен: без него API использует рекомендуемую длину `height_cm × 2`. Подробности модели находятся в [docs/RAMP_MODEL.md](docs/RAMP_MODEL.md).

