import psycopg2
import os
from dotenv import load_dotenv
import redis

def reset_db():
    """
    Drops all tables from the database defined in .env
    """
    load_dotenv()

    DB_HOST = os.getenv("DB_HOST")
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASS = os.getenv("DB_PASS")

    print(f"Connecting to database {DB_NAME} at {DB_HOST}...")

    try:
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
        cursor = conn.cursor()

        # Drop tables in correct order (child tables first) or use CASCADE
        tables = ["messages", "room_members", "room", "users"]
        
        print("Dropping tables...")
        for table in tables:
            cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
            print(f"Dropped table: {table}")

        conn.commit()
        print("SUCCESS: All tables dropped.")

        cursor.close()
        conn.close()
        
        # Reset Redis
        REDIS_URL = os.getenv("REDIS_URL")
        if REDIS_URL:
            print(f"Connecting to Redis at {REDIS_URL}...")
            try:
                r = redis.from_url(REDIS_URL)
                r.flushdb()
                print("SUCCESS: Redis flushed.")
            except Exception as e:
                print("ERROR flushing Redis:", e)
        else:
            print("Redis URL not set, skipping Redis flush.")

    except Exception as e:
        print("ERROR resetting database:", e)

if __name__ == "__main__":
    reset_db()
