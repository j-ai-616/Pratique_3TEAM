import json
import html
import streamlit.components.v1 as components
from src.config.settings import KAKAO_JAVASCRIPT_KEY


def render_kakao_map(search_results):
    if not KAKAO_JAVASCRIPT_KEY:
        components.html(
            """
            <div style="padding:16px; color:red; font-weight:bold;">
                KAKAO_JAVASCRIPT_KEY 가 설정되지 않았습니다. .env 파일을 확인하세요.
            </div>
            """,
            height=100,
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
                "place_url": str(loc.get("place_url", "")),
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
            #map {{
                width: 100%;
                height: 650px;
                min-height: 650px;
                border: 1px solid #ddd;
                border-radius: 10px;
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
    </head>
    <body>
        <div id="map"></div>

        <script>
            (function() {{
                var locations = {locations_json};

                function showEmptyMessage() {{
                    var mapDiv = document.getElementById("map");
                    mapDiv.outerHTML = '<div class="empty-box">지역을 검색하면 전기차 충전소가 지도에 표시됩니다.</div>';
                }}

                function initMap() {{
                    if (!window.kakao || !window.kakao.maps) {{
                        document.body.innerHTML += '<p style="color:red;">카카오맵 SDK 로드 실패</p>';
                        return;
                    }}

                    window.kakao.maps.load(function() {{
                        if (!locations || locations.length === 0) {{
                            showEmptyMessage();
                            return;
                        }}

                        var container = document.getElementById('map');
                        var options = {{
                            center: new window.kakao.maps.LatLng(locations[0].lat, locations[0].lng),
                            level: 5
                        }};

                        var map = new window.kakao.maps.Map(container, options);
                        var bounds = new window.kakao.maps.LatLngBounds();

                        // 현재 열린 정보창 1개만 관리
                        var currentInfowindow = null;

                        locations.forEach(function(loc) {{
                            var position = new window.kakao.maps.LatLng(loc.lat, loc.lng);
                            bounds.extend(position);

                            var marker = new window.kakao.maps.Marker({{
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

                            var infowindow = new window.kakao.maps.InfoWindow({{
                                content: content
                            }});

                            window.kakao.maps.event.addListener(marker, 'click', function() {{
                                if (currentInfowindow) {{
                                    currentInfowindow.close();
                                }}
                                infowindow.open(map, marker);
                                currentInfowindow = infowindow;
                            }});
                        }});

                        // 지도 빈 곳 클릭 시 닫기
                        window.kakao.maps.event.addListener(map, 'click', function() {{
                            if (currentInfowindow) {{
                                currentInfowindow.close();
                                currentInfowindow = null;
                            }}
                        }});

                        map.setBounds(bounds);
                    }});
                }}

                var script = document.createElement("script");
                script.src = "https://dapi.kakao.com/v2/maps/sdk.js?appkey={KAKAO_JAVASCRIPT_KEY}&autoload=false";
                script.onload = initMap;
                script.onerror = function() {{
                    document.body.innerHTML += '<p style="color:red;">카카오맵 SDK 스크립트 로드 오류</p>';
                }};
                document.head.appendChild(script);
            }})();
        </script>
    </body>
    </html>
    """

    components.html(html_code, height=700)