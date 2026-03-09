import streamlit as st
import feedparser
from google import genai
import datetime
import ssl
import os

# --- 1. CONFIGURATION & DESIGN ---
st.set_page_config(page_title="Le Cercle Infra - Global 360", page_icon="🏛️", layout="wide")

if not os.path.exists("archives"):
    os.makedirs("archives")

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

# --- 3. FONCTIONS MÉTIER ---
def recuperer_articles(flux_list):
    articles = []
    for url in flux_list:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:3]:
                articles.append({"titre": entry.title, "description": entry.description if hasattr(entry, 'description') else ""})
        except: pass
    return articles

def generer_brouillon(articles, api_key):
    try:
        client = genai.Client(api_key=api_key)
        # Votre moteur de référence
        model_id = "gemini-2.5-flash"
        
        prompt = f"""
        Tu es l'analyste senior du '{NOM_ASSO}'. Rédige une veille stratégique mondiale en FRANÇAIS.
        
        1. BAROMÈTRE : Tableau HTML (<table class="barometre">) : Prix CO2 (EUA), Elec Spot Europe, Brent ($), Indice Acier.
        2. NEWS : Sélectionne les 5 news les plus stratégiques (Diversité : Asie, Afrique, Europe, Amériques).
        3. RIGUEUR : Inclus des chiffres précis (ex: 23 Mds€ rail, 5% conso IA 2030, 25% fuites eau).
        4. STYLE : Professionnel, titres typo française, <strong> pour le gras. Texte JUSTIFIÉ.
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
        .header {{ background-color: #0B1F38; padding: 35px; text-align: center; border-bottom: 5px solid #D4AF37; }}
        .logo-text {{ font-size: 32px; font-weight: 800; color: #D4AF37; letter-spacing: 3px; text-transform: uppercase; margin: 0; }}
        .content {{ padding: 45px; }}
        .barometre {{ width: 100%; border-collapse: collapse; margin-bottom: 40px; background: #f8fafc; border: 1px solid #e2e8f0; }}
        .barometre td {{ padding: 12px; border: 1px solid #e2e8f0; text-align: center; color: #0B1F38; font-weight: 600; font-size: 13px; }}
        .article {{ margin-bottom: 50px; border-bottom: 1px solid #e2e8f0; padding-bottom: 30px; }}
        .article-num {{ font-size: 40px; font-weight: 900; color: #D4AF37; line-height: 1; }}
        .article-title {{ font-size: 22px; color: #0B1F38; margin: 0; font-weight: 700; }}
        .implications {{ background-color: #0B1F38; color: white; padding: 30px; border-radius: 8px; }}
        .footer {{ background-color: #0B1F38; color: #D4AF37; text-align: center; padding: 20px; font-size: 11px; }}
    </style></head>
    <body><div class="container">
        <div class="header"><h1 class="logo-text">{NOM_ASSO}</h1></div>
        <div class="content">{corps_html}</div>
        <div class="footer">© {datetime.datetime.now().year} {NOM_ASSO} · Diffusion restreinte</div>
    </div></body></html>
    """

# --- 4. INTERFACE ---
st.sidebar.title("🗄️ Archives")
archives = sorted(os.listdir("archives"), reverse=True)
if archives:
    selected = st.sidebar.selectbox("Historique :", archives)
    with open(f"archives/{selected}", "r") as f:
        st.sidebar.download_button("📥 Télécharger l'archive", f.read(), selected, "text/html")

st.title("🏛️ Cercle Infra : Production Stratégique")

# Gestion sécurisée de la clé
if "GEMINI_API_KEY" in st.secrets:
    user_key = st.secrets["AIzaSyCm0pIKYoHo1B7PnCVsLpRmtpiVisa4NI0"]
else:
    user_key = st.sidebar.text_input("Clé API Gemini :", type="password")

if "draft" not in st.session_state:
    st.session_state.draft = ""

if st.button("🚀 1. Lancer le Scan & Brouillon IA (20 Flux)", use_container_width=True):
    if not user_key:
        st.error("Veuillez saisir une clé API dans la barre latérale.")
    else:
        with st.spinner("Analyse stratégique mondiale..."):
            articles = recuperer_articles(FLUX_RSS)
            st.session_state.draft = generer_brouillon(articles, user_key)

if st.session_state.draft:
    st.markdown("### ✍️ Révision & Baromètre")
    st.session_state.draft = st.text_area("Éditeur (Modifiez les chiffres ici) :", value=st.session_state.draft, height=500)
    
    if st.button("✅ 2. Valider et Finaliser", use_container_width=True, type="primary"):
        final_html = finaliser_html(st.session_state.draft)
        filename = f"Veille_CercleInfra_{datetime.date.today()}.html"
        with open(f"archives/{filename}", "w") as f: f.write(final_html)
        st.success("Newsletter validée et archivée !")
        st.download_button("📥 3. Télécharger le rapport final", final_html, filename, "text/html")
        st.components.v1.html(final_html, height=1000, scrolling=True)
