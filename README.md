# Трекер фінансів

Вебзастосунок для обліку доходів і витрат з аналітикою за категоріями та періодами. Користувач додає транзакції, встановлює бюджети й ліміти та бачить наочні графіки і звіти про те, куди йдуть гроші.

**Frontend:** HTML5 · CSS3 (CSS Modules) · JavaScript · React 19 · React Router · TanStack Query · Recharts · Vite
**Backend:** Python 3.12 · FastAPI · PostgreSQL · SQLAlchemy 2 + Alembic · Redis
**Інфраструктура:** Docker Compose · nginx · GitHub Actions · GitHub Pages

**Демо:** https://merynov-back.github.io/treker/ — вхід `demo@treker.app` / `demo12345`

---

## Можливості

- **Акаунт** — реєстрація, вхід за JWT, сесії в Redis з ротацією refresh-токена, вихід, зміна імені й пароля (інші сесії при цьому завершуються). Захист від перебору пароля.
- **Транзакції** — доходи й витрати з категорією, датою та описом; редагування, видалення, пошук за описом і категорією, фільтри за місяцем і типом, пагінація, **експорт у CSV** (відкривається в Excel).
- **Категорії** — 10 стандартних створюються при реєстрації; свої можна додавати, перейменовувати й видаляти. Назви унікальні без урахування регістру.
- **Бюджети та ліміти** — ліміт на категорію або на всі витрати місяця, прогрес і попередження про перевищення, **перенесення лімітів з минулого місяця** в один клік.
- **Аналітика** — підсумок за період з порівнянням з минулим місяцем, структура витрат і доходів за категоріями, динаміка по днях і місяцях. Звіти кешуються в Redis і скидаються при будь-якій зміні даних.

---

## Зміст

- [Швидкий старт](#швидкий-старт)
- [Демо на GitHub Pages](#демо-на-github-pages)
- [Архітектура](#архітектура)
- [Змінні оточення](#змінні-оточення)
- [Розробка без Docker](#розробка-без-docker)
- [Тести та лінтери](#тести-та-лінтери)
- [Міграції](#міграції)
- [API](#api)
- [Структура проєкту](#структура-проєкту)
- [Командна робота](#командна-робота)
- [Часті проблеми](#часті-проблеми)

---

## Швидкий старт

Потрібен лише **Docker** з Compose.

```bash
git clone https://github.com/merynov-back/treker.git
cd treker
cp .env.example .env          # і впиши свій JWT_SECRET_KEY
docker compose up -d --build
```

| Що | Адреса |
|---|---|
| Застосунок | http://localhost:3001 |
| Swagger (документація API) | http://localhost:8001/docs |
| Стан сервісів | http://localhost:8001/health |

Зареєструйся — і можна користуватись. Міграції застосовуються автоматично перед стартом API.

> Згенерувати `JWT_SECRET_KEY`: `python3 -c "import secrets; print(secrets.token_urlsafe(64))"`

---

## Демо на GitHub Pages

https://merynov-back.github.io/treker/

GitHub Pages хостить лише статику, тому там працює окрема збірка фронтенду з `VITE_DEMO=true`: запити до API обробляє емулятор у браузері (`frontend/src/api/demo/`) з тими самими правилами й кодами помилок, що й бекенд. Дані зберігаються в `localStorage` — у кожного відвідувача свої.

Для входу є тестовий акаунт з історією за три місяці: `demo@treker.app` / `demo12345`. Можна й зареєструватися.

Збірку й публікацію робить `.github/workflows/pages.yml` на кожен push у `main`, що зачіпає `frontend/`. У звичайну збірку (Docker) код емулятора не потрапляє.

Локально:

```bash
cd frontend
VITE_DEMO=true npm run dev
```

---

## Архітектура

```
 Браузер ──► web (nginx :3001) ──┬── /         статика React (SPA)
                                 └── /api/*  ──► api (FastAPI :8000) ──┬──► PostgreSQL
                                                                       └──► Redis
```

- **nginx** роздає зібраний фронтенд і проксіює `/api` на бекенд, тож фронтенд і API на одному origin — CORS у продакшні не потрібен.
- **migrate** — одноразовий контейнер, що застосовує міграції Alembic; `api` стартує лише після його успішного завершення.

### Backend

Шари: **router → service → repository → БД**.

- `routers/` лише приймають HTTP-запит і віддають відповідь.
- `services/` містять бізнес-правила і кидають доменні помилки (`NotFoundError`, `ConflictError`, `AuthError`, …), які глобальні обробники перетворюють на HTTP-коди.
- `repositories/` — доступ до БД через SQLAlchemy; `UserOwnedRepository` гарантує, що користувач бачить лише свої записи.
- Залежності збираються через `Depends` у `dependencies/`, тож у тестах їх легко підмінити.

**Redis** використовується для трьох речей:

| Ключ | Навіщо |
|---|---|
| `session:<sid>`, `user:sessions:<id>` | Сесії. Токен дійсний, поки є його сесія — logout і зміна пароля відкликають токени одразу |
| `cache:<user>:v<версія>:<звіт>` | Кеш аналітики. Будь-яка зміна даних збільшує версію — старий кеш просто перестає читатися |
| `login:attempts:<email>` | Ліміт невдалих спроб входу |

### Frontend

- `api/` — HTTP-клієнт з автоматичним оновленням токена (один refresh на кілька паралельних 401), ендпоінти і хуки TanStack Query. Після будь-якої зміни даних кеш запитів інвалідується, тож графіки й бюджети оновлюються самі.
- `features/` — компоненти, згруповані за доменом: транзакції, бюджети, аналітика, категорії.
- `pages/` — сторінки; за логіном вантажаться ліниво.
- `components/` — layout і базові UI-елементи.
- Обраний місяць зберігається в URL (`?month=2026-10`) і спільний для всіх сторінок.
- Світла й темна теми — автоматично за налаштуваннями системи; верстка адаптивна.

---

## Змінні оточення

Файл `.env` у корені — спільний для Docker Compose і локального запуску. Він у `.gitignore`, **не комітьте його**. Шаблон — `.env.example`.

| Змінна | За замовчуванням | Опис |
|---|---|---|
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | — | Доступ до Postgres у Docker |
| `BASE_URL` | — | Адреса БД для запуску без Docker |
| `JWT_SECRET_KEY` | — | Секрет для підпису токенів |
| `JWT_ALGORITHM` | `HS256` | Алгоритм JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Строк життя access-токена |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Строк життя сесії |
| `REDIS_URL` | `redis://localhost:6379/0` | Адреса Redis для запуску без Docker |
| `ANALYTICS_CACHE_TTL_SECONDS` | `300` | Скільки живе кеш звітів |
| `LOGIN_MAX_ATTEMPTS` | `5` | Невдалих спроб входу до блокування |
| `LOGIN_BLOCK_SECONDS` | `300` | На скільки блокується вхід |
| `CORS_ORIGINS` | `["http://localhost:5173"]` | Звідки можна звертатись до API напряму (dev-сервер Vite) |
| `APP_TIMEZONE` | `Europe/Kyiv` | Пояс для «сьогодні» і «поточного місяця» |

У Docker Compose `BASE_URL` і `REDIS_URL` підміняються на адреси всередині мережі контейнерів.

---

## Розробка без Docker

Postgres і Redis зручно залишити в Docker:

```bash
docker compose up -d postgres redis
```

**Backend** (Python 3.12):

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

alembic upgrade head
uvicorn src.main:app --reload --port 8001
```

**Frontend** (Node 22), в окремому терміналі:

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173
```

Vite проксіює `/api` на `localhost:8001`, тож налаштовувати адресу API не потрібно.

---

## Тести та лінтери

Ті самі перевірки запускає CI на кожен push і pull request.

```bash
# Backend: SQLite у пам'яті + fakeredis, Postgres і Redis не потрібні
cd backend
ruff check .
pytest -v

# Frontend
cd frontend
npm run lint
npm test
npm run build
```

| Файл | Що перевіряє |
|---|---|
| `backend/tests/test_api.py` | Ендпоінти цілком, безпеку і узгодженість даних |
| `backend/tests/test_services.py` | Бізнес-логіку: сесії, аналітику, бюджети |
| `backend/tests/test_repositories.py` | Роботу з БД і ізоляцію даних між користувачами |
| `backend/tests/test_redis_service.py` | Кеш, сесії й ліміт входу |
| `backend/tests/test_schemas.py` | Валідацію вхідних даних |
| `frontend/src/utils/*.test.js` | Форматування сум і робота з періодами |
| `frontend/src/api/demo/server.test.js` | Емулятор API для демо |

---

## Міграції

Нову міграцію генеруй локально (Postgres з Docker на `localhost:5434`):

```bash
cd backend
source .venv/bin/activate
alembic revision --autogenerate -m "опис змін"
alembic upgrade head
```

У Docker міграції застосовуються самі при `docker compose up -d --build`.

---

## API

Повна інтерактивна документація — [Swagger](http://localhost:8001/docs). Усі ендпоінти, крім реєстрації, входу й оновлення токена, потребують заголовка `Authorization: Bearer <access_token>`. Суми передаються рядком (`"1250.50"`), щоб не втрачати копійки.

| Група | Ендпоінти |
|---|---|
| Auth | `POST /auth/register`, `POST /auth/token`, `POST /auth/refresh`, `POST /auth/logout`, `GET/PATCH /auth/me`, `POST /auth/change-password` |
| Категорії | `GET/POST /categories`, `PATCH/DELETE /categories/{id}` |
| Транзакції | `GET/POST /transactions`, `GET /transactions/export`, `GET/PATCH/DELETE /transactions/{id}` |
| Бюджети | `GET/POST /budgets`, `GET /budgets/status`, `POST /budgets/copy-previous`, `PATCH/DELETE /budgets/{id}` |
| Аналітика | `GET /analytics/summary`, `GET /analytics/by-category`, `GET /analytics/by-period` |
| Сервіс | `GET /health` |

| Код | Коли |
|---|---|
| `400` | Некоректні дані, які не відловила схема |
| `401` | Немає токена, він невалідний або сесію завершено |
| `404` | Об'єкт не знайдено або він чужий |
| `409` | Дублікат або дія, що ламає цілісність |
| `422` | Не пройшла валідація схеми |
| `429` | Забагато невдалих спроб входу (див. `Retry-After`) |

---

## Структура проєкту

```
treker/
├── backend/
│   ├── src/
│   │   ├── main.py            # FastAPI, CORS, роутери, /health
│   │   ├── config.py          # Налаштування з .env
│   │   ├── exceptions.py      # Доменні помилки і їхні HTTP-коди
│   │   ├── routers/           # HTTP-ендпоінти
│   │   ├── services/          # Бізнес-логіка
│   │   ├── repositories/      # Доступ до БД
│   │   ├── models/            # SQLAlchemy-моделі
│   │   ├── schemas/           # Pydantic-схеми
│   │   ├── dependencies/      # Залежності FastAPI
│   │   └── utils/             # Гроші та періоди
│   ├── migrations/            # Alembic
│   ├── tests/
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api/               # HTTP-клієнт, ендпоінти, хуки запитів
│   │   ├── components/        # Layout і UI-компоненти
│   │   ├── context/           # Авторизація
│   │   ├── features/          # Транзакції, бюджети, аналітика, категорії
│   │   ├── hooks/
│   │   ├── pages/
│   │   └── utils/
│   ├── nginx.conf
│   └── Dockerfile
├── .github/                   # CI, деплой на Pages, шаблон pull request
├── docker-compose.yml
├── .env.example
└── CONTRIBUTING.md
```

---

## Командна робота

Як працювати з гілками, комітами й pull request — у [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Часті проблеми

**Порт уже зайнятий.** Зміни ліву частину в `ports` у `docker-compose.yml`, наприклад `"3002:80"`.

**`relation "users" does not exist`.** Не застосовані міграції: `docker compose up -d --build` або `alembic upgrade head` у `backend/`.

**429 при вході.** Було 5 невдалих спроб — зачекай вказаний час або скинь лічильник:
`docker compose exec redis redis-cli del login:attempts:<email>`.

**Подивитися базу:** `docker compose exec postgres psql -U postgres -d treker`
(або будь-який GUI-клієнт на `localhost:5434`).

**Почати з чистого аркуша:** `docker compose down -v` — видалить дані БД і Redis ⚠️
