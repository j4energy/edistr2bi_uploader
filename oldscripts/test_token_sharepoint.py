import os, requests, msal
from dotenv import load_dotenv

load_dotenv()

tenant    = os.getenv("TENANT_ID")
client_id = os.getenv("CLIENT_ID")
site_url  = os.getenv("SHAREPOINT_URL")
resource  = "https://j4srl.sharepoint.com"

# leggi la PRIVATE KEY (PEM)
with open(os.getenv("CLIENT_CERT_PATH") or "private_key.pem", "rb") as f:
    private_key = f.read().decode("utf-8")

thumb = (os.getenv("CLIENT_CERT_THUMBPRINT") or "").replace(":","").strip()
if not (len(thumb) == 40 and all(c in "0123456789abcdefABCDEF" for c in thumb)):
    raise SystemExit("Thumbprint non valido: deve essere SHA1 (40 hex chars, senza due punti).")

app = msal.ConfidentialClientApplication(
    client_id=client_id,
    authority=f"https://login.microsoftonline.com/{tenant}",
    client_credential={"private_key": private_key, "thumbprint": thumb},
)

result = app.acquire_token_for_client(scopes=[f"{resource}/.default"])
if "access_token" not in result:
    raise SystemExit(f"Token error: {result}")

token = result["access_token"]
resp = requests.get(
    f"{site_url}/_api/web?$select=Title",
    headers={"Authorization": f"Bearer {token}", "Accept": "application/json;odata=nometadata"},
    timeout=30,
)
print("STATUS:", resp.status_code)
print("BODY  :", resp.text[:200])
