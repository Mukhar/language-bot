#!/usr/bin/env python3
"""
Simple database connection test for Healthcare Bot
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.database import engine, get_db
from app.models import Scenario, Response
from app.config import get_settings
from sqlalchemy import text
import uuid


def test_database_connection():
    """Test database connectivity"""
    print("🔌 Testing database connection...")
    settings = get_settings()
    database_url = settings.get_database_url()
    
    # Mask password in output
    display_url = database_url.split('@')[0] + '@***' if '@' in database_url else database_url
    print(f"Database URL: {display_url}")
    
    try:
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Database connection successful!")
            
            # Check database type
            if "postgresql" in database_url:
                print("📊 Using PostgreSQL (Supabase)")
                # Test PostgreSQL-specific query
                version_result = conn.execute(text("SELECT version()")).fetchone()
                if version_result:
                    print(f"📝 PostgreSQL version: {version_result[0].split(',')[0]}")
            else:
                print("📊 Using SQLite (Development)")
                
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


def test_table_existence():
    """Check if required tables exist"""
    print("\n📋 Checking table existence...")
    
    try:
        with engine.connect() as conn:
            # Check for scenarios table
            try:
                result = conn.execute(text("SELECT COUNT(*) FROM scenarios"))
                count_result = result.fetchone()
                if count_result:
                    scenario_count = count_result[0]
                    print(f"✅ Scenarios table exists with {scenario_count} records")
                else:
                    print("❌ No data returned from scenarios table")
                    return False
            except Exception:
                print("❌ Scenarios table not found")
                return False
            
            # Check for responses table
            try:
                result = conn.execute(text("SELECT COUNT(*) FROM responses"))
                count_result = result.fetchone()
                if count_result:
                    response_count = count_result[0]
                    print(f"✅ Responses table exists with {response_count} records")
                else:
                    print("❌ No data returned from responses table")
                    return False
            except Exception:
                print("❌ Responses table not found")
                return False
                
        return True
        
    except Exception as e:
        print(f"❌ Error checking tables: {e}")
        return False


def test_basic_crud():
    """Test basic CRUD operations"""
    print("\n🧪 Testing basic CRUD operations...")
    
    try:
        # Get database session
        db_gen = get_db()
        db = next(db_gen)
        
        # Create a test scenario
        test_id = str(uuid.uuid4())
        test_scenario = Scenario(
            id=test_id,
            title="Connection Test Scenario",
            description="Testing database connectivity and CRUD operations.",
            category="general",
            difficulty="beginner"
        )
        
        print("  📝 Creating test scenario...")
        db.add(test_scenario)
        db.commit()
        db.refresh(test_scenario)
        print(f"  ✅ Scenario created with ID: {test_scenario.id}")
        
        # Retrieve the scenario
        print("  🔍 Retrieving test scenario...")
        retrieved_scenario = db.query(Scenario).filter(Scenario.id == test_id).first()
        
        if retrieved_scenario and retrieved_scenario.title == "Connection Test Scenario":
            print(f"  ✅ Scenario retrieved successfully: {retrieved_scenario.title}")
        else:
            print("  ❌ Failed to retrieve scenario correctly")
            return False
        
        # Clean up test data
        print("  🧹 Cleaning up test data...")
        db.delete(test_scenario)
        db.commit()
        print("  ✅ Test data cleaned up successfully")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"  ❌ CRUD operations test failed: {e}")
        if 'db' in locals():
            db.rollback()
            db.close()
        return False


def main():
    """Main function to run connection tests"""
    print("🏥 Healthcare Bot - Database Connection Test")
    print("=" * 50)
    
    # Test database connection
    if not test_database_connection():
        print("\n❌ Database connection failed. Please check your configuration.")
        return False
    
    # Test table existence
    if not test_table_existence():
        print("\n❌ Required tables not found. You may need to run migrations.")
        print("💡 Try running: alembic upgrade head")
        return False
    
    # Test basic CRUD operations
    if not test_basic_crud():
        print("\n❌ CRUD operations failed.")
        return False
    
    print("\n🎉 All database tests passed!")
    print("\n📊 Your database is ready for use.")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)