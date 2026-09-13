# ==============================================================================
# PHANTOMX GOOGLE DRIVE AUTOMATED UPLOADER ENGINE
# ==============================================================================
# Architecture Discipline: Surgical | Aviation | Military
# Account: manish91082@gmail.com
# Credentials: GCP OAuth Client ID (omnisweeper)
# ==============================================================================

import os
import sys
import json
import webbrowser
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")

ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(ENGINE_DIR)
ZIP_PATH = os.path.join(PROJECT_DIR, "v2_v3_engine_colab_ready.zip")
NOTEBOOK_PATH = os.path.join(ENGINE_DIR, "v2_v3_master_colab.ipynb")
CLIENT_SECRET_FILE = os.path.join(ENGINE_DIR, "client_secret.json")

print("================================================================================", flush=True)
print("🚀 PHANTOMX AUTOMATED GOOGLE DRIVE UPLOAD HARNESS", flush=True)
print("================================================================================", flush=True)
print(f"Target Account: manish91082@gmail.com", flush=True)
print(f"Zip File to Upload: {ZIP_PATH} ({os.path.getsize(ZIP_PATH)/(1024*1024):.2f} MB)", flush=True)
print(f"Notebook File to Upload: {NOTEBOOK_PATH}", flush=True)
print(f"GCP Credentials File: {CLIENT_SECRET_FILE}", flush=True)
print("--------------------------------------------------------------------------------", flush=True)

def upload_via_gdrive():
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials

        print("🔑 Initializing GCP OAuth Flow (Project: omnisweeper) for manish91082@gmail.com...", flush=True)

        SCOPES = ['https://www.googleapis.com/auth/drive.file']
        creds = None

        token_path = os.path.join(ENGINE_DIR, "gdrive_token.json")
        if os.path.exists(token_path):
            try:
                creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            except Exception:
                creds = None

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                print("🌐 Opening Google Account OAuth Authorization Page in your default browser (Chrome)...", flush=True)
                flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
                creds = flow.run_local_server(port=0, open_browser=True)

            with open(token_path, "w", encoding="utf-8") as token:
                token.write(creds.to_json())

        service = build('drive', 'v3', credentials=creds)

        print("\n[1/2] Uploading v2_v3_engine_colab_ready.zip to Google Drive...", flush=True)
        file_metadata = {'name': 'v2_v3_engine_colab_ready.zip'}
        media = MediaFileUpload(ZIP_PATH, mimetype='application/zip', resumable=True)
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        print(f"✅ Uploaded ZIP successfully! File ID: {file.get('id')}", flush=True)

        print("\n[2/2] Uploading v2_v3_master_colab.ipynb to Google Drive...", flush=True)
        nb_metadata = {'name': 'v2_v3_master_colab.ipynb'}
        nb_media = MediaFileUpload(NOTEBOOK_PATH, mimetype='application/x-ipynb+json', resumable=True)
        nb_file = service.files().create(body=nb_metadata, media_body=nb_media, fields='id').execute()
        print(f"✅ Uploaded Notebook successfully! File ID: {nb_file.get('id')}", flush=True)

        print("\n================================================================================", flush=True)
        print("🎉 ALL FILES UPLOADED TO GOOGLE DRIVE AUTOMATICALLY!", flush=True)
        print("================================================================================", flush=True)

    except Exception as e:
        print(f"\n⚠️ OAuth Authorization Notice: {e}", flush=True)

if __name__ == "__main__":
    upload_via_gdrive()
