from fastapi import FastAPI, HTTPException
import boto3
import os
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# 確保 AWS 認證環境變數存在
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")

if not AWS_ACCESS_KEY or not AWS_SECRET_KEY:
    raise Exception("AWS credentials are not set in environment variables")

AWS_REGION = "ap-northeast-1"  # 東京區

# 初始化 AWS 客戶端
ec2_client = boto3.client("ec2", region_name=AWS_REGION,
                          aws_access_key_id=AWS_ACCESS_KEY,
                          aws_secret_access_key=AWS_SECRET_KEY)

iam_client = boto3.client("iam", aws_access_key_id=AWS_ACCESS_KEY,
                          aws_secret_access_key=AWS_SECRET_KEY)

ce_client = boto3.client("ce", region_name=AWS_REGION,
                         aws_access_key_id=AWS_ACCESS_KEY,
                         aws_secret_access_key=AWS_SECRET_KEY)

cloudwatch_client = boto3.client("cloudwatch", region_name=AWS_REGION,
                                 aws_access_key_id=AWS_ACCESS_KEY,
                                 aws_secret_access_key=AWS_SECRET_KEY)

app = FastAPI()

class InstanceAction(BaseModel):
    instance_id: str

# EC2 相關 API
@app.get("/aws/ec2/status")
def get_ec2_status():
    try:
        response = ec2_client.describe_instance_status()
        if "InstanceStatuses" not in response:
            raise HTTPException(status_code=500, detail="Invalid response structure")
        return response.get("InstanceStatuses", [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get EC2 status: {str(e)}")

@app.post("/aws/ec2/restart")
def restart_instance(action: InstanceAction):
    try:
        ec2_client.reboot_instances(InstanceIds=[action.instance_id])
        return {"message": f"EC2 instance {action.instance_id} is rebooting"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to restart instance: {str(e)}")

# IAM 相關 API
@app.get("/aws/iam/users")
def list_iam_users(marker: Optional[str] = None):
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

# 成本相關 API
@app.get("/aws/billing/cost")
def get_aws_cost(start_date: str = None, end_date: str = None):
    # 若沒有傳入日期，使用今天日期作為預設值
    if not start_date:
        start_date = datetime.today().strftime('%Y-%m-%d')
    if not end_date:
        end_date = datetime.today().strftime('%Y-%m-%d')

    try:
        response = ce_client.get_cost_and_usage(
            TimePeriod={"Start": start_date, "End": end_date},
            Granularity="MONTHLY",
            Metrics=["AmortizedCost"]
        )
        return response["ResultsByTime"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get AWS cost: {str(e)}")

# CloudWatch 相關 API
def validate_time_format(time_str):
    try:
        # 驗證時間格式是否為 ISO 8601 格式
        datetime.fromisoformat(time_str)
        return True
    except ValueError:
        return False

@app.get("/aws/cloudwatch/metrics")
def get_cloudwatch_metrics(namespace: str, metric_name: str, instance_id: str, start_time: str, end_time: str):
    # 驗證時間格式
    if not validate_time_format(start_time) or not validate_time_format(end_time):
        raise HTTPException(status_code=400, detail="Invalid time format. Use ISO 8601 format (e.g., 2024-03-29T00:00:00Z).")
    
    try:
        response = cloudwatch_client.get_metric_data(
            MetricDataQueries=[
                {
                    "Id": "m1",
                    "MetricStat": {
                        "Metric": {
                            "Namespace": namespace,
                            "MetricName": metric_name,
                            "Dimensions": [{"Name": "InstanceId", "Value": instance_id}]
                        },
                        "Period": 3600,
                        "Stat": "Average",
                    },
                    "ReturnData": True,
                },
            ],
            StartTime=start_time,
            EndTime=end_time,
        )
        return response["MetricDataResults"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get CloudWatch metrics: {str(e)}")

@app.get("/")
def root():
    return {"message": "AWS Management API"}

