"""
Streamlit web app for keyword generation and categorization.
"""

import os
import json
import streamlit as st
from dotenv import load_dotenv

from src.google_ads_client import create_google_ads_client, generate_keyword_ideas
from src.geo_targets import resolve_countries, DEFAULT_COUNTRIES
from src.csv_export import keyword_ideas_to_csv, get_top_keywords_by_volume
from src.openai_client import create_openai_client, categorize_keywords_with_gpt52
from src.prompt import DEVELOPER_PROMPT
from src.text_export import format_results_as_text
from src.styles import GOOGLE_ADS_STYLE


# Load environment variables
# Try Streamlit secrets first (for Streamlit Cloud), then fall back to .env file (for local development)
if hasattr(st, "secrets") and st.secrets:
    # Streamlit Cloud secrets are already loaded
    pass
else:
    # Local development - load from .env file
    load_dotenv()

# Helper function to get environment variables from Streamlit secrets or os.environ
def get_env_var(var_name: str, default: str = None) -> str:
    """Get environment variable from Streamlit secrets or os.environ."""
    if hasattr(st, "secrets") and st.secrets:
        try:
            # Try flat access first: st.secrets["google_ads_client_id"]
            secret_key = var_name.lower()
            if secret_key in st.secrets:
                value = st.secrets[secret_key]
                return value if value else default
        except (KeyError, AttributeError, TypeError):
            pass
        
        try:
            # Try nested access: st.secrets.google_ads.client_id
            keys = var_name.lower().split("_")
            value = st.secrets
            for key in keys:
                value = value[key]
            return value if value else default
        except (KeyError, AttributeError, TypeError):
            pass
    
    # Fall back to os.environ
    return os.getenv(var_name, default)

# Page config
st.set_page_config(
    page_title="Keyword Generator",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply custom styling
st.markdown(GOOGLE_ADS_STYLE, unsafe_allow_html=True)

# Initialize session state
if "keyword_ideas" not in st.session_state:
    st.session_state.keyword_ideas = []
if "csv_content" not in st.session_state:
    st.session_state.csv_content = ""
if "gpt_results" not in st.session_state:
    st.session_state.gpt_results = None


def main():
    # Header section with Google Ads-like styling
    st.markdown("""
    <div style="background-color: #ffffff; padding: 1.5rem 0; border-bottom: 1px solid #dadce0; margin-bottom: 2rem;">
        <h1 style="color: #1a73e8; font-size: 1.75rem; font-weight: 400; margin: 0; padding: 0;">Keyword Generator</h1>
        <p style="color: #5f6368; margin: 0.5rem 0 0 0; font-size: 0.875rem;">Generate keyword ideas from Google Ads and categorize them with AI</p>
    </div>
    """, unsafe_allow_html=True)

    # Two columns layout
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### Blog Content")
        blog_content = st.text_area(
            "Paste your blog content here:",
            height=300,
            placeholder="Enter your blog post content...",
            label_visibility="collapsed",
        )

        st.markdown("### Settings")
        website_url = st.text_input(
            "Website URL (for keyword seed):",
            value="https://www.bewajihealth.com",
        )
        
        # Show warning if using test account
        customer_id_env = get_env_var("GOOGLE_ADS_CUSTOMER_ID", "")
        if customer_id_env:
            st.markdown(f"""
            <div style="background-color: #e8f0fe; border-left: 4px solid #1a73e8; border-radius: 4px; padding: 0.75rem; margin: 0.5rem 0;">
                <strong>Using Customer ID:</strong> {customer_id_env}<br>
                <small style="color: #5f6368;">💡 If your developer token is 'approved for test accounts only', make sure this is a test customer ID.</small>
            </div>
            """, unsafe_allow_html=True)

        col1a, col1b = st.columns(2)
        with col1a:
            max_keywords = st.number_input(
                "Max Keywords",
                min_value=100,
                max_value=5000,
                value=2000,
                step=100,
            )
        with col1b:
            include_adult = st.checkbox("Include Adult Keywords", value=False)

    with col2:
        st.markdown("### Targeting")
        st.markdown(f"""
        <div style="background-color: #f8f9fa; border: 1px solid #dadce0; border-radius: 4px; padding: 1rem; margin-bottom: 1rem;">
            <div style="margin-bottom: 0.5rem;"><strong>Language:</strong> English</div>
            <div style="margin-bottom: 0.5rem;"><strong>Network:</strong> Google Search</div>
            <div><strong>Locations:</strong> {len(DEFAULT_COUNTRIES)} countries</div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Generate Keywords", type="primary", use_container_width=True):
            if not blog_content or not blog_content.strip():
                st.markdown("""
                <div style="background-color: #fce8e6; border-left: 4px solid #ea4335; border-radius: 4px; padding: 1rem; margin: 1rem 0;">
                    Please paste blog content before generating keywords.
                </div>
                """, unsafe_allow_html=True)
                return

            if not website_url or not website_url.strip():
                st.markdown("""
                <div style="background-color: #fce8e6; border-left: 4px solid #ea4335; border-radius: 4px; padding: 1rem; margin: 1rem 0;">
                    Please provide a website URL.
                </div>
                """, unsafe_allow_html=True)
                return

            # Validate environment variables
            required_vars = [
                "GOOGLE_ADS_DEVELOPER_TOKEN",
                "GOOGLE_ADS_CLIENT_ID",
                "GOOGLE_ADS_CLIENT_SECRET",
                "GOOGLE_ADS_REFRESH_TOKEN",
                "GOOGLE_ADS_CUSTOMER_ID",
                "OPENAI_API_KEY",
            ]
            missing_vars = [var for var in required_vars if not get_env_var(var)]
            if missing_vars:
                st.markdown(f"""
                <div style="background-color: #fce8e6; border-left: 4px solid #ea4335; border-radius: 4px; padding: 1rem; margin: 1rem 0;">
                    <strong>Missing environment variables:</strong> {', '.join(missing_vars)}<br>
                    Please check your Streamlit Cloud secrets or .env file.
                </div>
                """, unsafe_allow_html=True)
                return

            with st.spinner("Generating keywords..."):
                try:
                    # Step 1: Create Google Ads client
                    google_ads_client = create_google_ads_client()
                    customer_id = get_env_var("GOOGLE_ADS_CUSTOMER_ID")
                    # Remove dashes from customer ID for API calls
                    customer_id_clean = customer_id.replace("-", "") if customer_id else None

                    # Step 2: Resolve geo targets
                    with st.spinner("Resolving geo targets..."):
                        geo_targets = resolve_countries(google_ads_client, DEFAULT_COUNTRIES)
                        if not geo_targets:
                            st.markdown("""
                            <div style="background-color: #fce8e6; border-left: 4px solid #ea4335; border-radius: 4px; padding: 1rem; margin: 1rem 0;">
                                <strong>Failed to resolve geo targets.</strong> Please check your Google Ads credentials.<br>
                                💡 Tip: Some territories may not be available. Try with a smaller country list or check your API access.
                            </div>
                            """, unsafe_allow_html=True)
                            return
                        
                        total_resolved = len(geo_targets)
                        # Note: API limits to 10 geo targets per request
                        if total_resolved > 10:
                            st.markdown(f"""
                            <div style="background-color: #fef7e0; border-left: 4px solid #fbbc04; border-radius: 4px; padding: 1rem; margin: 1rem 0;">
                                ⚠️ Resolved {total_resolved} geo targets, but API limits to 10 per request. Using first 10.
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"""
                            <div style="background-color: #e6f4ea; border-left: 4px solid #34a853; border-radius: 4px; padding: 1rem; margin: 1rem 0;">
                                ✓ Resolved {total_resolved} geo targets (out of {len(DEFAULT_COUNTRIES)} countries)
                            </div>
                            """, unsafe_allow_html=True)

                    # Step 3: Generate keyword ideas
                    with st.spinner(f"Fetching keyword ideas from Google Ads (up to {max_keywords})..."):
                        keyword_ideas = generate_keyword_ideas(
                            client=google_ads_client,
                            customer_id=customer_id_clean,
                            website_url=website_url,
                            geo_target_constants=geo_targets,
                            max_results=max_keywords,
                            include_adult_keywords=include_adult,
                        )

                    if not keyword_ideas:
                        st.markdown("""
                        <div style="background-color: #fef7e0; border-left: 4px solid #fbbc04; border-radius: 4px; padding: 1rem; margin: 1rem 0;">
                            No keyword ideas were returned from Google Ads API.
                        </div>
                        """, unsafe_allow_html=True)
                        return

                    st.session_state.keyword_ideas = keyword_ideas

                    # Step 4: Generate CSV
                    csv_content = keyword_ideas_to_csv(keyword_ideas)
                    st.session_state.csv_content = csv_content

                    st.markdown(f"""
                    <div style="background-color: #e6f4ea; border-left: 4px solid #34a853; border-radius: 4px; padding: 1rem; margin: 1rem 0;">
                        Generated {len(keyword_ideas)} keyword ideas!
                    </div>
                    """, unsafe_allow_html=True)

                    # Step 5: Send to GPT-5.2
                    with st.spinner("Categorizing keywords with GPT-5.2..."):
                        # Use top keywords for GPT to save tokens
                        top_keywords = get_top_keywords_by_volume(keyword_ideas, top_k=500)
                        top_csv = keyword_ideas_to_csv(top_keywords)

                        openai_client = create_openai_client()
                        gpt_results = categorize_keywords_with_gpt52(
                            client=openai_client,
                            blog_content=blog_content,
                            csv_content=top_csv,
                            developer_prompt=DEVELOPER_PROMPT,
                        )

                        st.session_state.gpt_results = gpt_results

                    if "error" in gpt_results:
                        st.markdown(f"""
                        <div style="background-color: #fce8e6; border-left: 4px solid #ea4335; border-radius: 4px; padding: 1rem; margin: 1rem 0;">
                            <strong>GPT-5.2 Error:</strong> {gpt_results['error']}
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown("""
                        <div style="background-color: #e6f4ea; border-left: 4px solid #34a853; border-radius: 4px; padding: 1rem; margin: 1rem 0;">
                            Keywords categorized successfully!
                        </div>
                        """, unsafe_allow_html=True)

                except Exception as e:
                    error_msg = str(e)
                    # Check for API not enabled error
                    if "SERVICE_DISABLED" in error_msg or "has not been used" in error_msg:
                        st.error("⚠️ Google Ads API Not Enabled")
                        st.markdown("""
                        **The Google Ads API needs to be enabled in your Google Cloud project.**
                        
                        1. Visit: https://console.developers.google.com/apis/api/googleads.googleapis.com/overview?project=978403786956
                        2. Click **"Enable"** button
                        3. Wait a few minutes for the API to activate
                        4. Try again
                        
                        If you just enabled it, wait 2-3 minutes for the changes to propagate.
                        """)
                    elif "PERMISSION_DENIED" in error_msg:
                        st.error("⚠️ Permission Denied")
                        # The error message already contains helpful guidance
                        st.markdown(error_msg.split("\n\n⚠️")[1] if "\n\n⚠️" in error_msg else error_msg)
                    else:
                        st.error(f"Error: {error_msg}")
                        # Only show full traceback for non-user-friendly errors
                        if "⚠️" not in error_msg:
                            with st.expander("Technical Details"):
                                st.exception(e)

    # Results section
    if st.session_state.keyword_ideas:
        st.markdown("<hr style='margin: 2rem 0; border: none; border-top: 1px solid #dadce0;'>", unsafe_allow_html=True)
        st.markdown("## Results")

        # Keyword ideas preview
        st.markdown("### Keyword Ideas Preview")
        import pandas as pd
        df_keywords = pd.DataFrame(st.session_state.keyword_ideas[:100])  # Show top 100
        st.dataframe(df_keywords, use_container_width=True)

        # CSV download
        st.markdown("### Download CSV")
        st.download_button(
            label="Download Keyword Ideas CSV",
            data=st.session_state.csv_content,
            file_name="keyword_ideas.csv",
            mime="text/csv",
        )

        # GPT-5.2 results
        if st.session_state.gpt_results:
            st.markdown("### Categorized Keywords (GPT-5.2)")
            
            if "error" in st.session_state.gpt_results:
                st.markdown(f"""
                <div style="background-color: #fce8e6; border-left: 4px solid #ea4335; border-radius: 4px; padding: 1rem; margin: 1rem 0;">
                    {st.session_state.gpt_results["error"]}
                </div>
                """, unsafe_allow_html=True)
            else:
                # Display results in a nice format
                results = st.session_state.gpt_results

                col3, col4 = st.columns(2)

                with col3:
                    st.markdown("#### SEO Metadata")
                    st.markdown("""
                    <div style="background-color: #f8f9fa; border: 1px solid #dadce0; border-radius: 4px; padding: 1rem; margin-bottom: 1rem;">
                    """, unsafe_allow_html=True)
                    st.text_input("Focus Keyphrase", value=results.get("FocusKeyphrase", ""), disabled=True, label_visibility="visible")
                    st.text_area("SEO Title", value=results.get("SEOTitle", ""), disabled=True, height=60, label_visibility="visible")
                    st.text_area("SEO Excerpt", value=results.get("SEOExcerpt", ""), disabled=True, height=100, label_visibility="visible")
                    st.markdown("</div>", unsafe_allow_html=True)

                with col4:
                    st.markdown("#### Keyword Categories")
                    st.markdown("""
                    <div style="background-color: #f8f9fa; border: 1px solid #dadce0; border-radius: 4px; padding: 1rem;">
                    """, unsafe_allow_html=True)
                    
                    categories = [
                        ("High Search Volume", results.get("HighSearchVolumeKeywords", [])),
                        ("High Growth", results.get("HighGrowthKeywords", [])),
                        ("Long Tail", results.get("LongTailKeywords", [])),
                        ("Niche Emerging", results.get("NicheEmergingKeywords", [])),
                        ("Action Oriented", results.get("ActionOrientedKeywords", [])),
                    ]

                    for category_name, keywords in categories:
                        if keywords and keywords != "No applicable keywords.":
                            st.markdown(f"**{category_name}:**")
                            for kw in keywords:
                                st.markdown(f"- {kw}")
                        else:
                            st.markdown(f"**{category_name}:** *No applicable keywords*")
                    
                    st.markdown("</div>", unsafe_allow_html=True)

                # Downloads section
                st.markdown("### Download Results")
                st.markdown("""
                <div style="background-color: #ffffff; border: 1px solid #dadce0; border-radius: 8px; padding: 1.5rem; margin: 1rem 0;">
                """, unsafe_allow_html=True)
                
                # Primary download - Text document (highlighted)
                text_content = format_results_as_text(st.session_state.gpt_results)
                st.download_button(
                    label="📥 Download Keywords",
                    data=text_content,
                    file_name="keyword_categorization.txt",
                    mime="text/plain",
                    type="primary",
                    use_container_width=True,
                )
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Secondary download - JSON
                json_str = json.dumps(st.session_state.gpt_results, indent=2)
                st.download_button(
                    label="Download JSON",
                    data=json_str,
                    file_name="keyword_categorization.json",
                    mime="application/json",
                    use_container_width=True,
                )
                
                st.markdown("</div>", unsafe_allow_html=True)

                # Raw JSON viewer
                with st.expander("View Raw JSON"):
                    st.json(st.session_state.gpt_results)


if __name__ == "__main__":
    main()
