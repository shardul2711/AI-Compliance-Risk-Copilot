import pymysql
from sqlalchemy import create_engine, text
import sys
import os

# Add parent directory of backend to path so we can import backend package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.core.config import settings
from backend.app.db.session import engine, Base, SessionLocal
from backend.app.models.models import User
from backend.app.core.security import get_password_hash

def ensure_database_exists():
    """Ensure that the MySQL database exists before running table creation."""
    print("Connecting to MySQL server to check database...")
    db_url = settings.DATABASE_URL
    
    # Parse username, password, host, port, and db name from connection string
    # Connection string format: mysql+pymysql://user:pass@host:port/dbname
    try:
        # We replace the db name with empty to connect to the server first
        base_url, db_name = db_url.rsplit('/', 1)
        if '?' in db_name:
            db_name = db_name.split('?')[0]
            
        print(f"Database name to check: {db_name}")
        
        # Connect to MySQL server using sqlalchemy_utils
        # SQLAlchemy utils database_exists doesn't always handle mysql+pymysql well without server setup
        temp_engine = create_engine(base_url)
        with temp_engine.connect() as conn:
            conn.execution_options(isolation_level="AUTOCOMMIT").execute(text(f"CREATE DATABASE IF NOT EXISTS `{db_name}`"))
            print(f"Database '{db_name}' verified/created successfully.")
    except Exception as e:
        print(f"Error creating database: {e}")
        print("Will attempt to create tables directly. Make sure the database exists in MySQL Workbench.")

def seed_db():
    print("Creating all tables in the database...")
    # This will create tables in the database
    Base.metadata.create_all(bind=engine)
    print("Tables created.")
    
    db = SessionLocal()
    try:
        # Check if users already exist
        admin = db.query(User).filter(User.email == "admin@compliance.com").first()
        if not admin:
            print("Seeding default Admin user...")
            admin = User(
                name="System Administrator",
                email="admin@compliance.com",
                password_hash=get_password_hash("admin123"),
                role="Admin"
            )
            db.add(admin)
            
        analyst = db.query(User).filter(User.email == "analyst@compliance.com").first()
        if not analyst:
            print("Seeding default Analyst user...")
            analyst = User(
                name="Risk Analyst",
                email="analyst@compliance.com",
                password_hash=get_password_hash("analyst123"),
                role="Analyst"
            )
            db.add(analyst)
            
        db.commit()
        print("Seeding completed successfully.")
    except Exception as e:
        db.rollback()
        print(f"Error during seeding: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    ensure_database_exists()
    seed_db()
