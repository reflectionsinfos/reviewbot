"""
Quickstart script for AI Tech & Delivery Review Agent
Sets up the database and creates a demo user
"""
import asyncio
import os
from pathlib import Path


async def setup_database():
    """Initialize database tables"""
    from app.db.session import init_db
    print("📦 Initializing database...")
    await init_db()
    print("✅ Database initialized!")


async def create_demo_user():
    """Create a demo user for testing"""
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.db.session import AsyncSessionLocal
    from app.models import User
    from passlib.context import CryptContext
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    async with AsyncSessionLocal() as session:
        # Check if admin user exists
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.email == "admin@example.com"))
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(
                email="admin@example.com",
                full_name="Admin User",
                hashed_password=pwd_context.hash("admin123"),
                role="admin"
            )
            session.add(user)
            await session.commit()
            print("✅ Demo user created!")
            print("   Email: admin@example.com")
            print("   Password: admin123")
            print("   ⚠️  Change this password in production!")
        else:
            print("ℹ️  Demo user already exists")


async def create_directories():
    """Create required directories"""
    dirs = ["uploads", "reports", "chroma_db", "uploads/voice"]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {dir_path}")


def create_env_file():
    """Create .env file if it doesn't exist"""
    env_path = Path(".env")
    
    if not env_path.exists():
        env_content = """# AI Tech & Delivery Review Agent Configuration

# OpenAI API Key (required for LLM and voice features)
OPENAI_API_KEY=your-openai-api-key-here

# Database
DATABASE_URL="sqlite+aiosqlite:///./reviews.db"

# Security (CHANGE IN PRODUCTION!)
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application Settings
APP_NAME="AI Tech & Delivery Review Agent"
DEBUG=true
VOICE_ENABLED=true
REQUIRE_HUMAN_APPROVAL=true

# Storage
CHROMA_PERSIST_DIR="./chroma_db"
UPLOAD_DIR="./uploads"
REPORTS_DIR="./reports"
"""
        with open(env_path, 'w') as f:
            f.write(env_content)
        print("✅ Created .env file")
        print("   ⚠️  Edit .env and add your OpenAI API key!")
    else:
        print("ℹ️  .env file already exists")


async def main():
    """Main setup function"""
    print("=" * 60)
    print("🚀 AI Tech & Delivery Review Agent - Setup")
    print("=" * 60)
    print()
    
    # Create directories
    create_directories()
    print()
    
    # Create env file
    create_env_file()
    print()
    
    # Setup database
    await setup_database()
    print()
    
    # Create demo user
    await create_demo_user()
    print()
    
    print("=" * 60)
    print("✅ Setup complete!")
    print()
    print("Next steps:")
    print("1. Edit .env and add your OPENAI_API_KEY")
    print("2. Run: uvicorn main:app --reload")
    print("3. Open: http://localhost:8000/docs")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
