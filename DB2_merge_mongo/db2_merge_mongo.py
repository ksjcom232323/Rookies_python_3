import pandas as pd, os, time
from dotenv import load_dotenv
from notion_client import Client
from notion_client.errors import APIResponseError

load_dotenv()


def get_notion_db_data():
    """Notion API로 DB_2에 접속해 전체 데이터를 조회하는 함수."""

    token = os.getenv("NOTION_TOKEN")
    source_id = os.getenv("NOTION_SOURCE_ID_2")
    notion = Client(auth=token)

    # Notion 데이터는 한 번에 최대 100개씩 조회되므로
    # cursor를 이용해 마지막 페이지까지 반복 조회
    results, cursor = [], None

    while True:
        # API 오류 발생 시 최대 5번까지 재시도
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
    """Notion 속성에서 plain_text 값을 추출하는 함수."""

    items = prop.get(key, [])
    return items[0].get("plain_text", "") if items else ""


# 지역명을 분석에 사용할 짧은 명칭으로 통일
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

# Notion 데이터를 필요한 컬럼만 추출해 리스트 형태로 저장
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


# DataFrame 변환 후 중복값과 빈 지역 데이터 제거
df = pd.DataFrame(rows).drop_duplicates()
df = df[df["region"] != ""]


숫자컬럼 = [
    "accident_count",
    "death_count",
    "serious_injury_count",
    "minor_injury_count",
    "reported_injury_count"
]


# 사고 관련 컬럼을 숫자형으로 변환
for col in 숫자컬럼:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)


# 시군구 단위 데이터를 지역 단위로 합산
df = df.groupby("region", as_index=False)[숫자컬럼].sum()


# 전처리 결과 확인
print(df.to_string(index=False))
print("최종 지역 개수:", len(df))


# 전처리 결과를 CSV 파일로 저장
df.to_csv("accident.csv", index=False, encoding="utf-8-sig")