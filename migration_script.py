import sqlalchemy
import pandas as pd
from sqlalchemy import create_engine, inspect

# --- CONFIGURATION ---
# Local: postgresql://username:password@localhost:5432/india_aviation
LOCAL_DB_URL = "postgresql://postgres:admin123@localhost:5432/india_aviation"

# Render: Use the EXTERNAL URL from your Render Dashboard
RENDER_DB_URL = "postgresql://india_aviation_db_user:a99pTxadRL6zkO0Ck0Rc5n6khXNQa5sq@dpg-d7s6e0q8qa3s73ducbs0-a.oregon-postgres.render.com/india_aviation_db"

# Fix Render URL prefix if necessary
if RENDER_DB_URL.startswith("postgres://"):
    RENDER_DB_URL = RENDER_DB_URL.replace("postgres://", "postgresql://", 1)

def ship_it():
    try:
        # Create Engines
        local_engine = create_engine(LOCAL_DB_URL)
        render_engine = create_engine(RENDER_DB_URL)
        
        # 1. Identify Tables
        inspector = inspect(local_engine)
        tables = ["airports", "edges_economic", "flights"]
        
        print(f"🚀 Starting Migration: Local -> Render")
        
        for table in tables:
            print(f"--- Processing Table: {table} ---")
            
            # 2. Read from Local
            print(f"Reading data from local {table}...")
            df = pd.read_sql_table(table, local_engine, schema='public')
            
            # 3. Write to Render
            # if_exists='replace' will create the table using the schema inferred from the DataFrame
            print(f"Creating table and uploading data to Render...")
            df.to_sql(table, render_engine, schema='public', if_exists='replace', index=False)
            
            print(f"✅ {table} synced successfully ({len(df)} rows).")

        print("\n✨ ALL TABLES MIGRATED TO CLOUD!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")

if __name__ == "__main__":
    ship_it()