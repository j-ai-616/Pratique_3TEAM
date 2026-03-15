from __future__ import annotations

import pandas as pd



def filter_region_ev_data(ev_registration_data: pd.DataFrame, selected_regions: list[str] | None = None) -> pd.DataFrame:
    if ev_registration_data is None or ev_registration_data.empty:
        return pd.DataFrame(columns=['year_month', 'region', 'ev_count'])

    filtered_region_ev_data = ev_registration_data.copy()
    if selected_regions:
        filtered_region_ev_data = filtered_region_ev_data[
            filtered_region_ev_data['region'].isin(selected_regions)
        ]

    return filtered_region_ev_data.sort_values(['year_month', 'region']).reset_index(drop=True)



def summarize_region_ev_data(filtered_region_ev_data: pd.DataFrame) -> dict:
    if filtered_region_ev_data is None or filtered_region_ev_data.empty:
        return {
            'latest_month': None,
            'latest_region_data': pd.DataFrame(columns=['year_month', 'region', 'ev_count']),
            'total_ev_count': 0,
            'average_ev_count': 0,
            'top_region': '-',
            'top_region_count': 0,
            'covered_region_count': 0,
        }

    latest_month = filtered_region_ev_data['year_month'].max()
    latest_region_data = filtered_region_ev_data[
        filtered_region_ev_data['year_month'] == latest_month
    ].sort_values('ev_count', ascending=False)

    total_ev_count = int(latest_region_data['ev_count'].fillna(0).sum())
    average_ev_count = int(latest_region_data['ev_count'].fillna(0).mean()) if not latest_region_data.empty else 0
    covered_region_count = int(latest_region_data['region'].nunique())

    if latest_region_data.empty:
        top_region = '-'
        top_region_count = 0
    else:
        top_row = latest_region_data.iloc[0]
        top_region = str(top_row.get('region', '-'))
        top_region_count = int(top_row.get('ev_count', 0) or 0)

    return {
        'latest_month': latest_month,
        'latest_region_data': latest_region_data,
        'total_ev_count': total_ev_count,
        'average_ev_count': average_ev_count,
        'top_region': top_region,
        'top_region_count': top_region_count,
        'covered_region_count': covered_region_count,
    }



def build_region_ev_trend(filtered_region_ev_data: pd.DataFrame) -> pd.DataFrame:
    if filtered_region_ev_data is None or filtered_region_ev_data.empty:
        return pd.DataFrame()

    region_ev_trend = filtered_region_ev_data.pivot_table(
        index='year_month',
        columns='region',
        values='ev_count',
        aggfunc='sum',
    ).sort_index()

    region_ev_trend.index = [
        year_month.strftime('%Y-%m') if pd.notna(year_month) else '-'
        for year_month in region_ev_trend.index
    ]
    return region_ev_trend.fillna(0)
