import streamlit as st
import feedparser
from google import genai
import datetime
import ssl

# --- CONFIGURATION INTERFACE ---
st.set_page_config(page_title="Le Cercle Infra - Dashboard", page_icon="🏛️", layout="wide")

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError: pass
else: ssl._create_default_https_context = _create_unverified_https_context

feedparser.USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

FLUX_RSS = [
    "https://www.enr.com/rss/articles",
    "https://www.renewableenergyworld.com/feed/",
    "https://www.masstransitmag.com/rss",
    "https://news.google.com/rss/search?q=infrastructure+megaproject+energy+construction&hl=en-US&gl=US&ceid=US:en"
]

NOM_ASSO = "LE CERCLE INFRA"

def recuperer_articles(flux_list, max_articles=10):
    articles = []
    for url in flux_list:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:max_articles]:
                articles.append({
                    "titre": entry.title,
                    "description": entry.description if hasattr(entry, 'description') else "",
                    "lien": entry.link
                })
        except: pass
    return articles

def generer_newsletter(articles, api_key):
    client = genai.Client(api_key=api_key)
    ctx = ""
    for i, art in enumerate(articles):
        ctx += f"ID:{i} | TITRE:{art['titre']} | DESC:{art['description']}\n\n"

    prompt = f"""
    Tu es l'analyste senior du think-tank '{NOM_ASSO}'. 
    Sélectionne les 5 news les plus stratégiques.
    Titres : Typographie française. 
    CHIFFRE CLÉ : Obligatoire d'extraire un NOMBRE ($, %, GW, km).
    TEXTE : Justifié, professionnel. Utilise <strong> pour le gras.
    
    STRUCTURE HTML :
    <h2>[Titre Semaine]</h2>
    <div class="editorial">[Édito justifié]</div>
    [Pour chaque article 01 à 05] :
    <div class="article">
        <div class="article-header"><span class="article-num">[N°]</span><h3 class="article-title">[Titre]</h3></div>
        <div class="article-text">[Texte justifié]</div>
        <div class="article-highlight"><strong>CHIFFRE CLÉ :</strong> [Valeur] — [Contexte]</div>
        <a href="[LIEN]" class="source-link">LIRE LA SOURCE ↗</a>
    </div>
    <div class="implications"><h3>Perspectives stratégiques</h3><p>[Analyse finale]</p></div>
    """
    
    # ON UTILISE LE MODÈLE DISPONIBLE (0/15 sur ta capture)
    response = client.models.generate_content(model='gemini-3.1-flash-lite', contents=prompt)
    return response.text

def creer_html_complet(contenu_html):
    return f"""
    <!DOCTYPE html><html lang="fr"><head><meta charset="UTF-8">
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; max-width: 800px; margin: auto; padding: 20px; color: #1f2937; background-color: #f3f4f6; }}
        .container {{ background-color: #ffffff; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); overflow: hidden; }}
        .header {{ background-color: #0B1F38; padding: 30px 20px; text-align: center; border-bottom: 4px solid #D4AF37; }}
        .logo-text {{ font-size: 32px; font-weight: 800; color: #D4AF37; letter-spacing: 3px; margin: 0; text-transform: uppercase; }}
        .content {{ padding: 40px; }}
        h2 {{ font-size: 26px; color: #0B1F38; margin-bottom: 25px; font-weight: 800; text-align: center; }}
        .article {{ margin-bottom: 50px; border-bottom: 1px solid #e2e8f0; padding-bottom: 30px; }}
        .article-num {{ font-size: 40px; font-weight: 900; color: #D4AF37; line-height: 1; }}
        .article-title {{ font-size: 22px; color: #0B1F38; margin: 0; font-weight: 700; }}
        .article-text {{ color: #334155; line-height: 1.7; font-size: 15px; margin-bottom: 20px; text-align: justify; }}
        .article-highlight {{ background-color: #f8fafc; border-left: 4px solid #D4AF37; color: #0B1F38; padding: 15px 20px; font-weight: 500; margin-bottom: 20px; }}
        .implications {{ background-color: #0B1F38; color: white; padding: 30px; border-radius: 8px; margin-top: 20px; }}
        .footer {{ background-color: #0B1F38; color: #D4AF37; text-align: center; padding: 25px 20px; font-size: 11px; font-weight: 600; text-transform: uppercase; }}
    </style></head>
    <body><div class="container">
        <div class="header"><h1 class="logo-text">{NOM_ASSO}</h1></div>
        <div class="content">{contenu_html}</div>
        <div class="footer">© {datetime.datetime.now().year} {NOM_ASSO} · Diffusion restreinte</div>
    </div></body></html>
    """

st.title("🏛️ Cercle Infra : Production Stratégique")
user_api_key = st.text_input("Clé API Gemini :", type="password", value="AIzaSyBq8v1PYc6D-PqLyqIQ3tZiNSz_wRyyGMY")

if st.button("🚀 Lancer la production", use_container_width=True):
    with st.spinner("Analyse en cours..."):
        data = recuperer_articles(FLUX_RSS)
        if data:
            html_body = generer_newsletter(data, user_api_key)
            final_output = creer_html_complet(html_body)
            st.download_button("📥 Télécharger le fichier", final_output, f"CercleInfra_Veille.html", "text/html")
            st.components.v1.html(final_output, height=1000, scrolling=True)
