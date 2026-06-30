FROM python:3.10-slim
WORKDIR /code
COPY requirements.txt .  <- النقطة دي مهمة. معناها "انسخو في الفولدر الحالي /code"
RUN pip install --no-cache-dir -r requirements.txt
COPY .                 <- النقطتين ديل: انسخ كل شي من هنا لهنا
CMD ["python", "app.py"]
