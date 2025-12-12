"""
Google Ads API client for keyword idea generation.
"""

import os
from typing import List, Dict, Any, Optional
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException


def create_google_ads_client() -> GoogleAdsClient:
    """Create and return a Google Ads client using environment variables."""
    config = {
        "developer_token": os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN"),
        "client_id": os.getenv("GOOGLE_ADS_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_ADS_CLIENT_SECRET"),
        "refresh_token": os.getenv("GOOGLE_ADS_REFRESH_TOKEN"),
        "use_proto_plus": True,
    }
    
    # Only add login_customer_id if it's set and valid (10 digits)
    login_customer_id = os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID")
    if login_customer_id:
        # Remove dashes and validate
        login_customer_id_clean = login_customer_id.replace("-", "")
        if login_customer_id_clean.isdigit() and len(login_customer_id_clean) == 10:
            config["login_customer_id"] = login_customer_id_clean
    
    return GoogleAdsClient.load_from_dict(config)


def generate_keyword_ideas(
    client: GoogleAdsClient,
    customer_id: str,
    website_url: str,
    geo_target_constants: List[str],
    language_id: str = "1000",  # English
    max_results: int = 2000,
    include_adult_keywords: bool = False,
) -> List[Dict[str, Any]]:
    """
    Generate keyword ideas using Google Ads KeywordPlanIdeaService.
    
    Args:
        client: Google Ads client instance
        customer_id: Google Ads customer ID
        website_url: Website URL to use as seed (e.g., https://www.bewajihealth.com)
        geo_target_constants: List of geo target constant resource names
        language_id: Language constant ID (default: 1000 for English)
        max_results: Maximum number of results to return
        include_adult_keywords: Whether to include adult keywords
        
    Returns:
        List of keyword idea dictionaries with metrics
    """
    try:
        # Validate inputs
        if not customer_id:
            raise ValueError("Customer ID is required")
        
        if not geo_target_constants:
            raise ValueError("At least one geo target constant is required")
        
        # Filter out None or empty geo targets
        valid_geo_targets = [gt for gt in geo_target_constants if gt and isinstance(gt, str) and gt.strip()]
        if not valid_geo_targets:
            raise ValueError("No valid geo target constants found")
        
        # Remove duplicates
        valid_geo_targets = list(dict.fromkeys(valid_geo_targets))  # Preserves order
        
        # Validate format - should be geoTargetConstants/XXXXX
        validated_geo_targets = []
        for gt in valid_geo_targets:
            gt = gt.strip()
            if gt.startswith("geoTargetConstants/") and len(gt) > 20:  # Basic validation
                validated_geo_targets.append(gt)
            else:
                print(f"Warning: Invalid geo target format skipped: {gt}")
        
        if not validated_geo_targets:
            raise ValueError("No valid geo target constants found after validation")
        
        # Limit to 10 geo targets (Google Ads API maximum per request)
        # See: https://developers.google.com/google-ads/api/reference/rpc/v16/GenerateKeywordIdeasRequest
        if len(validated_geo_targets) > 10:
            print(f"Warning: Limiting geo targets to 10 (API maximum). Had {len(validated_geo_targets)}, using first 10.")
            validated_geo_targets = validated_geo_targets[:10]
        
        keyword_plan_idea_service = client.get_service("KeywordPlanIdeaService")
        
        # Build request - use client.get_type for compatibility
        request = client.get_type("GenerateKeywordIdeasRequest")
        # Remove dashes from customer ID (Google Ads API expects format: 1234567890)
        customer_id_clean = customer_id.replace("-", "")
        request.customer_id = customer_id_clean
        request.language = f"languageConstants/{language_id}"
        
        # Get KeywordPlanNetwork enum from client
        # Use get_enum for version-agnostic access
        keyword_plan_network_enum = client.get_type("KeywordPlanNetworkEnum").KeywordPlanNetwork
        request.keyword_plan_network = keyword_plan_network_enum.GOOGLE_SEARCH
        
        # Only add validated geo targets
        request.geo_target_constants.extend(validated_geo_targets)
        request.include_adult_keywords = include_adult_keywords
        
        # Extract domain from URL for site_seed
        from urllib.parse import urlparse
        parsed = urlparse(website_url)
        domain = parsed.netloc or parsed.path.strip("/")
        
        # Clean up domain
        if not domain:
            raise ValueError(f"Invalid website URL: {website_url}")
        
        # Remove www. prefix if present for site_seed
        if domain.startswith("www."):
            domain = domain[4:]
        
        # Remove protocol if present
        domain = domain.replace("https://", "").replace("http://", "")
        
        # Ensure URL has protocol for url_seed fallback
        if not website_url.startswith(("http://", "https://")):
            website_url = f"https://{website_url}"
        
        # Set the seed - API requires exactly ONE seed type
        # Use url_seed (most reliable and widely supported)
        # Ensure URL is properly formatted
        if not website_url.startswith(("http://", "https://")):
            website_url = f"https://{website_url}"
        
        try:
            # Use url_seed - this is the most reliable option
            request.url_seed.url = website_url
        except AttributeError:
            # If url_seed doesn't exist, try site_seed as fallback
            try:
                request.site_seed.site = domain
            except AttributeError as e:
                raise ValueError(f"Could not set website seed. Neither url_seed nor site_seed available. URL: {website_url}, Domain: {domain}, Error: {e}")
        except Exception as e:
            raise ValueError(f"Error setting website seed. URL: {website_url}, Error: {e}")

        # Execute request
        response = keyword_plan_idea_service.generate_keyword_ideas(request)

        # Extract results
        results = []
        count = 0
        for result in response:
            if count >= max_results:
                break

            keyword_text = result.text
            metrics = result.keyword_idea_metrics

            keyword_data = {
                "keyword": keyword_text,
                "avg_monthly_searches": metrics.avg_monthly_searches if metrics.avg_monthly_searches else 0,
                "competition": metrics.competition.name if metrics.competition else "UNKNOWN",
                "competition_index": metrics.competition_index if metrics.competition_index else None,
                "low_top_of_page_bid_micros": metrics.low_top_of_page_bid_micros if metrics.low_top_of_page_bid_micros else None,
                "high_top_of_page_bid_micros": metrics.high_top_of_page_bid_micros if metrics.high_top_of_page_bid_micros else None,
            }

            # Add monthly search volume breakdown if available
            if hasattr(metrics, "monthly_search_volumes") and metrics.monthly_search_volumes:
                monthly_volumes = []
                for volume in metrics.monthly_search_volumes:
                    monthly_volumes.append({
                        "year": volume.year if hasattr(volume, "year") else None,
                        "month": volume.month.name if hasattr(volume, "month") else None,
                        "monthly_searches": volume.monthly_searches if hasattr(volume, "monthly_searches") else None,
                    })
                keyword_data["monthly_breakdown"] = monthly_volumes

            results.append(keyword_data)
            count += 1

        return results

    except GoogleAdsException as ex:
        error_message = f"Google Ads API error"
        error_code = None
        error_details = None
        
        if hasattr(ex, 'error') and ex.error:
            if hasattr(ex.error, 'code') and ex.error.code():
                error_code = ex.error.code().name
                error_message += f": {error_code}"
            if hasattr(ex.error, 'location') and callable(ex.error.location):
                try:
                    location = ex.error.location()
                    if location:
                        error_message += f" at {location}"
                except:
                    pass
            if hasattr(ex.error, 'details') and callable(ex.error.details):
                try:
                    details = ex.error.details()
                    if details:
                        error_details = details
                        error_message += f" - {details}"
                except:
                    pass
        else:
            error_message += f": {str(ex)}"
        
        # Add helpful guidance for common errors
        if error_code == "INVALID_ARGUMENT" or (error_details and "invalid value" in str(error_details).lower()):
            error_message += "\n\n" + """
⚠️ INVALID_ARGUMENT Error - Possible causes:

1. **Invalid Geo Targets**: Some geo targets may be invalid or not supported
   - The app filters out invalid targets, but some may still cause issues
   - Check that geo targets are valid resource names (format: geoTargetConstants/XXXXX)
   - Try with fewer countries or check the geo_target_cache.json file

2. **Website URL Format**: The website URL may be in an invalid format
   - Ensure it's a valid URL (e.g., https://www.bewajihealth.com)
   - The domain should be accessible and properly formatted

3. **Empty Request**: No valid geo targets were resolved
   - Check that at least some countries were successfully resolved
   - The app needs at least one valid geo target to work
   - You should see "Resolved X geo targets" message before the error

4. **API Version Compatibility**: Some parameters may not be supported
   - Try updating the google-ads package: pip install --upgrade google-ads
            """
        elif error_code == "PERMISSION_DENIED":
            error_message += "\n\n" + """
⚠️ PERMISSION_DENIED Error - Possible causes:

1. **Test Account vs Production**: Your developer token may be approved for TEST accounts only
   - If your token is "approved for test accounts", you MUST use a test customer ID
   - Production customer IDs (like 814-562-8296) won't work with test-only tokens
   - Get a test customer ID: https://developers.google.com/google-ads/api/docs/first-call/test-account-generator
   - Update GOOGLE_ADS_CUSTOMER_ID in your .env file with a test customer ID

2. **Developer Token Not Approved**: Your developer token may still be pending approval
   - Check: https://ads.google.com/ → Tools & Settings → API Center
   - Status should be "Approved" (not just "Approved for test accounts")

3. **Customer ID Access**: The OAuth account may not have access to this customer ID
   - Verify the customer ID is correct
   - Ensure the Google account used for OAuth has access to this Google Ads account

4. **OAuth Scope**: The refresh token may not have the required permissions
   - Try regenerating your refresh token: python get_refresh_token.py
   - Make sure you grant all requested permissions during OAuth

5. **Manager Account**: If using a manager account, ensure GOOGLE_ADS_LOGIN_CUSTOMER_ID is set correctly
            """
        
        raise Exception(error_message) from ex
    except Exception as ex:
        # Handle other exceptions (like gRPC errors)
        error_message = f"Google Ads API error: {str(ex)}"
        raise Exception(error_message) from ex

