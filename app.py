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

def update_quantita(id_item, nuova_quantita):
    supabase.table("integratori").update({"quantita": nuova_quantita}).eq("id", id_item).execute()

# --- NUOVE FUNZIONI DISPENSA ---
def aggiungi_a_dispensa(nome, cal, prot, carb, grassi):
    supabase.table("dispensa").insert({
        "nome_prodotto": nome, "calorie": cal, "proteine": prot, 
        "carboidrati": carb, "grassi": grassi, "quantita_attuale": 1
    }).execute()

def get_dispensa():
    return supabase.table("dispensa").select("*").order("nome_prodotto").execute().data

# --- 3. NAVIGAZIONE ---
st.sidebar.title("🎮 Menu")
pagina = st.sidebar.radio("Vai a:", ["Assunzione Dose", "Scanner Dispensa", "Gestione Magazzino"])

# --- PAGINA 1: ASSUNZIONE DOSE ---
if pagina == "Assunzione Dose":
    st.title("⚡️ Registro Assunzioni")
    scorte = get_integratori()
    if not scorte:
        st.info("Nessun integratore trovato.")
    else:
        for item in scorte:
            dosi_rimanenti = item['quantita'] / item['dose']
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.write(f"### {'🔴' if dosi_rimanenti <= 10 else '🟢'} {item['nome']}")
                st.write(f"Residuo: {item['quantita']} {item['unita']}")
            with col2:
                q = st.number_input(f"Dose", value=float(item['dose']), key=f"in_{item['id']}")
            with col3:
                st.write(" ")
                if st.button("Preso", key=f"btn_{item['id']}"):
                    update_quantita(item['id'], max(0, item['quantita'] - q))
                    st.rerun()
            st.divider()

# --- PAGINA 2: SCANNER DISPENSA (NEW!) ---
elif pagina == "Scanner Dispensa":
    st.title("🛒 Scanner Dispensa")
    
    barcode = st.text_input("Inserisci o scansiona il Codice a Barre")
    
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
        else:
            st.error("Prodotto non trovato nel database mondiale.")

    st.divider()
    st.subheader("🥫 La tua dispensa")
    cibi = get_dispensa()
    for cibo in cibi:
        st.write(f"**{cibo['nome_prodotto']}** - {cibo['calorie']} kcal (P: {cibo['proteine']}g)")

# --- PAGINA 3: GESTIONE MAGAZZINO ---
else:
    st.title("⚙️ Gestione")
    # Qui tieni il codice per aggiungere/eliminare integratori (omesso per brevità, ma puoi reintegrarlo)
    st.write("Usa questa pagina per configurare i tuoi integratori.")
