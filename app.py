import streamlit as st
import feedparser
from google import genai
import datetime
import ssl
import os

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Le Cercle Infra - Intelligence Suite", page_icon="🏛️", layout="wide")

if not os.path.exists("archives"):
    os.makedirs("archives")

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError: pass
else: ssl._create_default_https_context = _create_unverified_https_context

feedparser.USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

NOM_ASSO = "LE CERCLE INFRA"

# --- 2. SOURCES MONDIALES ---
FLUX_RSS = [
    "https://asia.nikkei.com/rss/feed/nar", 
    "https://african.business/category/sectors/infrastructure/feed/",
    "https://www.construction-europe.com/rss/articles",
    "https://www.railwaygazette.com/139.rss",
    "https://news.google.com/rss/search?q=infrastructure+energy+nuclear+projects&hl=fr&gl=FR&ceid=FR:fr"
]

# --- 3. MOTEUR DE GÉNÉRATION ---
def generer_brouillon(articles, api_key):
    try:
        client = genai.Client(api_key=api_key)
        # UTILISATION DU MEILLEUR MOTEUR DISPONIBLE
        model_id = "gemini-3-flash" 
        
        prompt = f"""
        Tu es l'analyste senior du '{NOM_ASSO}'. Rédige une veille stratégique mondiale en FRANÇAIS.
        
        SECTION 1 : BAROMÈTRE (Table HTML)
        Indices : Prix CO2 (EUA), Elec Spot Europe, Brent ($), Indice Acier.
        
        SECTION 2 : 5 NEWS CRITIQUES (DIVERSIFIÉES)
        - Focus : Énergie, Transport, Digital, Hydrique[cite: 10, 16, 26, 32].
        - Rigueur : Inclus des chiffres précis (ex: 5% conso IA d'ici 2030, 23 Mds€ MIE, 25% pertes eau)[cite: 14, 24, 30].
        
        SECTION 3 : PERSPECTIVES
        Analyse de souveraineté et résilience[cite: 54].
        
        Format : HTML, texte JUSTIFIÉ, titres typo française, <strong> pour le gras.
        """
        
        response = client.models.generate_content(model=model_id, contents=prompt)
        return response.text
    except Exception as e:
        return f"ERREUR_API: {str(e)}"

# --- 4. DESIGN ---
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
        .barometre {{ width: 100%; border-collapse: collapse; margin-bottom: 40px; background: #f8fafc; }}
        .barometre td {{ padding: 12px; border: 1px solid #e2e8f0; text-align: center; color: #0B1F38; font-weight: 600; }}
        .article {{ margin-bottom: 50px; border-bottom: 1px solid #eee; padding-bottom: 30px; }}
        .article-num {{ font-size: 40px; font-weight: 900; color: #D4AF37; line-height: 1; }}
        .article-title {{ font-size: 22px; color: #0B1F38; font-weight: 700; margin: 0; }}
        .article-text {{ color: #334155; line-height: 1.7; text-align: justify; }}
        .article-highlight {{ background-color: #f8fafc; border-left: 5px solid #D4AF37; color: #0B1F38; padding: 15px; }}
        .implications {{ background-color: #0B1F38; color: white; padding: 30px; border-radius: 4px; }}
        .footer {{ background-color: #0B1F38; color: #D4AF37; text-align: center; padding: 20px; font-size: 11px; }}
    </style></head>
    <body><div class="container">
        <div class="header"><h1 class="logo-text">{NOM_ASSO}</h1><div style="color:white; font-size:12px; margin-top:5px;">Veille Stratégique • {date_str}</div></div>
        <div class="content">{corps_html}</div>
        <div class="footer">© {datetime.datetime.now().year} {NOM_ASSO} • DIFFUSION RESTREINTE</div>
    </div></body></html>
    """

# --- 5. INTERFACE ---
st.title("🏛️ Intelligence Center - Le Cercle Infra")

if "GEMINI_API_KEY" in st.secrets:
    user_key = st.secrets["GEMINI_API_KEY"]
else:
    user_key = st.sidebar.text_input("Clé API Gemini :", type="password")

if "draft" not in st.session_state:
    st.session_state.draft = ""

if st.button("🚀 Lancer le Scan (Moteur Gemini 3 Flash)", use_container_width=True):
    with st.spinner("Analyse avec le moteur de dernière génération..."):
        feed_data = []
        for url in FLUX_RSS:
            try:
                f = feedparser.parse(url)
                feed_data.extend([{"titre": e.title, "description": e.description} for e in f.entries[:5]])
            except: pass
        res = generer_brouillon(feed_data, user_key)
        if "ERREUR_API" in res: st.error("Quota atteint. Attendez 60s ou passez sur le moteur Lite.")
        else: st.session_state.draft = res

if st.session_state.draft:
    st.session_state.draft = st.text_area("Édition Collaborative :", value=st.session_state.draft, height=500)
    if st.button("✅ Valider l'édition", use_container_width=True, type="primary"):
        final_html = finaliser_html(st.session_state.draft)
        filename = f"Veille_CercleInfra_{datetime.date.today()}.html"
        with open(f"archives/{filename}", "w") as f: f.write(final_html)
        st.download_button("📥 Télécharger le Rapport", final_html, filename, "text/html")
        st.components.v1.html(final_html, height=1000, scrolling=True)
