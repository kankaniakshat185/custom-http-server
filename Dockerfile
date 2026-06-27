FROM python:3.11-slim

WORKDIR /app

COPY app/ .

EXPOSE 4221

CMD ["python3", "-u", "main.py", "--directory", "/data"]