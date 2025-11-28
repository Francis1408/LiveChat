import psycopg2
import os
from dotenv import load_dotenv

def init_db():

    """
        Lê o schema.sql e cria a table no BD referênciado no .env
    """

    load_dotenv()

    DB_HOST = os.getenv("DB_HOST")
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASS = os.getenv("DB_PASS")
    # Conecta-se ao BD
    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
    cursor = conn.cursor()

    # Lê o SQL file
    with open("schema.sql", "r") as file:
        schema = file.read()

    # Executa os comandos
    cursor.execute(schema)
    conn.commit()

    cursor.close()
    conn.close()

    print("DB Tables ensured (created if missing)")