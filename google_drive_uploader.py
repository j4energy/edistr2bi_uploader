import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Definisce a quali servizi l'app può accedere (sola scrittura su Drive)
SCOPES = ['https://www.googleapis.com/auth/drive.file']
TOKEN_FILE = 'token.json'

def get_drive_service():
    """
    Gestisce l'autenticazione e restituisce un oggetto 'service' per interagire con Drive.
    """
    creds = None
    # Il file token.json salva le credenziali dell'utente dopo il primo login
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    # Se le credenziali non sono valide o sono scadute, l'utente deve fare il login
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Avvia il flusso di login interattivo la prima volta
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            # Il messaggio per il login apparirà nel terminale dove gira 'flask run'
            print("\n--- AUTENTICAZIONE GOOGLE DRIVE RICHIESTA ---")
            print("Copia il link sottostante nel browser, accedi e autorizza l'app.")
            print("Poi copia il codice che ricevi e incollalo qui nel terminale.")
            creds = flow.run_local_server(port=0)
        
        # Salva le credenziali per le esecuzioni future
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
            
    return build('drive', 'v3', credentials=creds)

def upload_to_google_drive(file_path, folder_id):
    """
    Carica un file in una cartella specifica di Google Drive,
    con supporto per i Drive Condivisi.
    """
    try:
        service = get_drive_service()
        file_name = os.path.basename(file_path)
        
        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }
        
        media = MediaFileUpload(file_path)
        
        # --- MODIFICA CHIAVE ---
        # Aggiunto il parametro 'supportsAllDrives=True' per abilitare
        # il supporto ai Drive Condivisi.
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id',
            supportsAllDrives=True  # <-- QUESTA È LA RIGA AGGIUNTA
        ).execute()
        
        print(f"File '{file_name}' caricato con successo su Google Drive. ID: {file.get('id')}")
        return True
        
    except Exception as e:
        if 'invalid_grant' in str(e) and os.path.exists(TOKEN_FILE):
            os.remove(TOKEN_FILE)
            print("Token di Google Drive non valido o scaduto. Rimosso. Riprova per autenticarti di nuovo.")
        
        print(f"Errore durante l'upload su Google Drive: {e}")
        return False

