import os
import io
import json
import secrets
import requests
import mimetypes
import tempfile
import openpyxl
import logging
import pandas as pd
from dotenv import load_dotenv
from functools import wraps
from typing import Optional
from datetime import datetime, timedelta
from flask import Flask, request, render_template, redirect, session, url_for, jsonify, send_from_directory
from flask_cors import CORS
from urllib.parse import urlencode
from config import (
    CLIENT_ID,
    CLIENT_SECRET,
    TENANT_ID,
    REDIRECT_URI,
    SHARED_FOLDER_DRIVE_ID,
    SHARED_FOLDER_ITEM_ID,
    SCOPES,
    MS_GRAPH_API_BASE,
    AUTH_URL,
    TOKEN_URL,
    CHUNK_SIZE
)

app = Flask(__name__, static_folder='../frontend/build')
app.secret_key = os.urandom(32)  # Required for sessions

# CORS setup
CORS(app, 
     resources={r"/*": {
         "origins": ["http://localhost:3000"],  # Changed from 5173 to 3000
         "methods": ["GET", "POST", "OPTIONS"],
         "allow_headers": ["Content-Type", "Accept", "Authorization"],
         "supports_credentials": True
     }},
     expose_headers=["Content-Type", "Authorization"])

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def refresh_access_token() -> Optional[str]:
    """Refresh the access token using the refresh token"""
    refresh_token = session.get('refresh_token')
    if not refresh_token:
        return None

    try:
        data = {
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'scope': ' '.join(SCOPES)
        }

        response = requests.post(TOKEN_URL, data=data)
        if response.status_code == 200:
            tokens = response.json()
            store_tokens(tokens)
            return tokens['access_token']
        else:
            logger.error(f"Token refresh failed: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error refreshing token: {str(e)}")
        return None

def store_tokens(tokens: dict) -> None:
    """Store tokens in session with expiration"""
    session['access_token'] = tokens['access_token']
    session['refresh_token'] = tokens.get('refresh_token')  # Might not be present in refresh response
    # Store expiration time (subtract 5 minutes for safety margin)
    expires_in = int(tokens['expires_in']) - 300
    session['token_expiration'] = (datetime.now() + timedelta(seconds=expires_in)).timestamp()

def requires_auth(f):
    """Decorator to check for valid access token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        # Check if token exists and is not expired
        if not is_token_valid():
            # Try to refresh token
            new_token = refresh_access_token()
            if not new_token:
                return jsonify({
                    'success': False,
                    'message': 'Authentication required'
                }), 401
        return f(*args, **kwargs)
    return decorated

def is_token_valid() -> bool:
    """Check if the current access token is valid"""
    token_expiration = session.get('token_expiration')
    if not token_expiration:
        return False
    return datetime.now().timestamp() < token_expiration

def get_graph_headers(access_token: Optional[str] = None) -> dict:
    """Get headers for Microsoft Graph API requests"""
    if not access_token:
        access_token = session.get('access_token')
    
    return {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
def create_upload_session(relative_path: str, filename: str) -> Optional[str]:
    """Create an upload session for a file in the predefined shared folder"""
    if not is_token_valid():
        if not refresh_access_token():
            logger.error("Unable to refresh token.")
            return None

    endpoint = (
        f"{MS_GRAPH_API_BASE}/drives/{SHARED_FOLDER_DRIVE_ID}/items/{SHARED_FOLDER_ITEM_ID}"
        f":/{relative_path}/{filename}:/createUploadSession"
    )

    headers = get_graph_headers()
    body = {
        "item": {
            "@microsoft.graph.conflictBehavior": "replace"
        }
    }

    try:
        response = requests.post(endpoint, headers=headers, json=body)
        if response.status_code not in (200, 201):
            logger.error(f"Error creating upload session: {response.text}")
            return None

        data = response.json()
        return data.get("uploadUrl")
    except Exception as e:
        logger.error(f"Failed to create upload session: {str(e)}")
        return None

def upload_file_in_chunks(upload_url: str, file_content: bytes, chunk_size: int = CHUNK_SIZE):
    """Upload a file in chunks using the upload session URL"""
    file_size = len(file_content)
    bytes_uploaded = 0

    try:
        while bytes_uploaded < file_size:
            chunk_end = min(bytes_uploaded + chunk_size, file_size)
            chunk_data = file_content[bytes_uploaded:chunk_end]

            content_range = f"bytes {bytes_uploaded}-{chunk_end - 1}/{file_size}"
            headers = {
                "Content-Length": str(len(chunk_data)),
                "Content-Range": content_range,
            }
            
            put_response = requests.put(upload_url, headers=headers, data=chunk_data)

            if put_response.status_code in (200, 201):
                # Upload complete
                return put_response.json()
            elif put_response.status_code == 202:
                # Partial upload success, continue with next chunk
                bytes_uploaded = chunk_end
            else:
                raise Exception(f"Error uploading chunk: {put_response.text}")

        raise Exception("Unexpected end of upload loop.")
    except Exception as e:
        logger.error(f"Failed during chunk upload: {str(e)}")
        raise

def upload_large_file_to_shared_folder(
    drive_id: str,
    folder_item_id: str,
    relative_path: str,
    filename: str,
    file_content: bytes
):
    """Upload a large file to a shared folder in OneDrive"""
    upload_url = create_upload_session(
        relative_path=relative_path, 
        filename=filename
    )
    if not upload_url:
        raise Exception("No uploadUrl returned for shared folder upload.")
    return upload_file_in_chunks(upload_url, file_content)

def process_excel_file(file_content: bytes, company: str, brand_name: str, season: str):
    """Process Excel file based on company requirements"""
    try:
        # Create file-like object from bytes
        file_stream = io.BytesIO(file_content)
        wb = openpyxl.load_workbook(file_stream, data_only=True)
        today = datetime.today().strftime("%Y%m%d")
        files_to_upload = []

        if company == "UP THERE":
            # Process Product sheet
            product_sheet = wb["InventoryList_Master"]
            df_product = pd.DataFrame(product_sheet.values)
            df_product.columns = df_product.iloc[0]
            df_product = df_product.drop(df_product.index[0])

            # Process PO sheet
            po_sheet = wb["PO_MASTER"]
            df_po = pd.DataFrame(po_sheet.values)
            df_po.columns = df_po.iloc[0]
            df_po = df_po.drop(df_po.index[0])

            # Prepare files for upload
            product_csv = io.StringIO()
            df_product.to_csv(product_csv, index=False)
            
            po_csv = io.StringIO()
            df_po.to_csv(po_csv, index=False)

            files_to_upload = [
                {
                    'content': product_csv.getvalue().encode(),
                    'filename': f"Product{brand_name}_{today}.csv",
                    'relative_path': f"Product/{season}/{company}/Product - CSV"
                },
                {
                    'content': po_csv.getvalue().encode(),
                    'filename': f"PO{brand_name}_{today}.csv",
                    'relative_path': f"Product/{season}/{company}/PO - CSV"
                },
                {
                    'content': file_content,
                    'filename': f"Master{brand_name}_{today}.xlsx",
                    'relative_path': f"Product/{season}/{company}/Master - XLSX"
                }
            ]

        elif company == "UTA":
            # Process UTA data
            product_sheet = wb["InventoryList_Master"]
            df_product = pd.DataFrame(product_sheet.values)
            df_product.columns = df_product.iloc[0]
            df_product = df_product.drop(df_product.index[0])

            # Prepare files for upload
            product_csv = io.StringIO()
            df_product.to_csv(product_csv, index=False)

            files_to_upload = [
                {
                    'content': product_csv.getvalue().encode(),
                    'filename': f"Product{brand_name}_{today}.csv",
                    'relative_path': f"Product/{season}/{company}/Product - CSV"
                },
                {
                    'content': file_content,
                    'filename': f"Master{brand_name}_{today}.xlsx",
                    'relative_path': f"Product/{season}/{company}/Master - XLSX"
                }
            ]

        else:
            raise ValueError("Unknown company provided")

        return files_to_upload, "Files processed successfully"

    except Exception as e:
        logger.error(f"Error processing Excel file: {str(e)}")
        raise

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

@app.route("/auth/status")
def auth_status():
    """Check if the user has a valid session"""
    try:
        # Check if token exists and is valid
        if is_token_valid():
            return jsonify({
                'isAuthenticated': True
            })
            
        # Try to refresh token if we have a refresh token
        if refresh_access_token():
            return jsonify({
                'isAuthenticated': True
            })
            
        return jsonify({
            'isAuthenticated': False
        })
        
    except Exception as e:
        logger.error(f"Error checking auth status: {str(e)}")
        return jsonify({
            'isAuthenticated': False,
            'error': str(e)
        }), 500

def process_excel_file(file_content: bytes, company: str, brand_name: str, season: str):
    """Process Excel file based on company requirements"""
    try:
        # Create file-like object from bytes
        file_stream = io.BytesIO(file_content)
        wb = openpyxl.load_workbook(file_stream, data_only=True)
        today = datetime.today().strftime("%Y%m%d")
        files_to_upload = []

        if company == "UP THERE":
            # Process Product sheet
            product_sheet = wb["InventoryList_Master"]
            df_product = pd.DataFrame(product_sheet.values)
            df_product.columns = df_product.iloc[0]
            df_product = df_product.drop(df_product.index[0])

            # Process PO sheet
            po_sheet = wb["PO_MASTER"]
            df_po = pd.DataFrame(po_sheet.values)
            df_po.columns = df_po.iloc[0]
            df_po = df_po.drop(df_po.index[0])

            # Prepare files for upload
            product_csv = io.StringIO()
            df_product.to_csv(product_csv, index=False)
            
            po_csv = io.StringIO()
            df_po.to_csv(po_csv, index=False)

            files_to_upload = [
                {
                    'content': product_csv.getvalue().encode(),
                    'filename': f"Product{brand_name}_{today}.csv",
                    'relative_path': f"Product/{season}/{company}/Product - CSV"
                },
                {
                    'content': po_csv.getvalue().encode(),
                    'filename': f"PO{brand_name}_{today}.csv",
                    'relative_path': f"Product/{season}/{company}/PO - CSV"
                },
                {
                    'content': file_content,
                    'filename': f"Master{brand_name}_{today}.xlsx",
                    'relative_path': f"Product/{season}/{company}/Master - XLSX"
                }
            ]

        elif company == "UTA":
            # Process UTA data
            product_sheet = wb["InventoryList_Master"]
            df_product = pd.DataFrame(product_sheet.values)
            df_product.columns = df_product.iloc[0]
            df_product = df_product.drop(df_product.index[0])

            # Prepare files for upload
            product_csv = io.StringIO()
            df_product.to_csv(product_csv, index=False)

            files_to_upload = [
                {
                    'content': product_csv.getvalue().encode(),
                    'filename': f"Product{brand_name}_{today}.csv",
                    'relative_path': f"Product/{season}/{company}/Product - CSV"
                },
                {
                    'content': file_content,
                    'filename': f"Master{brand_name}_{today}.xlsx",
                    'relative_path': f"Product/{season}/{company}/Master - XLSX"
                }
            ]

        else:
            raise ValueError("Unknown company provided")

        return files_to_upload, "Files processed successfully"

    except Exception as e:
        logger.error(f"Error processing Excel file: {str(e)}")
        raise

@app.route("/auth/url")
def get_auth_url():
    try:
        logger.debug("Generating auth URL...")
        state = secrets.token_urlsafe(16)
        params = {
            'client_id': CLIENT_ID,
            'response_type': 'code',
            'redirect_uri': REDIRECT_URI,
            'scope': ' '.join(SCOPES),
            'response_mode': 'query',
            'state': state
        }
        auth_url = f"{AUTH_URL}?{urlencode(params)}"
        logger.debug(f"Generated auth URL: {auth_url}")
        return jsonify({
            'auth_url': auth_url
        })
    except Exception as e:
        logger.error(f"Error generating auth URL: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route("/onedrive/callback")
def onedrive_callback():
    try:
        code = request.args.get('code')
        if not code:
            return redirect("http://localhost:3000?error=no_code")

        token_data = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "scope": ' '.join(SCOPES)
        }

        token_response = requests.post(TOKEN_URL, data=token_data)
        if token_response.status_code != 200:
            logger.error(f"Token exchange failed: {token_response.text}")
            return redirect("http://localhost:3000?error=token_exchange_failed")

        tokens = token_response.json()
        store_tokens(tokens)  # Store tokens in session
        logger.debug("Tokens stored successfully")
        
        return redirect("http://localhost:3000?auth=success")

    except Exception as e:
        logger.error(f"Callback error: {str(e)}")
        return redirect("http://localhost:3000?error=callback_failed")

@app.route("/upload", methods=["POST"])
@requires_auth
def upload():
    try:
        logger.debug(f"Received upload request")
        logger.debug(f"Files in request: {request.files}")
        logger.debug(f"Form data: {request.form}")

        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': 'No file provided'
            }), 400

        # Get form data
        file = request.files['file']
        brand_name = request.form.get('brand_name')
        company = request.form.get('company')
        season = request.form.get('season')

        if not all([brand_name, company, season]):
            missing_fields = [field for field, value in 
                            [('brand_name', brand_name), 
                             ('company', company), 
                             ('season', season)] 
                            if not value]
            return jsonify({
                'success': False,
                'message': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400

        # Read file content
        file_content = file.read()
        
        # Process Excel file
        try:
            files_to_upload, message = process_excel_file(
                file_content, 
                company, 
                brand_name, 
                season
            )
        except Exception as e:
            logger.error(f"Error processing Excel file: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Error processing Excel file: {str(e)}'
            }), 400

        # Upload all files
        upload_results = []
        for file_info in files_to_upload:
            try:
                result = upload_large_file_to_shared_folder(
                    SHARED_FOLDER_DRIVE_ID,
                    SHARED_FOLDER_ITEM_ID,
                    file_info['relative_path'],
                    file_info['filename'],
                    file_info['content']
                )
                
                upload_results.append({
                    'filename': file_info['filename'],
                    'path': f"{file_info['relative_path']}/{file_info['filename']}",
                    'web_url': result.get('webUrl')
                })
            except Exception as e:
                logger.error(f"Error uploading {file_info['filename']}: {str(e)}")
                return jsonify({
                    'success': False,
                    'message': f'Error uploading {file_info["filename"]}: {str(e)}'
                }), 500

        return jsonify({
            'success': True,
            'message': message,
            'files': upload_results
        })

    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Upload failed: {str(e)}'
        }), 500

        
@app.route("/health")
def health_check():
    return jsonify({"status": "healthy"})

if __name__ == "__main__":
    app.run(port=8080, debug=True)