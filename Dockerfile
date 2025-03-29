# 使用官方 Python 映像
FROM python:3.9-slim

# 設定工作目錄
WORKDIR /app

# 安裝必要的依賴
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# 複製你的應用程式
COPY . /app/

# 告訴容器在執行時會用這個端口
EXPOSE 8000

# 啟動 FastAPI 應用
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

