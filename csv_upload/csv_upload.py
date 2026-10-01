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
NOTION_PARENT_PAGE_ID = os.getenv("NOTION_PARENT_PAGE_ID")
notion = Client(auth=NOTION_TOKEN)

#csv_folder
csv_folder = Path("csv_file")

#.csv파일명만 선택
for file in csv_folder.glob("*.csv"):
    #형식이 utf-8이아니라 cp949였음
    with open(file, "r", encoding="cp949") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        columns = reader.fieldnames
    print(columns)

    # CSV - Notion 속성 생성
    notion_properties = {}
    for index, column in enumerate(columns):
        # 첫 번째 컬럼 → title
        if index == 0:
            notion_properties[column] = {
                "title": {}
            }
        # 나머지 컬럼 → 전부 문자
        else:
            notion_properties[column] = {
                "rich_text": {}
            }
    # 데이터베이스 생성
    database = notion.databases.create(
        parent={
            "type": "page_id",
            "page_id": NOTION_PARENT_PAGE_ID
        },
        title=[
            {
                "type": "text",
                "text": {
                    "content": file.stem
                }
            }
        ],
        initial_data_source={
            "properties": notion_properties
        }
    )

    # 생성된 Database ID
    database_id = database.get('id', '')
    # 생성된 Data Source ID
    data_source_id = database.get('data_sources', [{}])[0].get('id', '')

    print("NotionDB 생성 완료")
    print("Database ID:", database_id)
    print("Data Source ID:", data_source_id)

    #.env업데이트
    #NOTION_DATABASE_ID_숫자, 존재여부확인후 다음숫자 사용(소규모프로젝트라 적게 생성될 예정)
    id_num = 1
    while True:
        if not os.getenv(f"NOTION_DATABASE_ID_{id_num}"): break
        id_num += 1
    set_key(env, f"NOTION_DATABASE_ID_{id_num}", database_id, quote_mode="never")
    set_key(env, f"NOTION_SOURCE_ID_{id_num}", data_source_id, quote_mode="never")
    #set_key는 현재 로드된 환경변수에 반영안됨, override옵션을 켜야 새로로드하면서 덮어씀
    load_dotenv(env, override=True)
    print(".env 키 추가 완료")

    # CSV 데이터를 Notion DB에 추가
    for row in rows:
        properties = {}
        for index, column in enumerate(columns):
            value = row[column]
            # 첫 번째 컬럼 → title
            if index == 0:
                properties[column] = {
                    "title": [
                        {"text": {"content": value}}
                    ]
                }
            # 나머지 컬럼 → rich_text
            else:
                properties[column] = {
                    "rich_text": [
                        {"text": {"content": value}}
                    ]
                }
        # Notion 데이터베이스에 데이터 추가 (row)
        notion.pages.create(
            parent={
                "data_source_id": data_source_id
            },
            properties=properties
        )

    print(f"{file.name} NotionDB 업로드 완료")
