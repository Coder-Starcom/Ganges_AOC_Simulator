import os
import psycopg2
from psycopg2.extras import execute_values

# Strict Production Boundary: Pull target cloud environment string dynamically.
# Hardcoded fallbacks stripped to prevent credential leaks on public VCS commits.
NEON_DB_URI = os.getenv("DATABASE_URL")

if not NEON_DB_URI:
    raise EnvironmentError(
        "❌ CRITICAL CONFIGURATION FAULT: The 'DATABASE_URL' environment variable is unassigned. "
        "User seeding initialization aborted to safeguard credentials."
    )


def seed_synthetic_profiles():
    print("🚀 Initializing Ganges International Synthetic Passenger Provisioning Engine...")
    
    # 2. DEFINING EXPERIMENTAL SIMULATION ACCOUNTS
    # Maps perfectly to the zero-auth login profiles hardcoded on your dashboard UI matrix.
    # Note: Explicitly matched schema constraint definitions ('INSTITUTIONAL_WHOLESALE')
    profiles = [
        ("usr_einstein_001", "usr_einstein_001", "Albert Einstein", "QUANT_STRESS_BOT"),
        ("usr_curie_002", "usr_curie_002", "Marie Curie", "INSTITUTIONAL_WHOLESALE"),
        ("usr_tesla_003", "usr_tesla_003", "Nikola Tesla", "QUANT_STRESS_BOT"),
        ("usr_turing_004", "usr_turing_004", "Alan Turing", "INSTITUTIONAL_WHOLESALE")
    ]
    
    print(f"📥 Connecting to NeonDB cluster to clear and provision {len(profiles)} master profiles...")
    try:
        connection = psycopg2.connect(NEON_DB_URI)
        cursor = connection.cursor()
        
        # Safe merge strategy: clear out matching usernames if they exist to avoid unique constraint traps
        user_ids_tuple = tuple(p[0] for p in profiles)
        cursor.execute("DELETE FROM users WHERE user_id IN %s;", (user_ids_tuple,))
        
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
        print(f"❌ PROFILE DEPLOYMENT FAULT: Operation rolled back. Details:\n{error}")
        if 'connection' in locals():
            connection.rollback()
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()
        print("🔌 Connection isolated back to pool cluster.")


if __name__ == "__main__":
    seed_synthetic_profiles()