from __future__ import annotations

import pandas as pd



def filter_charger_operation_data(
    charger_operation_data: pd.DataFrame,
    selected_regions: list[str] | None = None,
    selected_charger_types: list[str] | None = None,
    only_available: bool = False,
) -> pd.DataFrame:
    if charger_operation_data is None or charger_operation_data.empty:
        return pd.DataFrame(
            columns=[
                'region',
                'charger_name',
                'charger_type',
                'operator',
                'address',
                'latitude',
                'longitude',
                'available_count',
                'total_count',
                'status',
                'operating_hours',
                'phone',
                'road_address',
            ]
        )

    filtered_charger_operation_data = charger_operation_data.copy()

    if selected_regions:
        filtered_charger_operation_data = filtered_charger_operation_data[
            filtered_charger_operation_data['region'].isin(selected_regions)
        ]

    if selected_charger_types:
        filtered_charger_operation_data = filtered_charger_operation_data[
            filtered_charger_operation_data['charger_type'].isin(selected_charger_types)
        ]

    if only_available and 'available_count' in filtered_charger_operation_data.columns:
        filtered_charger_operation_data = filtered_charger_operation_data[
            filtered_charger_operation_data['available_count'].fillna(0) > 0
        ]

    return filtered_charger_operation_data.reset_index(drop=True)



def summarize_charger_operation_data(filtered_charger_operation_data: pd.DataFrame) -> dict:
    if filtered_charger_operation_data is None or filtered_charger_operation_data.empty:
        return {
            'charger_station_count': 0,
            'available_charger_count': 0,
            'total_charger_count': 0,
        }

    charger_station_count = int(len(filtered_charger_operation_data))
    available_charger_count = int(filtered_charger_operation_data['available_count'].fillna(0).sum())
    total_charger_count = int(filtered_charger_operation_data['total_count'].fillna(0).sum())

    return {
        'charger_station_count': charger_station_count,
        'available_charger_count': available_charger_count,
        'total_charger_count': total_charger_count,
    }



def build_charger_map_results(filtered_charger_operation_data: pd.DataFrame) -> list[dict]:
    if filtered_charger_operation_data is None or filtered_charger_operation_data.empty:
        return []

    charger_map_results: list[dict] = []
    for _, charger_row in filtered_charger_operation_data.iterrows():
        latitude = charger_row.get('latitude')
        longitude = charger_row.get('longitude')
        if pd.isna(latitude) or pd.isna(longitude):
            continue

        charger_map_results.append(
            {
                'name': str(charger_row.get('charger_name', '충전소')),
                'lat': float(latitude),
                'lng': float(longitude),
                'address': str(charger_row.get('address', '')),
                'road_address': str(charger_row.get('road_address', '')),
                'phone': str(charger_row.get('phone', '')),
                'category': str(charger_row.get('charger_type', '')),
                'place_url': '',
            }
        )

    return charger_map_results
