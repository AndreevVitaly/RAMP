# RAMP на виртуальном хостинге Timeweb

Это схема для **виртуального хостинга**, где Python-приложения запускаются через Apache/mod_wsgi. У Timeweb доступен Python 3.10; Django 5.2 его поддерживает. Исходный код Django и `.env` должны находиться вне `public_html`.

Ожидаемая структура после создания сайта в панели:

```text
SITE_DIR/
  public_html/       # собранный React, wsgi.py, .htaccess, static/, media/
  ramp/              # git clone репозитория RAMP
    backend/.env      # секреты, не публиковать
  venv/              # virtualenv Timeweb
```

1. В панели Timeweb создать сайт и привязать домен. Для испытаний можно взять бесплатный технический домен `*.webtm.ru`, `*.tw1.ru` или `*.tw1.su`. Включить SSL и HTTPS в настройках сайта.
2. Через SSH создать окружение Python 3.10 по инструкции Timeweb и клонировать репозиторий в `SITE_DIR/ramp`. Важно, чтобы окружение `SITE_DIR/venv` содержало `bin/activate_this.py` (его создаёт `virtualenv`, на который ссылается инструкция Timeweb).
3. Установить `backend/requirements.txt` в этом окружении. Скопировать `.env.example` в `ramp/backend/.env`, затем задать настоящий домен в `DJANGO_ALLOWED_HOSTS`, `DJANGO_DEBUG=false`, уникальный `DJANGO_SECRET_KEY` длиной от 50 символов и параметры БД. Указать абсолютные `DJANGO_STATIC_ROOT=SITE_DIR/public_html/static` и `DJANGO_MEDIA_ROOT=SITE_DIR/public_html/media`, заменив `SITE_DIR` на путь сайта. Файл `.env` остаётся вне открытой директории.
4. Применить миграции и выполнить `python manage.py collectstatic --noinput` из `ramp/backend` с активным окружением. Для тестового старта с SQLite можно установить `USE_SQLITE=true`; её файл останется в закрытой папке `backend`. Для постоянной базы понадобится отдельная PostgreSQL с внешним доступом: встроенные БД виртуального хостинга Timeweb — MySQL.
5. Собрать React командой `npm ci` и `npm run build` в `ramp/frontend` на компьютере или сервере с Node.js. Скопировать **содержимое** `frontend/dist/` в `SITE_DIR/public_html/`.
6. Скопировать `deploy/timeweb/wsgi.py` и `deploy/timeweb/.htaccess` в `SITE_DIR/public_html/`. Шаблоны предполагают именно указанную структуру каталогов. Не переносить туда `backend`, `.env`, `.git` или `node_modules`.
7. Проверить `python manage.py check --deploy` с production `.env`, а затем публичные `/`, `/api/ramp/images/`, `/admin/`, `/static/admin/css/base.css`. После изменения Python-кода перезапустить WSGI-приложение средствами панели Timeweb.

До настройки SMTP посетители могут открыть конструктор как гости. Вход по коду и сохранение клиентских проектов не будут работать. Для полного теста добавить параметры SMTP в закрытый `.env` и указать адрес администратора в кабинете. Не отправлять пароль почты или базы в чат или Git.

На виртуальном хостинге маршруты `/api/` и `/admin/` направляет Apache в Django; корень и файлы Vite обслуживаются как статические. Доступность PostgreSQL, Python-пакетов и этих правил Apache нужно проверить на конкретном аккаунте Timeweb до рассылки адреса близким.
