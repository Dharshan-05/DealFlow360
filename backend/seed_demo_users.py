from app.db.session import SessionLocal
from app.models.user import User
from app.models.role import Role
from app.models.company import Company
from app.core.security import get_password_hash
from sqlalchemy import select

def seed_demo_users():
    db = SessionLocal()
    try:
        company = db.scalars(select(Company)).first()
        admin_role = db.scalars(select(Role).where(Role.name == "Admin")).first()
        customer_role = db.scalars(select(Role).where(Role.name == "Customer Portal")).first()

        # 1. Internal User: Arjun Sharma
        arjun = db.scalars(select(User).where(User.email == "arjun.sharma@dealflow360.io")).first()
        if not arjun:
            arjun = User(
                email="arjun.sharma@dealflow360.io",
                first_name="Arjun",
                last_name="Sharma",
                password_hash=get_password_hash("password123"),
                company_id=company.id if company else None,
                is_active=True,
            )
            if admin_role:
                arjun.roles.append(admin_role)
            db.add(arjun)
            print("Created demo internal user: arjun.sharma@dealflow360.io (password: password123)")
        else:
            print("Demo user arjun.sharma@dealflow360.io already exists")

        # 2. Customer User: Rajesh Kumar
        rajesh = db.scalars(select(User).where(User.email == "rajesh@acme.com")).first()
        if not rajesh:
            rajesh = User(
                email="rajesh@acme.com",
                first_name="Rajesh",
                last_name="Kumar",
                password_hash=get_password_hash("password123"),
                company_id=company.id if company else None,
                is_active=True,
            )
            if customer_role:
                rajesh.roles.append(customer_role)
            db.add(rajesh)
            print("Created demo customer user: rajesh@acme.com (password: password123)")
        else:
            print("Demo user rajesh@acme.com already exists")

        db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    seed_demo_users()
