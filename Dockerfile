FROM python:3.11-alpine
WORKDIR /app

COPY modules app.py config.json requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

CMD ["python", "app.py"]
