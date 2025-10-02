# Uploader Consumi → Google Drive (Flask)

App Flask che elabora un file di **consumi totali**, integra dati **PV** e carica i risultati su **Google Drive**.

## Struttura
- `app.py`: app Flask e routing
- `google_drive_uploader.py`: autenticazione e upload su Drive (OAuth)
- `script_analisiF3.py`: logica di analisi/Excel
- `templates/index.html` *oppure* root `index.html` (vedi nota)
- `uploads/` e `output/`: cartelle di lavoro (create all'avvio)


## Setup locale

1. Python 3.11+ consigliato (qui uso 3.12).  
2. Creare un virtualenv e installare i pacchetti:
   ```bash
   python -m venv .venv
   . .venv/bin/activate  # su Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Configurare il file `.env` (vedi `.env.example`).
4. Preparare le **API Google Drive**:
   - Vai su Google Cloud Console → abilita **Drive API**.
   - Crea credenziali **OAuth client ID** → tipo *Desktop App*.
   - Scarica `credentials.json` e **salvalo accanto ad `app.py`**.
5. Avvio in locale:
   ```bash
   flask --app app run
   # oppure
   python app.py
   ```
6. Alla **prima esecuzione** verrà richiesto il login Google. Si genererà `token.json` (cachato per gli usi successivi).

> **Sicurezza**: *non* committare `credentials.json` e `token.json` (sono già nel `.gitignore`).

## Variabili d'ambiente

Crea un file `.env` partendo da `.env.example`:

```
GOOGLE_DRIVE_FOLDER_ID=xxxxxxxxxxxxxxxxxxxxxxxxx
ADMIN_PASSWORD=change-me
```

- `GOOGLE_DRIVE_FOLDER_ID`: ID della cartella Drive di destinazione (o Shared Drive).  
- `ADMIN_PASSWORD`: password per consentire l'upload di un file PV alternativo da UI.

## Note su `index.html`
Se usi Flask con *template engine*, sposta `index.html` nella cartella `templates/` ed aggiorna il percorso se necessario. In alternativa, lascia `index.html` nella root e usa `render_template('index.html')` con `template_folder='.'` in Flask.


## Deploy rapido (Render o Railway)

### Render (consigliato)
1. Effettua il push del repo su GitHub.
2. Su Render → **New Web Service** → collega il repo.
3. Environment:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Python Version**: 3.12 (o imposta `runtime.txt`).
4. **Env Vars**: imposta `GOOGLE_DRIVE_FOLDER_ID` e `ADMIN_PASSWORD`.
5. **Secrets**: carica **come Secret Files**:
   - `credentials.json` → contenuto del file OAuth.
   - (opzionale) `token.json` se vuoi pre-caricare il token generato in locale.
6. Abilita *Auto Deploy* dal branch principale.

> Con OAuth “Installed App” l’autenticazione è **interattiva**. In hosting **headless** la prima autorizzazione è più semplice se esegui una volta in locale per generare `token.json`, poi lo carichi come Secret su Render. Per scenari 100% server-side valuta **Service Account** + condivisione cartella (vedi sotto).

### Railway / Fly.io / Heroku
- Usa lo stesso `Procfile` (`web: gunicorn app:app`).
- Imposta le env vars e carica `credentials.json`/`token.json` come secreti (o variabili/volume, a seconda della piattaforma).
- Assicurati che le cartelle `uploads/` e `output/` siano scrivibili (volume/persistent storage se richiesto).

## Alternativa production: Service Account
Per evitare il login interattivo in produzione:
1. Crea un **Service Account** in Google Cloud, genera una **JSON key**.
2. **Condividi** la cartella di Drive di destinazione con l’email del Service Account.
3. Modifica `google_drive_uploader.py` per usare `google.oauth2.service_account.Credentials` e lo scope `drive.file`/`drive`.
4. Carica la key JSON come secret nel provider.

## Pubblicazione su GitHub

```bash
git init
git add .
git commit -m "Initial commit: Flask + Drive uploader"
git branch -M main
git remote add origin https://github.com/<tuo-utente>/<nome-repo>.git
git push -u origin main
```

## Troubleshooting
- **403 su Drive in Shared Drive**: assicurati di usare `supportsAllDrives=True` nell’API (già impostato nel codice).
- **Login in hosting**: pre-genera `token.json` in locale, poi caricalo come secret; in alternativa passa a Service Account.
- **Excel read**: serve `openpyxl`. Già in `requirements.txt`.
