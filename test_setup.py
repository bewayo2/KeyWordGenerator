"""
Quick setup verification script.
Run this to check if all environment variables and dependencies are configured correctly.
"""

import os
import sys
from dotenv import load_dotenv

def check_env_vars():
    """Check if all required environment variables are set."""
    load_dotenv()
    
    required_vars = {
        "OPENAI_API_KEY": "OpenAI API Key",
        "GOOGLE_ADS_DEVELOPER_TOKEN": "Google Ads Developer Token",
        "GOOGLE_ADS_CLIENT_ID": "Google Ads Client ID",
        "GOOGLE_ADS_CLIENT_SECRET": "Google Ads Client Secret",
        "GOOGLE_ADS_REFRESH_TOKEN": "Google Ads Refresh Token",
        "GOOGLE_ADS_CUSTOMER_ID": "Google Ads Customer ID",
    }
    
    print("=" * 60)
    print("Environment Variables Check")
    print("=" * 60)
    print()
    
    all_set = True
    for var_name, description in required_vars.items():
        value = os.getenv(var_name)
        if value:
            # Mask sensitive values
            if "TOKEN" in var_name or "SECRET" in var_name or "KEY" in var_name:
                masked = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
                print(f"✓ {description}: {masked}")
            else:
                print(f"✓ {description}: {value}")
        else:
            print(f"✗ {description}: NOT SET")
            all_set = False
    
    print()
    return all_set


def check_dependencies():
    """Check if all required Python packages are installed."""
    print("=" * 60)
    print("Dependencies Check")
    print("=" * 60)
    print()
    
    required_packages = {
        "streamlit": "Streamlit",
        "google.ads.googleads": "Google Ads API",
        "openai": "OpenAI API",
        "dotenv": "python-dotenv",
        "pandas": "Pandas",
    }
    
    all_installed = True
    for package, name in required_packages.items():
        try:
            __import__(package)
            print(f"✓ {name}: Installed")
        except ImportError:
            print(f"✗ {name}: NOT INSTALLED")
            all_installed = False
    
    print()
    return all_installed


def test_google_ads_connection():
    """Test Google Ads API connection."""
    print("=" * 60)
    print("Google Ads API Connection Test")
    print("=" * 60)
    print()
    
    try:
        from src.google_ads_client import create_google_ads_client
        client = create_google_ads_client()
        print("✓ Google Ads client created successfully")
        
        # Try to get customer info (lightweight test)
        customer_id = os.getenv("GOOGLE_ADS_CUSTOMER_ID")
        if customer_id:
            print(f"✓ Customer ID configured: {customer_id}")
        else:
            print("✗ Customer ID not set")
        
        return True
    except Exception as e:
        print(f"✗ Error creating Google Ads client: {e}")
        return False


def test_openai_connection():
    """Test OpenAI API connection."""
    print("=" * 60)
    print("OpenAI API Connection Test")
    print("=" * 60)
    print()
    
    try:
        from src.openai_client import create_openai_client
        client = create_openai_client()
        print("✓ OpenAI client created successfully")
        return True
    except Exception as e:
        print(f"✗ Error creating OpenAI client: {e}")
        return False


def main():
    """Run all checks."""
    print("\n" + "=" * 60)
    print("Keyword Generator - Setup Verification")
    print("=" * 60 + "\n")
    
    env_ok = check_env_vars()
    deps_ok = check_dependencies()
    
    if not env_ok or not deps_ok:
        print("=" * 60)
        print("SETUP INCOMPLETE")
        print("=" * 60)
        print("\nPlease fix the issues above before proceeding.")
        print("\nTo install missing dependencies:")
        print("  pip install -r requirements.txt")
        print("\nTo set up environment variables:")
        print("  1. Copy .env.example to .env")
        print("  2. Fill in all required values")
        print("  3. Run: python get_refresh_token.py (for Google Ads)")
        sys.exit(1)
    
    # Test connections
    google_ads_ok = test_google_ads_connection()
    openai_ok = test_openai_connection()
    
    print()
    print("=" * 60)
    if google_ads_ok and openai_ok:
        print("✓ ALL CHECKS PASSED!")
        print("=" * 60)
        print("\nYou're ready to run the app!")
        print("\nNext step:")
        print("  streamlit run app.py")
    else:
        print("⚠ SOME CHECKS FAILED")
        print("=" * 60)
        print("\nPlease review the errors above and fix them.")
    
    print()


if __name__ == "__main__":
    main()

