import os
import psycopg2
from psycopg2.extras import execute_values

# --- 1. CONFIGURATION AND CLOUD CONNECTION ---
NEON_DB_URI = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:admin123@ep-ganges-aviation-pool.east-us-2.aws.neon.tech/gi_aviation_db?sslmode=require"
)

def seed_synthetic_profiles():
    print("🚀 Initializing Ganges International Synthetic Passenger Provisioning Engine...")
    
    # 2. DEFINING EXPERIMENTAL SIMULATION ACCOUNTS
    # Maps perfectly to the zero-auth login profiles hardcoded on your dashboard UI matrix
    profiles = [
        ("usr_einstein_001", "usr_einstein_001", "Albert Einstein", "QUANT_STRESS_BOT"),
        ("usr_curie_002", "usr_curie_002", "Marie Curie", "INSTITUTIONAL_WHOSALE"),
        ("usr_tesla_003", "usr_tesla_003", "Nikola Tesla", "QUANT_STRESS_BOT"),
        ("usr_turing_004", "usr_turing_004", "Alan Turing", "INSTITUTIONAL_WHOSALE")
    ]
    
    print(f"📥 Connecting to NeonDB cluster to clear and provision {len(profiles)} master profiles...")
    try:
        connection = psycopg2.connect(NEON_DB_URI)
        cursor = connection.cursor()
        
        # Safe merge strategy: clear out matching usernames if they exist to avoid unique constraint traps
        cursor.execute("DELETE FROM users WHERE user_id IN %s;", (tuple(p[0] for p in profiles),))
        
        # Batch insert using optimized execute_values
        insert_query = """
            INSERT INTO users (user_id, username, full_name, profile_tier)
            VALUES %s;
        """
        execute_values(cursor, insert_query, profiles)
        
        connection.commit()
        print("\n✅ SYSTEM SUCCESS: Synthetic Passenger Simulation Profiles fully operational.")
        
        # Print a quick terminal confirmation matrix for visual verification
        print("\n=== LIVE PROFILE REGISTRY ===")
        cursor.execute("SELECT user_id, full_name, profile_tier FROM users;")
        for row in cursor.fetchall():
            print(f" ID: {row[0]:<20} | Operator: {row[1]:<18} | Tier: {row[2]}")
        print("=============================")
        
    except Exception as error:
        print(f"❌ PROFILE DEPLOYMENT FAULT: {error}")
        if 'connection' in locals():
            connection.rollback()
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()
        print("\n🔌 Connection isolated back to pool cluster.")

if __name__ == "__main__":
    seed_synthetic_profiles()