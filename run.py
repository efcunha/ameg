#!/usr/bin/env python3
from app import app

if __name__ == '__main__':
    print("=== SISTEMA AMEG ===")
    print("Acesse: http://localhost:5000")
    print("Usuário: admin")
    print("Senha: admin123")
    print("====================")
    app.run(debug=True, host='0.0.0.0', port=5000)
