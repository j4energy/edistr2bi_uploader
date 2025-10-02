import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Il file token.json ora sarà caricato come "Secret File" su Render
TOKEN_FILE = 'token.json'
CREDENTIALS_FILE = 'credentials.json'
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def get_drive_service():
    """
    Gestisce l'autenticazione in modo automatico usando token.json.
    Se il token è scaduto, lo aggiorna usando il refresh_token.
    """
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    # Se non ci sono credenziali o non sono valide, le aggiorna
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Aggiornamento del token di accesso scaduto...")
            creds.refresh(Request())
            # Salva le credenziali aggiornate per il futuro
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
        else:
            # Questo blocco non dovrebbe mai essere raggiunto su un server configurato correttamente
            raise Exception(f"Errore: Manca il file '{TOKEN_FILE}' o non contiene un refresh_token valido. "
                            "Genera un nuovo token.json in locale e caricalo come Secret File su Render.")
            
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
        
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id',
            supportsAllDrives=True
        ).execute()
        
        print(f"File '{file_name}' caricato con successo su Google Drive. ID: {file.get('id')}")
        return True
        
    except Exception as e:
        print(f"Errore durante l'upload su Google Drive: {e}")
        return False