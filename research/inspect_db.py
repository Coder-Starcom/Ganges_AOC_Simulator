import os
from sqlalchemy import create_engine, inspect
from dotenv import load_dotenv

load_dotenv()

# Pull target environment string safely
DB_URI = os.getenv("DATABASE_URL")

if not DB_URI:
    raise RuntimeError("CRITICAL: DATABASE_URL environment variable is missing.")

engine = create_engine(DB_URI)

def print_exact_database_schema():
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    print("\n" + "="*75)
    print("🚀 QUANT SIMULATOR CORE: EXTRACTING EXACT LIVE TABLE SCHEMAS 🚀")
    print("="*75)
    
    for table_name in tables:
        print(f"\n📋 LIVE TABLE STRUCTURE: {table_name.upper()}")
        print("-" * 75)
        
        # 1. Fetch structural columns & native Postgres types
        columns = inspector.get_columns(table_name)
        print(f"{'COLUMN NAME':<32} | {'DATA TYPE':<16} | {'NULLABLE':<8} | {'DEFAULT VALUE'}")
        print("-" * 75)
        for col in columns:
            nullable_status = "YES" if col['nullable'] else "NO"
            default_val = f"{col['default']}" if col.get('default') is not None else "NONE"
            print(f"🔹 {col['name']:<30} | {str(col['type']):<16} | {nullable_status:<8} | {default_val}")
        
        print("-" * 75)
        
        # 2. Extract Primary Keys safely
        pk_constraint = inspector.get_pk_constraint(table_name)
        pk_cols = pk_constraint.get("constrained_columns", [])
        if pk_cols:
            print(f"🔑 PRIMARY KEY: {', '.join(pk_cols)}")
        else:
            print("🔑 PRIMARY KEY: [No Explicit Primary Key Constrained]")
            
        # 3. Extract Foreign Keys
        fk_constraints = inspector.get_foreign_keys(table_name)
        if fk_constraints:
            print("🔗 FOREIGN KEY RELATIONSHIPS:")
            for fk in fk_constraints:
                src_col = fk['constrained_columns'][0]
                referred_t = fk['referred_table']
                referred_col = fk['referred_columns'][0]
                print(f"   ▪️ ({src_col}) ➔ References: {referred_t.upper()}({referred_col})")
        
        print("="*75)

if __name__ == "__main__":
    print_exact_database_schema()