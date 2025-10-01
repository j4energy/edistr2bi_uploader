import os
import msal
from dotenv import load_dotenv
from office365.sharepoint.client_context import ClientContext

load_dotenv()

# --- Carica le credenziali per il certificato ---
site_url = os.getenv("SHAREPOINT_URL")
client_id = os.getenv("CLIENT_ID")
tenant_id = os.getenv("TENANT_ID")
private_key_path = os.getenv("PRIVATE_KEY_PATH")
cert_thumbprint = os.getenv("CERT_THUMBPRINT")

def acquire_token_func():
    with open(private_key_path, "r") as f:
        private_key = f.read()

    client_credential = {
        "private_key": private_key,
        "thumbprint": cert_thumbprint,
    }

    authority_url = f'https://login.microsoftonline.com/{tenant_id}'
    app = msal.ConfidentialClientApplication(
        client_id=client_id,
        client_credential=client_credential,
        authority=authority_url
    )
    scopes = [f"https://{site_url.split('/')[2]}/.default"]
    result = app.acquire_token_for_client(scopes=scopes)
    
    if "access_token" not in result:
        raise Exception(f"Autenticazione con certificato fallita: {result.get('error_description')}")
        
    return result['access_token']

def add_authorization_header(request, *args, **kwargs):
    access_token = acquire_token_func()
    request.headers['Authorization'] = f'Bearer {access_token}'

try:
    ctx = ClientContext(site_url)
    ctx.pending_request().beforeExecute += add_authorization_header
    
    web = ctx.web.get().execute_query()
    print("Connessione con certificato a SharePoint riuscita! ✅ - Titolo sito:", web.title)

except Exception as e:
    print(f"Si è verificato un errore: {e}")