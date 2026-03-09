import streamlit as st
import feedparser
from google import genai
import datetime
import ssl
import os

# --- 1. CONFIGURATION (ALIGNEMENT STRICT & SÉCURITÉ) ---
st.set_page_config(page_title="Le Cercle Infra - Hebdo", page_icon="🏛️", layout="wide")

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError: pass
else: ssl._create_default_https_context = _create_unverified_https_context

# User-Agent renforcé pour éviter les "VIDE" sur les sites protégés
feedparser.USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

NOM_ASSO = "LE CERCLE INFRA"

# --- 2. LES 20 FLUX STRATÉGIQUES (MIS À JOUR POUR ÉVITER LES ERREURS) ---
FLUX_RSS = [
    "https://www.iaea.org/newscenter/news/rss.xml",                  # Nucléaire (IAEA - Plus robuste)
    "https://asia.nikkei.com/rss/feed/nar",                        # Asie
    "http://feeds.reuters.com/reuters/AFRICANews",                  # Afrique (Reuters)
    "https://www.construction-europe.com/rss/articles",             # Construction Europe
    "https://www.globalrailwayreview.com/feed/",                    # Rail Monde
    "https://www.smart-energy.com/feed/",                           # Grids / Transition
    "https://www.power-technology.com/feed/",                       # Énergie
    "https://www.renewableenergyworld.com/feed/",                   # Renouvelables
    "https://www.globalconstructionreview.com/feed/",               # BTP Mondial
    "https://www.offshore-energy.biz/feed/",                        # Offshore
    "https://www.datacenterdynamics.com/en/feeds/news/",            # Data Centers
    "https://www.porttechnology.org/feed/",                         # Ports
    "https://www.enr.com/rss/articles",                              # Engineering News
    "https://www.railwaygazette.com/139.rss",                       # Rail Gazette
    "https://infrapppworld.com/feed",                               # PPP & Finance
    "https://www.waterworld.com/rss/articles",                      # Eau
    "https://www.smartcitiesworld.net/news/rss",                    # Smart Cities
    "https://www.international-construction.com/rss/articles",      # BTP International
    "https://news.google.com/rss/search?q=infrastructure+energy+nuclear&hl=fr&gl=FR&ceid=FR:fr",
    "https://news.google.com/rss/search?q=SMR+nuclear+reactor+deployment&hl=en&gl=US&ceid=US:en"
]

# --- 3. RÉCUPÉRATION AVEC LOGS ---
def recuperer_articles(flux_list, max_articles=3):
    articles = []
    logs = []
    for url in flux_list:
        try:
            feed = feedparser.parse(url)
            if feed.entries:
                logs.append(f"✅ {url} OK")
                for entry in feed.entries[:max_articles]:
                    articles.append({
                        "titre": entry.title,
                        "description": entry.description if hasattr(entry, 'description') else "",
                        "lien": entry.link
                    })
            else:
                logs.append(f"⚠️ {url} VIDE (Accès bloqué ou flux vide)")
        except Exception as e:
            logs.append(f"❌ {url} ERR : {str(e)}")
    return articles, logs

# --- 4. GÉNÉRATION (DATA-DRIVEN SANS GRAPHIQUE) ---
def generer_newsletter(articles, api_key):
    client = genai.Client(api_key=api_key)
    ctx = "\n".join([f"ID:{i} | TITRE:{art['titre']} | DESC:{art['description']}" for i, art in enumerate(articles)])

    # Prompt avec injonction de chiffres impérative
    prompt = f"""
    Rédige la veille hebdomadaire du 9 mars 2026 pour le think-tank '{NOM_ASSO}'. 
    Analyse ces news d'infrastructure : {ctx}

    CONSIGNES CRITIQUES :
    1. LE BAROMÈTRE : Tu DOIS fournir des valeurs chiffrées réalistes pour :
       - 🌿 Prix CO2 (EUA) | ⚡ Elec Spot (EU) | 🛢️ Brent ($) | 🏗️ Indice Acier.
       AUCUN CHAMP VIDE. Format : <div class="barometre-grid"> avec 4 <div class="baro-card">.
    
    2. CHIFFRES CLÉS : Chaque news choisie (01 à 05) DOIT impérativement mettre en avant un CHIFFRE CLÉ ($, %, GW, km). 
       Sans chiffre, la news est inutile.
    
    3. PAS DE GRAPHIQUE à la fin. 
    
    4. STYLE : Professionnel, titres typo française, texte JUSTIFIÉ, <strong> pour le gras. Pas d'astérisques.
    """
    
    response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
    return response.text

# --- 5. STYLE (VOTRE FORME HÉRITAGE - AUCUNE MODIFICATION) ---
def creer_html_complet(contenu_html):
    return f"""
    <!DOCTYPE html><html lang="fr"><head><meta charset="UTF-8">
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; max-width: 800px; margin: auto; padding: 20px; color: #1f2937; background-color: #f3f4f6; }}
        .container {{ background-color: #ffffff; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); overflow: hidden; }}
        .header {{ background-color: #0B1F38; padding: 30px; text-align: center; border-bottom: 4px solid #D4AF37; }}
        .logo-text {{ font-size: 32px; font-weight: 800; color: #D4AF37; letter-spacing: 3px; text-transform: uppercase; margin: 0; }}
        .content {{ padding: 40px; }}
        
        .barometre-grid {{ display: flex; gap: 15px; margin-bottom: 40px; justify-content: space-between; }}
        .baro-card {{ background: #f8fafc; border: 1px solid #e2e8f0; border-top: 4px solid #D4AF37; padding: 15px; flex: 1; text-align: center; border-radius: 4px; }}
        .baro-label {{ font-size: 11px; color: #64748b; text-transform: uppercase; font-weight: 700; margin-bottom: 5px; }}
        .baro-value {{ font-size: 18px; color: #0B1F38; font-weight: 800; }}
        
        h2 {{ font-size: 26px; color: #0B1F38; margin-bottom: 25px; font-weight: 800; text-align: center; }}
        .editorial {{ background-color: #f8fafc; padding: 20px; border-left: 4px solid #0B1F38; margin-bottom: 50px; font-style: italic; text-align: justify; }}
        .article {{ margin-bottom: 50px; border-bottom: 1px solid #e2e8f0; padding-bottom: 30px; }}
        .article-header {{ display: flex; align-items: baseline; gap: 15px; margin-bottom: 15px; }}
        .article-num {{ font-size: 40px; font-weight: 900; color: #D4AF37; line-height: 1; }}
        .article-title {{ font-size: 22px; color: #0B1F38; margin: 0; font-weight: 700; }}
        .article-text {{ color: #334155; line-height: 1.7; text-align: justify; font-size: 15px; }}
        .article-highlight {{ background-color: #f8fafc; border-left: 4px solid #D4AF37; color: #0B1F38; padding: 15px 20px; font-weight: 500; margin-bottom: 20px; }}
        .implications {{ background-color: #0B1F38; color: white; padding: 30px; border-radius: 8px; }}
        .footer {{ background-color: #0B1F38; color: #D4AF37; text-align: center; padding: 25px; font-size: 11px; font-weight: 600; text-transform: uppercase; }}
    </style></head>
    <body><div class="container">
        <div class="header"><h1 class="logo-text">{NOM_ASSO}</h1></div>
        <div class="content">{contenu_html}</div>
        <div class="footer">© {datetime.datetime.now().year} {NOM_ASSO} · Diffusion restreinte</div>
    </div></body></html>
    """

# --- 6. INTERFACE ---
st.title("🏛️ Cercle Infra : Production Hebdomadaire")

# Récupération sécurisée
if "GEMINI_API_KEY" in st.secrets:
    user_api_key = st.secrets["GEMINI_API_KEY"]
else:
    user_api_key = st.sidebar.text_input("Clé API Gemini :", type="password")

if "scan_logs" not in st.session_state: st.session_state.scan_logs = []

if st.button("🚀 Lancer la production", use_container_width=True):
    if not user_api_key:
        st.error("Veuillez configurer votre clé API.")
    else:
        with st.spinner("Scan mondial et analyse des chiffres..."):
            articles, logs = recuperer_articles(FLUX_RSS)
            st.session_state.scan_logs = logs
            if articles:
                try:
                    html_body = generer_newsletter(articles, user_api_key)
                    final_output = creer_html_complet(html_body)
                    st.download_button("📥 Télécharger la Newsletter", final_output, f"CercleInfra_Hebdo.html", "text/html")
                    st.components.v1.html(final_output, height=1200, scrolling=True)
                except Exception as e:
                    st.error(f"Erreur : {e}")

if st.session_state.scan_logs:
    with st.expander("📊 Rapport technique du scan (Vérifiez les sources ici)"):
        for log in st.session_state.scan_logs: st.write(log)
