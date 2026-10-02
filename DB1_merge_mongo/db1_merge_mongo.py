import pandas as pd
import os
from dotenv import load_dotenv
from notion_client import Client
from pymongo import MongoClient

client = MongoClient(
    "mongodb://mongoadmin:password@222.101.236.155:27017/"
    "?authSource=admin"
)
db = client['python_three']
col = db['accident_license_data']

def get_notion_db_data():
    """notion API로 DB_1에 접속후 쿼리값을 받아서 리턴하는 함수."""
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


def preprocess_license_data(result):
    """데이터 전처리하는 함수\n
    지역(경기북부,경기남부는 경기로 통일), 면허인구수\n
    2개의 칼럼으로 데이터를 처리한다."""
    #속성값 통일
    csv_properties = {
        "region": "",
        "licensed_population": 0,
        # 아래는 현재 DB에서 없는 속성값
        # "accident_count": 0,
        # "death_count": 0,
        # "serious_injury_count": 0,
        # "minor_injury_count": 0,
        # "reported_injury_count": 0
    }
    
    지역목록 = ["서울", "제주", "경북", "경남", "전북", "전남", "충북", "충남", "강원", 
            "경기", "세종", "울산", "대전", "대구", "광주", "인천", "부산"]

    면허종류 = ["1종_대형견인", "1종_구난", "1종_대형", "1종_보통", "1종_소형견인",
            "1종_소형", "2종_보통", "2종_소형", "2종_원자"]
    
    결과 = {}
    
    for 지역명 in 지역목록:
        #csv_properties dict복사, 새 dict "row" 생성
        row = csv_properties.copy()
        row["region"] = 지역명
        결과[지역명] = row

    # csv 값 전처리 과정, pandas
    rows = []
    for page in result["results"]:
        data = page["properties"]
        row = {"region": data.get("지역별", {}).get("title", [{}])[0].get("plain_text", "")}
        for 면허 in 면허종류:
            row[면허] = int((data.get(면허, {}).get("rich_text") or [{}])[0].get("plain_text", "0") or 0)
        rows.append(row)

    df = pd.DataFrame(rows)
    df["region"] = df["region"].replace({"경기북부": "경기", "경기남부": "경기"})
    df["licensed_population"] = df[면허종류].sum(axis=1)
    합계 = df.groupby("region")["licensed_population"].sum()

    for 지역명 in 합계.index.difference(지역목록):
        print("목록에 없는 지역:", 지역명)

    for 지역명 in 지역목록:
        결과[지역명]["licensed_population"] = int(합계.get(지역명, 0))

    # 확인용 출력 (MongoDB 저장 없음)
    for 지역명, row in 결과.items():
        print(지역명, row)
    return 결과

def mongodb_update(preprocessed_data):
    """mongodb에 전처리데이터 업데이트하는 함수"""
    for result in preprocessed_data.items():
        data = col.find_one({'region':result[1].get('region')})
        if data is not None:
            col.update_one({'region':data['region']},
                            {"$set":result[1]})
            print(f'[중복] {result[0]}')
        else:
            save_id = col.insert_one(result[1])
            print(f'[저장 성공] 지역 : {result[0]} | 저장ID : {save_id}')

if __name__ == "__main__":
    result = get_notion_db_data()
    # print(result)
    preprocessed_data = preprocess_license_data(result)
    mongodb_update(preprocessed_data)

