from __future__ import annotations



def format_number(value) -> str:
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return '-'



def find_default_regions(search_region: str, region_list: list[str]) -> list[str]:
    if not search_region:
        return region_list

    cleaned_search_region = search_region.strip()
    if not cleaned_search_region:
        return region_list

    matched_regions = [
        region_name
        for region_name in region_list
        if cleaned_search_region in region_name or region_name in cleaned_search_region
    ]
    return matched_regions or region_list
