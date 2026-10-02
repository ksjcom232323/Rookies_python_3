from flask import Flask, render_template
from pymongo import MongoClient
import json
import os
from dotenv import load_dotenv, set_key, find_dotenv

env = find_dotenv()
load_dotenv(env)

app = Flask(__name__)

DBCON = os.getenv("MONGO_DB_CON")
print(DBCON)

# client = MongoClient('mongodb://localhost:27017/')
# db = client['python_three'] # 222.101 DB 이름
# col = db['accident_license_data'] #222.101 내부 컬렉션 이름
# client = MongoClient('222.101.236.155:27017', serverSelectionTimeoutMS=2000)
client = MongoClient(
    f"{DBCON}"
    "?authSource=admin"
)
db = client['python_three']
col = db['accident_license_data']
print(client)

try:
    # MongoDB의 기본 포트 - 27017
    client = MongoClient('mongodb://222.101.236.155:27017/', serverSelectionTimeoutMS=2000)
    print(client.server_info().get('version'))
    print("MongoDB 엔진 가동 확인 완료!")
except Exception as e:
    print("연결 실패: 서버가 꺼져 있거나 설치가 잘못됨.", e)




@app.route("/")
def index():
    data_list = list(col.find({}, {"_id": False}))

    print("--- [디버그] MongoDB에서 가져온 데이터 ---")
    print(data_list)
    print(f"--- 데이터 개수: {len(data_list)}개 ---")
    return render_template("test_map.html", data=data_list)

if __name__ == "__main__":
    app.run(debug=True)