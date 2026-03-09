import streamlit as st
import feedparser
from google import genai
import datetime
import ssl
import urllib.parse

# Configuration Cloud
st.set_page_config(page_title="Le Cercle Infra - Global Monitor", page_icon="🌍", layout="wide")

# Utilisation de la clé secrète configurée dans Streamlit Cloud
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    API_KEY = st.text_input("Clé API Gemini :", type="password")

client = genai.Client(api_key=API_KEY)

# Bypass SSL pour l'hébergement
ssl._create_default_https_context = ssl._create_unverified_context
feedparser.USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

FLUX_RSS = [
    "https://www.enr.com/rss/articles", 
    "https://www.renewableenergyworld.com/feed/", 
    "https://www.masstransitmag.com/rss",
    "https://elpais.com/rss/economia/macroeconomia.xml",
    "https://news.google.com/rss/search?q=infrastructure+megaproject+energy+nuclear&hl=en-US&gl=US&ceid=US:en"
]

NOM_ASSO = "LE CERCLE INFRA"

def recuperer_articles(flux_list):
    articles = []
    for url in flux_list:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:8]:
                articles.append({"titre": entry.title, "description": entry.description, "lien": entry.link})
        except: pass
    return articles

def generer_newsletter(articles):
    ctx = ""
    for i, art in enumerate(articles):
        ctx += f"ID:{i} | TITRE:{art['titre']} | DESC:{art['description']}\n\n"

    prompt = f"""
    Tu es l'analyste senior du think-tank '{NOM_ASSO}'. 
    Rédige une veille stratégique en FRANÇAIS sur les 5 news les plus importantes.
    
    CONSIGNES :
    - Typographie française (Majuscule au début seulement).
    - Texte JUSTIFIÉ (HTML <div style='text-align: justify;'>).
    - CHIFFRE CLÉ : Obligatoire d'extraire une donnée chiffrée.
    - Pas d'astérisques, utilise <strong>.
    - Graphique DATA VIZ : Génère 3 catégories et 3 valeurs au format [CHART_DATA: Categorie1,Valeur1|Categorie2,Valeur2|Categorie3,Valeur3]
    
    STRUCTURE :
    <h2>[Titre]</h2>
    <div class="editorial">[Édito analytique]</div>
    [5 blocs Article avec titre, texte justifié, chiffre clé et lien <a href="..." target="_blank">]
    [CHART_DATA]
    <div class="implications"><h3>Perspectives stratégiques</h3><p>[Analyse]</p></div>
    """
    response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
    raw_html = response.text
    
    # Construction du graphique via QuickChart
    chart_url = "https://quickchart.io/chart?c={type:'bar',data:{labels:['A','B','C'],datasets:[{label:'Infra',data:[1,2,3],backgroundColor:'#0B1F38'}]}}"
    if "[CHART_DATA:" in raw_html:
        try:
            data_part = raw_html.split("[CHART_DATA:")[1].split("]")[0]
            items = [i.split(",") for i in data_part.split("|")]
            labels = [i[0].strip() for i in items]
            values = [i[1].strip() for i in items]
            chart_config = f"{{type:'bar',data:{{labels:{labels},datasets:[{{label:'Indicateurs Sectoriels',data:[{','.join(values)}],backgroundColor:'#0B1F38'}}]}}}}"
            chart_url = f"https://quickchart.io/chart?c={urllib.parse.quote(chart_config)}"
            raw_html = raw_html.split("[CHART_DATA:")[0]
        except: pass

    chart_html = f'<div style="text-align: center; margin: 40px 0;"><img src="{chart_url}" width="100%" style="max-width: 600px; border-radius: 8px;"></div>'
    return raw_html + chart_html

# Structure visuelle Navy & Gold (comme vos documents) [cite: 1, 21, 91]
def creer_html(contenu):
    return f"""
    <!DOCTYPE html><html><head><meta charset="UTF-8">
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; max-width: 800px; margin: auto; padding: 20px; color: #1f2937; background-color: #f3f4f6; }}
        .container {{ background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
        .header {{ background-color: #0B1F38; padding: 30px; text-align: center; border-bottom: 4px solid #D4AF37; }}
        .logo-text {{ font-size: 32px; font-weight: 800; color: #D4AF37; letter-spacing: 2px; text-transform: uppercase; margin: 0; }}
        .content {{ padding: 40px; text-align: justify; }}
        h2 {{ color: #0B1F38; text-align: center; font-weight: 800; }}
        .article {{ margin-bottom: 40px; border-bottom: 1px solid #eee; padding-bottom: 20px; }}
        .article-num {{ font-size: 36px; font-weight: 900; color: #D4AF37; }}
        .article-highlight {{ background-color: #f8fafc; border-left: 4px solid #D4AF37; padding: 15px; margin: 15px 0; }}
        .implications {{ background-color: #0B1F38; color: white; padding: 25px; border-radius: 8px; }}
        .footer {{ background-color: #0B1F38; color: #D4AF37; text-align: center; padding: 20px; font-size: 11px; text-transform: uppercase; }}
    </style></head>
    <body><div class="container">
        <div class="header"><h1 class="logo-text">{NOM_ASSO}</h1></div>
        <div class="content">{contenu}</div>
        <div class="footer">© {datetime.datetime.now().year} {NOM_ASSO} · Diffusion restreinte</div>
    </div></body></html>
    """

st.title("🏛️ Veille Stratégique - Le Cercle Infra")
if st.button("🚀 Générer l'édition de la semaine", use_container_width=True):
    with st.spinner("Analyse des flux internationaux et rédaction..."):
        data = recuperer_articles(FLUX_RSS)
        html_body = generer_newsletter(data)
        final_output = creer_html(html_body)
        st.download_button("📥 Télécharger le fichier prêt à l'envoi", final_output, f"Veille_CercleInfra_{datetime.date.today()}.html", "text/html")
        st.components.v1.html(final_output, height=1000, scrolling=True)
