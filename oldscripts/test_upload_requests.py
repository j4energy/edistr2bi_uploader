# test_upload_requests.py
import os, msal, requests, urllib.parse
from dotenv import load_dotenv

load_dotenv()

TENANT      = os.getenv("TENANT_ID")                          # es. "j4srl.onmicrosoft.com" o GUID
CLIENT_ID   = os.getenv("CLIENT_ID")                          # App (client) ID
SITE_URL    = os.getenv("SHAREPOINT_URL")                     # https://j4srl.sharepoint.com/sites/J4EnenergyDataStorage
FOLDER_REL  = f"/sites/J4EnenergyDataStorage/{os.getenv('SHAREPOINT_FOLDER')}"  # "Shared Documents/Florence_group"
RESOURCE    = "https://j4srl.sharepoint.com"                  # scope base per SPO
CERT_PATH   = os.getenv("CLIENT_CERT_PATH") or "private_key.pem"
THUMBPRINT  = (os.getenv("CLIENT_CERT_THUMBPRINT") or "").replace(":","").strip() or None

# === 1) Token app-only via certificato ===
with open(CERT_PATH, "r") as f:
    private_key = f.read()

client_cred = {"private_key": private_key}
if THUMBPRINT:
    client_cred["thumbprint"] = THUMBPRINT

app = msal.ConfidentialClientApplication(
    client_id=CLIENT_ID,
    authority=f"https://login.microsoftonline.com/{TENANT}",
    client_credential=client_cred,
)
result = app.acquire_token_for_client(scopes=[f"{RESOURCE}/.default"])
if "access_token" not in result:
    raise SystemExit(f"Token error: {result}")

access_token = result["access_token"]

# === 2) Upload via REST ===
headers = {
    "Authorization": f"Bearer {access_token}",
    "Accept": "application/json;odata=nometadata",
    "Content-Type": "application/octet-stream",
}

# Prepara file di prova
os.makedirs("uploads", exist_ok=True)
local_path = "uploads/test.txt"
with open(local_path, "wb") as f:
    f.write(b"upload via REST + MSAL cert")

with open(local_path, "rb") as f:
    content = f.read()

# Server-relative path della cartella (URL-encoded)
folder_encoded = urllib.parse.quote(FOLDER_REL, safe="/")
file_name = "test.txt"
file_name_encoded = urllib.parse.quote(file_name)

# Endpoint REST:
# /_api/web/GetFolderByServerRelativePath(DecodedUrl='<encoded>')/Files/add(overwrite=true,url='<filename>')
upload_url = (
    f"{SITE_URL}/_api/web/"
    f"GetFolderByServerRelativePath(DecodedUrl='{folder_encoded}')/"
    f"Files/add(overwrite=true,url='{file_name_encoded}')"
)

import jwt
hdr = jwt.get_unverified_header(access_token)
claims = jwt.decode(access_token, options={"verify_signature": False})
print("aud:", claims.get("aud"))   # deve essere https://j4srl.sharepoint.com
print("scp/roles:", claims.get("roles") or claims.get("scp"))


resp = requests.post(upload_url, headers=headers, data=content, timeout=60)
print("STATUS:", resp.status_code)
print("BODY  :", resp.text[:300])

if resp.ok:
    print("Upload OK ->", f"{FOLDER_REL}/{file_name}")
else:
    raise SystemExit("Upload FAILED")
