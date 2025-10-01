# test_upload_clean.py
import os, msal
from dotenv import load_dotenv
from office365.sharepoint.client_context import ClientContext
from office365.sharepoint.files.file import File

load_dotenv()

TENANT      = os.getenv("TENANT_ID")                     # es. j4srl.onmicrosoft.com o GUID
CLIENT_ID   = os.getenv("CLIENT_ID")
SITE_URL    = os.getenv("SHAREPOINT_URL")                # https://j4srl.sharepoint.com/sites/J4EnenergyDataStorage
FOLDER_REL  = f"/sites/J4EnenergyDataStorage/{os.getenv('SHAREPOINT_FOLDER')}"  # es. Shared Documents/Florence_group
RESOURCE    = "https://j4srl.sharepoint.com"
CERT_PATH   = os.getenv("CLIENT_CERT_PATH") or "private_key.pem"
THUMBPRINT  = (os.getenv("CLIENT_CERT_THUMBPRINT") or "").replace(":", "").strip() or None

# 1) Prendo un access token app-only via certificato
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
token_str = app.acquire_token_for_client(scopes=[f"{RESOURCE}/.default"])["access_token"]

# 2) La libreria vuole un oggetto token con .tokenType e .accessToken
class TokenObj:
    def __init__(self, access_token: str):
        self.tokenType = "Bearer"
        self.accessToken = access_token

def get_token_obj():
    # Se vuoi, qui puoi anche rigenerare il token quando scade
    return TokenObj(token_str)

# 3) Costruisco il contesto passando un CALLABLE che restituisce TokenObj
ctx = ClientContext(SITE_URL).with_access_token(get_token_obj)

# 4) Test connessione
web = ctx.web.get().execute_query()
print("Connessione OK:", web.title)

# 5) Upload di prova
os.makedirs("uploads", exist_ok=True)
test_path = "uploads/test.txt"
with open(test_path, "wb") as f:
    f.write(b"prova upload via certificato")

with open(test_path, "rb") as f:
    content = f.read()

dest = f"{FOLDER_REL}/test.txt"   # es: /sites/.../Shared Documents/Florence_group/test.txt
File.save_binary(ctx, dest, content)
print("Upload OK ->", dest)
