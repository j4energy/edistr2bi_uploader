from flask import Flask, render_template, request, flash, send_from_directory, redirect, url_for
import os
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from datetime import datetime

from script_analisiF3 import crea_input_da_csv, aggiungi_dati_pv
from google_drive_uploader import upload_to_google_drive

load_dotenv()

app = Flask(__name__)
app.secret_key = 'una-chiave-segreta-qualsiasi'

# Configurazione cartelle e nomi file
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
DEFAULT_PV_FILENAME = 'Info_PV_per_script.xlsx'
TEMPLATE_FILENAME = 'CONSUMI_TOTALI_F1-F2-F3.xlsx'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Legge le configurazioni dal file .env
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

@app.route('/download/template')
def download_template():
    """Route per scaricare il file template."""
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], TEMPLATE_FILENAME, as_attachment=True)
    except FileNotFoundError:
        flash(f"Errore: File template '{TEMPLATE_FILENAME}' non trovato sul server nella cartella 'uploads'.", "error")
        return redirect(url_for('upload_file'))

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # --- CONTROLLI PRELIMINARI ---
        if 'consumi_file' not in request.files or request.files['consumi_file'].filename == '':
            flash('Errore: Il file dei consumi totali è obbligatorio.', 'error')
            return render_template('index.html')

        if not GOOGLE_DRIVE_FOLDER_ID or not ADMIN_PASSWORD:
            flash("Errore di configurazione: GOOGLE_DRIVE_FOLDER_ID e ADMIN_PASSWORD devono essere impostati nel file .env.", "error")
            return render_template('index.html')

        consumi_file = request.files['consumi_file']
        consumi_filename = secure_filename(consumi_file.filename)
        consumi_path = os.path.join(app.config['UPLOAD_FOLDER'], consumi_filename)
        consumi_file.save(consumi_path)

        # --- GESTIONE FILE PV (DEFAULT O NUOVO) ---
        pv_file = request.files.get('pv_file_override')
        admin_pass = request.form.get('admin_password')
        pv_path = os.path.join(app.config['UPLOAD_FOLDER'], DEFAULT_PV_FILENAME) # Path di default

        if pv_file and pv_file.filename != '':
            if admin_pass == ADMIN_PASSWORD:
                pv_override_filename = secure_filename(pv_file.filename)
                pv_path_override = os.path.join(app.config['UPLOAD_FOLDER'], pv_override_filename)
                pv_file.save(pv_path_override)
                pv_path = pv_path_override
                flash('File PV personalizzato caricato con successo per questa sessione.', 'success')
            else:
                flash('Password amministratore errata. Verrà usato il file PV di default.', 'error')
        
        if not os.path.exists(pv_path):
            flash(f"Errore: File PV di default '{DEFAULT_PV_FILENAME}' non trovato.", 'error')
            return render_template('index.html')

        try:
            # --- MODIFICA: Genera la data per il nome del file ---
            date_prefix = datetime.now().strftime('%Y%m%d')

            # Passa il prefisso della data alle funzioni di creazione dei file
            dati_per_mese, input_generato_path = crea_input_da_csv(consumi_path, OUTPUT_FOLDER, date_prefix)
            risultato_finale_path = aggiungi_dati_pv(dati_per_mese, pv_path, OUTPUT_FOLDER, date_prefix)
            
            # Estrae i nuovi nomi dei file per i messaggi
            nome_file_input = os.path.basename(input_generato_path)
            nome_file_risultato = os.path.basename(risultato_finale_path)

            flash('Analisi completata. Inizio caricamento su Google Drive...', 'success')
            
            success1 = upload_to_google_drive(input_generato_path, GOOGLE_DRIVE_FOLDER_ID)
            if success1:
                flash(f'File "{nome_file_input}" caricato con successo!', 'success')
            else:
                flash(f'Caricamento del file "{nome_file_input}" FALLITO.', 'error')

            success2 = upload_to_google_drive(risultato_finale_path, GOOGLE_DRIVE_FOLDER_ID)
            if success2:
                flash(f'File "{nome_file_risultato}" caricato con successo!', 'success')
            else:
                flash(f'Caricamento del file "{nome_file_risultato}" FALLITO.', 'error')

        except Exception as e:
            flash(f"Si è verificato un errore durante l'elaborazione: {e}", 'error')

        return render_template('index.html')

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)




