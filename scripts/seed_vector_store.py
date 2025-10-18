"""Script to seed vector store with initial data"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.vector_store import VectorStoreService


def main():
    """Seed vector store with job descriptions, rubrics, and case studies"""
    print("🌱 Seeding vector store with initial data...")
    
    try:
        vector_store = VectorStoreService()
        vector_store.seed_initial_data()
        print("✅ Vector store seeded successfully!")
        
    except Exception as e:
        print(f"❌ Error seeding vector store: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()

