# Streamlit Cloud Setup Guide

This guide explains how to configure your environment variables (secrets) for Streamlit Cloud deployment.

## Setting Up Secrets in Streamlit Cloud

1. **Go to your Streamlit Cloud dashboard**: https://share.streamlit.io/
2. **Select your app** (or create a new app if you haven't already)
3. **Click on "Settings"** (or the gear icon)
4. **Click on "Secrets"** in the left sidebar
5. **Add your secrets** in TOML format

## Secrets Format

Add all your environment variables in the following format:

```toml
google_ads_developer_token = "your_developer_token_here"
google_ads_client_id = "your_client_id_here"
google_ads_client_secret = "your_client_secret_here"
google_ads_refresh_token = "your_refresh_token_here"
google_ads_customer_id = "XXX-XXX-XXXX"
openai_api_key = "your_openai_api_key_here"
```

**Important Notes:**
- Use **lowercase with underscores** (e.g., `google_ads_client_id` not `GOOGLE_ADS_CLIENT_ID`)
- The app will automatically convert these to the expected format
- Do NOT include quotes around the values in the TOML file
- Each secret should be on its own line

## Example Secrets File

```toml
google_ads_developer_token = "ABC123..."
google_ads_client_id = "123456789-abcdefg.apps.googleusercontent.com"
google_ads_client_secret = "GOCSPX-..."
google_ads_refresh_token = "1//0g..."
google_ads_customer_id = "814-562-8296"
openai_api_key = "sk-..."
```

## After Adding Secrets

1. **Save** the secrets file
2. **Redeploy** your app (or it will auto-redeploy)
3. The app should now be able to access all environment variables

## Troubleshooting

If you still see "Missing environment variables" errors:

1. **Check the secret names** - they must be lowercase with underscores
2. **Verify the values** - make sure there are no extra spaces or quotes
3. **Check the app logs** - Streamlit Cloud shows errors in the app logs
4. **Redeploy** - sometimes a redeploy is needed after adding secrets

## Local Development

For local development, continue using the `.env` file. The app will automatically:
- Use Streamlit secrets when running on Streamlit Cloud
- Use `.env` file when running locally

