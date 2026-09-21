import asyncio
from app.db.base import SessionLocal
from app.models.credit_request import CreditRequest
from app.models.user import User
from app.routers.admin.credit_requests import _out

db = SessionLocal()
try:
    query = db.query(CreditRequest, User).join(User, User.id == CreditRequest.user_id)
    total = query.count()
    rows = query.order_by(CreditRequest.id.desc()).limit(100).offset(0).all()
    print("Total:", total)
    items = [_out(r, u) for r, u in rows]
    print("Items:", len(items))
except Exception as e:
    import traceback
    traceback.print_exc()
finally:
    db.close()
