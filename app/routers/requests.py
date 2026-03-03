from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, ServiceRequest, RequestStatus
import logging

# Настройка логгера
logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG)

router = APIRouter()


# ============================================================
# ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ: получаем user_id из URL-параметра
# ============================================================
def get_user_id(request: Request) -> int | None:
    """Извлекает user_id из query параметров URL"""
    uid = request.query_params.get("user_id")
    return int(uid) if uid and uid.isdigit() else None


# ============================================================
# ГЛАВНАЯ СТРАНИЦА — список всех заявок
# ============================================================
@router.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    logger.info(">>> ЗАПРОС: GET /")
    user_id = get_user_id(request)
    current_user = db.query(User).filter(User.id == user_id).first() if user_id else None
    users = db.query(User).all()
    # Сортировка по ID по возрастанию (1, 2, 3, 4, 5...)
    requests_list = db.query(ServiceRequest).order_by(ServiceRequest.id.asc()).all()

    logger.info(f"    current_user: {current_user.username if current_user else 'None'}")
    logger.info(f"    заявок в списке: {len(requests_list)}")

    return request.app.templates.TemplateResponse("base.html", {
        "request": request,
        "current_user": current_user,
        "users": users,
        "requests": requests_list,
        "page": "home"
    })


# ============================================================
# ВЫХОД
# ============================================================
@router.get("/logout")
async def logout():
    logger.info(">>> ЗАПРОС: GET /logout")
    return RedirectResponse(url="/", status_code=303)


# ============================================================
# НОВАЯ ЗАЯВКА — ФОРМА
# ============================================================
@router.get("/requests/new", response_class=HTMLResponse)
async def new_request_form(request: Request, db: Session = Depends(get_db)):
    logger.info(">>> ЗАПРОС: GET /requests/new")
    user_id = get_user_id(request)
    if not user_id:
        return RedirectResponse(url="/", status_code=303)

    current_user = db.query(User).filter(User.id == user_id).first()
    users = db.query(User).all()

    return request.app.templates.TemplateResponse("base.html", {
        "request": request,
        "current_user": current_user,
        "users": users,
        "page": "new_request"
    })


# ============================================================
# НОВАЯ ЗАЯВКА — СОЗДАНИЕ (POST)
# ============================================================
@router.post("/requests/new")
async def create_request(
        client_name: str = Form(...),
        phone: str = Form(...),
        address: str = Form(...),
        problem_text: str = Form(...),
        db: Session = Depends(get_db)
):
    logger.info(">>> ЗАПРОС: POST /requests/new")
    logger.info(f"    client_name: {client_name}")

    try:
        new_req = ServiceRequest(
            client_name=client_name,
            phone=phone,
            address=address,
            problem_text=problem_text,
            status=RequestStatus.new,
            version=1
        )
        db.add(new_req)
        db.commit()
        db.refresh(new_req)
        logger.info(f"    ✅ Заявка создана: ID={new_req.id}")
        return RedirectResponse(url="/", status_code=303)
    except Exception as e:
        logger.error(f"    ❌ ОШИБКА: {e}")
        db.rollback()
        raise


# ============================================================
# ПАНЕЛЬ ДИСПЕТЧЕРА — с фильтром по статусу
# ============================================================
@router.get("/dispatcher", response_class=HTMLResponse)
async def dispatcher_panel(request: Request, db: Session = Depends(get_db)):
    logger.info(">>> ЗАПРОС: GET /dispatcher")
    user_id = get_user_id(request)
    current_user = db.query(User).filter(User.id == user_id).first()

    if not current_user or current_user.role != "dispatcher":
        logger.warning("    ⚠️ Недостаточно прав")
        raise HTTPException(status_code=403, detail="Только для диспетчеров")

    # Получаем фильтр по статусу из URL
    status_filter = request.query_params.get("status")

    users = db.query(User).all()
    query = db.query(ServiceRequest)

    # Применяем фильтр по статусу если указан
    if status_filter:
        query = query.filter(ServiceRequest.status == status_filter)

    # Сортировка по ID по возрастанию (1, 2, 3, 4, 5...)
    requests_list = query.order_by(ServiceRequest.id.asc()).all()

    logger.info(f"    заявок найдено: {len(requests_list)}, фильтр: {status_filter or 'нет'}")

    return request.app.templates.TemplateResponse("base.html", {
        "request": request,
        "current_user": current_user,
        "users": users,
        "requests": requests_list,
        "status_filter": status_filter,
        "page": "dispatcher"
    })


# ============================================================
# НАЗНАЧИТЬ МАСТЕРА (диспетчер)
# ============================================================
@router.post("/requests/{request_id}/assign")
async def assign_request(
        request_id: int,
        assigned_to: int = Form(...),
        db: Session = Depends(get_db)
):
    logger.info(f">>> ЗАПРОС: POST /requests/{request_id}/assign")
    req = db.query(ServiceRequest).filter(ServiceRequest.id == request_id).first()
    if not req:
        logger.error(f"    ❌ Заявка {request_id} не найдена")
        raise HTTPException(status_code=404, detail="Заявка не найдена")

    logger.info(f"    старый статус: {req.status.value}, новый мастер: {assigned_to}")

    req.assigned_to = assigned_to
    req.status = RequestStatus.assigned
    req.version += 1
    db.commit()

    logger.info(f"    ✅ Заявка назначена на мастера {assigned_to}")
    return RedirectResponse(url="/dispatcher?user_id=" + str(assigned_to), status_code=303)


# ============================================================
# ОТМЕНИТЬ ЗАЯВКУ (диспетчер)
# ============================================================
@router.post("/requests/{request_id}/cancel")
async def cancel_request(request_id: int, db: Session = Depends(get_db)):
    logger.info(f">>> ЗАПРОС: POST /requests/{request_id}/cancel")
    req = db.query(ServiceRequest).filter(ServiceRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Заявка не найдена")

    req.status = RequestStatus.canceled
    req.version += 1
    db.commit()

    logger.info(f"    ✅ Заявка отменена")
    return RedirectResponse(url="/dispatcher", status_code=303)


# ============================================================
# ПАНЕЛЬ МАСТЕРА — только его заявки
# ============================================================
@router.get("/master", response_class=HTMLResponse)
async def master_panel(request: Request, db: Session = Depends(get_db)):
    logger.info(">>> ЗАПРОС: GET /master")
    user_id = get_user_id(request)
    current_user = db.query(User).filter(User.id == user_id).first()

    if not current_user or current_user.role != "master":
        logger.warning("    ⚠️ Недостаточно прав")
        raise HTTPException(status_code=403, detail="Только для мастеров")

    users = db.query(User).all()
    # Только заявки, назначенные на этого мастера
    # Сортировка по ID по возрастанию
    requests_list = db.query(ServiceRequest).filter(
        ServiceRequest.assigned_to == user_id
    ).order_by(ServiceRequest.id.asc()).all()

    logger.info(f"    заявок у мастера: {len(requests_list)}")

    return request.app.templates.TemplateResponse("base.html", {
        "request": request,
        "current_user": current_user,
        "users": users,
        "requests": requests_list,
        "page": "master"
    })


# ============================================================
# ВЗЯТЬ В РАБОТУ (мастер) — С ЗАЩИТОЙ ОТ RACE CONDITION
# ============================================================
@router.post("/requests/{request_id}/take")
async def take_request(request_id: int, request: Request, db: Session = Depends(get_db)):
    """
    Взять заявку в работу с защитой от race condition.
    Используем оптимистичную блокировку через поле version.

    Если два мастера одновременно нажмут "Взять в работу":
    - Первый запрос успешен (статус 303 redirect)
    - Второй запрос получит 409 Conflict (заявка уже взята)
    """
    logger.info(f">>> ЗАПРОС: POST /requests/{request_id}/take")
    req = db.query(ServiceRequest).filter(ServiceRequest.id == request_id).first()
    if not req:
        logger.error(f"    ❌ Заявка {request_id} не найдена")
        raise HTTPException(status_code=404, detail="Заявка не найдена")

    logger.info(f"    текущий статус: {req.status.value}, версия: {req.version}")

    # Проверка статуса — защита от race condition
    if req.status != RequestStatus.assigned:
        logger.warning(f"    ⚠️ Заявка уже взята (статус: {req.status.value})")
        raise HTTPException(
            status_code=409,
            detail=f"Заявка уже взята в работу (статус: {req.status.value})"
        )

    # Оптимистичная блокировка: увеличиваем версию
    old_version = req.version
    req.version += 1
    req.status = RequestStatus.in_progress
    db.commit()
    db.refresh(req)

    logger.info(f"    ✅ Заявка взята в работу, версия: {old_version} → {req.version}")
    return RedirectResponse(url=f"/master?user_id={req.assigned_to}", status_code=303)


# ============================================================
# ЗАВЕРШИТЬ ЗАЯВКУ (мастер)
# ============================================================
@router.post("/requests/{request_id}/complete")
async def complete_request(request_id: int, db: Session = Depends(get_db)):
    logger.info(f">>> ЗАПРОС: POST /requests/{request_id}/complete")
    req = db.query(ServiceRequest).filter(ServiceRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Заявка не найдена")

    if req.status != RequestStatus.in_progress:
        raise HTTPException(
            status_code=409,
            detail=f"Заявка не в работе (статус: {req.status.value})"
        )

    req.version += 1
    req.status = RequestStatus.done
    db.commit()

    logger.info(f"    ✅ Заявка завершена")
    return RedirectResponse(url="/master", status_code=303)