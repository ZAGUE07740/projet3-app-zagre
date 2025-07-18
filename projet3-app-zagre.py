import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import base64
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import streamlit.components.v1 as components
import plotly.express as px

from datetime import datetime
import re
import os
import time

# Palette de couleurs
COLOR_PRIMARY = "#1976D2"
COLOR_BG = "#F4F7FA"
COLOR_ACCENT = "#FFB300"
COLOR_SUCCESS = "#43A047"
COLOR_ERROR = "#E53935"
COLOR_TEXT = "#222C36"
COLOR_TEXT_SECONDARY = "#5A7184"

# Configuration de la page
st.set_page_config(
    page_title="Analyse & Scraping CoinAfrique",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Titre principal avec style
st.markdown(f"""
    <h1 style='text-align: center; color: {COLOR_PRIMARY}; font-size: 3rem; margin-bottom: 0;'>
        📈 Analyse et Scraping CoinAfrique
    </h1>
    <p style='text-align: center; color: {COLOR_TEXT_SECONDARY}; font-size: 1.2rem; margin-bottom: 2rem;'>
        Collecte, nettoyage et visualisation de données des annonces CoinAfrique Sénégal
    </p>
""", unsafe_allow_html=True)

# Description de l'app
st.markdown(f"""
    <div style='background-color: {COLOR_BG}; padding: 1rem; border-radius: 10px; margin: 1rem 0;'>
        <p>
            Fonctionnalités :
            <ul>
                <li>🧹 Scraping nettoyé (BeautifulSoup)</li>
                <li>🕸️ Scraping brut (Web Scraper)</li>
                <li>💾 Téléchargement de CSV</li>
                <li>📈 Dashboard interactif</li>
                <li>🗨️ Formulaire d’évaluation</li>
            </ul>
            <br>Sources : <a href="https://sn.coinafrique.com/">Coinafrique Sénégal</a>
        </p>
    </div>
""", unsafe_allow_html=True)

# Fonction de scraping avec BeautifulSoup (avec nettoyage)
def scrape_with_beautifulsoup(url_base, category_name, pages, clean_data=True):
    """Scraper avec BeautifulSoup et nettoyage optionnel"""
    data = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    for page in range(1, pages + 1):
        status_text.text(f'Scraping page {page}/{pages} - {category_name}...')
        progress_bar.progress(page / pages)
        url = f"{url_base}?page={page

