# RAMP — конструктор пандусов для собак

Backend рассчитывает боковой профиль и единую пространственную модель пандуса: поверхность, основание, шарнир на 75%, складную стойку, упор и поперечные рейки. React отображает из одних XYZ-координат вид сбоку, сверху, спереди и техническую аксонометрию. Конфигурации пока не сохраняются, интерактивная 3D-модель и цена не рассчитываются.

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
  "support_panel_width_cm": 20,
  "support_panel_visual_thickness_cm": 2,
  "color": "beige",
  "has_slats": true,
  "side_rails": false
}
```

`ramp_length_cm` необязателен: без него API использует рекомендуемую длину `height_cm × 2`. Подробности модели находятся в [docs/RAMP_MODEL.md](docs/RAMP_MODEL.md).

