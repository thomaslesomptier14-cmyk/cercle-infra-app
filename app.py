import streamlit as st
import feedparser
from google import genai
import datetime
import ssl
import os

# --- CONFIGURATION PAGE ---
st.set_page_config(page_title="Le Cercle Infra - Intelligence Suite", page_icon="🏛️", layout="wide")

if not os.path.exists("archives"):
    os.makedirs("archives")

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError: pass
else: ssl._create_default_https_context = _create_unverified_https_context

feedparser.USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# --- SOURCES MONDIALES ---
FLUX_RSS = [
    "https://asia.nikkei.com/rss/feed/nar", 
    "https://african.business/category/sectors/infrastructure/feed/",
    "https://www.construction-europe.com/rss/articles",
    "https://news.google.com/rss/search?q=infrastructure+energy+nuclear+europe&hl=fr&gl=FR&ceid=FR:fr"
]

NOM_ASSO = "LE CERCLE INFRA"

def recuperer_articles(flux_list):
    articles = []
    for url in flux_list:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:8]:
                articles.append({"titre": entry.title, "description": entry.description})
        except: pass
    return articles

def generer_brouillon(articles, api_key):
    try:
        client = genai.Client(api_key=api_key)
        # CHANGEMENT DE MODÈLE ICI : 1.5 Flash est plus stable pour le Free Tier
        model_id = "gemini-1.5-flash" 
        
        ctx = "\n".join([f"Titre: {a['titre']}" for a in articles])

        prompt = f"""
        Tu es l'analyste senior du '{NOM_ASSO}'. Rédige une veille stratégique mondiale en FRANÇAIS.
        
        Indices du Baromètre : Propose des valeurs pour Prix CO2 (EUA), Elec Spot, Brent, et Indice Acier.
        Contenu : Sélectionne 5 news stratégiques mondiales.
        Format : HTML, titres typo française, texte JUSTIFIÉ, <strong> pour le gras.
        """
        
        response = client.models.generate_content(model=model_id, contents=prompt)
        return response.text
    except Exception as e:
        return f"ERREUR_QUOTA: {str(e)}"

def finaliser_html(corps_html):
    date_str = datetime.datetime.now().strftime('%d %b %Y')
    return f"""
    <!DOCTYPE html><html lang="fr"><head><meta charset="UTF-8">
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; max-width: 800px; margin: auto; padding: 20px; color: #1f2937; background-color: #f3f4f6; }}
        .container {{ background-color: #ffffff; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); overflow: hidden; }}
        .header {{ background-color: #0B1F38; padding: 30px; text-align: center; border-bottom: 4px solid #D4AF37; }}
        .logo-text {{ font-size: 32px; font-weight: 800; color: #D4AF37; letter-spacing: 3px; text-transform: uppercase; margin: 0; }}
        .content {{ padding: 40px; }}
        h2 {{ font-size: 26px; color: #0B1F38; margin-bottom: 25px; font-weight: 800; text-align: center; }}
        .article {{ margin-bottom: 50px; border-bottom: 1px solid #e2e8f0; padding-bottom: 30px; }}
        .article-header {{ display: flex; align-items: baseline; gap: 15px; margin-bottom: 15px; }}
        .article-num {{ font-size: 40px; font-weight: 900; color: #D4AF37; line-height: 1; }}
        .article-title {{ font-size: 22px; color: #0B1F38; margin: 0; font-weight: 700; }}
        .article-text {{ color: #334155; line-height: 1.7; font-size: 15px; margin-bottom: 20px; text-align: justify; }}
        .article-highlight {{ background-color: #f8fafc; border-left: 4px solid #D4AF37; color: #0B1F38; padding: 15px 20px; font-weight: 500; }}
        .implications {{ background-color: #0B1F38; color: white; padding: 30px; border-radius: 8px; }}
        .footer {{ background-color: #0B1F38; color: #D4AF37; text-align: center; padding: 20px; font-size: 11px; }}
    </style></head>
    <body><div class="container">
        <div class="header"><h1 class="logo-text">{NOM_ASSO}</h1><div style="color:white; margin-top:5px;">Veille Stratégique • {date_str}</div></div>
        <div class="content">{corps_html}</div>
        <div class="footer">© {datetime.datetime.now().year} {NOM_ASSO} • DOCUMENT RÉSERVÉ</div>
    </div></body></html>
    """

# --- INTERFACE ---
st.title("🏛️ Intelligence Center - Le Cercle Infra")

if "GEMINI_API_KEY" in st.secrets:
    user_key = st.secrets["GEMINI_API_KEY"]
else:
    user_key = st.sidebar.text_input("Clé API Gemini :", type="password")

if "draft" not in st.session_state:
    st.session_state.draft = ""

if st.button("🚀 1. Lancer le Scan & Brouillon IA", use_container_width=True):
    with st.spinner("Analyse en cours..."):
        articles = recuperer_articles(FLUX_RSS)
        res = generer_brouillon(articles, user_key)
        if "ERREUR_QUOTA" in res:
            st.error("Quota atteint. Attendez 60 secondes ou vérifiez votre clé API sur Google AI Studio.")
        else:
            st.session_state.draft = res

if st.session_state.draft:
    st.session_state.draft = st.text_area("Éditeur (Brouillon) :", value=st.session_state.draft, height=400)
    if st.button("✅ 2. Valider et Finaliser", use_container_width=True, type="primary"):
        final_html = finaliser_html(st.session_state.draft)
        st.download_button("📥 3. Télécharger la Newsletter", final_html, f"Veille_CercleInfra_{datetime.date.today()}.html", "text/html")
        st.components.v1.html(final_html, height=1000, scrolling=True)
