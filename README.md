# Fullstack test task — файловый обменник

MVP сервиса для обмена файлами: пользователь загружает файлы, backend проверяет их на подозрительное содержимое, извлекает базовые metadata и создаёт alerts.

## Run locally

Собрать и запустить локальный stack:

```bash
docker compose -f docker-compose.dev.yml up --build
```

Применить database migrations:

```bash
docker exec -it backend alembic upgrade head
```

Открыть:

- Frontend: http://localhost:3000/test
- Backend API docs: http://localhost:8000/docs

Frontend image собирается с browser-facing `NEXT_PUBLIC_BACKEND_URL=http://localhost:8000`. Здесь намеренно используется `localhost`, а не имя Docker service, потому что этот URL использует браузер.

## Architecture

Backend использует простую layered structure, а не полноценную реализацию Clean Architecture.

```text
HTTP API
  -> services
    -> repositories
      -> SQLAlchemy / PostgreSQL

services
  -> storage
    -> local filesystem

Celery tasks
  -> processing service
```

- `api/`: FastAPI routers, request/response concerns и преобразование ошибок в HTTP.
- `services/`: application flow и границы транзакций.
- `repositories/`: SQLAlchemy queries и persistence operations.
- `storage/`: операции с локальными файлами: path, save, read, exists и delete.
- `core/`: общая configuration и SQLAlchemy engine/sessionmaker.
- `tasks.py`: тонкая Celery orchestration вокруг функций processing service.

Frontend structure:

```text
page.tsx
  -> api layer
    -> backend

page.tsx
  -> presentational components
```

`page.tsx` всё ещё владеет page state и orchestration. API calls находятся в `src/api`, backend DTO types — в `src/types/api.ts`, а UI-блоки вынесены в presentational components, которые не делают HTTP calls. Включён strict TypeScript.

## Key fixes

### Delete consistency

Изначально physical file удалялся до database delete. Если `Alert` всё ещё ссылался на `StoredFile`, database delete мог упасть на foreign key уже после удаления файла с диска.

Текущая последовательность delete:

1. Удалить alerts для файла.
2. Удалить file row.
3. Закоммитить database transaction.
4. Удалить physical file.

Database остаётся source of truth. Если filesystem delete падает после успешного database commit, database остаётся консистентной, а orphan physical file может остаться для последующей cleanup.

### Upload consistency

Если upload успел сохранить physical file, но database insert/commit упал до успешного завершения, сохранённый файл очищается, а исходная exception не скрывается.

### Upload memory and event-loop optimization

Это основная bonus optimization.

Предыдущий upload path читал весь файл в память и писал его синхронно:

```python
await upload_file.read()
Path.write_bytes(...)
```

Текущее поведение:

- upload читается chunk by chunk;
- default chunk size — 1 MiB;
- размер файла считается во время streaming;
- blocking disk writes вынесены через `asyncio.to_thread`;
- partial files удаляются при ошибке записи.

Так memory usage в upload path не растёт вместе с полным размером файла. Benchmark numbers не заявляются.

### Background processing

Celery tasks теперь являются тонкими orchestration functions. Scan, metadata extraction и alert creation находятся в `services/processing.py`. Переиспользуемого global event loop больше нет; каждая task использует `asyncio.run(...)`, а SQLAlchemy async engine после этого dispose-ится, чтобы pooled async connections не переходили между event loops.

### Frontend

- включён strict TypeScript;
- API layer вынесен из `page.tsx`;
- UI разбит на `FilesTable`, `AlertsTable` и `UploadFileModal`;
- улучшены loading, refresh, empty, error и submit states;
- добавлен практичный accessibility pass;
- добавлены тесты на Jest + React Testing Library.

### Reproducible Docker

- убрана зависимость frontend Docker build от отсутствующего `.env.production`;
- frontend build получает `NEXT_PUBLIC_BACKEND_URL` через Docker build arg;
- Redis env naming приведён к `REDIS_URL`;
- Docker Compose build был проверен локально.

## Quality checks

Backend:

```bash
cd backend
uv sync --extra dev --frozen
uv run --extra dev pytest tests
uv run --extra dev ruff check src tests
uv run --extra dev ruff format --check src tests
uv run --extra dev mypy src tests
```

Frontend:

```bash
cd frontend
npm ci
npm test -- --runInBand
npx tsc --noEmit
npm run build
```

Текущие verified test counts:

- backend: 22 pytest tests;
- frontend: 13 Jest/RTL tests.

GitHub Actions запускает backend и frontend jobs независимо на `push` и `pull_request`.

## Technical decisions and tradeoffs

- Local filesystem storage оставлен, потому что это MVP test task. В production deployment, скорее всего, стоило бы использовать object storage.
- Database и filesystem operations нельзя сделать по-настоящему atomic без дополнительного механизма.
- Celery processing steps сохраняют отдельные database transactions, что соответствует границам tasks и оставляет workflow простым.
- Processing всё ещё делает local file reads для metadata extraction; оптимизированы только upload writes, чтобы они не блокировали request event loop.
- React Query, Redux, Context и feature-folder architecture не добавлялись, потому что page-local state достаточно для этого scope.
- Deployment и production orchestration не добавлялись, кроме локального Docker Compose и CI checks.

## Project structure

```text
backend/src/
  api/
  core/
  repositories/
  services/
  storage/
  app.py
  tasks.py

frontend/src/
  api/
  app/
  components/
  types/

.github/workflows/ci.yml
docker-compose.dev.yml
```

## Tests

Backend tests покрывают:

- file API upload/list/get/update/delete/download behavior;
- 404 cases;
- delete consistency for files referenced by alerts;
- streaming upload behavior and cleanup paths;
- processing clean/suspicious/failed paths;
- alerts listing and creation behavior.

Frontend tests покрывают:

- files and alerts tables;
- loading and empty states;
- upload modal interactions and submitting state;
- page initial load, successful upload refresh and API error display.

## Notes

Проект остаётся MVP. В нём намеренно нет object storage, distributed transactions, сложного frontend state management, deployment pipelines и coverage thresholds. Цель — читаемый refactor с tests, CI и воспроизводимым локальным запуском, а не production platform.
