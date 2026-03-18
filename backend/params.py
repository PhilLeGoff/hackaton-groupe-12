import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

MONGODBURL=os.getenv("MONGODBURL",default="mongodb://localhost:27017")
JWT_SECRET=os.getenv("JWT_SECRET", "fallback_secret")
ALGORITHM = "HS256"

HDFS_WEBHDFS_URL = os.getenv("HDFS_WEBHDFS_URL", "http://hdfs-namenode:9870/webhdfs/v1")
AIRFLOW_BASE_URL = os.getenv("AIRFLOW_BASE_URL", "http://airflow-webserver:8080")
AIRFLOW_USERNAME = os.getenv("AIRFLOW_USERNAME")
AIRFLOW_PASSWORD = os.getenv("AIRFLOW_PASSWORD")