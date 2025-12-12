"""
CSV export functionality for keyword ideas.
"""

import csv
import io
from typing import List, Dict, Any


def keyword_ideas_to_csv(keyword_ideas: List[Dict[str, Any]]) -> str:
    """
    Convert keyword ideas to CSV string.
    
    Args:
        keyword_ideas: List of keyword idea dictionaries
        
    Returns:
        CSV string
    """
    if not keyword_ideas:
        return ""

    # Define CSV columns
    fieldnames = [
        "keyword",
        "avg_monthly_searches",
        "competition",
        "competition_index",
        "low_top_of_page_bid_micros",
        "high_top_of_page_bid_micros",
    ]

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()

    for idea in keyword_ideas:
        # Flatten the data for CSV
        row = {
            "keyword": idea.get("keyword", ""),
            "avg_monthly_searches": idea.get("avg_monthly_searches", 0),
            "competition": idea.get("competition", "UNKNOWN"),
            "competition_index": idea.get("competition_index") or "",
            "low_top_of_page_bid_micros": idea.get("low_top_of_page_bid_micros") or "",
            "high_top_of_page_bid_micros": idea.get("high_top_of_page_bid_micros") or "",
        }
        writer.writerow(row)

    return output.getvalue()


def get_top_keywords_by_volume(
    keyword_ideas: List[Dict[str, Any]], top_k: int = 500
) -> List[Dict[str, Any]]:
    """
    Get top K keywords sorted by average monthly search volume.
    
    Args:
        keyword_ideas: List of keyword idea dictionaries
        top_k: Number of top keywords to return
        
    Returns:
        Top K keywords sorted by volume (descending)
    """
    sorted_keywords = sorted(
        keyword_ideas,
        key=lambda x: x.get("avg_monthly_searches", 0),
        reverse=True,
    )
    return sorted_keywords[:top_k]

