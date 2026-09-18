import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from database import async_session, engine
from models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Uses passlib bcrypt to match main.py"""
    return pwd_context.hash(password)

async def seed_data():
    """Populates the database with 5 test users."""
    async with async_session() as session:
        users_to_create = [
            User(
                username="algo_master",
                email="master@test.com",
                hashed_password=hash_password("pass123"),
                elo_rating=2500,
                college_campus="MIT",
                academic_section="CS101",
                equipped_perk="syntax_shield"
            ),
            User(
                username="code_ninja",
                email="ninja@test.com",
                hashed_password=hash_password("pass123"),
                elo_rating=1800,
                college_campus="Stanford",
                academic_section="CS202",
                equipped_perk="haste"
            ),
            User(
                username="bug_hunter",
                email="hunter@test.com",
                hashed_password=hash_password("pass123"),
                elo_rating=1450,
                college_campus="MIT",
                academic_section="CS101",
                equipped_perk="extra_time"
            ),
            User(
                username="noob_coder",
                email="noob@test.com",
                hashed_password=hash_password("pass123"),
                elo_rating=900,
                college_campus="Stanford",
                academic_section="CS101",
                equipped_perk="none"
            ),
            User(
                username="script_kiddie",
                email="kiddie@test.com",
                hashed_password=hash_password("pass123"),
                elo_rating=1200,
                college_campus="Berkeley",
                academic_section="CS202",
                equipped_perk="syntax_shield"
            )
        ]
        
        # Adding users to the session
        session.add_all(users_to_create)
        
        try:
            await session.commit()
            print(f"Successfully seeded {len(users_to_create)} test users.")
        except Exception as e:
            await session.rollback()
            print(f"Failed to seed data. Ensure schema is loaded. Error: {e}")

async def main():
    print("Starting database seed...")
    await seed_data()
    # Dispose the engine to close connections cleanly
    await engine.dispose()
    print("Seed complete.")

if __name__ == "__main__":
    asyncio.run(main())
