#!/usr/bin/env python3
"""
Database migration and testing script for Healthcare Bot
Supports both SQLite (development) and Supabase PostgreSQL (production)
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.database import engine, create_tables, get_db
from app.models import Scenario, Response
from app.config import get_settings
from sqlalchemy.orm import Session
import uuid


def test_database_connection():
    """Test database connectivity"""
    print("Testing database connection...")
    settings = get_settings()
    database_url = settings.get_database_url()
    
    print(f"Database URL: {database_url.split('@')[0]}@***" if '@' in database_url else database_url)
    
    try:
        # Test connection
        with engine.connect() as conn:
            from sqlalchemy import text
            result = conn.execute(text("SELECT 1"))
            print("✅ Database connection successful!")
            
            # Check database type
            if "postgresql" in database_url:
                print("📊 Using PostgreSQL (Supabase)")
            else:
                print("📊 Using SQLite (Development)")
                
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


def run_migrations():
    """Run Alembic migrations"""
    print("\nRunning database migrations...")
    try:
        import subprocess
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        
        if result.returncode == 0:
            print("✅ Migrations completed successfully!")
            print(result.stdout)
        else:
            print(f"❌ Migration failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to run migrations: {e}")
        return False
        
    return True


def test_scenario_operations():
    """Test scenario CRUD operations"""
    print("\nTesting scenario operations...")
    
    try:
        # Get database session
        db_gen = get_db()
        db = next(db_gen)
        
        # Create a test scenario
        test_scenario = Scenario(
            id=str(uuid.uuid4()),
            title="Test Scenario - Database Migration",
            description="This is a test scenario to verify database operations work correctly.",
            category="general",
            difficulty="beginner"
        )
        
        print("Creating test scenario...")
        db.add(test_scenario)
        db.commit()
        db.refresh(test_scenario)
        print(f"✅ Scenario created with ID: {test_scenario.id}")
        
        # Retrieve the scenario
        print("Retrieving test scenario...")
        retrieved_scenario = db.query(Scenario).filter(Scenario.id == test_scenario.id).first()
        
        if retrieved_scenario:
            print(f"✅ Scenario retrieved successfully: {retrieved_scenario.title}")
        else:
            print("❌ Failed to retrieve scenario")
            return False
            
        # Create a test response
        test_response = Response(
            id=str(uuid.uuid4()),
            scenario_id=test_scenario.id,
            response_text="This is a test response to verify the relationship works.",
            score=8.5,
            feedback="Good test response!"
        )
        
        print("Creating test response...")
        db.add(test_response)
        db.commit()
        db.refresh(test_response)
        print(f"✅ Response created with ID: {test_response.id}")
        
        # Clean up test data
        print("Cleaning up test data...")
        db.delete(test_response)
        db.delete(test_scenario)
        db.commit()
        print("✅ Test data cleaned up")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Scenario operations test failed: {e}")
        if 'db' in locals():
            db.rollback()
            db.close()
        return False


def main():
    """Main function to run all tests"""
    print("🏥 Healthcare Bot Database Setup and Testing")
    print("=" * 50)
    
    # Test database connection
    if not test_database_connection():
        print("❌ Cannot proceed without database connection")
        return False
    
    # Create tables (in case they don't exist)
    print("\nCreating/updating database tables...")
    try:
        create_tables()
        print("✅ Tables created/updated successfully!")
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        return False
    
    # Run migrations
    if not run_migrations():
        print("❌ Migration failed")
        return False
    
    # Test scenario operations
    if not test_scenario_operations():
        print("❌ Scenario operations test failed")
        return False
    
    print("\n🎉 All tests passed! Database is ready for use.")
    print("\nNext steps:")
    print("1. Update your .env file with Supabase credentials")
    print("2. Set DATABASE_URL to your Supabase PostgreSQL connection string")
    print("3. Restart your application")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)