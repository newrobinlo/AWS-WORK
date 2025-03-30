# 使用官方 Python 映像
FROM python:3.9-slim

# 設定工作目錄
WORKDIR /app

# 複製當前目錄的內容到容器內
COPY . /app

# 安裝依賴
RUN pip install --no-cache-dir -r requirements.txt

# 開放 FastAPI 需要的端口（通常是 8000）
EXPOSE 8000

# 設定容器啟動時執行的命令
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]




















