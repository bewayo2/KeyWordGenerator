"""
Helper script to obtain Google Ads API refresh token via OAuth 2.0 flow.
Run this script once to generate your refresh token.
"""

import os
import sys
import webbrowser
from urllib.parse import urlparse, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from dotenv import load_dotenv

try:
    from google_auth_oauthlib.flow import Flow
except ImportError:
    print("Installing required package: google-auth-oauthlib")
    os.system(f"{sys.executable} -m pip install google-auth-oauthlib")
    from google_auth_oauthlib.flow import Flow


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP server to handle OAuth callback."""
    
    auth_code = None
    
    def do_GET(self):
        """Handle GET request from OAuth redirect."""
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)
        
        if "code" in query_params:
            OAuthCallbackHandler.auth_code = query_params["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"""
                <html>
                <body>
                <h1>Authorization Successful!</h1>
                <p>You can close this window and return to the terminal.</p>
                </body>
                </html>
                """
            )
        elif "error" in query_params:
            error = query_params["error"][0]
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(
                f"""
                <html>
                <body>
                <h1>Authorization Failed</h1>
                <p>Error: {error}</p>
                </body>
                </html>
                """.encode()
            )
        else:
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Invalid request</h1></body></html>")
    
    def log_message(self, format, *args):
        """Suppress log messages."""
        pass


def get_refresh_token():
    """Obtain refresh token via OAuth 2.0 flow."""
    
    # Load existing .env if it exists
    load_dotenv()
    
    print("=" * 60)
    print("Google Ads API Refresh Token Generator")
    print("=" * 60)
    print()
    
    # Get client ID and secret
    client_id = os.getenv("GOOGLE_ADS_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_ADS_CLIENT_SECRET")
    
    if not client_id:
        client_id = input("Enter your Google Ads Client ID: ").strip()
    
    if not client_secret:
        client_secret = input("Enter your Google Ads Client Secret: ").strip()
    
    if not client_id or not client_secret:
        print("Error: Client ID and Client Secret are required.")
        sys.exit(1)
    
    # OAuth 2.0 configuration
    redirect_uri = "http://127.0.0.1:8080/oauth2callback"
    scopes = ["https://www.googleapis.com/auth/adwords"]
    
    # Create OAuth flow
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri],
            }
        },
        scopes=scopes,
    )
    flow.redirect_uri = redirect_uri
    
    # Generate authorization URL
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",  # Force consent screen to get refresh token
    )
    
    print("Step 1: Opening browser for authorization...")
    print(f"Authorization URL: {auth_url}")
    print()
    print("Please authorize the application in your browser.")
    print("After authorization, you'll be redirected back to this script.")
    print()
    
    # Start local HTTP server to receive callback
    server = HTTPServer(("127.0.0.1", 8080), OAuthCallbackHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    
    # Open browser
    webbrowser.open(auth_url)
    
    # Wait for authorization code
    print("Waiting for authorization...")
    timeout = 300  # 5 minutes timeout
    elapsed = 0
    while OAuthCallbackHandler.auth_code is None and elapsed < timeout:
        import time
        time.sleep(1)
        elapsed += 1
    
    server.shutdown()
    
    if OAuthCallbackHandler.auth_code is None:
        print("Error: Authorization timeout. Please try again.")
        sys.exit(1)
    
    auth_code = OAuthCallbackHandler.auth_code
    print("Authorization code received!")
    print()
    
    # Exchange authorization code for tokens
    print("Step 2: Exchanging authorization code for tokens...")
    try:
        flow.fetch_token(code=auth_code)
        credentials = flow.credentials
        
        refresh_token = credentials.refresh_token
        
        if not refresh_token:
            print("Warning: No refresh token received.")
            print("This may happen if you've already authorized this app before.")
            print("Try revoking access and authorizing again.")
            sys.exit(1)
        
        print("Success! Refresh token obtained.")
        print()
        print("=" * 60)
        print("Your Refresh Token:")
        print("=" * 60)
        print(refresh_token)
        print("=" * 60)
        print()
        
        # Ask if user wants to save to .env
        save_to_env = input("Save refresh token to .env file? (y/n): ").strip().lower()
        
        if save_to_env == "y":
            env_file = ".env"
            env_content = ""
            
            # Read existing .env if it exists
            if os.path.exists(env_file):
                with open(env_file, "r", encoding="utf-8") as f:
                    env_content = f.read()
            
            # Update or add GOOGLE_ADS_REFRESH_TOKEN
            if "GOOGLE_ADS_REFRESH_TOKEN" in env_content:
                # Replace existing value
                lines = env_content.split("\n")
                updated_lines = []
                for line in lines:
                    if line.startswith("GOOGLE_ADS_REFRESH_TOKEN"):
                        updated_lines.append(f"GOOGLE_ADS_REFRESH_TOKEN={refresh_token}")
                    else:
                        updated_lines.append(line)
                env_content = "\n".join(updated_lines)
            else:
                # Add new line
                if env_content and not env_content.endswith("\n"):
                    env_content += "\n"
                env_content += f"GOOGLE_ADS_REFRESH_TOKEN={refresh_token}\n"
            
            # Also ensure Client ID and Secret are saved
            if "GOOGLE_ADS_CLIENT_ID" not in env_content:
                env_content = f"GOOGLE_ADS_CLIENT_ID={client_id}\n{env_content}"
            if "GOOGLE_ADS_CLIENT_SECRET" not in env_content:
                env_content = f"GOOGLE_ADS_CLIENT_SECRET={client_secret}\n{env_content}"
            
            # Write .env file
            with open(env_file, "w", encoding="utf-8") as f:
                f.write(env_content)
            
            print(f"Refresh token saved to {env_file}")
        else:
            print("Refresh token not saved. Please add it to your .env file manually:")
            print(f"GOOGLE_ADS_REFRESH_TOKEN={refresh_token}")
        
        print()
        print("Setup complete! You can now use the Google Ads API.")
        
    except Exception as e:
        print(f"Error exchanging authorization code: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        get_refresh_token()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(1)

