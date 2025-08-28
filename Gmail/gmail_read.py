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

# Import the connection manager
from gmail_login import connection_manager

# Load environment variables
load_dotenv()

# Initialize Composio client
composio_client = Composio()

# Basic Gmail reader class
class GmailReader:
    def __init__(self):
        self.user_id = "content@clai.vc"  # Your Gmail address
        self.verified = False
        self._verify_connection()
    
    def _verify_connection(self):
        """Verify the Gmail connection using the connection manager"""
        try:
            # Use the connection manager to verify the connection
            if connection_manager.verify_connection():
                self.verified = connection_manager.verified
                return True
            else:
                print("❌ Connection verification failed")
                return False
        except Exception as e:
            print(f"❌ Error verifying connection: {e}")
            return False
    
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
                    "include_payload": False,
                    "verbose": False # think I have these last two set the way I want.
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
        result = gmail_reader.read_emails(max_results=1)
        print(f"Result: {result}")

    else:
        print("❌ Gmail connection not verified")
        print("💡 Please complete the OAuth authentication in your browser and run the script again.")
