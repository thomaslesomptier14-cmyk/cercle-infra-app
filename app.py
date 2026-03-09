import streamlit as st
import feedparser
from google import genai
import datetime
import ssl
import os

# --- CONFIGURATION PAGE ---
st.set_page_config(page_title="Le Cercle Infra - Intelligence Suite", page_icon="🏛️", layout="wide")

# Dossier pour les archives
if not os.path.exists("archives"):
    os.makedirs("archives")

# Déblocage SSL
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError: pass
else: ssl._create_default_https_context = _create_unverified_https_context

feedparser.USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# --- 1. SOURCES (INCLUANT SIGNAUX FAIBLES) ---
FLUX_RSS = [
    "https://www.construction-europe.com/rss/articles", 
    "https://www.railwaygazette.com/139.rss",
    "https://www.smart-energy.com/feed/",
    "https://news.google.com/rss/search?q=infrastructure+tenders+funding+projects+nuclear&hl=fr&gl=FR&ceid=FR:fr"
]

NOM_ASSO = "LE CERCLE INFRA"

# --- 2. FONCTIONS DE RÉCUPÉRATION ET GÉNÉRATION ---
def recuperer_articles(flux_list):
    articles = []
    for url in flux_list:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:8]:
                articles.append({"titre": entry.title, "description": entry.description, "lien": entry.link})
        except: pass
    return articles

def generer_draft(articles, api_key):
    client = genai.Client(api_key=api_key)
    ctx = "\n".join([f"TITRE:{a['titre']} | DESC:{a['description']}" for a in articles])

    prompt = f"""
    Tu es l'analyste senior du '{NOM_ASSO}'. Rédige une veille stratégique mondiale en FRANÇAIS.
    
    SECTION 1 : LE BAROMÈTRE DU CERCLE
    Crée un tableau HTML simple avec 3 indicateurs de marché estimés ou réels (ex: Prix CO2, Électricité Spot, Brent).
    
    SECTION 2 : LES 5 ACTUALITÉS CRITIQUES (DIVERSITÉ MONDIALE)
    - 5 news max (Europe, Asie, Afrique, Amériques).
    - Pour chaque news : Titre typo française, Analyse experte justifiée, CHIFFRE CLÉ obligatoire.
    - Utilise <strong> pour le gras. PAS d'astérisques (**). 
    - Texte JUSTIFIÉ (text-align: justify).
    
    SECTION 3 : PERSPECTIVES STRATÉGIQUES
    Analyse prospective finale.
    """
    response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
    return response.text

def finaliser_html(corps_html):
    date_str = datetime.datetime.now().strftime('%d/%m/%Y')
    return f"""
    <!DOCTYPE html><html lang="fr"><head><meta charset="UTF-8">
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; max-width: 800px; margin: auto; padding: 20px; color: #1f2937; background-color: #f3f4f6; }}
        .container {{ background-color: #ffffff; border-radius: 4px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); overflow: hidden; }}
        .header {{ background-color: #0B1F38; padding: 35px; text-align: center; border-bottom: 5px solid #D4AF37; }}
        .logo-text {{ font-size: 32px; font-weight: 800; color: #D4AF37; letter-spacing: 3px; text-transform: uppercase; margin: 0; }}
        .content {{ padding: 45px; text-align: justify; }}
        h2 {{ font-size: 24px; color: #0B1F38; text-align: center; margin-bottom: 30px; }}
        .barometre {{ width: 100%; border-collapse: collapse; margin-bottom: 40px; background: #f8fafc; border: 1px solid #e2e8f0; }}
        .barometre td {{ padding: 15px; border: 1px solid #e2e8f0; text-align: center; font-size: 14px; }}
        .article {{ margin-bottom: 50px; border-bottom: 1px solid #eee; padding-bottom: 30px; }}
        .article-num {{ font-size: 40px; font-weight: 900; color: #D4AF37; line-height: 1; }}
        .article-highlight {{ background-color: #f8fafc; border-left: 5px solid #D4AF37; padding: 15px; margin: 20px 0; }}
        .implications {{ background-color: #0B1F38; color: white; padding: 30px; border-radius: 4px; }}
        .footer {{ background-color: #0B1F38; color: #D4AF37; text-align: center; padding: 20px; font-size: 11px; }}
    </style></head>
    <body><div class="container">
        <div class="header"><h1 class="logo-text">{NOM_ASSO}</h1><div style="color:white; margin-top:5px;">Veille Stratégique • {date_str}</div></div>
        <div class="content">{corps_html}</div>
        <div class="footer">© {datetime.datetime.now().year} {NOM_ASSO} • DOCUMENT STRICTEMENT RÉSERVÉ</div>
    </div></body></html>
    """

# --- 3. INTERFACE UTILISATEUR ---
st.sidebar.title("🗄️ Archives & Outils")
archives = sorted(os.listdir("archives"), reverse=True)
if archives:
    selected_archive = st.sidebar.selectbox("Consulter une veille passée :", archives)
    if st.sidebar.button("Charger l'archive"):
        with open(f"archives/{{selected_archive}}", "r") as f:
            st.sidebar.download_button("Télécharger cette archive", f.read(), selected_archive, "text/html")

if "GEMINI_API_KEY" in st.secrets:
    user_api_key = st.secrets["GEMINI_API_KEY"]
else:
    user_api_key = st.sidebar.text_input("Clé API :", type="password")

st.title("🏛️ Intelligence Center - Le Cercle Infra")

# Initialisation du brouillon dans la session
if "draft_content" not in st.session_state:
    st.session_state.draft_content = ""

col_a, col_b = st.columns(2)

with col_a:
    if st.button("🔄 1. Générer le Brouillon IA", use_container_width=True):
        with st.spinner("Récupération des signaux mondiaux..."):
            articles = recuperer_articles(FLUX_RSS)
            st.session_state.draft_content = generer_draft(articles, user_api_key)

with col_b:
    if st.session_state.draft_content:
        st.success("Brouillon prêt pour révision.")

# Zone d'édition collaborative
if st.session_state.draft_content:
    st.markdown("### ✍️ Mode Brouillon (Modifiez le texte ou les chiffres ici)")
    st.session_state.draft_content = st.text_area("Éditeur HTML / Texte :", value=st.session_state.draft_content, height=500)
    
    if st.button("✅ 2. Valider et Apercevoir la Newsletter", use_container_width=True, type="primary"):
        final_html = finaliser_html(st.session_state.draft_content)
        
        # Sauvegarde automatique en archive
        filename = f"Veille_{datetime.date.today()}.html"
        with open(f"archives/{{filename}}", "w") as f:
            f.write(final_html)
            
        st.divider()
        st.components.v1.html(final_html, height=800, scrolling=True)
        st.download_button("📥 3. Télécharger le fichier final pour envoi", final_html, filename, "text/html")
