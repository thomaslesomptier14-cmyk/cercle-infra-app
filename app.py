import streamlit as st
import feedparser
from google import genai
import datetime
import ssl

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Le Cercle Infra - Global 360", page_icon="🏛️", layout="wide")

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError: pass
else: ssl._create_default_https_context = _create_unverified_https_context

feedparser.USER_AGENT = "Mozilla/5.0 (CercleInfraBot/1.0)"

NOM_ASSO = "LE CERCLE INFRA"

# --- 2. LES 20 FLUX STRATÉGIQUES ---
FLUX_RSS = [
    # --- GLOBAL & ÉCONOMIE ---
    "https://asia.nikkei.com/rss/feed/nar", 
    "https://african.business/category/sectors/infrastructure/feed/",
    "https://www.reutersagency.com/feed/?best-topics=infrastructure&format=xml",
    "https://infrapppworld.com/feed", 
    
    # --- ÉNERGIE & NUCLÉAIRE ---
    "https://world-nuclear-news.org/RSS/WNN-News-Feed",
    "https://www.smart-energy.com/feed/",
    "https://www.renewableenergyworld.com/feed/",
    "https://www.power-technology.com/feed/",
    "https://www.offshore-energy.biz/feed/",
    
    # --- TRANSPORT & LOGISTIQUE ---
    "https://www.globalrailwayreview.com/feed/",
    "https://www.railwaygazette.com/139.rss",
    "https://www.porttechnology.org/feed/",
    "https://www.shippingazette.com/rss/news.xml",
    
    # --- CONSTRUCTION & EAU ---
    "https://www.construction-europe.com/rss/articles",
    "https://www.international-construction.com/rss/articles",
    "https://www.enr.com/rss/articles",
    "https://www.waterworld.com/rss/articles",
    "https://www.globalconstructionreview.com/feed/",
    
    # --- DIGITAL & VILLE INTELLIGENTE ---
    "https://www.smartcitiesworld.net/news/rss",
    "https://www.datacenterdynamics.com/en/feeds/news/"
]

# --- 3. LOGIQUE ---
def recuperer_articles(flux_list):
    articles = []
    for url in flux_list:
        try:
            feed = feedparser.parse(url)
            # On prend 3 articles par flux pour avoir une large base sans saturer
            for entry in feed.entries[:3]:
                articles.append({"titre": entry.title, "description": entry.description if hasattr(entry, 'description') else ""})
        except: pass
    return articles

def generer_newsletter(articles, api_key):
    client = genai.Client(api_key=api_key)
    ctx = "\n".join([f"NEWS: {a['titre']}" for a in articles])

    prompt = f"""
    Tu es l'analyste senior du '{NOM_ASSO}'. 
    Analyse ces 60 news mondiales et sélectionne les 5 pépites les plus stratégiques.
    
    CONSIGNES :
    - Équilibre mondial : Ne reste pas sur un seul continent.
    - Focus métier : Énergie (nucléaire, modulation), Transport (rail, ports), Eau, Digital (conso IA).
    - Rigueur : Rappelle les chiffres clés (ex: 23 Mds€ rail, 5% conso IA 2030, 25% fuites eau).
    - Style : Professionnel, titres typo française, <strong> pour le gras. Texte JUSTIFIÉ.
    
    STRUCTURE :
    <h2>[Titre de la Veille]</h2>
    <div class="editorial">[Édito analytique]</div>
    [Les 5 articles formatés avec N° Or 40px]
    <div class="implications"><h3>Perspectives stratégiques</h3><p>[Analyse prospective]</p></div>
    """
    response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
    return response.text

def finaliser_html(corps_html):
    return f"""
    <!DOCTYPE html><html lang="fr"><head><meta charset="UTF-8">
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; max-width: 800px; margin: auto; padding: 20px; color: #1f2937; background-color: #f3f4f6; }}
        .container {{ background-color: #ffffff; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); overflow: hidden; }}
        .header {{ background-color: #0B1F38; padding: 30px; text-align: center; border-bottom: 4px solid #D4AF37; }}
        .logo-text {{ font-size: 32px; font-weight: 800; color: #D4AF37; letter-spacing: 3px; text-transform: uppercase; margin: 0; }}
        .content {{ padding: 40px; }}
        .article {{ margin-bottom: 50px; border-bottom: 1px solid #e2e8f0; padding-bottom: 30px; }}
        .article-num {{ font-size: 40px; font-weight: 900; color: #D4AF37; line-height: 1; }}
        .article-title {{ font-size: 22px; color: #0B1F38; margin: 0; font-weight: 700; }}
        .article-text {{ color: #334155; line-height: 1.7; text-align: justify; }}
        .article-highlight {{ background-color: #f8fafc; border-left: 4px solid #D4AF37; color: #0B1F38; padding: 15px 20px; }}
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
st.title("🏛️ Cercle Infra : Veille Globale 360")
user_key = st.text_input("Clé API Gemini :", type="password", value="AIzaSyBq8v1PYc6D-PqLyqIQ3tZiNSz_wRyyGMY")

if st.button("🚀 Lancer la production (20 Flux)", use_container_width=True):
    with st.spinner("Scan mondial en cours (environ 15 secondes)..."):
        data = recuperer_articles(FLUX_RSS)
        if data:
            try:
                html_body = generer_newsletter(data, user_key)
                final_output = finaliser_html(html_body)
                st.download_button("📥 Télécharger le Rapport", final_output, "Veille_360_CercleInfra.html", "text/html")
                st.components.v1.html(final_output, height=1000, scrolling=True)
            except Exception as e:
                st.error(f"Quota toujours à 6/5. Patientez. Erreur : {e}")
