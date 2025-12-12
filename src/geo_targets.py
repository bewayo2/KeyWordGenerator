"""
Geo target resolution and caching for Google Ads API.
"""

import json
import os
from typing import Dict, List, Optional
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException


CACHE_FILE = "geo_target_cache.json"


def load_cache() -> Dict[str, str]:
    """Load geo target cache from file."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_cache(cache: Dict[str, str]) -> None:
    """Save geo target cache to file."""
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print(f"Warning: Could not save geo target cache: {e}")


def resolve_country_to_geo_target(
    client: GoogleAdsClient, country_name: str, cache: Dict[str, str]
) -> Optional[str]:
    """
    Resolve a country name to a GeoTargetConstant resource name.
    Uses cache if available, otherwise queries Google Ads API.
    """
    # Check cache first
    if country_name in cache:
        return cache[country_name]

    # Query Google Ads API
    try:
        geo_target_constant_service = client.get_service("GeoTargetConstantService")
        
        # Build request using client.get_type for version compatibility
        request = client.get_type("SuggestGeoTargetConstantsRequest")
        request.locale = "en"
        request.location_names.names.append(country_name)

        response = geo_target_constant_service.suggest_geo_target_constants(request)

        # Find the best match
        if hasattr(response, "geo_target_constant_suggestions") and response.geo_target_constant_suggestions:
            # Priority 1: COUNTRY type
            for suggestion in response.geo_target_constant_suggestions:
                geo_target = suggestion.geo_target_constant
                target_type = geo_target.target_type
                if isinstance(target_type, str):
                    target_type_str = target_type
                else:
                    target_type_str = target_type.name if hasattr(target_type, "name") else str(target_type)
                
                if target_type_str == "COUNTRY" or "COUNTRY" in target_type_str:
                    resource_name = geo_target.resource_name
                    cache[country_name] = resource_name
                    return resource_name

            # Priority 2: PROVINCE type (for territories like Puerto Rico, etc.)
            for suggestion in response.geo_target_constant_suggestions:
                geo_target = suggestion.geo_target_constant
                target_type = geo_target.target_type
                if isinstance(target_type, str):
                    target_type_str = target_type
                else:
                    target_type_str = target_type.name if hasattr(target_type, "name") else str(target_type)
                
                if target_type_str == "PROVINCE" or "PROVINCE" in target_type_str:
                    resource_name = geo_target.resource_name
                    cache[country_name] = resource_name
                    return resource_name

            # Priority 3: Any geographic target (fallback)
            # Accept the first suggestion if it exists
            first_suggestion = response.geo_target_constant_suggestions[0]
            geo_target = first_suggestion.geo_target_constant
            resource_name = geo_target.resource_name
            cache[country_name] = resource_name
            return resource_name

        # No suggestions returned
        print(f"Warning: Could not resolve geo target for '{country_name}' - no suggestions returned from API")
        return None

    except GoogleAdsException as ex:
        # Don't print full exception for API errors - just log that it failed
        print(f"Warning: Could not resolve geo target for '{country_name}' (API error)")
        return None
    except Exception as ex:
        print(f"Warning: Could not resolve geo target for '{country_name}' (Unexpected error: {type(ex).__name__})")
        return None


def resolve_countries(
    client: GoogleAdsClient, country_names: List[str]
) -> List[str]:
    """
    Resolve a list of country names to GeoTargetConstant resource names.
    Uses caching to avoid redundant API calls.
    """
    cache = load_cache()
    geo_targets = []

    for country_name in country_names:
        geo_target = resolve_country_to_geo_target(client, country_name, cache)
        if geo_target:
            geo_targets.append(geo_target)

    # Save updated cache
    save_cache(cache)

    return geo_targets


# Default country list - Focus on larger Caribbean countries + major markets
DEFAULT_COUNTRIES = [
    # Major markets
    "United States",
    "Canada",
    "United Kingdom",
    
    # Larger Caribbean countries (by population/economic size)
    "Jamaica",
    "Dominican Republic",
    "Trinidad and Tobago",
    "Puerto Rico",
    "Bahamas",
    "Barbados",
    "Guyana",
    "Suriname",
]

