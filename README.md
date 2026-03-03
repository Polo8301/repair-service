# 🔧 Ремонтная служба (Repair Service)

Веб-сервис для приёма и обработки заявок в ремонтную службу. Поддерживает роли диспетчера и мастера с защитой от race condition при взятии заявок в работу.

> **Статус:** ✅ Готово к сдаче  
> **Автор:** Юрий  
> **Дата:** 2026-03-04

---

## 📋 Оглавление

1. [Быстрый старт](#-быстрый-старт)
2. [Тестовые пользователи](#-тестовые-пользователи)
3. [Основные страницы](#-основные-страницы)
4. [Статусы заявок](#-статусы-заявок)
5. [Проверка Race Condition](#-проверка-race-condition)
6. [Автотесты](#-автотесты)
7. [API Endpoints](#-api-endpoints)
8. [Структура проекта](#-структура-проекта)
9. [Troubleshooting](#-troubleshooting)

---

## 🚀 Быстрый старт

### Предварительные требования

- Python 3.11+
- pip
- Git

### Шаг 1: Клонирование репозитория

```bash
git clone https://github.com/YOUR_USERNAME/repair-service.git
cd repair-service

Шаг 2: Создание виртуального окружения

Windows (PowerShell):
python -m venv .venv
.venv\Scripts\Activate.ps1

Linux/macOS:
python3 -m venv .venv
source .venv/bin/activate

Шаг 3: Установка зависимостей

pip install -r requirements.txt

Шаг 4: Инициализация базы данных

python init_db.py

✅ Ожидаемый вывод:
База данных инициализирована, сиды добавлены

Шаг 5: Запуск сервера

uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

Шаг 6: Открыть в браузере

👉 http://localhost:8001

👥 Тестовые пользователи
После запуска init_db.py создаются следующие пользователи:
Логин dispatcher1 - Роль dispatcher - ID 1 - Описание Диспетчер: назначает мастеров
Логин master1 - Роль master - ID 2 - Описание Мастер №1: выполняет заявки
Логин master2 - Роль master - ID 3 - Описание Мастер №2: выполняет заявки

Как войти в систему
Откройте http://localhost:8001
Выберите пользователя из выпадающего списка
Нажмите "Войти"
📄 Основные страницы
Страница Главная - URL / - Описание Список всех заявок
Страница Создание заявки - URL /requests/new?user_id=1 - Описание Форма создания новой заявки
Страница Панель диспетчера - URL /dispatcher?user_id=1 - Описание Управление заявками: назначить/отменить
Страница Панель мастера - URL /master?user_id=2 - Описание Работа с назначенными заявками

⚡ Проверка Race Condition
Требование: Действие "Взять в работу" должно быть безопасным при параллельных запросах.

Способ 1: Два терминала (PowerShell):
# Терминал 1 и Терминал 2 (запустить одновременно):
Invoke-WebRequest -Uri "http://localhost:8001/requests/3/take" -Method POST -UseBasicParsing

Подготовка:
Откройте /dispatcher?user_id=1
Найдите заявку со статусом new
Назначьте её на мастера (статус станет assigned)
Запомните ID заявки (например, 3)

Способ 2: Скрипт race_test.ps1:
.\race_test.ps1

Что делает скрипт:
Запрашивает ID заявки
Отправляет два POST-запроса с задержкой 100мс
Показывает результаты и валидирует защиту
Способ 3: Браузер (два окна)
Откройте два браузера (или инкогнито)
Войдите как master1 и master2
Диспетчером назначьте одну заявку на обоих мастеров
Одновременно нажмите "Взять в работу"

🧪 Автотесты

Запуск:
# Убедитесь, что сервер остановлен
pytest tests/test_race_condition.py -v -s

Ожидаемый результат:
tests/test_race_condition.py::test_create_request PASSED
tests/test_race_condition.py::test_assign_master PASSED
tests/test_race_condition.py::test_take_request_success PASSED
tests/test_race_condition.py::test_race_condition_take_request PASSED
tests/test_race_condition.py::test_complete_request PASSED
tests/test_race_condition.py::test_cannot_take_already_taken_request PASSED

======================== 6 passed in X.XXs =========================

📁 Структура проекта

repair-service/
├── app/
│   ├── __init__.py
│   ├── main.py              # Точка входа FastAPI
│   ├── models.py            # SQLAlchemy модели
│   ├── database.py          # Настройки БД
│   ├── routers/
│   │   └── requests.py      # Роуты для заявок
│   └── templates/
│       └── base.html        # HTML-шаблоны
├── tests/
│   └── test_race_condition.py  # Автотесты (6 тестов)
├── init_db.py               # Инициализация и сиды БД
├── requirements.txt         # Зависимости
├── README.md                # Этот файл
├── DECISIONS.md             # Ключевые решения
├── PROMPTS.md               # История запросов к AI
├── race_test.ps1            # Скрипт проверки race condition
└── screenshots/             # Скриншоты интерфейса







