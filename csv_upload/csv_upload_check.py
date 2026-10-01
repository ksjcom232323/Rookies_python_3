import os
from dotenv import load_dotenv, set_key, find_dotenv
from notion_client import Client

import csv
from pathlib import Path

# .env 파일 로드
env = find_dotenv()
load_dotenv(env)

# Notion 연결
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
notion = Client(auth=NOTION_TOKEN)

#키값이 존재하는 동안만 추가루프
id_num = 1

while os.getenv(f"NOTION_DATABASE_ID_{id_num}"):

    NOTION_DATABASE_ID = os.getenv(f"NOTION_DATABASE_ID_{id_num}")
    # Database 정보 조회
    db_info = notion.databases.retrieve(NOTION_DATABASE_ID)

    # Data Source ID
    data_source_id = db_info.get("data_sources", [{}])[0].get("id","")

    print(f"\n===== Database {id_num} =====")
    print("Database ID:", NOTION_DATABASE_ID)
    print("Data Source ID:", data_source_id)

    # 데이터 조회
    result = notion.data_sources.query(
        data_source_id=data_source_id
    )

    # 속성별 데이터 개수
    property_counts = {}
    for page in result["results"]:
        for property_name, property_data in page["properties"].items():
            property_counts[property_name] = property_counts.get(property_name, 0) + 1
    for property_name, count in property_counts.items():
        print(f"{property_name}: {count}개")
    id_num += 1