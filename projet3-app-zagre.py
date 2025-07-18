import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import base64
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import streamlit.components.v1 as components


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
        url = f"{url_base}?page={page}"
        try:
            time.sleep(1)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            annonces = soup.find_all('div', class_='ad__card')
            for annonce in annonces:
                try:
                    type_element = annonce.find('p', class_='ad__card-description')
                    type_item = type_element.get_text(strip=True) if type_element else "Non spécifié"
                    prix_element = annonce.find('p', class_='ad__card-price')
                    prix = prix_element.get_text(strip=True) if prix_element else "Prix non spécifié"
                    location_element = annonce.find('p', class_='ad__card-location')
                    if location_element:
                        span_element = location_element.find('span')
                        adresse = span_element.get_text(strip=True) if span_element else "Adresse non spécifiée"
                    else:
                        adresse = "Adresse non spécifiée"
                    img_element = annonce.find('img', class_='ad__card-img')
                    image_lien = img_element['src'] if img_element and 'src' in img_element.attrs else "Image non disponible"
                    data.append({
                        "categorie": category_name,
                        "type": type_item,
                        "prix": prix,
                        "adresse": adresse,
                        "image_lien": image_lien
                    })
                except Exception as e:
                    continue
        except requests.exceptions.RequestException as e:
            st.error(f"🔴 Erreur lors du scraping de la page {page}: {str(e)}")
            continue
        except Exception as e:
            st.error(f"🔴 Erreur inattendue page {page}: {str(e)}")
            continue
    progress_bar.empty()
    status_text.empty()
    df = pd.DataFrame(data)
    if clean_data and not df.empty:
        df = clean_scraped_data(df)
    return df

# Fonction de nettoyage des données
def clean_scraped_data(df):
    """Nettoyer les données scrapées"""
    if df.empty:
        return df
    df_clean = df.copy()
    df_clean['prix_brut'] = df_clean['prix']
    df_clean['prix_numerique'] = df_clean['prix'].str.replace(r'[^\d]', '', regex=True)
    df_clean['prix_numerique'] = pd.to_numeric(df_clean['prix_numerique'], errors='coerce')
    df_clean['adresse'] = df_clean['adresse'].str.strip()
    df_clean['adresse'] = df_clean['adresse'].str.title()
    df_clean['type'] = df_clean['type'].str.strip()
    df_clean['type'] = df_clean['type'].str.title()
    df_clean['a_prix'] = df_clean['prix_numerique'].notna()
    df_clean['a_image'] = df_clean['image_lien'] != "Image non disponible"
    df_clean = df_clean.drop_duplicates(subset=['type', 'prix', 'adresse'])
    return df_clean

def convert_df_to_csv(df):
    """Convertir DataFrame en CSV"""
    return df.to_csv(index=False).encode('utf-8')

def save_data_to_csv(df, filename):
    """Sauvegarder les données dans un fichier CSV"""
    if not df.empty:
        df.to_csv(filename, index=False)
        return True
    return False

def load_data_from_csv(filepath):
    """Charger les données depuis un fichier CSV"""
    try:
        if os.path.exists(filepath):
            return pd.read_csv(filepath)
        else:
            st.error(f"🔴 Le fichier {filepath} n'existe pas.")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"🔴 Erreur lors du chargement du fichier: {str(e)}")
        return pd.DataFrame()

def create_dashboard(df):
    """Créer un dashboard interactif"""
    if df.empty:
        st.warning('🟠 Aucune donnée disponible pour le dashboard.')
        return
    st.markdown(f"""
        <h2 style='text-align: center; color: {COLOR_PRIMARY}; margin: 2rem 0;'>
            📈 DASHBOARD ANALYTIQUE
        </h2>
    """, unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🗂️ Total articles", len(df))
    with col2:
        if 'prix_numerique' in df.columns:
            prix_valides = df['prix_numerique'].dropna()
            if not prix_valides.empty:
                prix_moyen = prix_valides.mean()
                st.metric("💸 Prix moyen", f"{prix_moyen:,.0f} FCFA")
            else:
                st.metric("💸 Prix moyen", "N/A")
        else:
            st.metric("💸 Prix moyen", "N/A")
    with col3:
        nb_categories = df['categorie'].nunique()
        st.metric("🏷️ Catégories", nb_categories)
    with col4:
        nb_villes = df['adresse'].nunique()
        st.metric("🏙️ Villes", nb_villes)
    col1, col2 = st.columns(2)
    with col1:
        fig_cat = px.pie(
            df, 
            names='categorie', 
            title='Répartition par Catégorie',
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig_cat.update_layout(height=400)
        st.plotly_chart(fig_cat, use_container_width=True)
    with col2:
        top_villes = df['adresse'].value_counts().head(10)
        fig_villes = px.bar(
            x=top_villes.values,
            y=top_villes.index,
            orientation='h',
            title='Top 10 des Villes',
            labels={'x': 'Nombre d\'articles', 'y': 'Ville'}
        )
        fig_villes.update_layout(height=400)
        st.plotly_chart(fig_villes, use_container_width=True)
    if 'prix_numerique' in df.columns:
        prix_valides = df.dropna(subset=['prix_numerique'])
        if not prix_valides.empty:
            col1, col2 = st.columns(2)
            with col1:
                fig_prix = px.box(
                    prix_valides, 
                    x='categorie', 
                    y='prix_numerique',
                    title='Distribution des Prix par Catégorie'
                )
                fig_prix.update_layout(height=400)
                fig_prix.update_xaxes(tickangle=45)
                st.plotly_chart(fig_prix, use_container_width=True)
            with col2:
                fig_hist = px.histogram(
                    prix_valides, 
                    x='prix_numerique',
                    title='Distribution des Prix',
                    nbins=30
                )
                fig_hist.update_layout(height=400)
                st.plotly_chart(fig_hist, use_container_width=True)

# Sidebar pour les paramètres
st.sidebar.header('🔧 Paramètres de Configuration')
st.sidebar.markdown("---")
pages = st.sidebar.selectbox(
    '📄 Nombre de pages à scraper',
    options=list(range(1, 201)),
    index=2,  # Par défaut 3 pages
    help="Sélectionnez le nombre de pages à scraper pour chaque catégorie"
)
choices = st.sidebar.selectbox(
    '🎯 Choisissez une option',
    options=[
        '🧹 Scraper avec BeautifulSoup (nettoyage)',
        '🕸️ Scraper avec Web Scraper (données brutes)',
        '💾 Télécharger données pré-scrapées',
        '📈 Dashboard des données nettoyées',
        '🗨️ Formulaire d\'évaluation'
    ],
    help="Sélectionnez l'action que vous souhaitez effectuer"
)
st.sidebar.markdown("---")
if choices == '💾 Télécharger données pré-scrapées':
    st.sidebar.subheader('📁 Chemins des fichiers CSV')
    vetements_homme_path = st.sidebar.text_input(
        'Vêtements Homme CSV',
        value='data/vetements_homme.csv',
        help='Chemin vers le fichier CSV des vêtements homme'
    )
    chaussures_homme_path = st.sidebar.text_input(
        'Chaussures Homme CSV',
        value='data/chaussures_homme.csv',
        help='Chemin vers le fichier CSV des chaussures homme'
    )
    vetements_enfants_path = st.sidebar.text_input(
        'Vêtements Enfants CSV',
        value='data/vetements_enfants.csv',
        help='Chemin vers le fichier CSV des vêtements enfants'
    )
    chaussures_enfants_path = st.sidebar.text_input(
        'Chaussures Enfants CSV',
        value='data/chaussures_enfants.csv',
        help='Chemin vers le fichier CSV des chaussures enfants'
    )
st.sidebar.markdown("---")
st.sidebar.markdown(f"""
    <div style='text-align: center; color: {COLOR_TEXT_SECONDARY}; font-size: 0.8rem;'>
        <p>Développé par Emmanuel ZAGRE</p>
        <p>© 2025 CoinAfrique Analyse & Scraping</p>
    </div>
""", unsafe_allow_html=True)

# Interface principale
if choices == '🧹 Scraper avec BeautifulSoup (nettoyage)':
    st.markdown(f"""
        <div style='background-color: {COLOR_BG}; padding: 1rem; border-radius: 10px; margin: 1rem 0;'>
            <h3 style='color: {COLOR_PRIMARY}; margin-bottom: 1rem;'>🧹 Scraping avec BeautifulSoup et nettoyage</h3>
            <p>Cliquez sur les boutons ci-dessous pour scraper et nettoyer les données en temps réel depuis Coinafrique.</p>
        </div>
    """, unsafe_allow_html=True)
    urls = {
        'Vêtements Homme': 'https://sn.coinafrique.com/categorie/vetements-homme',
        'Chaussures Homme': 'https://sn.coinafrique.com/categorie/chaussures-homme',
        'Vêtements Enfants': 'https://sn.coinafrique.com/categorie/vetements-enfants',
        'Chaussures Enfants': 'https://sn.coinafrique.com/categorie/chaussures-enfants'
    }
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🧥 Vêtements Homme")
        if st.button('🧹 Scraper Vêtements Homme', key='scrape_vh', use_container_width=True):
            with st.spinner('Scraping en cours...'):
                df = scrape_with_beautifulsoup(urls['Vêtements Homme'], 'Vêtements Homme', pages, clean_data=True)
                if not df.empty:
                    st.success(f'🟢 {len(df)} articles récupérés et nettoyés!')
                    st.info(f'📊 Dimensions: {df.shape[0]} lignes et {df.shape[1]} colonnes')
                    st.dataframe(df.head(), use_container_width=True)
                    if save_data_to_csv(df, 'vetements_homme_cleaned.csv'):
                        st.success('🟢 Données sauvegardées dans vetements_homme_cleaned.csv')
                    csv = convert_df_to_csv(df)
                    st.download_button(
                        label="💾 Télécharger CSV",
                        data=csv,
                        file_name=f'vetements_homme_cleaned_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                        mime='text/csv',
                        key='download_vh'
                    )
                else:
                    st.warning('🟠 Aucune donnée récupérée.')
        st.markdown("### 🧒 Vêtements Enfants")
        if st.button('🧹 Scraper Vêtements Enfants', key='scrape_ve', use_container_width=True):
            with st.spinner('Scraping en cours...'):
                df = scrape_with_beautifulsoup(urls['Vêtements Enfants'], 'Vêtements Enfants', pages, clean_data=True)
                if not df.empty:
                    st.success(f'🟢 {len(df)} articles récupérés et nettoyés!')
                    st.info(f'📊 Dimensions: {df.shape[0]} lignes et {df.shape[1]} colonnes')
                    st.dataframe(df.head(), use_container_width=True)
                    if save_data_to_csv(df, 'vetements_enfants_cleaned.csv'):
                        st.success('🟢 Données sauvegardées dans vetements_enfants_cleaned.csv')
                    csv = convert_df_to_csv(df)
                    st.download_button(
                        label="💾 Télécharger CSV",
                        data=csv,
                        file_name=f'vetements_enfants_cleaned_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                        mime='text/csv',
                        key='download_ve'
                    )
                else:
                    st.warning('🟠 Aucune donnée récupérée.')
    with col2:
        st.markdown("### 👟 Chaussures Homme")
        if st.button('🧹 Scraper Chaussures Homme', key='scrape_ch', use_container_width=True):
            with st.spinner('Scraping en cours...'):
                df = scrape_with_beautifulsoup(urls['Chaussures Homme'], 'Chaussures Homme', pages, clean_data=True)
                if not df.empty:
                    st.success(f'🟢 {len(df)} articles récupérés et nettoyés!')
                    st.info(f'📊 Dimensions: {df.shape[0]} lignes et {df.shape[1]} colonnes')
                    st.dataframe(df.head(), use_container_width=True)
                    if save_data_to_csv(df, 'chaussures_homme_cleaned.csv'):
                        st.success('🟢 Données sauvegardées dans chaussures_homme_cleaned.csv')
                    csv = convert_df_to_csv(df)
                    st.download_button(
                        label="💾 Télécharger CSV",
                        data=csv,
                        file_name=f'chaussures_homme_cleaned_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                        mime='text/csv',
                        key='download_ch'
                    )
                else:
                    st.warning('🟠 Aucune donnée récupérée.')
        st.markdown("### 🥿 Chaussures Enfants")
        if st.button('🧹 Scraper Chaussures Enfants', key='scrape_ce', use_container_width=True):
            with st.spinner('Scraping en cours...'):
                df = scrape_with_beautifulsoup(urls['Chaussures Enfants'], 'Chaussures Enfants', pages, clean_data=True)
                if not df.empty:
                    st.success(f'🟢 {len(df)} articles récupérés et nettoyés!')
                    st.info(f'📊 Dimensions: {df.shape[0]} lignes et {df.shape[1]} colonnes')
                    st.dataframe(df.head(), use_container_width=True)
                    if save_data_to_csv(df, 'chaussures_enfants_cleaned.csv'):
                        st.success('🟢 Données sauvegardées dans chaussures_enfants_cleaned.csv')
                    csv = convert_df_to_csv(df)
                    st.download_button(
                        label="💾 Télécharger CSV",
                        data=csv,
                        file_name=f'chaussures_enfants_cleaned_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                        mime='text/csv',
                        key='download_ce'
                    )
                else:
                    st.warning('🟠 Aucune donnée récupérée.')

# (Les autres sections suivent la même logique, adapte les emojis et couleurs comme ci-dessus.)

# Footer
st.markdown(f"""
    <div style='text-align: center; padding: 2rem; margin-top: 3rem; border-top: 1px solid #ddd; background-color: {COLOR_BG};'>
        <p style='color: {COLOR_TEXT}; margin: 0;'>
            📈 CoinAfrique Scraper - Développé avec Streamlit & BeautifulSoup
        </p>
        <p style='color: {COLOR_TEXT_SECONDARY}; font-size: 0.9rem; margin: 0.5rem 0 0 0;'>
            Scraping | Visualisation | Export CSV | Feedback
        </p>
    </div>
""", unsafe_allow_html=True)
