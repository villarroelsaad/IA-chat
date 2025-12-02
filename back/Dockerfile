FROM python:3.11-slim

WORKDIR /app

# Copiar solo los ficheros necesarios
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8000

EXPOSE 8000

CMD ["python", "server.py"]
