"""Script to initialize database"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db


def main():
    """Initialize database tables"""
    print("🗄️  Initializing database...")
    
    try:
        app = create_app()
        
        with app.app_context():
            # Create all tables
            db.create_all()
            print("✅ Database initialized successfully!")
            
    except Exception as e:
        print(f"❌ Error initializing database: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()

