import asyncio
import sys

from sqlalchemy.future import select

from database import AsyncSessionLocal
from auth import hash_password
import models


async def main():
    email = input("Email nowego admina: ").strip().lower()
    password = input("Hasło: ")

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(models.User).where(models.User.email == email))
        existing = result.scalar_one_or_none()

        if existing:
            existing.role = "ADMIN"
            print(f"Użytkownik {email} już istniał — ustawiono rolę ADMIN.")
        else:
            new_admin = models.User(
                email=email,
                hashed_password=hash_password(password),
                role="ADMIN",
            )
            db.add(new_admin)
            print(f"Utworzono nowego admina: {email}")

        await db.commit()


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(main())