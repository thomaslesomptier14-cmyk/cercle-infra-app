import streamlit as st
import feedparser
from google import genai
import datetime
import ssl
import os

# --- 1. CONFIGURATION & DESIGN (RESTAURATION STRICTE) ---
st.set_page_config(page_title="Le Cercle Infra - Global 360", page_icon="🏛️", layout="wide")

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError: pass
else: ssl._create_default_https_context = _create_unverified_https_context

feedparser.USER_AGENT = "Mozilla/5.0 (CercleInfraBot/1.0)"
NOM_ASSO = "LE CERCLE INFRA"

# --- 2. LES 20 FLUX STRATÉGIQUES ---
FLUX_RSS = [
    "https://world-nuclear-news.org/RSS/WNN-News-Feed",
    "https://asia.nikkei.com/rss/feed/nar",
    "https://african.business/category/sectors/infrastructure/feed/",
    "https://www.construction-europe.com/rss/articles",
    "https://www.globalrailwayreview.com/feed/",
    "https://www.waterworld.com/rss/articles",
    "https://infrapppworld.com/feed",
    "https://www.smart-energy.com/feed/",
    "https://www.datacenterdynamics.com/en/feeds/news/",
    "https://www.railwaygazette.com/139.rss",
    "https://www.porttechnology.org/feed/",
    "https://www.enr.com/rss/articles",
    "https://www.power-technology.com/feed/",
    "https://www.renewableenergyworld.com/feed/",
    "https://www.smartcitiesworld.net/news/rss",
    "https://www.globalconstructionreview.com/feed/",
    "https://www.international-construction.com/rss/articles",
    "https://www.shippingazette.com/rss/news.xml",
    "https://www.offshore-energy.biz/feed/",
    "https://news.google.com/rss/search?q=infrastructure+energy+nuclear&hl=fr&gl=FR&ceid=FR:fr"
]

# --- 3. LOGIQUE MÉTIER ---
def recuperer_articles(flux_list):
    articles = []
    for url in flux_list:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:3]:
                articles.append({
                    "titre": entry.title, 
                    "description": entry.description if hasattr(entry, 'description') else "",
                    "lien": entry.link
                })
        except: pass
    return articles

def generer_brouillon(articles, api_key):
    try:
        client = genai.Client(api_key=api_key)
        # RETOUR AU MODÈLE DE TON DASHBOARD
        model_id = "gemini-2.5-flash"
        
        ctx = "\n".join([f"TITRE:{a['titre']} | DESC:{a['description']}" for a in articles])

        prompt = f"""
        Tu es l'analyste senior du think-tank '{NOM_ASSO}'. 
        Analyse ces news d'infrastructure : {ctx}

        CONSIGNES :
        1. Sélectionne les 5 news les plus stratégiques mondialement.
        2. Titres : Typographie française (Majuscule au début).
        3. CHIFFRE CLÉ : Obligation absolue d'extraire un NOMBRE ($, %, GW, km).
        4. TEXTE : Justifié, pro, expert. <strong> pour le gras. Pas d'astérisques.

        FORMAT HTML :
        - Inclus un tableau <table class="barometre"> avec Prix CO2, Elec, Brent, Acier.
        - Utilise <div class="article"> avec <span class="article-num"> pour le numéro.
        """
        response = client.models.generate_content(model=model_id, contents=prompt)
        return response.text
    except Exception as e:
        return f"ERREUR_API: {str(e)}"

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
        .source-link {{ display: inline-block; color: #0B1F38; font-weight: 700; text-decoration: none; font-size: 12px; border-bottom: 1px solid #D4AF37; }}
        .implications {{ background-color: #0B1F38; color: white; padding: 30px; border-radius: 8px; }}
        .footer {{ background-color: #0B1F38; color: #D4AF37; text-align: center; padding: 25px 20px; font-size: 11px; font-weight: 600; text-transform: uppercase; }}
    </style></head>
    <body><div class="container">
        <div class="header"><h1 class="logo-text">{NOM_ASSO}</h1><div class="date">Veille du {date_str}</div></div>
        <div class="content">{corps_html}</div>
        <div class="footer">© {datetime.datetime.now().year} {NOM_ASSO} · Diffusion restreinte</div>
    </div></body></html>
    """

# --- 4. INTERFACE ---
st.title("🏛️ Cercle Infra : Production Stratégique")

# Utilise le NOM de ton secret ici
if "GEMINI_API_KEY" in st.secrets:
    user_key = st.secrets["GEMINI_API_KEY"]
else:
    user_key = st.sidebar.text_input("Clé API Gemini :", type="password")

if "draft" not in st.session_state:
    st.session_state.draft = ""

if st.button("🚀 Lancer la production (Moteur 2.5 Flash)", use_container_width=True):
    if not user_key:
        st.error("Clé API manquante.")
    else:
        with st.spinner("Scan des 20 flux mondiaux..."):
            articles = recuperer_articles(FLUX_RSS)
            st.session_state.draft = generer_brouillon(articles, user_key)

if st.session_state.draft:
    st.markdown("### ✍️ Révision Collaborative")
    st.session_state.draft = st.text_area("Éditeur HTML :", value=st.session_state.draft, height=500)
    
    if st.button("✅ Valider et Finaliser", use_container_width=True, type="primary"):
        final_html = finaliser_html(st.session_state.draft)
        st.success("Newsletter générée !")
        st.download_button("📥 Télécharger le fichier final", final_html, f"Veille_CercleInfra.html", "text/html")
        st.components.v1.html(final_html, height=1000, scrolling=True)
