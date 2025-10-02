FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copiar código da aplicação
COPY . .

# Criar diretórios necessários
RUN mkdir -p uploads/saude data/uploads/saude

# Expor porta do Railway
EXPOSE $PORT

# Comando para iniciar no Railway
CMD gunicorn --bind 0.0.0.0:$PORT wsgi:app
