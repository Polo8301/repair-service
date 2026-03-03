# 🔧 Ремонтная служба (Repair Service)

Веб-сервис для приёма и обработки заявок в ремонтную службу. Поддерживает роли диспетчера и мастера с защитой от race condition при взятии заявок в работу.

---

## 📋 Оглавление

- [Технологии](#-технологии)
- [Структура проекта](#-структура-проекта)
- [Быстрый старт](#-быстрый-старт)
- [Тестовые пользователи](#-тестовые-пользователи)
- [Основные страницы](#-основные-страницы)
- [Проверка race condition](#-проверка-race-condition)
- [Автотесты](#-автотесты)
- [API Endpoints](#-api-endpoints)
- [Статусы заявок](#-статусы-заявок)

---

## 🛠 Технологии

| Компонент | Технология |
|-----------|------------|
| Язык | Python 3.11+ |
| Фреймворк | FastAPI |
| Шаблонизатор | Jinja2 |
| База данных | SQLite |
| ORM | SQLAlchemy |
| Тесты | pytest |
| Сервер | Uvicorn |

---

## 📁 Структура проекта

repair-service/
├── app/
│ ├── init.py
│ ├── main.py # Точка входа FastAPI
│ ├── models.py # SQLAlchemy модели
│ ├── schemas.py # Pydantic схемы
│ ├── database.py # Настройки БД
│ ├── routers/
│ │ └── requests.py # Роуты для заявок
│ └── templates/
│ └── base.html # HTML шаблоны
├── tests/
│ └── test_race_condition.py # Автотесты (6 тестов)
├── init_db.py # Инициализация и сиды БД
├── requirements.txt # Зависимости
├── README.md # Этот файл
├── DECISIONS.md # Ключевые решения
├── PROMPTS.md # История запросов к AI
├── race_test.ps1 # Скрипт проверки race condition
└── screenshots/ # Скриншоты интерфейса


---

## 🚀 Быстрый старт

### Шаг 1: Клонирование репозитория

```bash
git clone https://github.com/your-username/repair-service.git
cd repair-service

Шаг 2: Создание виртуального окружения
python -m venv .venv
.venv\Scripts\Activate.ps1

python3 -m venv .venv
source .venv/bin/activate

Шаг 3: Установка зависимостей
powershell
1
pip install -r requirements.txt
Шаг 4: Инициализация базы данных (сиды)
powershell
1
python init_db.py
Ожидаемый вывод:
1
✅ База данных инициализирована, сиды добавлены
Шаг 5: Запуск сервера
powershell
1
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
Шаг 6: Открыть в браузере
1
http://localhost:8001
👥 Тестовые пользователи
После запуска init_db.py в базе создаются следующие пользователи:
Логин
Роль
ID
Описание
dispatcher1
dispatcher
1
Диспетчер (назначает мастеров)
master1
master
2
Мастер №1 (выполняет заявки)
master2
master
3
Мастер №2 (выполняет заявки)
Как войти
Откройте http://localhost:8001
Выберите пользователя из выпадающего списка
Нажмите "Войти"
📄 Основные страницы
Страница
URL
Описание
Главная
/
Список всех заявок
Создание заявки
/requests/new?user_id=1
Форма создания новой заявки
Панель диспетчера
/dispatcher?user_id=1
Управление заявками (назначить/отменить)
Панель мастера
/master?user_id=2
Работа с назначенными заявками
Статусы заявок
Статус
Описание
Кто меняет
new
Новая заявка
Диспетчер
assigned
Назначена мастеру
Диспетчер
in_progress
В работе
Мастер
done
Завершена
Мастер
canceled
Отменена
Диспетчер
⚡ Проверка Race Condition
Обязательное условие по ТЗ
Действие "Взять в работу" должно быть безопасным при параллельных запросах. Если два мастера одновременно пытаются взять одну заявку:
✅ Первый запрос: успех (303 Redirect)
✅ Второй запрос: отказ (409 Conflict)
Способ 1: Через два терминала (PowerShell)
Шаг 1: Откройте два окна PowerShell
Шаг 2: В обоих окнах перейдите в папку проекта:
powershell
1
Шаг 3: Подготовьте заявку:
Откройте браузер: http://localhost:8001/dispatcher?user_id=1
Найдите заявку со статусом new
Назначьте её на мастера (статус станет assigned)
Запомните ID заявки (например, 3)
Шаг 4: Одновременно выполните в обоих окнах:
powershell
1
Invoke-WebRequest -Uri "http://localhost:8001/requests/3/take" -Method POST -UseBasicParsing
Ожидаемый результат:
Окно
Статус
Сообщение
Первое
200 или 303
Заявка взята в работу
Второе
409
"Заявка уже взята в работу"
Способ 2: Через скрипт race_test.ps1
Запуск:
powershell
1
.\race_test.ps1
Что делает скрипт:
Запрашивает ID заявки
Отправляет два POST-запроса одновременно
Показывает результаты обоих запросов
Проверяет корректность защиты
Ожидаемый вывод:
1234567891011121314151617
🔬 RACE CONDITION TEST
=====================

Enter request ID (must be in 'assigned' status): 3

Request ID: 3
URL: http://localhost:8001

Starting two simultaneous requests...


Способ 3: Через браузер (два окна)
Откройте два разных браузера (или инкогнито)
В обоих войдите как разные мастера (master1 и master2)
Перейдите в панель мастера: /master?user_id=2 и /master?user_id=3
Диспетчером назначьте одну и ту же заявку на обоих мастеров
Одновременно нажмите "Взять в работу" в обоих окнах
Один запрос успешен, второй получает ошибку 409
🧪 Автотесты
Запуск всех тестов
powershell
12
# Убедитесь, что сервер остановлен
pytest tests/test_race_condition.py -v -s
Список тестов (6 тестов)
№
Тест
Что проверяет
1
test_create_request
Создание новой заявки
2
test_assign_master
Назначение мастера диспетчером
3
test_take_request_success
Взять заявку в работу (успех)
4
test_race_condition_take_request
Защита от race condition (2 потока)
5
test_complete_request
Завершение заявки мастером
6
test_cannot_take_already_taken_request
Нельзя взять уже взятую заявку
Ожидаемый результат
12345678
tests/test_race_condition.py::test_create_request PASSED
tests/test_race_condition.py::test_assign_master PASSED
tests/test_race_condition.py::test_take_request_success PASSED
tests/test_race_condition.py::test_race_condition_take_request PASSED
tests/test_race_condition.py::test_complete_request PASSED
tests/test_race_condition.py::test_cannot_take_already_taken_request PASSED

======================== 6 passed in X.XXs =========================
📡 API Endpoints
Метод
Endpoint
Описание
GET
/
Главная страница (список заявок)
GET
/health
Проверка работоспособности
GET
/requests/new
Форма создания заявки
POST
/requests/new
Создать заявку
GET
/dispatcher
Панель диспетчера
POST
/requests/{id}/assign
Назначить мастера
POST
/requests/{id}/cancel
Отменить заявку
GET
/master
Панель мастера
POST
/requests/{id}/take
Взять в работу
POST
/requests/{id}/complete
Завершить заявку
GET
/logout
Выход
📸 Скриншоты
В папке screenshots/ представлены скриншоты основных страниц:
Файл
Страница
1_new_request.png
Форма создания заявки
2_dispatcher.png
Панель диспетчера
3_master.png
Панель мастера
🔧 Требования
Python 3.11+
pip
Установка зависимостей
powershell
1
contents of requirements.txt:
123456789
fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy==2.0.25
python-dotenv==1.0.0
jinja2==3.1.3
python-multipart==0.0.6
pytest==7.4.4
httpx==0.26.0
itsdangerous==2.1.2
📝 Дополнительные документы
Файл
Описание
DECISIONS.md
Ключевые архитектурные решения (5-7 пунктов)
PROMPTS.md
История всех запросов к AI с датами и временем
race_test.ps1
Скрипт для проверки race condition
❓ Troubleshooting
Порт 8001 занят
powershell
12345678
# Найдите процесс
netstat -ano | findstr :8001

# Убейте процесс (замените PID на ваш)
taskkill /F /PID 12345

# Или запустите на другом порту
uvicorn app.main:app --host 0.0.0.0 --port 8002
База данных заблокирована
powershell
123456
# Остановите сервер (Ctrl+C)
# Удалите файл БД
Remove-Item repair_db.sqlite3* -Force

# Инициализируйте заново
python init_db.py
Ошибка при запуске тестов
powershell
123456
📞 Контакты
Разработчик: Юрий
Email: 
GitHub: 

```