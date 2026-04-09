"""
Seed script — cria os dois utilizadores administradores.

Uso:
    cd biblioteca/
    python -m app.scripts.seed_admins
"""
import sys
import os

# Garante que o root do projecto está no path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.database import SessionLocal, engine, Base
import app.models.user      # noqa — registar modelo
import app.models.log       # noqa

from app.services.auth_service import get_user_by_email, create_user

ADMINS = [
    {
        "email": "anneheschkel@admin.com",
        "password": "Fr@nkFr@nk!!!",
        "full_name": "Anne Heschkel",
    },
    {
        "email": "filipaheschkel@admin.com",
        "password": "Ann€Ann€???",
        "full_name": "Filipa Heschkel",
    },
]


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        for admin_data in ADMINS:
            existing = get_user_by_email(db, admin_data["email"])
            if existing:
                print(f"[SKIP] Utilizador já existe: {admin_data['email']}")
                continue

            user = create_user(
                db,
                email=admin_data["email"],
                password=admin_data["password"],
                full_name=admin_data["full_name"],
                is_superadmin=True,
            )
            print(f"[OK]   Criado admin: {user.email} (id={user.id})")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
