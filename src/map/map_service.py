import requests
from src.config.settings import KAKAO_REST_API_KEY


EV_KEYWORDS = [
    "전기차",
    "전기자동차",
    "EV",
    "충전소",
    "충전기",
]


def _is_ev_related(doc: dict) -> bool:
    text = " ".join(
        [
            str(doc.get("place_name", "")),
            str(doc.get("category_name", "")),
            str(doc.get("address_name", "")),
            str(doc.get("road_address_name", "")),
        ]
    ).lower()

    text_kr = text.replace(" ", "")
    return any(keyword.lower() in text_kr for keyword in EV_KEYWORDS)


def search_ev_chargers(region_keyword: str):
    debug_info = {
        "input_keyword": region_keyword,
        "query_used": None,
        "has_rest_key": bool(KAKAO_REST_API_KEY),
        "status_code": None,
        "response_preview": None,
        "error": None,
    }

    if not region_keyword or not region_keyword.strip():
        debug_info["error"] = "검색어가 비어 있습니다."
        return [], debug_info

    if not KAKAO_REST_API_KEY:
        debug_info["error"] = "KAKAO_REST_API_KEY 가 비어 있습니다."
        return [], debug_info

    base_keyword = region_keyword.strip()
    query = f"{base_keyword} 전기차 충전소"
    debug_info["query_used"] = query

    try:
        resp = requests.get(
            "https://dapi.kakao.com/v2/local/search/keyword.json",
            headers={"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"},
            params={
                "query": query,
                "size": 15,
                "page": 1,
            },
            timeout=8,
        )

        debug_info["status_code"] = resp.status_code
        debug_info["response_preview"] = resp.text[:300]

        resp.raise_for_status()
        data = resp.json()

        raw_docs = data.get("documents", [])

        filtered_docs = [doc for doc in raw_docs if _is_ev_related(doc)]
        if not filtered_docs:
            filtered_docs = raw_docs

        results = []
        seen = set()

        for doc in filtered_docs:
            try:
                name = doc.get("place_name", "").strip()
                lat = float(doc.get("y", 0))
                lng = float(doc.get("x", 0))
                road_address = doc.get("road_address_name", "").strip()
                address = doc.get("address_name", "").strip()

                dedupe_key = (name, lat, lng)
                if dedupe_key in seen:
                    continue
                seen.add(dedupe_key)

                results.append(
                    {
                        "name": name,
                        "lat": lat,
                        "lng": lng,
                        "address": address,
                        "road_address": road_address,
                        "phone": doc.get("phone", "").strip(),
                        "category": doc.get("category_name", "").strip(),
                        "place_url": doc.get("place_url", "").strip(),
                    }
                )
            except (TypeError, ValueError):
                continue

        return results, debug_info

    except requests.RequestException as e:
        debug_info["error"] = str(e)
        return [], debug_info