#!/usr/bin/env python3
import os
from app import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    
    if os.environ.get('RAILWAY_ENVIRONMENT'):
        print("=== SISTEMA AMEG - RAILWAY ===")
        print(f"Rodando na porta: {port}")
        app.run(host='0.0.0.0', port=port)
    else:
        print("=== SISTEMA AMEG ===")
        print("Acesse: http://localhost:5000")
        print("Usuário: admin")
        print("Senha: admin123")
        print("====================")
        app.run(debug=True, host='0.0.0.0', port=5000)
