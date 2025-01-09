import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Auth Configuration
CLIENT_ID = os.getenv('AZURE_CLIENT_ID')
CLIENT_SECRET = os.getenv('AZURE_CLIENT_SECRET')
TENANT_ID = os.getenv('AZURE_TENANT_ID')
REDIRECT_URI = os.getenv('REDIRECT_URI', 'http://localhost:8080/onedrive/callback')

# OneDrive Configuration
SHARED_FOLDER_DRIVE_ID = os.getenv('SHARED_FOLDER_DRIVE_ID')
SHARED_FOLDER_ITEM_ID = os.getenv('SHARED_FOLDER_ITEM_ID')

# API Configuration
SCOPES = ["https://graph.microsoft.com/Files.ReadWrite", "offline_access"]
MS_GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"

# URLs
AUTH_URL = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/authorize"
TOKEN_URL = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"

# Upload Configuration
CHUNK_SIZE = 5 * 1024 * 1024  # 5MB chunks