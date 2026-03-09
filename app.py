import streamlit as st
import feedparser
from google import genai
import datetime
import ssl
import urllib.parse
import os

# --- 1. CONFIGURATION (ALIGNEMENT STRICT) ---
st.set_page_config(page_title="Le Cercle Infra - Dashboard", page_icon="🏛️", layout="wide")

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

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
            else: logs.append(f"⚠️ {url} VIDE")
        except Exception as e: logs.append(f"❌ {url} ERR")
    return articles, logs

# --- 4. GÉNÉRATION (PROMPT NEUTRE + BAROMÈTRE GRID) ---
def generer_newsletter(articles, api_key):
    client = genai.Client(api_key=api_key)
    ctx = "\n".join([f"ID:{i} | TITRE:{art['titre']} | DESC:{art['description']}" for i, art in enumerate(articles)])

    prompt = f"""
    Rédige la veille stratégique pour le think-tank '{NOM_ASSO}'. 
    Analyse ces news d'infrastructure : {ctx}

    1. LE BAROMÈTRE (GRILLE) : Génère un conteneur <div class="barometre-grid"> contenant 4 blocs <div class="baro-card"> :
       - 🌿 Prix CO2 (EUA) | ⚡ Elec Spot (EU) | 🛢️ Brent ($) | 🏗️ Indice Acier.
    
    2. LES 5 NEWS : 
    <div class="article">
        <div class="article-header"><span class="article-num">[N°]</span><h3 class="article-title">[Titre]</h3></div>
        <div class="article-text">[Texte justifié avec <strong>]</div>
        <div class="article-highlight"><strong>CHIFFRE CLÉ :</strong> [Valeur] — [Contexte]</div>
        <a href="[LIEN]" class="source-link">SOURCE ↗</a>
    </div>

    3. DATA VIZ : [CHART_DATA: Categorie1,Valeur1|Categorie2,Valeur2|Categorie3,Valeur3]
    """
    
    response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
    raw_html = response.text
    
    chart_url = "https://quickchart.io/chart?c={type:'bar',data:{labels:['A','B','C'],datasets:[{label:'Infra',data:[10,20,30],backgroundColor:'#0B1F38'}]}}"
    if "[CHART_DATA:" in raw_html:
        try:
            data_part = raw_html.split("[CHART_DATA:")[1].split("]")[0]
            items = [i.split(",") for i in data_part.split("|")]
            labels = [i[0].strip() for i in items]; values = [i[1].strip() for i in items]
            chart_config = f"{{type:'bar',data:{{labels:{labels},datasets:[{{label:'Analyse Sectorielle',data:[{','.join(values)}],backgroundColor:'#0B1F38'}}]}}}}"
            chart_url = f"https://quickchart.io/chart?c={urllib.parse.quote(chart_config)}"
            raw_html = raw_html.split("[CHART_DATA:")[0]
        except: pass

    chart_html = f'<div style="text-align: center; margin: 40px 0;"><img src="{chart_url}" width="100%" style="max-width: 600px; border-radius: 8px;"></div>'
    return raw_html + chart_html

# --- 5. STYLE (VOTRE FORME EXACTE + GRID) ---
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

# --- 6. INTERFACE (AUCUNE CLÉ HARDCODÉE) ---
st.title("🏛️ Cercle Infra : Production Stratégique")

# On vérifie d'abord les secrets Streamlit
if "GEMINI_API_KEY" in st.secrets:
    user_api_key = st.secrets["GEMINI_API_KEY"]
else:
    # Sinon on demande la clé (vide par défaut pour la sécurité)
    user_api_key = st.sidebar.text_input("Clé API Gemini :", type="password")

if "scan_logs" not in st.session_state: st.session_state.scan_logs = []

if st.button("🚀 Lancer la production", use_container_width=True):
    if not user_api_key:
        st.error("Veuillez saisir votre clé API dans la barre latérale.")
    else:
        with st.spinner("Scan mondial et analyse en cours..."):
            articles, logs = recuperer_articles(FLUX_RSS)
            st.session_state.scan_logs = logs
            if articles:
                try:
                    html_body = generer_newsletter(articles, user_api_key)
                    final_output = creer_html_complet(html_body)
                    st.download_button("📥 Télécharger le fichier", final_output, f"CercleInfra_Veille.html", "text/html")
                    st.components.v1.html(final_output, height=1200, scrolling=True)
                except Exception as e:
                    st.error(f"Erreur : {e}")

if st.session_state.scan_logs:
    with st.expander("📊 Rapport technique du scan"):
        for log in st.session_state.scan_logs: st.write(log)
