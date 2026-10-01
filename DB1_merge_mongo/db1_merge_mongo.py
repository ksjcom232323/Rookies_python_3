import pandas, os, csv
from dotenv import load_dotenv, find_dotenv
from notion_client import Client
from pathlib import Path
from pymongo import MongoClient

client = MongoClient(
    "mongodb://mongoadmin:password@222.101.236.155:27017/"
    "?authSource=admin"
)
db = client['python_three']
col = db['accident_license_data']

def get_notion_db_data():
    """
    notion API로 DB_1에 접속후 쿼리값을 받아서 리턴하는 함수.
    """
    load_dotenv()
    NOTION_TOKEN = os.getenv("NOTION_TOKEN")
    NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID_1")
    data_source_id = os.getenv("NOTION_SOURCE_ID_1")

    notion = Client(auth=NOTION_TOKEN)

    # data source ID가 .env에 없을 때만 데이터베이스 정보 조회
    if not data_source_id:
        db_info = notion.databases.retrieve(NOTION_DATABASE_ID)
        data_source_id = db_info.get("data_sources", [{}])[0].get("id")
    print("Data Source ID:", data_source_id)

    return notion.data_sources.query(data_source_id=data_source_id)

result = get_notion_db_data()
# print(result)

#속성값 통일
csv_properties = {
    "region": "",
    "licensed_population": 0,
    "accident_count": 0,
    "death_count": 0,
    "serious_injury_count": 0,
    "minor_injury_count": 0,
    "reported_injury_count": 0
}

지역목록 = ["서울", "제주", "경북", "경남", "전북", "전남", "충북", "충남", "강원", 
        "경기", "세종", "울산", "대전", "대구", "광주", "인천", "부산"]

면허종류 = ["1종_대형견인", "1종_구난", "1종_대형", "1종_보통", "1종_소형견인",
        "1종_소형", "2종_보통", "2종_소형", "2종_원자"]
        
def get_text(prop, key):
    """rich_text / title 속성에서 plain_text를 꺼냄"""
    items = prop.get(key, [])
    return items[0].get("plain_text", "") if items else ""

결과 = {}
for 지역명 in 지역목록:
    #csv_properties dict복사, 새 dict "row" 생성
    row = csv_properties.copy()
    row["region"] = 지역명
    결과[지역명] = row

for page in result["results"]:
    data = page["properties"]
    지역명 = get_text(data.get("지역별", {}), "title")
    if 지역명 == "경기북부" or 지역명 == "경기남부":
        지역명 = "경기"
    if 지역명 not in 결과:
        print("목록에 없는 지역:", 지역명)
        continue
    for 면허 in 면허종류:
        값 = get_text(data.get(면허, {}), "rich_text")
        결과[지역명]["licensed_population"] += int(값 or 0)

for result in 결과.items():
    data = col.find_one({'region':result[1].get('region')})
    if data is not None:
        col.update_one({'region':data['region']},
                       {"$set":result[1]})
        print(f'[중복] {result[0]}')
    else:
        save_id = col.insert_one(result[1])
        print(f'[저장 성공] 지역 : {result[0]} | 저장ID : {save_id}')