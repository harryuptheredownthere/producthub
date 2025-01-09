import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Microsoft OAuth Configuration
CLIENT_ID = os.getenv('AZURE_CLIENT_ID')
CLIENT_SECRET = os.getenv('AZURE_CLIENT_SECRET')
TENANT_ID = os.getenv('AZURE_TENANT_ID')
REDIRECT_URI = os.getenv('REDIRECT_URI', 'http://localhost:8080/onedrive/callback')

# OneDrive Configuration
SHARED_FOLDER_DRIVE_ID = os.getenv('SHARED_FOLDER_DRIVE_ID')
SHARED_FOLDER_ITEM_ID = os.getenv('SHARED_FOLDER_ITEM_ID')