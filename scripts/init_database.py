#!/usr/bin/env python3
"""Initialize database tables for Adamani AI RAG."""
import asyncio
import os
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import create_engine, text, inspect
from src.adamani_ai_rag.database.base import Base
from src.adamani_ai_rag.database.models import User, Organization, OrganizationMember, Document
from src.adamani_ai_rag.config import get_settings


async def init_database():
    """Initialize database tables."""
    settings = get_settings()

    print("=" * 60)
    print("🗄️  Database Initialization Script")
    print("=" * 60)

    # Convert asyncpg URL to sync psycopg2 URL for create_all
    db_url = settings.database_url
    if 'asyncpg' in db_url:
        db_url = db_url.replace('+asyncpg', '')

    print(f"\n📍 Database URL: {db_url[:30]}...{db_url[-20:]}")

    try:
        # Create engine
        print("\n🔧 Creating database engine...")
        engine = create_engine(db_url)

        # Test connection
        print("🔌 Testing database connection...")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ Connected to PostgreSQL: {version[:50]}...")

        # Check existing tables
        print("\n📋 Checking existing tables...")
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()

        if existing_tables:
            print(f"📊 Found {len(existing_tables)} existing tables:")
            for table in existing_tables:
                print(f"   - {table}")
        else:
            print("📭 No existing tables found")

        # Create all tables
        print("\n🏗️  Creating database tables...")
        Base.metadata.create_all(engine)
        print("✅ Tables created successfully!")

        # Verify tables were created
        print("\n✅ Verifying tables...")
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        print(f"📊 Database now has {len(tables)} tables:")
        for table in tables:
            print(f"   ✓ {table}")

        # Verify required tables exist
        required_tables = ['users', 'organizations', 'organization_members', 'documents']
        missing_tables = [t for t in required_tables if t not in tables]

        if missing_tables:
            print(f"\n❌ ERROR: Missing required tables: {missing_tables}")
            return False

        print("\n" + "=" * 60)
        print("🎉 Database initialization complete!")
        print("=" * 60)
        print("\n✅ Your backend is ready to accept requests!")
        print("✅ Try registering a user from your frontend now!")

        return True

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Run async function
    success = asyncio.run(init_database())
    sys.exit(0 if success else 1)
