from fastapi import FastAPI, HTTPException
import boto3
import os
from pydantic import BaseModel
from typing import Optional

# AWS 配置
AWS_REGION = "ap-northeast-1"  # 東京區
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")

# 初始化 AWS 客戶端
ec2_client = boto3.client("ec2", region_name=AWS_REGION, 
                          aws_access_key_id=AWS_ACCESS_KEY, 
                          aws_secret_access_key=AWS_SECRET_KEY)

iam_client = boto3.client("iam", aws_access_key_id=AWS_ACCESS_KEY, 
                          aws_secret_access_key=AWS_SECRET_KEY)

ce_client = boto3.client("ce", region_name=AWS_REGION, 
                          aws_access_key_id=AWS_ACCESS_KEY, 
                          aws_secret_access_key=AWS_SECRET_KEY)

app = FastAPI()

class InstanceAction(BaseModel):
    instance_id: str

@app.get("/ec2/status")
def get_ec2_status():
    """獲取 EC2 執行個體狀態"""
    try:
        response = ec2_client.describe_instance_status()
        return response.get("InstanceStatuses", [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get EC2 status: {str(e)}")

@app.post("/ec2/restart")
def restart_instance(action: InstanceAction):
    """重新啟動 EC2 執行個體"""
    try:
        ec2_client.reboot_instances(InstanceIds=[action.instance_id])
        return {"message": f"EC2 instance {action.instance_id} is rebooting"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to restart instance: {str(e)}")

@app.get("/iam/users")
def list_iam_users(marker: Optional[str] = None):
    """獲取 IAM 使用者列表，處理分頁"""
    try:
        users = []
        while True:
            response = iam_client.list_users(Marker=marker) if marker else iam_client.list_users()
            users.extend(response["Users"])
            marker = response.get("Marker")
            if not marker:
                break
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list IAM users: {str(e)}")

@app.get("/billing/cost")
def get_aws_cost(start_date: str = "2024-03-01", end_date: str = "2024-03-29"):
    """獲取 AWS 成本與使用報告，支持自訂日期範圍"""
    try:
        response = ce_client.get_cost_and_usage(
            TimePeriod={
                "Start": start_date,  # 使用查詢參數指定的開始日期
                "End": end_date       # 使用查詢參數指定的結束日期
            },
            Granularity="MONTHLY",
            Metrics=["AmortizedCost"]
        )
        return response["ResultsByTime"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get AWS cost: {str(e)}")

@app.get("/")
def root():
    return {"message": "AWS EC2 Monitoring & IAM Management API"}

