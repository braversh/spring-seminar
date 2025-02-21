FROM python:3.13-slim
COPY . /app
WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip 
RUN pip install --no-cache-dir flask

CMD ["flask", "run", "--host=0.0.0.0"]