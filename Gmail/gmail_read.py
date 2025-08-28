# the purpose of this file is to connect Composio and be able to read from my Gmail.

import os
from dotenv import load_dotenv

# Import the Composio SDK
try:
    from composio import Composio
    print("✅ Composio imported successfully!")
except ImportError as e:
    print(f"❌ Composio import failed: {e}")
    print("Please install composio-sdk: pip install composio-sdk")
    exit(1)

# Load environment variables
load_dotenv()

# Composio configuration
COMPOSIO_AUTH_CONFIG_ID = os.environ.get('COMPSIO_GMAIL_AUTH_CONFIG')

# Initialize Composio client
composio_client = Composio()

# Basic Gmail reader class
class GmailReader:
    def __init__(self):
        self.user_id = "content@clai.vc"  # Your Gmail address
        self.verified = False
        self._verify_connection()
    
    def _initiate_connection(self):
        """Initiate OAuth2 connection to Gmail"""
        try:
            if not COMPOSIO_AUTH_CONFIG_ID:
                print("❌ Composio auth config ID not configured")
                return False
            
            print(f"🔗 Initiating Gmail connection...")
            print(f"🔗 Auth Config ID: {COMPOSIO_AUTH_CONFIG_ID}")
            print(f"🔗 User ID: {self.user_id}")
            
            # Initiate OAuth2 connection using Composio SDK
            connection_request = composio_client.connected_accounts.initiate(
                user_id=self.user_id,
                auth_config_id=COMPOSIO_AUTH_CONFIG_ID,
            )
            
            print(f"✅ Connection request created: {connection_request.id}")
            print(f"🔗 Redirect URL: {connection_request.redirect_url}")
            print("\n🔗 Please open this URL in your browser to authenticate:")
            print(f"   {connection_request.redirect_url}")
            print("\nAfter authenticating, the connection will be persistent.")
            
            return True
                
        except Exception as e:
            print(f"❌ Connection initiation error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _verify_connection(self):
        """Verify the Gmail connection and check the email address"""
        try:
            print("🔍 Verifying Gmail connection...")
            
            # First, try to get the profile to verify the connection
            result = composio_client.tools.execute(
                "GMAIL_GET_PROFILE",
                user_id=self.user_id,
                arguments={"user_id": self.user_id}
            )
            
            if result and "data" in result and "response_data" in result["data"]:
                profile_data = result["data"]["response_data"]
                email_address = profile_data.get("emailAddress", "")
                
                print(f"✅ Gmail connection verified!")
                print(f"📧 Connected to: {email_address}")
                print(f"📊 Total messages: {profile_data.get('messagesTotal', 0)}")
                print(f"📊 Total threads: {profile_data.get('threadsTotal', 0)}")
                
                if email_address == self.user_id:
                    print("✅ Email address matches expected: content@clai.vc")
                    self.verified = True
                else:
                    print(f"⚠️  Warning: Connected to {email_address} instead of {self.user_id}")
                    self.verified = True  # Still mark as verified since connection works
                
                return True
            else:
                print("❌ No active Gmail connection found")
                print("🔗 Initiating new connection...")
                return self._initiate_connection()
                
        except Exception as e:
            print(f"❌ Error verifying connection: {e}")
            print("🔗 Attempting to initiate new connection...")
            return self._initiate_connection()
    
    def read_emails(self, max_results=10):
        """Read emails from Gmail"""
        try:
            if not self.verified:
                print("⚠️  Connection not verified. Attempting to verify...")
                if not self._verify_connection():
                    print("❌ Cannot read emails - connection verification failed")
                    return None
            
            print(f"📧 Reading {max_results} emails...")
            result = composio_client.tools.execute(
                "GMAIL_FETCH_EMAILS",
                user_id=self.user_id,
                arguments={
                    "user_id": self.user_id,
                    "max_results": max_results,
                    "include_payload": True,
                    "verbose": True
                }
            )
            return result
        except Exception as e:
            print(f"❌ Error reading emails: {e}")
            return None

# Initialize the reader
gmail_reader = GmailReader()

if __name__ == '__main__':
    print("🚀 Testing Gmail Reader")
    if gmail_reader.verified:
        result = gmail_reader.read_emails(max_results=5)
        print(f"Result: {result}")
    else:
        print("❌ Gmail connection not verified")
        print("💡 Please complete the OAuth authentication in your browser and run the script again.")
