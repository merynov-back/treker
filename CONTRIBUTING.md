# Як працюємо з репозиторієм

## Перший запуск

1. Прийми запрошення в репозиторій (прийде на пошту від GitHub).
2. Склонуй і підніми проєкт — див. [Швидкий старт](README.md#швидкий-старт).
3. Для розробки без Docker — [окремий розділ](README.md#розробка-без-docker).

`.env` у репозиторії немає — створи свій з `.env.example`. Секрети в git не комітимо ніколи.

## Гілки

`main` — завжди робоча версія. Напряму в неї не пушимо.

Для кожної задачі — окрема гілка від свіжого `main`:

```bash
git switch main
git pull
git switch -c feature/budget-notifications
```

Префікси: `feature/` — нова функція, `fix/` — виправлення, `refactor/`, `docs/`, `chore/` — решта.

## Коміти

Формат [Conventional Commits](https://www.conventionalcommits.org/): `тип(область): що зроблено`.

```
feat(budgets): add copy from previous month
fix(auth): rotate refresh token atomically
test(api): cover csv export
```

Типи: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `ci`. Область — `backend`, `frontend` або конкретний модуль.

Один коміт — одна логічна зміна.

## Pull request

1. Перед пушем запусти перевірки локально:
   ```bash
   cd backend && ruff check . && pytest -q
   cd frontend && npm run lint && npm test && npm run build
   ```
2. Запуш гілку і відкрий PR у `main`. Шаблон опису підставиться сам.
3. CI має бути зеленим.
4. Другий учасник переглядає код і апрувить.
5. Мерджимо через **Squash and merge**, гілку видаляємо.

## Якщо змінюєш…

- **моделі** — згенеруй міграцію (`alembic revision --autogenerate -m "..."`) і закоміть її разом зі змінами;
- **змінні оточення** — онови `.env.example` і таблицю в README;
- **API** — онови виклики у `frontend/src/api/endpoints.js`.
