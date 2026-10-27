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
3. Установить `backend/requirements.txt` в этом окружении. Из `SITE_DIR` выполнить `./venv/bin/python ramp/deploy/timeweb/configure.py ramp-dog434674.webtm.ru`, подставив свой домен. Команда создаёт закрытый `ramp/backend/.env` с новым секретным ключом, `USE_SQLITE=true` и абсолютными путями static/media. Повторный запуск не перезаписывает существующий `.env`. Файл остаётся вне открытой директории.
4. Применить миграции и выполнить `python manage.py collectstatic --noinput` из `ramp/backend` с активным окружением. База `backend/db.sqlite3` останется вне `public_html`. Если интерактивный `createsuperuser` не работает в веб-консоли, выполнить из `SITE_DIR` команду `./venv/bin/python ramp/deploy/timeweb/create_admin.py`: она создаст пользователя `admin` и временно сохранит случайный пароль в закрытом файле `ramp/backend/.admin-initial-password`. Прочитать пароль самостоятельно без скриншота, войти на сайт, сменить пароль и удалить временный файл. Локальная база и её учётные записи автоматически на хост не переносятся.
5. Собрать React командой `npm ci` и `npm run build` в `ramp/frontend` на компьютере или сервере с Node.js. Скопировать **содержимое** `frontend/dist/` в `SITE_DIR/public_html/`.
6. Скопировать `deploy/timeweb/wsgi.py` и `deploy/timeweb/.htaccess` в `SITE_DIR/public_html/`. Шаблоны предполагают именно указанную структуру каталогов. Не переносить туда `backend`, `.env`, `.git` или `node_modules`.
7. Проверить `python manage.py check --deploy` с production `.env`, а затем публичные `/`, `/api/ramp/images/`, `/admin/`, `/static/admin/css/base.css`. После изменения Python-кода перезапустить WSGI-приложение средствами панели Timeweb.

Перед обновлениями сохранять копии `ramp/backend/db.sqlite3` и `public_html/media/`; это разные части данных сайта. При активных записях в SQLite делать согласованную копию через SQLite Backup API, а не простым копированием файла. После пилотного запуска можно перенести данные в отдельную PostgreSQL; встроенные БД виртуального хостинга Timeweb — MySQL.

Без SMTP посетители могут зарегистрироваться по email и паролю, войти и сохранять проекты. Адрес email при этом не подтверждается; отправка кодов и PDF по почте не работает. Для доставки писем добавить параметры SMTP в закрытый `.env` и указать адрес администратора в кабинете. Не отправлять пароль почты или базы в чат или Git. После обновления кода для входа по паролю выполнить `./venv/bin/python ramp/backend/manage.py migrate` из `SITE_DIR`, затем загрузить новую сборку React в `public_html`.

На виртуальном хостинге маршруты `/api/` и `/admin/` направляет Apache в Django; корень и файлы Vite обслуживаются как статические. Работу Python-пакетов и этих правил Apache нужно проверить на конкретном аккаунте Timeweb до рассылки адреса близким.

## Обновление входа по паролю на действующем сайте

1. Сделать резервную копию SQLite через Backup API и каталога `public_html/media/`.
2. В SSH-консоли выполнить `cd /home/c/cu434674/RAMP/ramp`, затем `git pull --ff-only` и `../venv/bin/python backend/manage.py migrate`.
3. На компьютере собрать React через `npm ci` и `npm run build` в каталоге `frontend`, затем загрузить содержимое `frontend/dist/` в `/home/c/cu434674/RAMP/public_html/` через файловый менеджер Timeweb. Можно загрузить архив `frontend/ramp-frontend.zip` и распаковать его в `public_html`; файл `index.html` должен оказаться прямо в `public_html`, а не во вложенной папке.
4. Открыть сайт в приватном окне браузера. Проверить регистрацию, вход и сохранение проекта. Старые аккаунты, которые ещё открыты в браузере, могут установить пароль в личном кабинете.
