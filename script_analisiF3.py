import pandas as pd
import os

def crea_input_da_csv(consumi_input_path, output_folder, date_prefix):
    """
    Legge un file, lo divide per mese e crea un file Excel multi-foglio
    con un prefisso di data nel nome, includendo tutte le colonne richieste.
    """
    # Nomi delle colonne attesi nel file di input dei consumi
    COLONNA_POD = 'POD'
    COLONNA_AZIENDA = 'Azienda'  # Aggiunto per chiarezza
    COLONNA_MESE = 'Mese'
    COLONNA_F1 = 'kWh F1'
    COLONNA_F2 = 'kWh F2'
    COLONNA_F3 = 'kWh F3'
    COLONNA_TOTALE = 'Totale Energia'
    
    try:
        df = pd.read_excel(consumi_input_path)
    except Exception:
        df = pd.read_csv(consumi_input_path)

    # Pulisce i nomi delle colonne da eventuali spazi extra
    df.columns = [str(col).strip() for col in df.columns]

    df['mese_numero'] = pd.to_datetime(df[COLONNA_MESE]).dt.month
    
    # Rinomina le colonne per coerenza interna. Questo assicura che lo script funzioni
    # anche se i nomi delle colonne nel file di input dovessero avere lievi variazioni.
    df = df.rename(columns={
        COLONNA_POD: 'POD',
        COLONNA_AZIENDA: 'Azienda',
        COLONNA_MESE: 'Mese',
        COLONNA_F1: 'kWh F1',
        COLONNA_F2: 'kWh F2',
        COLONNA_F3: 'kWh F3',
        COLONNA_TOTALE: 'Totale Energia'
    })

    mese_to_nome_foglio = {
        1: "gen-25", 2: "feb-25", 3: "mar-25", 4: "apr-25",
        5: "mag-25", 6: "giu-25", 7: "lug-25", 8: "ago-25",
        9: "set-25", 10: "ott-25", 11: "nov-25", 12: "dic-25"
    }
    
    output_filename = f"{date_prefix}_Input_script_analisiF3.xlsx"
    output_excel_path = os.path.join(output_folder, output_filename)
    dati_per_mese = {}

    writer = pd.ExcelWriter(output_excel_path, engine='xlsxwriter')

    for mese_numero, dati_mese in df.groupby('mese_numero'):
        nome_foglio = mese_to_nome_foglio.get(mese_numero)
        if nome_foglio:
            # --- MODIFICA CHIAVE: Includi 'Azienda' e 'Mese' nell'output ---
            colonne_da_salvare = ['POD', 'Azienda', 'Mese', 'kWh F1', 'kWh F2', 'kWh F3', 'Totale Energia']
            
            # Assicura che solo le colonne effettivamente presenti nel dataframe vengano selezionate
            colonne_esistenti = [col for col in colonne_da_salvare if col in dati_mese.columns]
            dati_mese_output = dati_mese[colonne_esistenti]
            
            dati_mese_output.to_excel(writer, sheet_name=nome_foglio, index=False)
            dati_per_mese[mese_numero] = dati_mese_output.fillna(0)
    
    writer.close()

    print(f"File Excel di input creato: {output_excel_path}")
    return dati_per_mese, output_excel_path


def aggiungi_dati_pv(dati_per_mese, pv_info_path, output_folder, date_prefix):
    """
    Esegue l'analisi del fotovoltaico e salva il risultato con un prefisso di data.
    """
    # (Questa funzione non necessita di modifiche e rimane invariata)
    try:
        df_pv_info = pd.read_excel(pv_info_path, sheet_name=0)
        df_profilo_pv = pd.read_excel(pv_info_path, sheet_name=1)
        df_autoconsumo = pd.read_excel(pv_info_path, sheet_name=2)
    except FileNotFoundError:
        raise FileNotFoundError(f"File informazioni PV non trovato al percorso: {pv_info_path}")

    df_pv_info.columns = [str(col).strip() for col in df_pv_info.columns]
    
    required_cols_pv = ['POD', 'Taglia PV [kW]']
    if not all(col in df_pv_info.columns for col in required_cols_pv):
        missing_cols = [col for col in required_cols_pv if col not in df_pv_info.columns]
        raise ValueError(f"Colonne mancanti nel primo foglio del file Info_PV: {', '.join(missing_cols)}")

    mappa_pv = dict(zip(df_pv_info["POD"], df_pv_info["Taglia PV [kW]"]))
    for mese, df in dati_per_mese.items():
        if 'POD' in df.columns:
            df["Taglia_PV"] = df["POD"].map(mappa_pv).fillna(0)

    df_pv_orario = df_profilo_pv.copy()
    df_pv_orario["datetime"] = pd.to_datetime(df_pv_orario["time"].str[:8], format="%Y%m%d")
    df_pv_orario["month"] = df_pv_orario["datetime"].dt.month
    df_pv_orario["hour"] = df_pv_orario["time"].str[9:11].astype(int)
    
    festivita_2025 = set(pd.to_datetime(["2025-01-01", "2025-01-06", "2025-04-20", "2025-04-21", "2025-04-25", "2025-05-01", "2025-06-02", "2025-08-15", "2025-11-01", "2025-12-08", "2025-12-25", "2025-12-26"]).date)
    
    def determina_fascia(row):
        giorno = row['datetime'].date()
        weekday = row['datetime'].weekday()
        ora = row['hour']
        is_festivo = giorno in festivita_2025 or weekday == 6
        if is_festivo: return "F3"
        if weekday < 5:
            if 8 <= ora < 19: return "F1"
            if 7 <= ora < 8 or 19 <= ora < 23: return "F2"
            return "F3"
        if weekday == 5:
            if 7 <= ora < 23: return "F2"
            return "F3"
            
    df_pv_orario["Fascia"] = df_pv_orario.apply(determina_fascia, axis=1)
    
    riepilogo_pv_per_fascia = {}
    for mese, df_mese in df_pv_orario.groupby("month"):
        riepilogo_pv_per_fascia[mese] = df_mese.groupby("Fascia")["P"].agg(Somma_Produzione_Wh="sum", Ore="count").reset_index()
        
    consumi_con_PV = {}
    for mese, df in dati_per_mese.items():
        riepilogo = riepilogo_pv_per_fascia.get(mese)
        if riepilogo is not None:
            produzione_fasce = riepilogo.set_index("Fascia")["Somma_Produzione_Wh"]
            df["Produzione_PV_F1"] = df["Taglia_PV"] * produzione_fasce.get("F1", 0) / 1000
            df["Produzione_PV_F2"] = df["Taglia_PV"] * produzione_fasce.get("F2", 0) / 1000
            df["Produzione_PV_F3"] = df["Taglia_PV"] * produzione_fasce.get("F3", 0) / 1000
        consumi_con_PV[mese] = df
        
    gruppi_pod = [("IT001E72062156", "IT001E04433186"), ("IT001E48602056", "IT001E48183760")]
    consumi_con_PV_pesati = {}
    for mese, df in consumi_con_PV.items():
        df_corr = df.copy()
        fattori_mensili = {}
        for pod_a, pod_b in gruppi_pod:
            consumo_a = df_corr.loc[df_corr["POD"] == pod_a, "Totale Energia"].sum()
            consumo_b = df_corr.loc[df_corr["POD"] == pod_b, "Totale Energia"].sum()
            totale = consumo_a + consumo_b
            fattori_mensili[pod_a] = consumo_a / totale if totale > 0 else 0
            fattori_mensili[pod_b] = consumo_b / totale if totale > 0 else 0
        for fascia in ["Produzione_PV_F1", "Produzione_PV_F2", "Produzione_PV_F3"]:
            mappatura = df_corr["POD"].map(fattori_mensili).dropna()
            df_corr.loc[mappatura.index, fascia] *= mappatura
        consumi_con_PV_pesati[mese] = df_corr
        
    autoconsumo_dict = {}
    for _, row in df_autoconsumo.iterrows():
        mese_auto = row["mese"]
        if mese_auto not in autoconsumo_dict: autoconsumo_dict[mese_auto] = {}
        autoconsumo_dict[mese_auto][row["fascia"]] = row["%autoconsumo"]
        
    for mese, df in consumi_con_PV_pesati.items():
        autoconsumo_fasce = autoconsumo_dict.get(mese, {})
        df["Produzione_PV_F1_autocons"] = df["Produzione_PV_F1"] * autoconsumo_fasce.get("F1", 0)
        df["Produzione_PV_F2_autocons"] = df["Produzione_PV_F2"] * autoconsumo_fasce.get("F2", 0)
        df["Produzione_PV_F3_autocons"] = df["Produzione_PV_F3"] * autoconsumo_fasce.get("F3", 0)
        df["Tot produzione PV autocons [kWh]"] = df[["Produzione_PV_F1_autocons", "Produzione_PV_F2_autocons", "Produzione_PV_F3_autocons"]].sum(axis=1)
        df["F1 con PV"] = df["kWh F1"] + df["Produzione_PV_F1_autocons"]
        df["F2 con PV"] = df["kWh F2"] + df["Produzione_PV_F2_autocons"]
        df["F3 con PV"] = df["kWh F3"] + df["Produzione_PV_F3_autocons"]
        df["Totale consumi con PV"] = df[["F1 con PV", "F2 con PV", "F3 con PV"]].sum(axis=1)
        totale = df["Totale consumi con PV"].replace(0, 1)
        df["Peso F1 %"] = ((df["F1 con PV"] / totale) * 100).round(0)
        df["Peso F2 %"] = ((df["F2 con PV"] / totale) * 100).round(0)
        df["Peso F3 %"] = ((df["F3 con PV"] / totale) * 100).round(0)
        consumi_con_PV_pesati[mese] = df

    output_filename = f"{date_prefix}_Risultato_analisi_con_PV.xlsx"
    output_finale_path = os.path.join(output_folder, output_filename)
    
    mese_to_nome_foglio = {
        1: "gen-25", 2: "feb-25", 3: "mar-25", 4: "apr-25",
        5: "mag-25", 6: "giu-25", 7: "lug-25", 8: "ago-25",
        9: "set-25", 10: "ott-25", 11: "nov-25", 12: "dic-25"
    }
    
    writer_finale = pd.ExcelWriter(output_finale_path, engine='xlsxwriter')

    for mese, df in consumi_con_PV_pesati.items():
        nome_foglio = mese_to_nome_foglio.get(mese)
        if nome_foglio:
            df.to_excel(writer_finale, sheet_name=nome_foglio, index=False)
            
    writer_finale.close()
            
    print(f"File con risultato finale creato: {output_finale_path}")
    return output_finale_path

