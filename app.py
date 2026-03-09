import streamlit as st
import feedparser
from google import genai
import datetime
import ssl
import os

# --- 1. CONFIGURATION & STYLE ---
st.set_page_config(page_title="Le Cercle Infra - Dashboard", page_icon="🏛️", layout="wide")

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

# --- 3. FONCTIONS (La pièce manquante est ici !) ---
def recuperer_articles(flux_list):
    articles = []
    for url in flux_list:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:6]:
                articles.append({
                    "titre": entry.title, 
                    "description": entry.description if hasattr(entry, 'description') else ""
                })
        except: pass
    return articles

def generer_brouillon(articles, api_key):
    try:
        client = genai.Client(api_key=api_key)
        model_id = "gemini-1.5-flash"
        
        ctx = "\n".join([f"Titre: {a['titre']}" for a in articles])

        prompt = f"""
        Tu es l'analyste senior du '{NOM_ASSO}'. Rédige une veille stratégique mondiale en FRANÇAIS.
        
        SECTION 1 : BAROMÈTRE STRATÉGIQUE
        Crée un tableau HTML simple (<table class="barometre">) avec 4 indices : 
        1. Prix CO2 (EUA) | 2. Électricité Spot (Europe) | 3. Brent ($) | 4. Indice Acier/Construction.
        
        SECTION 2 : LES 5 NEWS CRITIQUES
        - Sélectionne 5 news (Diversité : Asie, Afrique, Europe, Amériques).
        - Rigueur : Rappelle des ordres de grandeur comme 23 Mds€ pour le rail européen ou 25% de fuites d'eau.
        - Format : Titre typo française, Analyse experte justifiée, CHIFFRE CLÉ obligatoire.
        - Utilise <strong> pour le gras. PAS d'astérisques.
        
        SECTION 3 : PERSPECTIVES STRATÉGIQUES
        Analyse de synthèse sur la souveraineté et la transition.
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
        .header {{ background-color: #0B1F38; padding: 30px 20px; text-align: center; border-bottom: 4px solid #D4AF37; }}
        .logo-text {{ font-size: 32px; font-weight: 800; color: #D4AF37; letter-spacing: 3px; margin: 0; text-transform: uppercase; }}
        .date {{ font-size: 13px; font-weight: 600; color: #ffffff; text-transform: uppercase; margin-top: 8px; opacity: 0.8; }}
        .content {{ padding: 40px; }}
        h2 {{ font-size: 26px; color: #0B1F38; margin-bottom: 25px; font-weight: 800; text-align: center; }}
        .barometre {{ width: 100%; border-collapse: collapse; margin-bottom: 40px; background: #f8fafc; border: 1px solid #e2e8f0; }}
        .barometre td {{ padding: 12px; border: 1px solid #e2e8f0; text-align: center; color: #0B1F38; font-weight: 600; font-size: 13px; }}
        .article {{ margin-bottom: 50px; border-bottom: 1px solid #e2e8f0; padding-bottom: 30px; }}
        .article-header {{ display: flex; align-items: baseline; gap: 15px; margin-bottom: 15px; }}
        .article-num {{ font-size: 40px; font-weight: 900; color: #D4AF37; line-height: 1; }}
        .article-title {{ font-size: 22px; color: #0B1F38; margin: 0;
