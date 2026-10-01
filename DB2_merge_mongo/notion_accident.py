# 중복 제거, 결측치 처리, 자료형 변환
# 지역명 표준화, 시군구 데이터를 시도 단위로 집계
# Notion API로 수집한 교통사고 데이터를 pandas로 전처리하면서 중복 제거, 결측치 처리, 자료형 변환, 
# 지역명 표준화, 시군구 단위 데이터를 시도 단위로 집계했습니다.
import pandas as pd, os, time
from dotenv import load_dotenv
from notion_client import Client
from notion_client.errors import APIResponseError

load_dotenv()

def get_notion_db_data():
    token = os.getenv("NOTION_TOKEN")
    source_id = os.getenv("NOTION_SOURCE_ID_2")
    notion = Client(auth=token)

    results, cursor = [], None

    while True:
        for i in range(5):
            try:
                args = {"data_source_id": source_id, "page_size": 100}
                if cursor:
                    args["start_cursor"] = cursor

                result = notion.data_sources.query(**args)
                break

            except APIResponseError:
                if i == 4:
                    raise
                time.sleep((i + 1) * 5)

        results += result.get("results", [])

        if not result.get("has_more"):
            break

        cursor = result.get("next_cursor")
        time.sleep(2)

    return results


def get_text(prop, key):
    items = prop.get(key, [])
    return items[0].get("plain_text", "") if items else ""


region_map = {
    "서울특별시":"서울", "부산광역시":"부산", "대구광역시":"대구",
    "인천광역시":"인천", "광주광역시":"광주", "대전광역시":"대전",
    "울산광역시":"울산", "세종특별자치시":"세종", "경기도":"경기",
    "강원특별자치도":"강원", "강원도":"강원",
    "충청북도":"충북", "충청남도":"충남",
    "전북특별자치도":"전북", "전라북도":"전북",
    "전라남도":"전남", "경상북도":"경북",
    "경상남도":"경남", "제주특별자치도":"제주"
}

rows = []

for page in get_notion_db_data():
    data = page["properties"]

    region = get_text(data.get("시도", {}), "title").strip()
    region = region_map.get(region, region)

    rows.append({
        "region": region,
        "city": get_text(data.get("시군구", {}), "rich_text"),
        "accident_count": get_text(data.get("사고건수", {}), "rich_text"),
        "death_count": get_text(data.get("사망자수", {}), "rich_text"),
        "serious_injury_count": get_text(data.get("중상자수", {}), "rich_text"),
        "minor_injury_count": get_text(data.get("경상자수", {}), "rich_text"),
        "reported_injury_count": get_text(data.get("부상신고자수", {}), "rich_text")
    })

df = pd.DataFrame(rows).drop_duplicates()
df = df[df["region"] != ""]

숫자컬럼 = [
    "accident_count",
    "death_count",
    "serious_injury_count",
    "minor_injury_count",
    "reported_injury_count"
]

for col in 숫자컬럼:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

df = df.groupby("region", as_index=False)[숫자컬럼].sum()

print(df.to_string(index=False))
print("최종 지역 개수:", len(df))

df.to_csv("accident.csv", index=False, encoding="utf-8-sig")