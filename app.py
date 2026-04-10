import streamlit as st
from supabase import create_client, Client
import openfoodfacts

# --- 1. CONNESSIONE AL CLOUD ---
@st.cache_resource
def init_connection() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_connection()

# --- 2. FUNZIONI DATABASE ---
def get_integratori():
    return supabase.table("integratori").select("*").order("nome").execute().data

def aggiungi_a_dispensa(n, c, p, cb, g):
    supabase.table("dispensa").insert({
        "nome_prodotto": n, "calorie": c, "proteine": p, 
        "carboidrati": cb, "grassi": g, "quantita_attuale": 1
    }).execute()

def get_dispensa():
    return supabase.table("dispensa").select("*").order("nome_prodotto").execute().data

# --- 3. NAVIGAZIONE ---
st.sidebar.title("🎮 Menu")
pagina = st.sidebar.radio("Vai a:", ["Assunzione Dose", "Scanner Dispensa", "Gestione Magazzino"])

# --- PAGINA 1 ---
if pagina == "Assunzione Dose":
    st.title("⚡️ Registro Assunzioni")
    st.write("Pagina in costruzione...")

# --- PAGINA 2: SCANNER DISPENSA (VERSIONE SICURA) ---
elif pagina == "Scanner Dispensa":
    st.title("🛒 Scanner Dispensa")
    
    # Widget nativo: apre la fotocamera su iPhone senza librerie extra
    foto = st.camera_input("Scatta una foto al codice a barre")
    
    barcode_manuale = st.text_input("Oppure inserisci il codice a mano")
    
    # Se scatti la foto, per ora usiamo un codice test (domani mettiamo l'IA che legge la foto)
    barcode = barcode_manuale
    if foto:
        barcode = "8000300264008" # Codice di test (es. Pasta)
        st.success("Foto acquisita correttamente!")

    if barcode:
        with st.spinner('Ricerca prodotto...'):
            api = openfoodfacts.API(user_agent="AthleteLab/1.0")
            res = api.product.get(barcode)
        
        if res and "product" in res:
            p = res["product"]
            nome = p.get("product_name", "Sconosciuto")
            nut = p.get("nutriments", {})
            cal = nut.get("energy-kcal_100g", 0)
            
            st.markdown(f"### 📦 {nome}")
            st.metric("Calorie (100g)", f"{cal} kcal")
            
            if st.button("Conferma e aggiungi in Dispensa"):
                aggiungi_a_dispensa(nome, cal, nut.get('proteins_100g', 0), 0, 0)
                st.balloons()
        else:
            st.error("Prodotto non trovato nel database.")

    st.divider()
    st.subheader("🥫 La tua dispensa")
    cibi = get_dispensa()
    if cibi:
        for c in cibi:
            st.write(f"• **{c['nome_prodotto']}** ({c['calorie']} kcal)")

# --- PAGINA 3 ---
else:
    st.title("⚙️ Gestione")
