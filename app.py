import streamlit as st
import feedparser
from google import genai
import datetime
import ssl
import os

# --- 1. CONFIGURATION & DESIGN ---
st.set_page_config(page_title="Le Cercle Infra - Dashboard", page_icon="🏛️", layout="wide")

if not os.path.exists("archives"):
    os.makedirs("archives")

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError: pass
else: ssl._create_default_https_context = _create_unverified_https_context

feedparser.USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

NOM_ASSO = "LE CERCLE INFRA"

# --- 2. SOURCES MONDIALES ---
FLUX_RSS = [
    "https://asia.nikkei.com/rss/feed/nar", 
    "https://african.business/category/sectors/infrastructure/feed/",
    "https://www.construction-europe.com/rss/articles",
    "https://www.railwaygazette.com/139.rss",
    "https://news.google.com/rss/search?q=infrastructure+energy+nuclear+projects&hl=fr&gl=FR&ceid=FR:fr"
]

# --- 3. MOTEUR DE GÉNÉRATION ---
def generer_brouillon(articles, api_key):
    try:
        client = genai.Client(api_key=api_key)
        # On utilise 1.5 Flash pour éviter tes erreurs 429 et 404 actuelles
        model_id = "gemini-1.5-flash"
        
        prompt = f"""
        Tu es l'analyste senior du '{NOM_ASSO}'. Rédige une veille stratégique mondiale en FRANÇAIS.
        
        SECTION 1 : BAROMÈTRE STRATÉGIQUE
        Crée un tableau HTML (<table class="barometre">) avec 4 indices : 
        1. Prix CO2 (EUA) | 2. Électricité Spot (Europe) | 3. Brent ($) | 4. Indice Acier/Construction.
        
        SECTION 2 : LES 5 NEWS CRITIQUES
        - Sélectionne 5 news (Diversité : Asie, Afrique, Europe, Amériques).
        - Format : Titre typo française, Analyse experte justifiée, CHIFFRE CLÉ obligatoire.
        - Utilise <strong> pour le gras. PAS d'astérisques.
        
        SECTION 3 : PERSPECTIVES STRATÉGIQUES
        Analyse de synthèse sur la souveraineté et la transition énergétique.
        """
        response = client.models.generate_content(model=model_id, contents=prompt)
        return response.text
    except Exception as e:
        return f"ERREUR_API: {str(e)}"

# --- 4. FORMAT VISUEL (TON STYLE PRÉFÉRÉ) ---
def finaliser_html(corps_html):
    date_str = datetime.datetime.now().strftime('%d %b %Y')
    return f"""
    <!DOCTYPE html><html lang="fr"><head><meta charset="UTF-8">
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; max-width: 800px; margin: auto; padding: 20px; color: #1f2937; background-color: #f3f4f6; }}
        .container {{ background-color: #ffffff; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); overflow: hidden; }}
        .header {{ background-color: #0B1F38; padding: 30px 20px; text-align: center; border-bottom: 4px solid #D4AF37; }}
        .logo-text {{ font-size: 32px; font-weight: 800; color: #D4AF37; letter-spacing: 3px; margin: 0; text-transform: uppercase; }}
        .date {{ font-size: 13px; font-weight: 600; color: #ffffff; text-transform: uppercase; margin-top: 8px; opacity: 0.8; }}
        .content {{ padding: 40px; }}
        h2 {{ font-size: 26px; color: #0B1F38; margin-bottom: 25px; font-weight: 800; text-align: center; }}
        .barometre {{ width: 100%; border-collapse: collapse; margin-bottom: 40px; background: #f8fafc; border: 1px solid #e2e8f0; }}
        .barometre td {{ padding: 12px; border: 1px solid #e2e8f0; text-align: center; color: #0B1F38; font-weight: 600; font-size: 13px; }}
        .article {{ margin-bottom: 50px; border-bottom: 1px solid #e2e8f0; padding-bottom: 30px; }}
        .article-header {{ display: flex; align-items: baseline; gap: 15px; margin-bottom: 15px; }}
        .article-num {{ font-size: 40px; font-weight: 900; color: #D4AF37; line-height: 1; }}
        .article-title {{ font-size: 22px; color: #0B1F38; margin: 0; font-weight: 700; }}
        .article-text {{ color: #334155; line-height: 1.7; font-size: 15px; margin-bottom: 20px; text-align: justify; }}
        .article-highlight {{ background-color: #f8fafc; border-left: 4px solid #D4AF37; color: #0B1F38; padding: 15px 20px; font-weight: 500; margin-bottom: 20px; }}
        .article-highlight strong {{ color: #D4AF37; font-weight: 800; text-transform: uppercase; }}
        .source-link {{ display: inline-block; color: #0B1F38; font-weight: 700; text-decoration: none; font-size: 12px; border-bottom: 1px solid #D4AF37; }}
        .implications {{ background-color: #0B1F38; color: white; padding: 30px; border-radius: 8px; margin-top: 20px; }}
        .implications h3 {{ color: #D4AF37; margin-top: 0; text-transform: uppercase; font-size: 18px; }}
        .implications p {{ text-align: justify; margin: 0; }}
        .footer {{ background-color: #0B1F38; color: #D4AF37; text-align: center; padding: 25px 20px; font-size: 11px; font-weight: 600; text-transform: uppercase; border-top: 1px solid #1a365d; }}
    </style></head>
    <body><div class="container">
        <div class="header"><h1 class="logo-text">{NOM_ASSO}</h1><div class="date">Édition du {date_str}</div></div>
        <div class="content">{corps_html}</div>
        <div class="footer">© {datetime.datetime.now().year} {NOM_ASSO} · Diffusion restreinte</div>
    </div></body></html>
    """

# --- 5. INTERFACE ---
st.title("🏛️ Cercle Infra : Production Stratégique")

if "GEMINI_API_KEY" in st.secrets:
    user_key = st.secrets["GEMINI_API_KEY"]
else:
    user_key = st.sidebar.text_input("Clé API Gemini :", type="password")

if "draft" not in st.session_state:
    st.session_state.draft = ""

if st.button("🚀 1. Lancer le Scan & Brouillon IA", use_container_width=True):
    with st.spinner("Analyse stratégique mondiale..."):
        articles = recuperer_articles(FLUX_RSS)
        res = generer_brouillon(articles, user_key)
        st.session_state.draft = res

if st.session_state.draft:
    st.markdown("### ✍️ Révision & Benchmark (Modifiez les indices ou le texte ici)")
    st.session_state.draft = st.text_area("Éditeur :", value=st.session_state.draft, height=500)
    
    if st.button("✅ 2. Valider et Finaliser", use_container_width=True, type="primary"):
        final_html = finaliser_html(st.session_state.draft)
        filename = f"CercleInfra_{datetime.date.today()}.html"
        st.success("Newsletter générée !")
        st.download_button("📥 3. Télécharger la version finale", final_html, filename, "text/html")
        st.components.v1.html(final_html, height=1000, scrolling=True)
