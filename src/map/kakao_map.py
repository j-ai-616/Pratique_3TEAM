import html
from typing import List, Dict, Any

import streamlit as st
import streamlit.components.v1 as components


def render_kakao_map(search_results: List[Dict[str, Any]]):
    try:
        import folium
    except ImportError:
        components.html(
            """
            <div style="padding:16px; color:red; font-weight:bold;">
                folium 패키지가 설치되어 있지 않습니다. requirements.txt 또는 환경을 확인하세요.
            </div>
            """,
            height=100,
        )
        return

    if not search_results:
        components.html(
            """
            <div style="
                height:650px;
                display:flex;
                align-items:center;
                justify-content:center;
                border:1px solid #ddd;
                border-radius:10px;
                background:#fafafa;
                color:#666;
                font-size:15px;
            ">
                지역을 검색하면 전기차 충전소가 지도에 표시됩니다.
            </div>
            """,
            height=700,
        )
        return

    valid_locations = []
    for loc in search_results:
        try:
            lat = float(loc.get("lat"))
            lng = float(loc.get("lng"))
            valid_locations.append(
                {
                    "name": str(loc.get("name", "")),
                    "lat": lat,
                    "lng": lng,
                    "address": str(loc.get("address", "")),
                    "road_address": str(loc.get("road_address", "")),
                    "phone": str(loc.get("phone", "")),
                    "category": str(loc.get("category", "")),
                    "place_url": str(loc.get("place_url", "")),
                }
            )
        except (TypeError, ValueError):
            continue

    if not valid_locations:
        components.html(
            """
            <div style="
                height:650px;
                display:flex;
                align-items:center;
                justify-content:center;
                border:1px solid #fca5a5;
                border-radius:10px;
                background:#fef2f2;
                color:#b91c1c;
                font-size:15px;
            ">
                지도에 표시할 좌표 데이터가 없습니다.
            </div>
            """,
            height=700,
        )
        return

    center_lat = valid_locations[0]["lat"]
    center_lng = valid_locations[0]["lng"]

    map_object = folium.Map(
        location=[center_lat, center_lng],
        zoom_start=13,
        control_scale=True,
    )

    bounds = []

    for loc in valid_locations:
        bounds.append([loc["lat"], loc["lng"]])

        popup_html = f"""
        <div style="min-width:220px; line-height:1.5; font-size:12px;">
            <div style="font-weight:bold; font-size:13px; margin-bottom:6px;">
                {html.escape(loc["name"])}
            </div>
            <div><b>도로명</b>: {html.escape(loc["road_address"] or "-")}</div>
            <div><b>지번</b>: {html.escape(loc["address"] or "-")}</div>
            <div><b>전화</b>: {html.escape(loc["phone"] or "-")}</div>
            <div><b>분류</b>: {html.escape(loc["category"] or "-")}</div>
            {
                f'<div style="margin-top:6px;"><a href="{html.escape(loc["place_url"])}" target="_blank">카카오맵 상세보기</a></div>'
                if loc["place_url"] else ""
            }
        </div>
        """

        folium.Marker(
            location=[loc["lat"], loc["lng"]],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=html.escape(loc["name"]),
        ).add_to(map_object)

    if bounds:
        map_object.fit_bounds(bounds)

    map_html = map_object._repr_html_()
    components.html(map_html, height=700)