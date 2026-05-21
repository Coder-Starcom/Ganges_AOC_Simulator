import os
import re
import sqlalchemy
from sqlalchemy import text

# Strict Production Boundary: Pull target cloud environment string dynamically.
# Hardcoded fallbacks stripped to prevent credential leaks on public VCS commits.
NEON_DB_URI = os.getenv("DATABASE_URL")

if not NEON_DB_URI:
    raise EnvironmentError(
        "❌ CRITICAL CONFIGURATION FAULT: The 'DATABASE_URL' environment variable is unassigned. "
        "Deployment aborted to safeguard system state."
    )

engine = sqlalchemy.create_engine(NEON_DB_URI)

def build_relational_schema_from_file(file_path="../data/schema.sql"):
    print("🚀 Initializing Ganges International Quant Operational Network Database Rebuild...")
    
    if not os.path.exists(file_path):
        print(f"❌ DEPLOYMENT ERROR: Target SQL script template '{file_path}' could not be located in the working path.")
        return

    # Read and parse the external SQL schema payload
    with open(file_path, "r", encoding="utf-8") as f:
        sql_content = f.read()

    # Regex engine: strips single-line comments and tokenizes atomic query strings by semicolon
    sql_clean = re.sub(r'--.*?\n', '\n', sql_content)
    raw_queries = sql_clean.split(';')
    
    # Process text sequences, dropping empty whitespace list segments
    schema_queries = [q.strip() for q in raw_queries if q.strip()]

    print(f"📁 Parsed execution vector file. Found {len(schema_queries)} atomic engine operations to process.")
    
    try:
        # Open context-managed transaction boundary on Neon cluster
        with engine.begin() as transaction:
            for index, query in enumerate(schema_queries, start=1):
                transaction.execute(text(query))
                print(f"🔹 Deployed Core Relational Infrastructure Structural Layer ({index}/{len(schema_queries)})")
                    
        print(f"\n✅ SYSTEM SUCCESS: Quant Operations Engine Schema safely read from '{file_path}' and compiled on Neon DB.")
    except Exception as e:
        print(f"\n❌ DEPLOYMENT CRASHED: Database transactions aborted and rolled back to preserve safety state. Error:\n{str(e)}")

if __name__ == "__main__":
    build_relational_schema_from_file()