from flask import Flask, render_template
from pymongo import MongoClient
import json

app = Flask(__name__)

client = MongoClient('mongodb://localhost:27017/')
db = client['python_three'] # 222.101 DB 이름
col = db['accident_license_data'] #222.101 내부 컬렉션 이름
# client = MongoClient('222.101.236.155:27017', serverSelectionTimeoutMS=2000)
# client = MongoClient(
#     "mongodb://mongoadmin:password@222.101.236.155:27017/"
#     "?authSource=admin"
# )
# db = client['python_three']
# col = db['accident_license_data']



# @app.route('/health')
# def health_check():
#     return {"status": "OK", "service": "security-dashboard"}
# try:
#     # MongoDB의 기본 포트 - 27017
#     client = MongoClient('mongodb://222.101.236.155:27017/', serverSelectionTimeoutMS=2000)
#     print(client.server_info().get('version'))
#     print("MongoDB 엔진 가동 확인 완료!")
# except Exception as e:
#     print("연결 실패: 서버가 꺼져 있거나 설치가 잘못됨.", e)




@app.route("/")
def index():
    # 2. MongoDB에서 데이터 가져오기 (_id 필드는 화면에 불필요하므로 제외 처리)
    # raw_data = list(col.find({}, {"_id": False}))
    data_list = list(col.find({}, {"_id": False}))

    # 3. 만약 DB에 eng 필드가 없다면 위 딕셔너리를 참고해서 추가해 줌
    # data_list = []
    # for item in raw_data:
    #     region_name = item.get("region")
    #     if "eng" not in item:
    #         item["eng"] = eng_mapping.get(region_name, "UNKNOWN")
    #     data_list.append(item)

    # 4. HTML로 데이터 전달 (jinja2 템플릿의 tojson 필터 사용)

    print("--- [디버그] MongoDB에서 가져온 데이터 ---")
    print(data_list)
    print(f"--- 데이터 개수: {len(data_list)}개 ---")
    return render_template("test_map.html", data=data_list)

if __name__ == "__main__":
    app.run(debug=True)