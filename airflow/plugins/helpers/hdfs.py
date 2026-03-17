"""Lecture/écriture HDFS via WebHDFS REST API."""

import requests

HDFS_WEBHDFS_URL = "http://hdfs-namenode:9870/webhdfs/v1"
HDFS_USER = "root"


def read(path: str) -> bytes:
    url = f"{HDFS_WEBHDFS_URL}{path}?op=OPEN&user.name={HDFS_USER}"
    resp = requests.get(url, allow_redirects=True)
    resp.raise_for_status()
    return resp.content


def write(path: str, data: bytes, overwrite: bool = True):
    url = f"{HDFS_WEBHDFS_URL}{path}?op=CREATE&user.name={HDFS_USER}&overwrite={str(overwrite).lower()}"
    resp = requests.put(url, allow_redirects=False)
    if resp.status_code == 307:
        resp2 = requests.put(resp.headers["Location"], data=data)
        resp2.raise_for_status()
    else:
        resp.raise_for_status()


def mkdir(path: str):
    url = f"{HDFS_WEBHDFS_URL}{path}?op=MKDIRS&user.name={HDFS_USER}"
    resp = requests.put(url)
    resp.raise_for_status()
