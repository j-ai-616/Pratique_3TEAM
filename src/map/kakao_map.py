import json
import html
import os

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / ".env"
load_dotenv(ENV_PATH)


def get_kakao_javascript_key() -> str:
    try:
        secret_key = st.secrets.get("KAKAO_JAVASCRIPT_KEY", "")
        if secret_key:
            return str(secret_key).strip()
    except Exception:
        pass

    return os.getenv("KAKAO_JAVASCRIPT_KEY", "").strip()


def render_kakao_map(search_results):
    kakao_javascript_key = get_kakao_javascript_key()

    if not kakao_javascript_key:
        components.html(
            """
            <div style="padding:16px; color:red; font-weight:bold;">
                KAKAO_JAVASCRIPT_KEY 가 설정되지 않았습니다. .env 파일을 확인하세요.
            </div>
            """,
            height=120,
        )
        return

    safe_results = []
    for loc in search_results:
        safe_results.append(
            {
                "name": html.escape(str(loc.get("name", ""))),
                "lat": loc.get("lat"),
                "lng": loc.get("lng"),
                "address": html.escape(str(loc.get("address", ""))),
                "road_address": html.escape(str(loc.get("road_address", ""))),
                "phone": html.escape(str(loc.get("phone", ""))),
                "category": html.escape(str(loc.get("category", ""))),
                "place_url": html.escape(str(loc.get("place_url", ""))),
            }
        )

    locations_json = json.dumps(safe_results, ensure_ascii=False)

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8" />
        <style>
            html, body {{
                margin: 0;
                padding: 0;
                width: 100%;
                height: 100%;
                font-family: Arial, sans-serif;
            }}
            #wrap {{
                width: 100%;
            }}
            #debug {{
                font-size: 12px;
                line-height: 1.5;
                color: #374151;
                background: #f9fafb;
                border: 1px solid #e5e7eb;
                border-radius: 10px;
                padding: 10px;
                margin-bottom: 10px;
                white-space: pre-wrap;
                word-break: break-word;
            }}
            #map {{
                width: 100%;
                height: 650px;
                min-height: 650px;
                border: 1px solid #ddd;
                border-radius: 10px;
                overflow: hidden;
                background: #fff;
            }}
            .empty-box {{
                height: 650px;
                display: flex;
                align-items: center;
                justify-content: center;
                border: 1px solid #ddd;
                border-radius: 10px;
                background: #fafafa;
                color: #666;
                font-size: 15px;
                text-align: center;
                padding: 20px;
                box-sizing: border-box;
            }}
            .error-box {{
                height: 650px;
                display: flex;
                align-items: center;
                justify-content: center;
                border: 1px solid #fca5a5;
                border-radius: 10px;
                background: #fef2f2;
                color: #b91c1c;
                font-size: 15px;
                text-align: center;
                padding: 20px;
                box-sizing: border-box;
                white-space: pre-wrap;
                line-height: 1.5;
            }}
            .info-wrap {{
                padding: 8px 10px;
                font-size: 12px;
                line-height: 1.5;
                min-width: 220px;
            }}
            .info-title {{
                font-size: 13px;
                font-weight: bold;
                margin-bottom: 6px;
                color: #111827;
            }}
            .info-row {{
                margin-bottom: 4px;
                color: #374151;
            }}
            .info-link {{
                display: inline-block;
                margin-top: 6px;
                color: #2563eb;
                text-decoration: none;
            }}
        </style>

        <script src="https://dapi.kakao.com/v2/maps/sdk.js?appkey={kakao_javascript_key}&libraries=services"></script>
    </head>
    <body>
        <div id="wrap">
            <div id="debug">디버그 시작</div>
            <div id="map"></div>
        </div>

        <script>
            (function() {{
                var locations = {locations_json};

                function setDebug(msg) {{
                    var debugDiv = document.getElementById("debug");
                    debugDiv.textContent += "\\n" + msg;
                }}

                function showEmptyMessage() {{
                    var mapDiv = document.getElementById("map");
                    mapDiv.innerHTML = '<div class="empty-box">지역을 검색하면 전기차 충전소가 지도에 표시됩니다.</div>';
                }}

                function showErrorMessage(msg) {{
                    var mapDiv = document.getElementById("map");
                    mapDiv.innerHTML = '<div class="error-box">' + msg + '</div>';
                }}

                function initMap() {{
                    try {{
                        setDebug("1) initMap 진입");

                        if (!window.kakao) {{
                            showErrorMessage("window.kakao 객체가 없습니다.");
                            return;
                        }}

                        if (!window.kakao.maps) {{
                            showErrorMessage("window.kakao.maps 객체가 없습니다.");
                            return;
                        }}

                        setDebug("2) locations length = " + (locations ? locations.length : "null"));
                        setDebug("3) typeof kakao.maps.LatLng = " + typeof window.kakao.maps.LatLng);
                        setDebug("4) typeof kakao.maps.Map = " + typeof window.kakao.maps.Map);

                        if (!locations || locations.length === 0) {{
                            showEmptyMessage();
                            return;
                        }}

                        var validLocations = locations.filter(function(loc) {{
                            return (
                                loc &&
                                loc.lat !== null &&
                                loc.lat !== undefined &&
                                loc.lng !== null &&
                                loc.lng !== undefined &&
                                !isNaN(Number(loc.lat)) &&
                                !isNaN(Number(loc.lng))
                            );
                        }});

                        setDebug("5) validLocations length = " + validLocations.length);

                        if (validLocations.length === 0) {{
                            showErrorMessage("지도에 표시할 좌표 데이터가 없습니다.");
                            return;
                        }}

                        var firstLat = Number(validLocations[0].lat);
                        var firstLng = Number(validLocations[0].lng);
                        setDebug("6) firstLat = " + firstLat + ", firstLng = " + firstLng);

                        var container = document.getElementById("map");
                        if (!container) {{
                            showErrorMessage("지도 컨테이너를 찾을 수 없습니다.");
                            return;
                        }}

                        var center = new kakao.maps.LatLng(firstLat, firstLng);
                        var map = new kakao.maps.Map(container, {{
                            center: center,
                            level: 5
                        }});

                        setDebug("7) Map 생성 성공");

                        var bounds = new kakao.maps.LatLngBounds();
                        var currentInfowindow = null;

                        validLocations.forEach(function(loc) {{
                            var position = new kakao.maps.LatLng(Number(loc.lat), Number(loc.lng));
                            bounds.extend(position);

                            var marker = new kakao.maps.Marker({{
                                position: position,
                                map: map
                            }});

                            var content = `
                                <div class="info-wrap">
                                    <div class="info-title">${{loc.name}}</div>
                                    <div class="info-row"><b>도로명</b>: ${{loc.road_address || '-'}}</div>
                                    <div class="info-row"><b>지번</b>: ${{loc.address || '-'}}</div>
                                    <div class="info-row"><b>전화</b>: ${{loc.phone || '-'}}</div>
                                    <div class="info-row"><b>분류</b>: ${{loc.category || '-'}}</div>
                                    ${{loc.place_url ? `<a class="info-link" href="${{loc.place_url}}" target="_blank">카카오맵 상세보기</a>` : ''}}
                                </div>
                            `;

                            var infowindow = new kakao.maps.InfoWindow({{
                                content: content
                            }});

                            kakao.maps.event.addListener(marker, "click", function() {{
                                if (currentInfowindow) {{
                                    currentInfowindow.close();
                                }}
                                infowindow.open(map, marker);
                                currentInfowindow = infowindow;
                            }});
                        }});

                        kakao.maps.event.addListener(map, "click", function() {{
                            if (currentInfowindow) {{
                                currentInfowindow.close();
                                currentInfowindow = null;
                            }}
                        }});

                        map.setBounds(bounds);
                        setDebug("8) setBounds 완료");
                    }} catch (err) {{
                        setDebug("ERR: " + err.message);
                        showErrorMessage("지도 초기화 오류: " + err.message);
                    }}
                }}

                if (document.readyState === "loading") {{
                    document.addEventListener("DOMContentLoaded", initMap);
                }} else {{
                    initMap();
                }}
            }})();
        </script>
    </body>
    </html>
    """

    components.html(html_code, height=820)