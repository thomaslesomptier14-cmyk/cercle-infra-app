import streamlit as st
import feedparser
from google import genai
import datetime
import ssl
import os

# --- 1. CONFIGURATION (STRICTEMENT INCHANGÉE) ---
st.set_page_config(page_title="Le Cercle Infra - Hebdo", page_icon="🏛️", layout="wide")

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError: pass
else: ssl._create_default_https_context = _create_unverified_https_context

feedparser.USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
NOM_ASSO = "LE CERCLE INFRA"

# --- 2. LES 20 FLUX (MIS À JOUR POUR ÉVITER LES ÉTATS "VIDE") ---
FLUX_RSS = [
    "https://news.google.com/rss/search?q=nuclear+energy+generation+SMR+iaea&hl=en&gl=US&ceid=US:en",
    "https://asia.nikkei.com/rss/feed/nar", 
    "https://news.google.com/rss/search?q=africa+infrastructure+investment+projects&hl=en&gl=ZA&ceid=ZA:en",
    "https://news.google.com/rss/search?q=europe+construction+infrastructure+projects&hl=en&gl=GB&ceid=GB:en",
    "https://www.globalrailwayreview.com/feed/",
    "https://news.google.com/rss/search?q=water+infrastructure+desalination+networks&hl=en&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=infrastructure+finance+PPP+investment&hl=en&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=smart+grid+energy+transition+storage&hl=en&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=data+center+infrastructure+AI+consumption&hl=en&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=rail+infrastructure+high+speed+trains&hl=en&gl=GB&ceid=GB:en",
    "https://news.google.com/rss/search?q=port+infrastructure+shipping+logistics&hl=en&gl=US&ceid=US:en",
    "https://www.enr.com/rss/articles",
    "https://www.power-technology.com/feed/",
    "https://www.renewableenergyworld.com/feed/",
    "https://news.google.com/rss/search?q=smart+cities+urban+infrastructure&hl=en&gl=US&ceid=US:en",
    "https://www.globalconstructionreview.com/feed/",
    "https://news.google.com/rss/search?q=global+construction+megaprojects&hl=en&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=maritime+shipping+infrastructure&hl=en&gl=US&ceid=US:en",
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
        except Exception: logs.append(f"❌ {url} ERR")
    return articles, logs

# --- 4. GÉNÉRATION (FORMAT HTML STRICT - SANS MARKDOWN) ---
def generer_newsletter(articles, api_key):
    client = genai.Client(api_key=api_key)
    ctx = "\n".join([f"ID:{i} | TITRE:{art['titre']} | DESC:{art['description']}" for i, art in enumerate(articles)])

    prompt = f"""
    Rédige la veille hebdomadaire du 9 mars 2026 pour le think-tank '{NOM_ASSO}'. 
    Analyse ces news : {ctx}

    IMPORTANT : RÉPONDS UNIQUEMENT EN HTML. INTERDICTION D'UTILISER DU MARKDOWN (PAS DE ** OU DE ###).
    
    1. LE BAROMÈTRE : Fournis impérativement les valeurs réelles pour :
       🌿 Prix CO2 (EUA) | ⚡ Elec Spot (EU) | 🛢️ Brent ($) | 🏗️ Indice Acier.
       Format : <div class="barometre-grid"> avec 4 <div class="baro-card"> contenant <div class="baro-label"> et <div class="baro-value">.
    
    2. TITRE : <h2>[Titre]</h2>
    
    3. ÉDITO : <div class="editorial">[Texte justifié]</div>
    
    4. LES 5 NEWS : Utilise impérativement cette structure pour chaque news :
    <div class="article">
        <div class="article-header"><span class="article-num">[01 à 05]</span><h3 class="article-title">[Titre]</h3></div>
        <div class="article-text">[Analyse justifiée]</div>
        <div class="article-highlight"><strong>CHIFFRE CLÉ :</strong> [Valeur numérique] — [Contexte]</div>
        <a href="[LIEN]" class="source-link">LIRE LA SOURCE ↗</a>
    </div>

    5. IMPLICATIONS : <div class="implications"><h3>Perspectives stratégiques</h3><p>[Texte]</p></div>
    """
    
    # Moteur 2.5 Flash selon vos quotas
    response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
    return response.text

# --- 5. STYLE (FORME HÉRITAGE - VERROUILLÉE) ---
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
        .article-highlight strong {{ color: #D4AF37; font-weight: 800; text-transform: uppercase; }}
        .source-link {{ display: inline-block; color: #0B1F38; font-weight: 700; text-decoration: none; font-size: 12px; border-bottom: 1px solid #D4AF37; }}
        .implications {{ background-color: #0B1F38; color: white; padding: 30px; border-radius: 8px; }}
        .implications h3 {{ color: #D4AF37; margin-top: 0; text-transform: uppercase; font-size: 18px; }}
        .footer {{ background-color: #0B1F38; color: #D4AF37; text-align: center; padding: 25px; font-size: 11px; font-weight: 600; text-transform: uppercase; border-top: 1px solid #1a365d; }}
    </style></head>
    <body><div class="container">
        <div class="header"><h1 class="logo-text">{NOM_ASSO}</h1></div>
        <div class="content">{contenu_html}</div>
        <div class="footer">© {datetime.datetime.now().year} {NOM_ASSO} · Diffusion restreinte</div>
    </div></body></html>
    """

# --- 6. INTERFACE STREAMLIT ---
st.title("🏛️ Cercle Infra : Production Hebdomadaire")

if "GEMINI_API_KEY" in st.secrets:
    user_api_key = st.secrets["GEMINI_API_KEY"]
else:
    user_api_key = st.sidebar.text_input("Clé API Gemini :", type="password")

if "scan_logs" not in st.session_state: st.session_state.scan_logs = []

if st.button("🚀 Lancer la production", use_container_width=True):
    if not user_api_key:
        st.error("Veuillez configurer votre clé API.")
    else:
        with st.spinner("Analyse stratégique en cours..."):
            articles, logs = recuperer_articles(FLUX_RSS)
            st.session_state.scan_logs = logs
            if articles:
                try:
                    html_body = generer_newsletter(articles, user_api_key)
                    final_output = creer_html_complet(html_body)
                    st.success("Newsletter générée !")
                    st.download_button("📥 Télécharger la Newsletter", final_output, f"CercleInfra_Hebdo.html", "text/html")
                    st.components.v1.html(final_output, height=1200, scrolling=True)
                except Exception as e:
                    st.error(f"Erreur API : {e}")

if st.session_state.scan_logs:
    with st.expander("📊 Rapport technique du scan"):
        for log in st.session_state.scan_logs: st.write(log)
