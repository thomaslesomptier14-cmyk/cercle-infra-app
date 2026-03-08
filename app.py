import streamlit as st
import feedparser
from google import genai
import datetime
import ssl
import urllib.parse

# Configuration
st.set_page_config(page_title="Le Cercle Infra - Global Monitor", page_icon="🌍", layout="wide")

# Déblocage SSL Mac
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

feedparser.USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# SOURCES INTERNATIONALES (Multi-langues)
FLUX_RSS = [
    "https://elpais.com/rss/economia/macroeconomia.xml", # Espagne - Macro/Infra
    "https://www.faz.net/rss/aktuell/wirtschaft/unternehmen/", # Allemagne - Entreprises/BTP
    "https://www.scmp.com/rss/318210/feed", # Asie - China Economy/Infra
    "https://www.enr.com/rss/articles", # USA - Engineering News-Record
    "https://www.smart-energy.com/feed/" # Global - Smart Energy
]

NOM_ASSO = "LE CERCLE INFRA"

def recuperer_articles(flux_list, max_articles=12):
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

def generer_newsletter(articles, api_key):
    client = genai.Client(api_key=api_key)
    
    ctx = ""
    for i, art in enumerate(articles):
        ctx += f"ID:{i} | TITRE:{art['titre']} | DESC:{art['description']}\n\n"

    # Prompt mis à jour pour le multi-langues et le style Cercle Infra [cite: 1, 5, 18, 26]
    prompt = f"""
    Tu es l'analyste senior du think-tank '{NOM_ASSO}'. 
    Tu vas recevoir des news d'infrastructure en plusieurs langues (Anglais, Espagnol, Allemand).
    
    MISSION :
    1. Sélectionne les 5 news les plus stratégiques au niveau MONDIAL.
    2. Traduis et synthétise-les en un FRANÇAIS expert, technique et fluide.
    3. Respecte le formatage 'Cercle Infra'[cite: 1, 21, 41]: titres en typographie française, texte JUSTIFIÉ, pas d'astérisques (**), utilise <strong>.
    
    CHIFFRE CLÉ :
    - Extraire IMPÉRATIVEMENT un nombre (Montant, %, GW, km). 
    - Le chiffre doit être le cœur de l'information[cite: 9, 12, 29].

    DATA VIZ (Graphique) :
    - Génère 3 catégories et 3 valeurs numériques cohérentes avec l'actualité.
    - Format : [CHART_DATA: Categorie1,Valeur1|Categorie2,Valeur2|Categorie3,Valeur3]

    STRUCTURE HTML :
    <h2>[Titre global - Typo française]</h2>
    <div class="editorial">[Édito justifié synthétisant la rupture de la semaine]</div>
    
    <div class="article">
        <div class="article-header"><span class="article-num">[N°]</span><h3 class="article-title">[Titre]</h3></div>
        <div class="article-text">[Analyse experte justifiée. Utilise <strong> pour les points clés et <ul><li> si besoin]</div>
        <div class="article-highlight"><strong>CHIFFRE CLÉ :</strong> [Valeur numérique] — [Contexte]</div>
        <a href="[LIEN]" class="source-link" target="_blank">CONSULTER LA SOURCE ↗</a>
    </div>
    """
    
    response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
    raw_html = response.text
    
    # Système de graphique sécurisé
    chart_url = "https://quickchart.io/chart?c={type:'bar',data:{labels:['Projets','Investissements','Innovation'],datasets:[{label:'Indicateurs Infra',data:[30,55,45],backgroundColor:'#0B1F38'}]}}"
    if "[CHART_DATA:" in raw_html:
        try:
            data_part = raw_html.split("[CHART_DATA:")[1].split("]")[0]
            items = [i.split(",") for i in data_part.split("|")]
            labels = [i[0].strip() for i in items]
            values = [i[1].strip() for i in items]
            chart_config = f"{{type:'bar',data:{{labels:{labels},datasets:[{{label:'Analyse Sectorielle',data:[{','.join(values)}],backgroundColor:'#0B1F38'}}]}}}}"
            chart_url = f"https://quickchart.io/chart?c={urllib.parse.quote(chart_config)}"
            raw_html = raw_html.split("[CHART_DATA:")[0]
        except: pass

    chart_html = f'<div style="text-align: center; margin: 40px 0;"><img src="{chart_url}" width="100%" style="max-width: 600px; border-radius: 8px;"></div>'
    return raw_html + chart_html

def creer_html_complet(contenu_html):
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
        .editorial {{ background-color: #f8fafc; padding: 20px 25px; border-left: 4px solid #0B1F38; margin-bottom: 50px; font-style: italic; color: #475569; text-align: justify; line-height: 1.6; }}
        .article {{ margin-bottom: 50px; border-bottom: 1px solid #e2e8f0; padding-bottom: 30px; }}
        .article-header {{ display: flex; align-items: baseline; gap: 15px; margin-bottom: 15px; }}
        .article-num {{ font-size: 40px; font-weight: 900; color: #D4AF37; line-height: 1; }}
        .article-title {{ font-size: 22px; color: #0B1F38; margin: 0; font-weight: 700; }}
        .article-text {{ color: #334155; line-height: 1.7; font-size: 15px; margin-bottom: 20px; text-align: justify; }}
        .article-text ul {{ padding-left: 20px; margin: 10px 0; }}
        .article-highlight {{ background-color: #f8fafc; border-left: 4px solid #D4AF37; color: #0B1F38; padding: 15px 20px; font-weight: 500; margin-bottom: 20px; }}
        .article-highlight strong {{ color: #D4AF37; font-weight: 800; }}
        .source-link {{ display: inline-block; color: #0B1F38; font-weight: 700; text-decoration: none; font-size: 12px; border-bottom: 1px solid #D4AF37; }}
        .implications {{ background-color: #0B1F38; color: white; padding: 30px; border-radius: 8px; }}
        .implications h3 {{ color: #D4AF37; margin-top: 0; text-transform: uppercase; font-size: 18px; }}
        .implications p {{ text-align: justify; margin: 0; line-height: 1.6; }}
        .footer {{ background-color: #0B1F38; color: #D4AF37; text-align: center; padding: 25px 20px; font-size: 11px; font-weight: 600; text-transform: uppercase; }}
    </style></head>
    <body><div class="container">
        <div class="header"><h1 class="logo-text">{NOM_ASSO}</h1><div class="date">Veille Internationale · {datetime.datetime.now().strftime('%d/%m/%Y')}</div></div>
        <div class="content">{contenu_html}</div>
        <div class="footer">© {datetime.datetime.now().year} {NOM_ASSO} · Diffusion restreinte</div>
    </div></body></html>
    """

st.title("🏛️ Cercle Infra : Global Intelligence")
st.info("Cette version scanne désormais des sources en Anglais, Espagnol et Allemand.")

user_api_key = st.text_input("Clé API Gemini :", type="password", value="AIzaSyBq8v1PYc6D-PqLyqIQ3tZiNSz_wRyyGMY")

if st.button("🚀 Générer la Veille Mondiale", use_container_width=True):
    with st.spinner("Analyse des flux internationaux..."):
        data = recuperer_articles(FLUX_RSS)
        if data:
            html_body = generer_newsletter(data, user_api_key)
            final_output = creer_html_complet(html_body)
            st.success("Veille générée avec succès !")
            st.download_button("📥 Télécharger (HTML)", final_output, f"CercleInfra_Global_{datetime.date.today()}.html", "text/html")
            st.components.v1.html(final_output, height=1000, scrolling=True)
