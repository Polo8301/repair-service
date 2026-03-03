from app.database import engine, Base, SessionLocal
from app.models import User, ServiceRequest, RequestStatus


def init_db():
    # Создаём таблицы
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    # Сиды пользователей: 1 диспетчер, 2 мастера
    users_data = [
        {"username": "dispatcher1", "role": "dispatcher"},
        {"username": "master1", "role": "master"},
        {"username": "master2", "role": "master"},
    ]

    for user_data in users_data:  # ← Исправлено: users_data + двоеточие
        existing = db.query(User).filter(User.username == user_data["username"]).first()
        if not existing:
            user = User(**user_data)
            db.add(user)

    db.commit()

    # Тестовые заявки
    test_requests = [
        {
            "client_name": "Иван Петров",
            "phone": "+79001234567",
            "address": "ул. Ленина, 10, кв. 5",
            "problem_text": "Не работает розетка на кухне",
            "status": RequestStatus.new,
        },
        {
            "client_name": "Мария Сидорова",
            "phone": "+79007654321",
            "address": "пр. Мира, 25, оф. 101",
            "problem_text": "Протекает кран в ванной",
            "status": RequestStatus.new,
        },
    ]

    for req_data in test_requests:
        existing = db.query(ServiceRequest).filter(
            ServiceRequest.client_name == req_data["client_name"],
            ServiceRequest.phone == req_data["phone"]
        ).first()
        if not existing:
            req = ServiceRequest(**req_data)
            db.add(req)

    db.commit()
    db.close()
    print("✅ База данных инициализирована, сиды добавлены")


if __name__ == "__main__":
    init_db()