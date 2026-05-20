import os
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

load_dotenv()

DB_URI = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:admin123@ep-ganges-aviation-pool.east-us-2.aws.neon.tech/gi_aviation_db?sslmode=require"
)

if not DB_URI:
    raise RuntimeError("DATABASE_URL environment variable is missing.")

engine = create_engine(DB_URI)

def inspect_database():
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    print(f"\n📌 Found {len(tables)} live asset tables in database.\n" + "="*80)
    
    with engine.connect() as conn:
        for idx, table_name in enumerate(tables):
            # Dynamic Cap: Show 3 records for initial lookup tables, 10 records for transactional tables
            limit = 3 if idx < 3 else 10
            
            print(f"\n📋 SAMPLE SAMPLING MATRIX: {table_name.upper()} (Showing up to {limit} records)")
            print("-" * 80)
            
            try:
                # Direct structural query with explicit limit parameterization
                query = text(f"SELECT * FROM {table_name} LIMIT :limit;")
                result = conn.execute(query, {"limit": limit})
                
                columns = result.keys()
                rows = result.fetchall()
                
                if not rows:
                    print("   [Empty Table - No Operational State Recorded]")
                    print("="*80)
                    continue
                
                # Print column headers cleanly formatted
                print(" | ".join(columns))
                print("-" * 80)
                
                # Print individual row vectors
                for row in rows:
                    print(" | ".join(str(val) for val in row))
                    
            except Exception as e:
                print(f"❌ DATA INFERENCE TRAPPED ERROR {table_name}: {str(e)}")
            
            print("\n" + "="*80)

if __name__ == "__main__":
    inspect_database()