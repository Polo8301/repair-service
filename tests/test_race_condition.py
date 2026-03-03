"""
Автотесты для проверки функционала и защиты от race condition.
Запуск: pytest tests/test_race_condition.py -v
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import engine, Base, SessionLocal
from app.models import User, ServiceRequest, RequestStatus
import threading
import time

# Тестовый клиент FastAPI
client = TestClient(app)

# Глобальные переменные для результатов потоков
race_results = []


@pytest.fixture(scope="function", autouse=True)
def setup_and_teardown_db():
    """
    Фикстура: перед каждым тестом создаёт таблицы и тестовые данные,
    после теста — очищает базу.
    """
    # Создаём таблицы
    Base.metadata.create_all(bind=engine)

    # Создаём тестовых пользователей
    db = SessionLocal()
    dispatcher = User(username="test_dispatcher", role="dispatcher")
    master1 = User(username="test_master1", role="master")
    master2 = User(username="test_master2", role="master")
    db.add_all([dispatcher, master1, master2])
    db.commit()

    # Сохраняем ID для тестов
    test_data = {
        "dispatcher_id": dispatcher.id,
        "master1_id": master1.id,
        "master2_id": master2.id,
    }

    yield test_data

    # Очищаем базу после теста
    db.close()
    Base.metadata.drop_all(bind=engine)


# ============================================================
# ТЕСТ 1: Создание заявки
# ============================================================
def test_create_request(setup_and_teardown_db):
    """Проверка создания новой заявки"""
    response = client.post(
        "/requests/new",
        data={
            "client_name": "Тест Клиент",
            "phone": "+79991234567",
            "address": "г. Тестовск, ул. Примерная, 1",
            "problem_text": "Тестовая проблема для проверки",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303  # Redirect после POST

    # Проверяем, что заявка появилась в БД
    db = SessionLocal()
    req = db.query(ServiceRequest).filter(
        ServiceRequest.client_name == "Тест Клиент"
    ).first()
    db.close()

    assert req is not None
    assert req.status == RequestStatus.new
    assert req.version == 1
    print("✅ Тест 1 пройден: Создание заявки работает")


# ============================================================
# ТЕСТ 2: Назначение мастера диспетчером
# ============================================================
def test_assign_master(setup_and_teardown_db):
    """Проверка назначения мастера диспетчером"""
    db = SessionLocal()

    # Создаём заявку
    req = ServiceRequest(
        client_name="Клиент для назначения",
        phone="+79991112233",
        address="г. Тест, ул. Тестовая, 1",
        problem_text="Нужно назначить мастера",
        status=RequestStatus.new,
        version=1,
    )
    db.add(req)
    db.commit()
    request_id = req.id
    master_id = setup_and_teardown_db["master1_id"]
    db.close()

    # Назначаем мастера
    response = client.post(
        f"/requests/{request_id}/assign",
        data={"assigned_to": master_id},
        follow_redirects=False,
    )

    assert response.status_code == 303

    # Проверяем результат в БД
    db = SessionLocal()
    req = db.query(ServiceRequest).filter(ServiceRequest.id == request_id).first()
    db.close()

    assert req.assigned_to == master_id
    assert req.status == RequestStatus.assigned
    assert req.version == 2
    print("✅ Тест 2 пройден: Назначение мастера работает")


# ============================================================
# ТЕСТ 3: Взять в работу (успешный сценарий)
# ============================================================
def test_take_request_success(setup_and_teardown_db):
    """Проверка успешного взятия заявки в работу"""
    db = SessionLocal()
    master_id = setup_and_teardown_db["master1_id"]

    # Создаём заявку в статусе assigned
    req = ServiceRequest(
        client_name="Клиент для взятия в работу",
        phone="+79994445566",
        address="г. Тест, ул. Рабочая, 5",
        problem_text="Мастер должен взять в работу",
        status=RequestStatus.assigned,
        assigned_to=master_id,
        version=1,
    )
    db.add(req)
    db.commit()
    request_id = req.id
    db.close()

    # Мастер берёт заявку в работу
    response = client.post(
        f"/requests/{request_id}/take",
        follow_redirects=False,
    )

    assert response.status_code == 303

    # Проверяем результат
    db = SessionLocal()
    req = db.query(ServiceRequest).filter(ServiceRequest.id == request_id).first()
    db.close()

    assert req.status == RequestStatus.in_progress
    assert req.version == 2
    print("✅ Тест 3 пройден: Взять в работу (успех) работает")


# ============================================================
# ТЕСТ 4: RACE CONDITION — два мастера одновременно
# ============================================================
def test_race_condition_take_request(setup_and_teardown_db):
    """
    ПРОВЕРКА ЗАЩИТЫ ОТ RACE CONDITION

    Два мастера одновременно пытаются взять одну заявку.
    Ожидаемое поведение:
    - Первый запрос: успех (303)
    - Второй запрос: отказ (409 Conflict)
    """
    db = SessionLocal()
    master1_id = setup_and_teardown_db["master1_id"]
    master2_id = setup_and_teardown_db["master2_id"]

    # Создаём заявку в статусе assigned (назначена, но ещё не взята)
    req = ServiceRequest(
        client_name="Клиент для race condition теста",
        phone="+79997778899",
        address="г. Тест, ул. Конфликтная, 1",
        problem_text="Два мастера хотят взять одновременно",
        status=RequestStatus.assigned,
        assigned_to=master1_id,  # Назначена на master1
        version=1,
    )
    db.add(req)
    db.commit()
    request_id = req.id
    db.close()

    # Функция для потока: пытается взять заявку
    def try_take_request(master_id, result_list, delay=0):
        time.sleep(delay)  # Небольшая задержка для имитации одновременности
        response = client.post(
            f"/requests/{request_id}/take",
            follow_redirects=False,
        )
        result_list.append({
            "master_id": master_id,
            "status_code": response.status_code,
            "response": response.text,
        })

    # Запускаем два потока одновременно
    race_results.clear()
    thread1 = threading.Thread(target=try_take_request, args=(master1_id, race_results, 0))
    thread2 = threading.Thread(target=try_take_request, args=(master2_id, race_results, 0.1))

    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()

    # Анализируем результаты
    success_count = sum(1 for r in race_results if r["status_code"] == 303)
    conflict_count = sum(1 for r in race_results if r["status_code"] == 409)

    print(f"\n📊 Результаты race condition теста:")
    for r in race_results:
        print(f"   Мастер {r['master_id']}: статус {r['status_code']}")

    # Проверяем: один успех, один конфликт
    assert success_count == 1, f"Ожидался 1 успешный запрос, получилось {success_count}"
    assert conflict_count == 1, f"Ожидался 1 конфликт (409), получилось {conflict_count}"

    # Проверяем финальный статус заявки
    db = SessionLocal()
    req = db.query(ServiceRequest).filter(ServiceRequest.id == request_id).first()
    db.close()

    assert req.status == RequestStatus.in_progress
    assert req.version == 2  # Версия увеличилась только один раз

    print("✅ Тест 4 пройден: Защита от race condition работает!")


# ============================================================
# ТЕСТ 5: Завершить заявку
# ============================================================
def test_complete_request(setup_and_teardown_db):
    """Проверка завершения заявки мастером"""
    db = SessionLocal()
    master_id = setup_and_teardown_db["master1_id"]

    # Создаём заявку в статусе in_progress
    req = ServiceRequest(
        client_name="Клиент для завершения",
        phone="+79990001122",
        address="г. Тест, ул. Финальная, 10",
        problem_text="Мастер должен завершить",
        status=RequestStatus.in_progress,
        assigned_to=master_id,
        version=2,
    )
    db.add(req)
    db.commit()
    request_id = req.id
    db.close()

    # Мастер завершает заявку
    response = client.post(
        f"/requests/{request_id}/complete",
        follow_redirects=False,
    )

    assert response.status_code == 303

    # Проверяем результат
    db = SessionLocal()
    req = db.query(ServiceRequest).filter(ServiceRequest.id == request_id).first()
    db.close()

    assert req.status == RequestStatus.done
    assert req.version == 3
    print("✅ Тест 5 пройден: Завершение заявки работает")


# ============================================================
# ТЕСТ 6: Нельзя взять уже взятую заявку (без потоков)
# ============================================================
def test_cannot_take_already_taken_request(setup_and_teardown_db):
    """Проверка, что нельзя взять заявку, которая уже в работе"""
    db = SessionLocal()
    master_id = setup_and_teardown_db["master1_id"]

    # Создаём заявку сразу в статусе in_progress (уже взята)
    req = ServiceRequest(
        client_name="Клиент, заявка уже в работе",
        phone="+79993334455",
        address="г. Тест, ул. Занятая, 7",
        problem_text="Эту заявку уже взяли в работу",
        status=RequestStatus.in_progress,
        assigned_to=master_id,
        version=2,
    )
    db.add(req)
    db.commit()
    request_id = req.id
    db.close()

    # Попытка взять заявку должна вернуть 409
    response = client.post(
        f"/requests/{request_id}/take",
        follow_redirects=False,
    )

    assert response.status_code == 409  # Conflict

    print("✅ Тест 6 пройден: Нельзя взять уже взятую заявку")