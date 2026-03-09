import streamlit as st
import feedparser
from google import genai
import datetime
import ssl
import urllib.parse
import re

# --- CONFIGURATION PAGE ---
st.set_page_config(page_title="Le Cercle Infra - Intelligence", page_icon="🏛️", layout="wide")

# Déblocage SSL pour Mac
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError: pass
else: ssl._create_default_https_context = _create_unverified_https_context

feedparser.USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# --- 1. SOURCES INTERNATIONALES ÉLARGIES ---
FLUX_RSS = [
    "https://www.enr.com/rss/articles", # USA - Méga-projets
    "https://www.renewableenergyworld.com/feed/", # Global - Énergie
    "https://www.masstransitmag.com/rss", # Global - Transports
    "https://elpais.com/rss/economia/macroeconomia.xml", # Espagne - Macro/Infra
    "https://www.faz.net/rss/aktuell/wirtschaft/unternehmen/", # Allemagne - Industrie
    "https://news.google.com/rss/search?q=infrastructure+energy+nuclear+funding&hl=en-US&gl=US&ceid=US:en" # Google News Global
]

NOM_ASSO = "LE CERCLE INFRA"

# --- 2. RÉCUPÉRATION DES ARTICLES ---
def recuperer_articles(flux_list, max_articles=10):
    articles = []
    for url in flux_list:
        try:
            feed = feedparser.parse(url)
            if not feed.entries: continue
            for entry in feed.entries[:max_articles]:
                articles.append({
                    "titre": entry.title,
                    "description": entry.description if hasattr(entry, 'description') else "",
                    "lien": entry.link
                })
        except Exception: pass
    return articles

# --- 3. GÉNÉRATION PAR L'IA ---
def generer_newsletter(articles, api_key):
    client = genai.Client(api_key=api_key)
    
    ctx = ""
    for i, art in enumerate(articles):
        ctx += f"ID:{i} | TITRE:{art['titre']} | DESC:{art['description']}\n\n"

    prompt = f"""
    Tu es l'analyste senior du think-tank '{NOM_ASSO}'. 
    Analyse ces news d'infrastructure mondiales (Anglais, Espagnol, Allemand) : {ctx}

    CONSIGNES DE RÉDACTION (FRANÇAIS) :
    1. Sélectionne les 5 news les plus stratégiques.
    2. TYPOGRAPHIE : Majuscule uniquement au début du titre (ex: "Le projet avance" et non "Le Projet Avance").
    3. CHIFFRE CLÉ : Obligation d'extraire un NOMBRE réel ($, %, GW, km). Sois précis.
    4. FORMATAGE : Texte JUSTIFIÉ. Utilise <strong> pour le gras. JAMAIS d'astérisques (**).
    5. DATA VIZ : Génère 3 catégories et 3 valeurs numériques issues des actualités.
       Format : [CHART_DATA: Categorie1,Valeur1|Categorie2,Valeur2|Categorie3,Valeur3]

    STRUCTURE HTML :
    <h2>[Titre Semaine]</h2>
    <div class="editorial">[Édito analytique justifié]</div>
    
    [Pour chaque article 01 à 05] :
    <div class="article">
        <div class="article-header"><span class="article-num">[N°]</span><h3 class="article-title">[Titre]</h3></div>
        <div class="article-text">[Analyse fluide, justifiée, avec <strong> et éventuellement <ul><li>]</div>
        <div class="article-highlight"><strong>CHIFFRE CLÉ :</strong> [Valeur numérique] — [Contexte]</div>
        <a href="[LIEN]" class="source-link" target="_blank">LIRE LA SOURCE ↗</a>
    </div>

    <div class="implications"><h3>Perspectives stratégiques</h3><p>[Analyse finale justifiée]</p></div>
    """
    
    response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
    raw_html = response.text
    
    # --- FIX CHART ERROR : Traitement Python du graphique ---
    chart_url = "https://quickchart.io/chart?c={type:'bar',data:{labels:['Projets','Invest.','R&D'],datasets:[{label:'Secteur',data:[40,60,30],backgroundColor:'#0B1F38'}]}}"
    match = re.search(r"\[CHART_DATA:\s*(.*?)\]", raw_html)
    if match:
        try:
            data_str = match.group(1)
            pairs = [p.split(",") for p in data_str.split("|")]
            labels = [p[0].strip() for p in pairs]
            values = [p[1].strip() for p in pairs]
            config = f"{{type:'bar',data:{{labels:{labels},datasets:[{{label:'Indicateurs Hebdomadaires',data:[{','.join(values)}],backgroundColor:'#0B1F38'}}]}}}}"
            chart_url = f"https://quickchart.io/chart?c={urllib.parse.quote(config)}"
            raw_html = raw_html.replace(match.group(0), "") # Nettoyage du tag
        except: pass

    chart_html = f'<div style="text-align: center; margin: 40px 0;"><img src="{chart_url}" width="100%" style="max-width: 600px; border-radius: 8px; border: 1px solid #e2e8f0;"></div>'
    return raw_html + chart_html

# --- 4. CRÉATION DU TEMPLATE NAVY & GOLD ---
def creer_html_complet(contenu_html):
    return f"""
    <!DOCTYPE html><html lang="fr"><head><meta charset="UTF-8">
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; max-width: 800px; margin: auto; padding: 20px; color: #1f2937; background-color: #f3f4f6; }}
        .container {{ background-color: #ffffff; border-radius: 4px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); overflow: hidden; }}
        .header {{ background-color: #0B1F38; padding: 35px 20px; text-align: center; border-bottom: 5px solid #D4AF37; }}
        .logo-text {{ font-size: 32px; font-weight: 800; color: #D4AF37; letter-spacing: 3px; margin: 0; text-transform: uppercase; }}
        .date {{ font-size: 13px; font-weight: 600; color: #ffffff; text-transform: uppercase; margin-top: 8px; opacity: 0.8; }}
        .content {{ padding: 45px; }}
        h2 {{ font-size: 26px; color: #0B1F38; margin-bottom: 25px; font-weight: 800; text-align: center; }}
        .editorial {{ background-color: #f8fafc; padding: 20px 25px; border-left: 5px solid #0B1F38; margin-bottom: 50px; font-style: italic; color: #475569; text-align: justify; line-height: 1.6; }}
        .article {{ margin-bottom: 60px; border-bottom: 1px solid #e2e8f0; padding-bottom: 35px; }}
        .article-header {{ display: flex; align-items: baseline; gap: 15px; margin-bottom: 15px; }}
        .article-num {{ font-size: 45px; font-weight: 900; color: #D4AF37; line-height: 1; opacity: 0.9; }}
        .article-title {{ font-size: 24px; color: #0B1F38; margin: 0; font-weight: 700; line-height: 1.2; }}
        .article-text {{ color: #334155; line-height: 1.7; font-size: 15px; margin-bottom: 20px; text-align: justify; }}
        .article-highlight {{ background-color: #f8fafc; border-left: 5px solid #D4AF37; color: #0B1F38; padding: 15px 20px; font-weight: 500; margin: 25px 0; }}
        .article-highlight strong {{ color: #D4AF37; font-weight: 800; text-transform: uppercase; }}
        .source-link {{ display: inline-block; color: #0B1F38; font-weight: 700; text-decoration: none; font-size: 12px; border: 1px solid #D4AF37; padding: 8px 15px; border-radius: 2px; }}
        .implications {{ background-color: #0B1F38; color: white; padding: 30px; border-radius: 4px; margin-top: 30px; }}
        .implications h3 {{ color: #D4AF37; margin-top: 0; text-transform: uppercase; font-size: 18px; border-bottom: 1px solid #1a365d; padding-bottom: 10px; }}
        .implications p {{ text-align: justify; margin: 0; line-height: 1.6; }}
        .footer {{ background-color: #0B1F38; color: #D4AF37; text-align: center; padding: 25px 20px; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 2px; }}
    </style></head>
    <body><div class="container">
        <div class="header"><h1 class="logo-text">{NOM_ASSO}</h1><div class="date">Édition du {datetime.datetime.now().strftime('%d/%m/%Y')}</div></div>
        <div class="content">{contenu_html}</div>
        <div class="footer">© {datetime.datetime.now().year} {NOM_ASSO} · Diffusion restreinte</div>
    </div></body></html>
    """

# --- 5. INTERFACE ET GESTION SECRETS ---
st.title("🏛️ Intelligence Center - Le Cercle Infra")

# Si on est sur le cloud, on prend la clé dans les secrets, sinon on la demande
if "GEMINI_API_KEY" in st.secrets:
    user_api_key = st.secrets["GEMINI_API_KEY"]
else:
    user_api_key = st.text_input("Clé API Gemini :", type="password", value="AIzaSyBq8v1PYc6D-PqLyqIQ3tZiNSz_wRyyGMY")

if st.button("🚀 GÉNÉRER L'ÉDITION STRATÉGIQUE", use_container_width=True, type="primary"):
    with st.spinner("Analyse des flux internationaux et synthèse en cours..."):
        data = recuperer_articles(FLUX_RSS)
        if data:
            html_body = generer_newsletter(data, user_api_key)
            final_output = creer_html_complet(html_body)
            st.success("Veille internationale générée !")
            st.download_button("📥 TÉLÉCHARGER LE RAPPORT (HTML)", final_output, f"CercleInfra_Global_{datetime.date.today()}.html", "text/html")
            st.components.v1.html(final_output, height=1200, scrolling=True)
        else:
            st.error("Aucune actualité n'a pu être récupérée.")
