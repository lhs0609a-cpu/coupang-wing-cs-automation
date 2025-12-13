from app.database import SessionLocal
from app.models.coupang_account import CoupangAccount

db = SessionLocal()
try:
    accounts = db.query(CoupangAccount).all()
    print(f'Total accounts: {len(accounts)}')
    for a in accounts:
        print(f'  - ID: {a.id}, Vendor: {a.vendor_id}, Active: {a.is_active}')
finally:
    db.close()
