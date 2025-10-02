import os
print("🔍 Testando ambiente Railway...")
print(f"RAILWAY_ENVIRONMENT: {os.environ.get('RAILWAY_ENVIRONMENT')}")
print(f"DATABASE_URL exists: {bool(os.environ.get('DATABASE_URL'))}")

try:
    import psycopg2
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        result = cursor.fetchone()
        print(f"✅ PostgreSQL OK: {result}")
        conn.close()
    else:
        print("❌ DATABASE_URL não encontrada")
except Exception as e:
    print(f"❌ Erro PostgreSQL: {e}")

print("🚀 Iniciando Flask simples...")
from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello():
    return "OK"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
