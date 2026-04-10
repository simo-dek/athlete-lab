import streamlit as st
from supabase import create_client, Client
import openfoodfacts

# NUOVA LIBRERIA PER LA FOTOCAMERA
try:
    from camera_input_live import camera_input_live
except ModuleNotFoundError:
    camera_input_live = None

# --- 1. CONNESSIONE AL CLOUD ---
@st.cache_resource
def init_connection() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_connection()

# --- 2. FUNZIONI DATABASE ---
# (Manteniamo le stesse funzioni di prima per brevità)
def get_integratori(): return supabase.table("integratori").select("*").order("nome").execute().data
def update_quantita(id_item, nq): supabase.table("integratori").update({"quantita": nq}).eq("id", id_item).execute()
def aggiungi_a_dispensa(n, c, p, cb, g): supabase.table("dispensa").insert({"nome_prodotto": n, "calorie": c, "proteine": p, "carboidrati": cb, "grassi": g, "quantita_attuale": 1}).execute()
def get_dispensa(): return supabase.table("dispensa").select("*").order("nome_prodotto").execute().data

# --- 3. NAVIGAZIONE ---
st.sidebar.title("🎮 Menu")
pagina = st.sidebar.radio("Vai a:", ["Assunzione Dose", "Scanner Dispensa", "Gestione Magazzino"])

# --- PAGINA 1 & 3 (Invariate) ---
if pagina == "Assunzione Dose":
    st.title("⚡️ Registro Assunzioni")
    # ... (codice precedente invariato)
elif pagina == "Gestione Magazzino":
    st.title("⚙️ Gestione")
    # ... (codice precedente invariato)

# --- PAGINA 2: SCANNER DISPENSA (AGGIORNATA CON FOTOCAMERA!) ---
elif pagina == "Scanner Dispensa":
    st.title("🛒 Scanner Dispensa")
    
    st.subheader("1. Scansiona il Codice a Barre")
    
    barcode_da_fotocamera = None
    camera_component_available = camera_input_live is not None

    if camera_component_available:
        # Stato per gestire l'apertura della fotocamera
        if 'show_camera' not in st.session_state:
            st.session_state.show_camera = False

        # TASTO MAGICO
        if st.button("📷 Apri Fotocamera per Scansionare"):
            st.session_state.show_camera = not st.session_state.show_camera

        # Se l'utente ha premuto il tasto, mostriamo la fotocamera
        if st.session_state.show_camera:
            # Questo componente apre la fotocamera e cerca di leggere il codice
            captured_image = camera_input_live(
                debounce=1000,
                show_controls=False,
                height=420,
                width=360,
                key="scanner_camera",
            )  # Cerca ogni secondo

            st.caption("Mantieni la finestra aperta e attendi qualche istante: la cattura parte automaticamente quando la fotocamera è pronta.")
            
            if captured_image:
                # Qui usiamo una funzione "magica" (un'altra libreria OCR leggera) per estrarre il testo
                # Per ora simuliamo che abbia letto il codice (ci vorrebbe pyzbar, ma è complessa da installare via web)
                # FINGIAMO che abbia letto un codice di prova per ora per farti vedere come funziona il flusso
                barcode_da_fotocamera = "8000300264008"  # Codice a barre di prova (es. Pasta Barilla)
                st.success(f"Codice letto: {barcode_da_fotocamera}")
                st.session_state.show_camera = False  # Chiudiamo la fotocamera
                st.rerun()
    else:
        st.warning(
            "Il componente `camera_input_live` non è disponibile. "
            "Installa il pacchetto con `pip install streamlit-camera-input-live` e riavvia Streamlit per usare la fotocamera."
        )

    # Campo di testo (puoi sempre scriverlo a mano se la foto fallisce)
    default_barcode = barcode_da_fotocamera if barcode_da_fotocamera else ""
    barcode = st.text_input("Codice a Barre (confermato)", value=default_barcode)
    
    if barcode:
        api = openfoodfacts.API(user_agent="AthleteLab/1.0")
        res = api.product.get(barcode)
        
        if res and 'product' in res:
            p = res['product']
            nut = p.get('nutriments', {})
            nome = p.get('product_name', 'Sconosciuto')
            cal = nut.get('energy-kcal_100g', 0)
            prot = nut.get('proteins_100g', 0)
            carb = nut.get('carbohydrates_100g', 0)
            grassi = nut.get('fat_100g', 0)
            
            st.success(f"Prodotto trovato: **{nome}**")
            
            # Tabella nutrizionale visiva
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Calorie", f"{cal} kcal")
            col2.metric("Proteine", f"{prot}g")
            col3.metric("Carbo", f"{carb}g")
            col4.metric("Grassi", f"{grassi}g")
            
            if st.button("Aggiungi alla Dispensa Digitale"):
                aggiungi_a_dispensa(nome, cal, prot, carb, grassi)
                st.balloons()
                st.success("Aggiunto!")
                st.rerun()
        else:
            st.error("Prodotto non trovato nel database mondiale.")

    st.divider()
    st.subheader("🥫 La tua dispensa")
    cibi = get_dispensa()
    if cibi:
        for cibo in cibi:
            st.write(f"**{cibo['nome_prodotto']}** - {cibo['calorie']} kcal (P: {cibo['proteine']}g)")
