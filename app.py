import streamlit as st
from supabase import create_client, Client

# --- 1. CONNESSIONE AL CLOUD ---
@st.cache_resource
def init_connection() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_connection()

# --- 2. FUNZIONI DATABASE ---
def get_integratori():
    response = supabase.table("integratori").select("*").order("nome").execute()
    return response.data

def add_integratore(nome, quantita, dose, unita, soglia):
    supabase.table("integratori").insert({
        "nome": nome, "quantita": quantita, "dose": dose, "unita": unita, "soglia": soglia
    }).execute()

def update_quantita(id_item, nuova_quantita):
    supabase.table("integratori").update({"quantita": nuova_quantita}).eq("id", id_item).execute()

def delete_integratore(id_item):
    supabase.table("integratori").delete().eq("id", id_item).execute()

# --- 3. NAVIGAZIONE ---
st.sidebar.title("🏋🏿‍♂️ Menu")
pagina = st.sidebar.radio("Vai a:", ["Assunzione Dose", "Gestione Magazzino"])

# --- PAGINA 1: ASSUNZIONE DOSE (QUOTIDIANA) ---
if pagina == "Assunzione Dose":
    st.title("⚡️ Registro Assunzioni")
    st.write("Inserisci la quantità assunta e conferma.")
    
    scorte = get_integratori()
    
    if not scorte:
        st.info("Nessun integratore trovato. Vai in 'Gestione Magazzino' per aggiungerli.")
    else:
        for item in scorte:
            dosi_rimanenti = item['quantita'] / item['dose']
            
            with st.container():
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    colore = "🔴" if dosi_rimanenti <= 10 else "🟢"
                    st.write(f"### {colore} {item['nome']}")
                    st.write(f"Residuo: **{item['quantita']} {item['unita']}**")
                
                with col2:
                    # Input per decidere quanta dose scalare (impostato di default sulla dose standard)
                    quantita_da_scalare = st.number_input(
                        f"Dose ({item['unita']})", 
                        min_value=0.0, 
                        value=float(item['dose']), 
                        step=0.5, 
                        key=f"input_{item['id']}"
                    )
                
                with col3:
                    st.write(" ") # Spaziatore per allineare il bottone
                    st.write(" ")
                    if st.button(f"Conferma", key=f"btn_{item['id']}"):
                        if quantita_da_scalare > 0:
                            nuovo_residuo = max(0, item['quantita'] - quantita_da_scalare)
                            update_quantita(item['id'], nuovo_residuo)
                            st.toast(f"Hai preso {quantita_da_scalare} {item['unita']} di {item['nome']}")
                            st.rerun()
                        else:
                            st.warning("Inserisci una quantità valida")
                
                st.divider()

# --- PAGINA 2: GESTIONE MAGAZZINO (MODIFICA/ELIMINA) ---
else:
    st.title("⚙️ Gestione Magazzino")
    
    # Form per nuovo inserimento
    with st.expander("➕ Aggiungi Nuovo Integratore", expanded=False):
        with st.form("nuovo"):
            n = st.text_input("Nome")
            q = st.number_input("Quantità Totale", min_value=0.0)
            d = st.number_input("Singola Dose", min_value=0.1)
            u = st.selectbox("Unità", ["grammi", "capsule", "misurini"])
            if st.form_submit_button("Salva nel Cloud"):
                add_integratore(n, q, d, u, d*10)
                st.success("Aggiunto!")
                st.rerun()

    st.subheader("🛠️ Modifica o Elimina esistenti")
    scorte = get_integratori()
    
    for item in scorte:
        with st.expander(f"Modifica {item['nome']}"):
            with st.form(key=f"edit_{item['id']}"):
                nuovo_n = st.text_input("Nome", value=item['nome'])
                nuova_q = st.number_input("Quantità residua", value=float(item['quantita']))
                nuova_d = st.number_input("Dose", value=float(item['dose']))
                if st.form_submit_button("Aggiorna Dati"):
                    supabase.table("integratori").update({
                        "nome": nuovo_n, "quantita": nuova_q, "dose": nuova_d, "soglia": nuova_d*10
                    }).eq("id", item['id']).execute()
                    st.rerun()
            
            if st.button(f"🗑️ Elimina {item['nome']}", key=f"del_{item['id']}"):
                delete_integratore(item['id'])
                st.warning("Eliminato!")
                st.rerun()