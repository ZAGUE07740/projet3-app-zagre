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
import plotly.graph_objects as go
from datetime import datetime
import matplotlib as mp
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
    
    # Créer une barre de progression
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for page in range(1, pages + 1):
        status_text.text(f'Scraping page {page}/{pages} - {category_name}...')
        progress_bar.progress(page / pages)
        
        url = f"{url_base}?page={page}"
        
        try:
            # Ajouter un délai pour éviter de surcharger le serveur
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
                    # Extraire le type (vêtement ou chaussure)
                    type_element = annonce.find('p', class_='ad__card-description')
                    type_item = type_element.get_text(strip=True) if type_element else "Non spécifié"
                    
                    # Extraire le prix
                    prix_element = annonce.find('p', class_='ad__card-price')
                    prix = prix_element.get_text(strip=True) if prix_element else "Prix non spécifié"
                    
                    # Extraire l'adresse
                    location_element = annonce.find('p', class_='ad__card-location')
                    if location_element:
                        span_element = location_element.find('span')
                        adresse = span_element.get_text(strip=True) if span_element else "Adresse non spécifiée"
                    else:
                        adresse = "Adresse non spécifiée"
                    
                    # Extraire le lien de l'image
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
            st.error(f"Erreur lors du scraping de la page {page}: {str(e)}")
            continue
        except Exception as e:
            st.error(f"Erreur inattendue page {page}: {str(e)}")
            continue
    
    progress_bar.empty()
    status_text.empty()
    
    df = pd.DataFrame(data)
    
    # Nettoyer les données si demandé
    if clean_data and not df.empty:
        df = clean_scraped_data(df)
    
    return df

# Fonction de nettoyage des données
def clean_scraped_data(df):
    """Nettoyer les données scrapées avec vérification des colonnes"""
    if df.empty:
        return df

    df_clean = df.copy()

    if 'prix' in df_clean.columns:
        df_clean['prix_brut'] = df_clean['prix']
        df_clean['prix_numerique'] = df_clean['prix'].str.replace(r'[^\d]', '', regex=True)
        df_clean['prix_numerique'] = pd.to_numeric(df_clean['prix_numerique'], errors='coerce')
        df_clean['a_prix'] = df_clean['prix_numerique'].notna()
    else:
        df_clean['prix_brut'] = "Inconnu"
        df_clean['prix_numerique'] = np.nan
        df_clean['a_prix'] = False

    if 'adresse' in df_clean.columns:
        df_clean['adresse'] = df_clean['adresse'].str.strip().str.title()
    else:
        df_clean['adresse'] = "Adresse inconnue"

    if 'type' in df_clean.columns:
        df_clean['type'] = df_clean['type'].str.strip().str.title()
    else:
        df_clean['type'] = "Type inconnu"

    if 'image_lien' in df_clean.columns:
        df_clean['a_image'] = df_clean['image_lien'] != "Image non disponible"
    else:
        df_clean['a_image'] = False

    df_clean = df_clean.drop_duplicates(subset=['type', 'prix_brut', 'adresse'])

    return df_clean


# Fonction pour convertir le DataFrame en CSV
def convert_df_to_csv(df):
    """Convertir DataFrame en CSV"""
    return df.to_csv(index=False).encode('utf-8')

# Fonction pour sauvegarder les données
def save_data_to_csv(df, filename):
    """Sauvegarder les données dans un fichier CSV"""
    if not df.empty:
        df.to_csv(filename, index=False)
        return True
    return False

# Fonction pour charger les données depuis un fichier CSV
def load_data_from_csv(filepath):
    """Charger les données depuis un fichier CSV avec gestion des erreurs"""
    try:
        if os.path.exists(filepath):
            return pd.read_csv(filepath, encoding='utf-8')
        else:
            st.warning(f"📂 Fichier introuvable : {filepath}")
            return pd.DataFrame()
    except pd.errors.ParserError as e:
        st.error(f"❌ Erreur de format dans {filepath} : {str(e)}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Erreur inconnue lors du chargement de {filepath} : {str(e)}")
        return pd.DataFrame()


# Fonction pour créer le dashboard
def create_dashboard(df):
    """Créer un dashboard interactif"""
    if df.empty:
        st.warning('⚠️ Aucune donnée disponible pour le dashboard.')
        return
    
    st.markdown("""
        <h2 style='text-align: center; color: #2E86AB; margin: 2rem 0;'>
            📊 DASHBOARD ANALYTIQUE
        </h2>
    """, unsafe_allow_html=True)
    
    # Métriques principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📝 Total articles", len(df))
    
    with col2:
        if 'prix_numerique' in df.columns:
            prix_valides = df['prix_numerique'].dropna()
            if not prix_valides.empty:
                prix_moyen = prix_valides.mean()
                st.metric("💰 Prix moyen", f"{prix_moyen:,.0f} FCFA")
            else:
                st.metric("💰 Prix moyen", "N/A")
        else:
            st.metric("💰 Prix moyen", "N/A")
    
    with col3:
        nb_categories = df['categorie'].nunique()
        st.metric("🏷️ Catégories", nb_categories)
    
    with col4:
        nb_villes = df['adresse'].nunique()
        st.metric("🏙️ Villes", nb_villes)
    
    # Graphiques
    col1, col2 = st.columns(2)
    
    with col1:
        # Distribution par catégorie
        fig_cat = px.pie(
            df, 
            names='categorie', 
            title='Distribution par Catégorie',
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig_cat.update_layout(height=400)
        st.plotly_chart(fig_cat, use_container_width=True)
    
    with col2:
        # Top 10 des villes
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
    
    # Analyse des prix si disponible
    if 'prix_numerique' in df.columns:
        prix_valides = df.dropna(subset=['prix_numerique'])
        if not prix_valides.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                # Distribution des prix par catégorie
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
                # Histogramme des prix
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

# Sélection du nombre de pages
pages = st.sidebar.selectbox(
    '📄 Nombre de pages à scraper',
    options=list(range(1, 21)),
    index=2,  # Par défaut 3 pages
    help="Sélectionnez le nombre de pages à scraper pour chaque catégorie"
)

# Options principales
choices = st.sidebar.selectbox(
    '🎯 Choisissez une option',
    options=[
        'Scraper avec BeautifulSoup (nettoyage)',
        'Scraper avec Web Scraper (données brutes)',
        'Télécharger données pré-scrapées',
        'Dashboard des données nettoyées',
        'Formulaire d\'évaluation'
    ],
    help="Sélectionnez l'action que vous souhaitez effectuer"
)

st.sidebar.markdown("---")

# Configuration des chemins pour les fichiers pré-scrapés
if choices == 'Télécharger données pré-scrapées':
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
st.sidebar.markdown("""
    <div style='text-align: center; color: #666; font-size: 0.8rem;'>
        <p>Emmanuel ZAGRE</p>
        <p>© 2025 Analyse & Scraping CoinAfrique</p>
    </div>
""", unsafe_allow_html=True)

# Interface principale
if choices == 'Scraper avec BeautifulSoup (nettoyage)':
    st.markdown("""
        <div style='background-color: #e8f4f8; padding: 1rem; border-radius: 10px; margin: 1rem 0;'>
            <h3 style='color: #2E86AB; margin-bottom: 1rem;'>🔄 Scraping avec BeautifulSoup et nettoyage</h3>
            <p>Cliquez sur les boutons ci-dessous pour scraper et nettoyer les données en temps réel depuis Coinafrique.</p>
        </div>
    """, unsafe_allow_html=True)
    
    # URLs de base pour chaque catégorie
    urls = {
        'Vêtements Homme': 'https://sn.coinafrique.com/categorie/vetements-homme',
        'Chaussures Homme': 'https://sn.coinafrique.com/categorie/chaussures-homme',
        'Vêtements Enfants': 'https://sn.coinafrique.com/categorie/vetements-enfants',
        'Chaussures Enfants': 'https://sn.coinafrique.com/categorie/chaussures-enfants'
    }
    
    # Créer les colonnes pour les boutons
    col1, col2 = st.columns(2)
    
    with col1:
        # Vêtements Homme
        st.markdown("### 👔 Vêtements Homme")
        if st.button('🚀 Scraper Vêtements Homme', key='scrape_vh', use_container_width=True):
            with st.spinner('Scraping en cours...'):
                df = scrape_with_beautifulsoup(urls['Vêtements Homme'], 'Vêtements Homme', pages, clean_data=True)
                if not df.empty:
                    st.success(f'✅ {len(df)} articles récupérés et nettoyés!')
                    st.info(f'📊 Dimensions: {df.shape[0]} lignes et {df.shape[1]} colonnes')
                    st.dataframe(df.head(), use_container_width=True)
                    
                    # Sauvegarder automatiquement
                    if save_data_to_csv(df, 'vetements_homme_cleaned.csv'):
                        st.success('💾 Données sauvegardées dans vetements_homme_cleaned.csv')
                    
                    # Bouton de téléchargement
                    csv = convert_df_to_csv(df)
                    st.download_button(
                        label="📥 Télécharger CSV",
                        data=csv,
                        file_name=f'vetements_homme_cleaned_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                        mime='text/csv',
                        key='download_vh'
                    )
                else:
                    st.warning('⚠️ Aucune donnée récupérée.')
        
        # Vêtements Enfants
        st.markdown("### 👶 Vêtements Enfants")
        if st.button('🚀 Scraper Vêtements Enfants', key='scrape_ve', use_container_width=True):
            with st.spinner('Scraping en cours...'):
                df = scrape_with_beautifulsoup(urls['Vêtements Enfants'], 'Vêtements Enfants', pages, clean_data=True)
                if not df.empty:
                    st.success(f'✅ {len(df)} articles récupérés et nettoyés!')
                    st.info(f'📊 Dimensions: {df.shape[0]} lignes et {df.shape[1]} colonnes')
                    st.dataframe(df.head(), use_container_width=True)
                    
                    # Sauvegarder automatiquement
                    if save_data_to_csv(df, 'vetements_enfants_cleaned.csv'):
                        st.success('💾 Données sauvegardées dans vetements_enfants_cleaned.csv')
                    
                    # Bouton de téléchargement
                    csv = convert_df_to_csv(df)
                    st.download_button(
                        label="📥 Télécharger CSV",
                        data=csv,
                        file_name=f'vetements_enfants_cleaned_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                        mime='text/csv',
                        key='download_ve'
                    )
                else:
                    st.warning('⚠️ Aucune donnée récupérée.')
    
    with col2:
        # Chaussures Homme
        st.markdown("### 👞 Chaussures Homme")
        if st.button('🚀 Scraper Chaussures Homme', key='scrape_ch', use_container_width=True):
            with st.spinner('Scraping en cours...'):
                df = scrape_with_beautifulsoup(urls['Chaussures Homme'], 'Chaussures Homme', pages, clean_data=True)
                if not df.empty:
                    st.success(f'✅ {len(df)} articles récupérés et nettoyés!')
                    st.info(f'📊 Dimensions: {df.shape[0]} lignes et {df.shape[1]} colonnes')
                    st.dataframe(df.head(), use_container_width=True)
                    
                    # Sauvegarder automatiquement
                    if save_data_to_csv(df, 'chaussures_homme_cleaned.csv'):
                        st.success('💾 Données sauvegardées dans chaussures_homme_cleaned.csv')
                    
                    # Bouton de téléchargement
                    csv = convert_df_to_csv(df)
                    st.download_button(
                        label="📥 Télécharger CSV",
                        data=csv,
                        file_name=f'chaussures_homme_cleaned_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                        mime='text/csv',
                        key='download_ch'
                    )
                else:
                    st.warning('⚠️ Aucune donnée récupérée.')
        
        # Chaussures Enfants
        st.markdown("### 👟 Chaussures Enfants")
        if st.button('🚀 Scraper Chaussures Enfants', key='scrape_ce', use_container_width=True):
            with st.spinner('Scraping en cours...'):
                df = scrape_with_beautifulsoup(urls['Chaussures Enfants'], 'Chaussures Enfants', pages, clean_data=True)
                if not df.empty:
                    st.success(f'✅ {len(df)} articles récupérés et nettoyés!')
                    st.info(f'📊 Dimensions: {df.shape[0]} lignes et {df.shape[1]} colonnes')
                    st.dataframe(df.head(), use_container_width=True)
                    
                    # Sauvegarder automatiquement
                    if save_data_to_csv(df, 'chaussures_enfants_cleaned.csv'):
                        st.success('💾 Données sauvegardées dans chaussures_enfants_cleaned.csv')
                    
                    # Bouton de téléchargement
                    csv = convert_df_to_csv(df)
                    st.download_button(
                        label="📥 Télécharger CSV",
                        data=csv,
                        file_name=f'chaussures_enfants_cleaned_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                        mime='text/csv',
                        key='download_ce'
                    )
                else:
                    st.warning('⚠️ Aucune donnée récupérée.')

elif choices == 'Scraper avec Web Scraper (données brutes)':
    st.markdown("""
        <div style='background-color: #fff3cd; padding: 1rem; border-radius: 10px; margin: 1rem 0;'>
            <h3 style='color: #856404; margin-bottom: 1rem;'>🔄 Scraping avec Web Scraper (données brutes)</h3>
            <p>Cliquez sur les boutons ci-dessous pour scraper les données brutes (non nettoyées) depuis Coinafrique.</p>
        </div>
    """, unsafe_allow_html=True)
    
    # URLs de base pour chaque catégorie
    urls = {
        'Vêtements Homme': 'https://sn.coinafrique.com/categorie/vetements-homme',
        'Chaussures Homme': 'https://sn.coinafrique.com/categorie/chaussures-homme',
        'Vêtements Enfants': 'https://sn.coinafrique.com/categorie/vetements-enfants',
        'Chaussures Enfants': 'https://sn.coinafrique.com/categorie/chaussures-enfants'
    }
    
    # Créer les colonnes pour les boutons
    col1, col2 = st.columns(2)
    
    with col1:
        # Vêtements Homme
        st.markdown("### 👔 Vêtements Homme")
        if st.button('🚀 Scraper Vêtements Homme (Brut)', key='scrape_vh_raw', use_container_width=True):
            with st.spinner('Scraping en cours...'):
                df = scrape_with_beautifulsoup(urls['Vêtements Homme'], 'Vêtements Homme', pages, clean_data=False)
                if not df.empty:
                    st.success(f'✅ {len(df)} articles récupérés (données brutes)!')
                    st.info(f'📊 Dimensions: {df.shape[0]} lignes et {df.shape[1]} colonnes')
                    st.dataframe(df.head(), use_container_width=True)
                    
                    # Sauvegarder automatiquement
                    if save_data_to_csv(df, 'vetements_homme_raw.csv'):
                        st.success('💾 Données sauvegardées dans vetements_homme_raw.csv')
                    
                    # Bouton de téléchargement
                    csv = convert_df_to_csv(df)
                    st.download_button(
                        label="📥 Télécharger CSV",
                        data=csv,
                        file_name=f'vetements_homme_raw_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                        mime='text/csv',
                        key='download_vh_raw'
                    )
                else:
                    st.warning('⚠️ Aucune donnée récupérée.')
        
        # Vêtements Enfants
        st.markdown("### 👶 Vêtements Enfants")
        if st.button('🚀 Scraper Vêtements Enfants (Brut)', key='scrape_ve_raw', use_container_width=True):
            with st.spinner('Scraping en cours...'):
                df = scrape_with_beautifulsoup(urls['Vêtements Enfants'], 'Vêtements Enfants', pages, clean_data=False)
                if not df.empty:
                    st.success(f'✅ {len(df)} articles récupérés (données brutes)!')
                    st.info(f'📊 Dimensions: {df.shape[0]} lignes et {df.shape[1]} colonnes')
                    st.dataframe(df.head(), use_container_width=True)
                    
                    # Sauvegarder automatiquement
                    if save_data_to_csv(df, 'vetements_enfants_raw.csv'):
                        st.success('💾 Données sauvegardées dans vetements_enfants_raw.csv')
                    
                    # Bouton de téléchargement
                    csv = convert_df_to_csv(df)
                    st.download_button(
                        label="📥 Télécharger CSV",
                        data=csv,
                        file_name=f'vetements_enfants_raw_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                        mime='text/csv',
                        key='download_ve_raw'
                    )
                else:
                    st.warning('⚠️ Aucune donnée récupérée.')
    
    with col2:
        # Chaussures Homme
        st.markdown("### 👞 Chaussures Homme")
        if st.button('🚀 Scraper Chaussures Homme (Brut)', key='scrape_ch_raw', use_container_width=True):
            with st.spinner('Scraping en cours...'):
                df = scrape_with_beautifulsoup(urls['Chaussures Homme'], 'Chaussures Homme', pages, clean_data=False)
                if not df.empty:
                    st.success(f'✅ {len(df)} articles récupérés (données brutes)!')
                    st.info(f'📊 Dimensions: {df.shape[0]} lignes et {df.shape[1]} colonnes')
                    st.dataframe(df.head(), use_container_width=True)
                    
                    # Sauvegarder automatiquement
                    if save_data_to_csv(df, 'chaussures_homme_raw.csv'):
                        st.success('💾 Données sauvegardées dans chaussures_homme_raw.csv')
                    
                    # Bouton de téléchargement
                    csv = convert_df_to_csv(df)
                    st.download_button(
                        label="📥 Télécharger CSV",
                        data=csv,
                        file_name=f'chaussures_homme_raw_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                        mime='text/csv',
                        key='download_ch_raw'
                    )
                else:
                    st.warning('⚠️ Aucune donnée récupérée.')
        
        # Chaussures Enfants
        st.markdown("### 👟 Chaussures Enfants")
        if st.button('🚀 Scraper Chaussures Enfants (Brut)', key='scrape_ce_raw', use_container_width=True):
            with st.spinner('Scraping en cours...'):
                df = scrape_with_beautifulsoup(urls['Chaussures Enfants'], 'Chaussures Enfants', pages, clean_data=False)
                if not df.empty:
                    st.success(f'✅ {len(df)} articles récupérés (données brutes)!')
                    st.info(f'📊 Dimensions: {df.shape[0]} lignes et {df.shape[1]} colonnes')
                    st.dataframe(df.head(), use_container_width=True)
                    
                    # Sauvegarder automatiquement
                    if save_data_to_csv(df, 'chaussures_enfants_raw.csv'):
                        st.success('💾 Données sauvegardées dans chaussures_enfants_raw.csv')
                    
                    # Bouton de téléchargement
                    csv = convert_df_to_csv(df)
                    st.download_button(
                        label="📥 Télécharger CSV",
                        data=csv,
                        file_name=f'chaussures_enfants_raw_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                        mime='text/csv',
                        key='download_ce_raw'
                    )
                else:
                    st.warning('⚠️ Aucune donnée récupérée.')

elif choices == 'Télécharger données pré-scrapées':
    st.markdown("""
        <div style='background-color: #d1ecf1; padding: 1rem; border-radius: 10px; margin: 1rem 0;'>
            <h3 style='color: #0c5460; margin-bottom: 1rem;'>📥 Télécharger données pré-scrapées</h3>
            <p>Chargez et téléchargez les données qui ont été pré-scrapées et sauvegardées dans des fichiers CSV.</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Créer les colonnes pour les boutons
    col1, col2 = st.columns(2)
    
    with col1:
        # Vêtements Homme
        st.markdown("### 👔 Vêtements Homme")
        if st.button('📂 Charger Vêtements Homme', key='load_vh', use_container_width=True):
            df = load_data_from_csv(vetements_homme_path)
            if not df.empty:
                st.success(f'✅ {len(df)} articles chargés depuis {vetements_homme_path}!')
                st.info(f'📊 Dimensions: {df.shape[0]} lignes et {df.shape[1]} colonnes')
                st.dataframe(df.head(10), use_container_width=True)
                
                # Bouton de téléchargement
                csv = convert_df_to_csv(df)
                st.download_button(
                    label="📥 Télécharger CSV",
                    data=csv,
                    file_name=f'vetements_homme_prescraped_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                    mime='text/csv',
                    key='download_vh_pre'
                )
            else:
                st.warning('⚠️ Aucune donnée trouvée ou fichier inexistant.')
        
        # Vêtements Enfants
        st.markdown("### 👶 Vêtements Enfants")
        if st.button('📂 Charger Vêtements Enfants', key='load_ve', use_container_width=True):
            df = load_data_from_csv(vetements_enfants_path)
            if not df.empty:
                st.success(f'✅ {len(df)} articles chargés depuis {vetements_enfants_path}!')
                st.info(f'📊 Dimensions: {df.shape[0]} lignes et {df.shape[1]} colonnes')
                st.dataframe(df.head(10), use_container_width=True)
                
                # Bouton de téléchargement
                csv = convert_df_to_csv(df)
                st.download_button(
                    label="📥 Télécharger CSV",
                    data=csv,
                    file_name=f'vetements_enfants_prescraped_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                    mime='text/csv',
                    key='download_ve_pre'
                )
            else:
                st.warning('⚠️ Aucune donnée trouvée ou fichier inexistant.')
    
    with col2:
        # Chaussures Homme
        st.markdown("### 👞 Chaussures Homme")
        if st.button('📂 Charger Chaussures Homme', key='load_ch', use_container_width=True):
            df = load_data_from_csv(chaussures_homme_path)
            if not df.empty:
                st.success(f'✅ {len(df)} articles chargés depuis {chaussures_homme_path}!')
                st.info(f'📊 Dimensions: {df.shape[0]} lignes et {df.shape[1]} colonnes')
                st.dataframe(df.head(10), use_container_width=True)
                
                # Bouton de téléchargement
                csv = convert_df_to_csv(df)
                st.download_button(
                    label="📥 Télécharger CSV",
                    data=csv,
                    file_name=f'chaussures_homme_prescraped_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                    mime='text/csv',
                    key='download_ch_pre'
                )
            else:
                st.warning('⚠️ Aucune donnée trouvée ou fichier inexistant.')
        
        # Chaussures Enfants
        st.markdown("### 👟 Chaussures Enfants")
        if st.button('📂 Charger Chaussures Enfants', key='load_ce', use_container_width=True):
            df = load_data_from_csv(chaussures_enfants_path)
            if not df.empty:
                st.success(f'✅ {len(df)} articles chargés depuis {chaussures_enfants_path}!')
                st.info(f'📊 Dimensions: {df.shape[0]} lignes et {df.shape[1]} colonnes')
                st.dataframe(df.head(10), use_container_width=True)
                
                # Bouton de téléchargement
                csv = convert_df_to_csv(df)
                st.download_button(
                    label="📥 Télécharger CSV",
                    data=csv,
                    file_name=f'chaussures_enfants_prescraped_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                    mime='text/csv',
                    key='download_ce_pre'
                )
            else:
                st.warning('⚠️ Aucune donnée trouvée ou fichier inexistant.')
    
    # Section pour charger tous les fichiers à la fois
    st.markdown("---")
    st.markdown("### 📊 Charger toutes les données")
    
    if st.button('📂 Charger toutes les catégories', key='load_all', use_container_width=True):
        all_data = []
        paths = [
            (vetements_homme_path, 'Vêtements Homme'),
            (chaussures_homme_path, 'Chaussures Homme'),
            (vetements_enfants_path, 'Vêtements Enfants'),
            (chaussures_enfants_path, 'Chaussures Enfants')
        ]
        
        for path, category in paths:
            df = load_data_from_csv(path)
            if not df.empty:
                all_data.append(df)
                st.success(f'✅ {category}: {len(df)} articles chargés')
            else:
                st.warning(f'⚠️ {category}: Aucune donnée trouvée')
        
        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            st.success(f'🎉 Total combiné: {len(combined_df)} articles de {len(all_data)} catégories')
            st.dataframe(combined_df.head(20), use_container_width=True)
            
            # Bouton de téléchargement pour toutes les données
            csv_all = convert_df_to_csv(combined_df)
            st.download_button(
                label="📥 Télécharger toutes les données (CSV)",
                data=csv_all,
                file_name=f'coinafrique_all_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                mime='text/csv',
                key='download_all_pre'
            )

elif choices == 'Dashboard des données nettoyées':
    st.markdown("""
        <div style='background-color: #d4edda; padding: 1rem; border-radius: 10px; margin: 1rem 0;'>
            <h3 style='color: #155724; margin-bottom: 1rem;'>📊 Dashboard des données nettoyées</h3>
            <p>Visualisez les données nettoyées sous forme de graphiques interactifs.</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Option pour choisir la source des données
    data_source = st.selectbox(
        '📂 Choisir la source des données',
        options=[
            'Charger depuis fichiers CSV',
            'Utiliser données d\'exemple',
            'Combiner toutes les sources'
        ],
        help="Sélectionnez la source des données pour le dashboard"
    )
    
    if data_source == 'Charger depuis fichiers CSV':
        st.markdown("### 📁 Sélectionner les fichiers à analyser")
        
        # Checkboxes pour sélectionner les fichiers
        use_vh = st.checkbox('Vêtements Homme', value=True)
        use_ch = st.checkbox('Chaussures Homme', value=True)
        use_ve = st.checkbox('Vêtements Enfants', value=True)
        use_ce = st.checkbox('Chaussures Enfants', value=True)
        
        if st.button('🚀 Générer Dashboard', key='generate_dashboard'):
            dashboard_data = []
            
            if use_vh:
                df_vh = load_data_from_csv('data/vetements_homme.csv')
                if not df_vh.empty:
                    dashboard_data.append(df_vh)
            
            if use_ch:
                df_ch = load_data_from_csv('data/chaussures_homme.csv')
                if not df_ch.empty:
                    dashboard_data.append(df_ch)
            
            if use_ve:
                df_ve = load_data_from_csv('data/vetements_enfants.csv')
                if not df_ve.empty:
                    dashboard_data.append(df_ve)
            
            if use_ce:
                df_ce = load_data_from_csv('data/chaussures_enfants.csv')
                if not df_ce.empty:
                    dashboard_data.append(df_ce)
            
            if dashboard_data:
                combined_df = pd.concat(dashboard_data, ignore_index=True)
                # Nettoyer les données avant de créer le dashboard
                cleaned_df = clean_scraped_data(combined_df)
                create_dashboard(cleaned_df)
            else:
                st.warning('⚠️ Aucune donnée trouvée dans les fichiers sélectionnés.')
    
    elif data_source == 'Utiliser données d\'exemple':
        # Créer des données d'exemple réalistes
        sample_data = pd.DataFrame({
            'categorie': ['Vêtements Homme', 'Chaussures Homme', 'Vêtements Enfants', 'Chaussures Enfants'] * 50,
            'type': ['Chemise', 'Sneakers', 'T-shirt', 'Sandales'] * 50,
            'prix': ['15000 FCFA', '25000 FCFA', '8000 FCFA', '12000 FCFA'] * 50,
            'adresse': ['Dakar', 'Thiès', 'Kaolack', 'Saint-Louis', 'Ziguinchor'] * 40,
            'image_lien': ['https://example.com/img1.jpg'] * 200
        })
        
        # Ajouter de la variabilité
        np.random.seed(42)
        prix_variations = np.random.normal(1, 0.3, len(sample_data))
        sample_data['prix'] = sample_data['prix'].str.replace(r'[^\d]', '', regex=True).astype(int)
        sample_data['prix'] = (sample_data['prix'] * prix_variations).astype(int)
        sample_data['prix'] = sample_data['prix'].astype(str) + ' FCFA'
        
        cleaned_sample = clean_scraped_data(sample_data)
        create_dashboard(cleaned_sample)
    
    else:  # Combiner toutes les sources
        st.markdown("### 📊 Dashboard combiné")
        def create_dashboard(df):
            """Créer un dashboard interactif adapté à l'application CoinAfrique"""
            if df.empty:
                st.warning('⚠️ Aucune donnée disponible pour le dashboard.')
                return

            st.markdown("""
                <h2 style='text-align: center; color: #2E86AB; margin: 2rem 0;'>
                    📊 DASHBOARD ANALYTIQUE
                </h2>
            """, unsafe_allow_html=True)

            # 🔢 Métriques principales
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("📝 Total articles", len(df))

            with col2:
                if 'prix_numerique' in df.columns and df['prix_numerique'].notna().any():
                    st.metric("💰 Prix moyen", f"{df['prix_numerique'].mean():,.0f} FCFA")
                else:
                    st.metric("💰 Prix moyen", "N/A")

            with col3:
                if 'categorie' in df.columns:
                    st.metric("🏷️ Catégories", df['categorie'].nunique())
                else:
                    st.metric("🏷️ Catégories", "N/A")

            with col4:
                if 'adresse' in df.columns:
                    st.metric("🏙️ Villes", df['adresse'].nunique())
                else:
                    st.metric("🏙️ Villes", "N/A")

            # 📈 Graphiques
            col1, col2 = st.columns(2)

            with col1:
                if 'categorie' in df.columns:
                    fig_cat = px.pie(
                        df,
                        names='categorie',
                        title='Répartition par catégorie',
                        color_discrete_sequence=px.colors.qualitative.Set3
                    )
                    fig_cat.update_layout(height=400)
                    st.plotly_chart(fig_cat, use_container_width=True)

            with col2:
                if 'adresse' in df.columns:
                    top_villes = df['adresse'].value_counts().head(10)
                    fig_villes = px.bar(
                        x=top_villes.values,
                        y=top_villes.index,
                        orientation='h',
                        title='Top 10 des villes',
                        labels={'x': 'Nombre d\'articles', 'y': 'Ville'}
                    )
                    fig_villes.update_layout(height=400)
                    st.plotly_chart(fig_villes, use_container_width=True)

            # 📊 Analyse des prix
            if 'prix_numerique' in df.columns and df['prix_numerique'].notna().any():
                prix_valides = df.dropna(subset=['prix_numerique'])

                col1, col2 = st.columns(2)

                with col1:
                    if 'categorie' in df.columns:
                        fig_box = px.box(
                            prix_valides,
                            x='categorie',
                            y='prix_numerique',
                            title='Distribution des prix par catégorie'
                        )
                        fig_box.update_layout(height=400)
                        fig_box.update_xaxes(tickangle=45)
                        st.plotly_chart(fig_box, use_container_width=True)

                with col2:
                    fig_hist = px.histogram(
                        prix_valides,
                        x='prix_numerique',
                        nbins=30,
                        title='Distribution des prix'
                    )
                    fig_hist.update_layout(height=400)
                    st.plotly_chart(fig_hist, use_container_width=True)
            if all_sources:
                combined_df = pd.concat(all_sources, ignore_index=True).drop_duplicates()
                cleaned_df = clean_scraped_data(combined_df)

        if 'categorie' not in cleaned_df.columns:
            st.warning("⚠️ La colonne 'categorie' est absente. Le dashboard ne peut pas être généré.")
            st.dataframe(cleaned_df.head())
        else:
            create_dashboard(cleaned_df)  # 
            

            
            # Fichiers possibles
            base_path = "C:/Users/ZAGRE/OneDrive/Desktop/ZAGRE-Emmanuel-DC/data"

            possible_files = [
                (f"{base_path}/vetements_homme.csv", "Vêtements Homme"),
                (f"{base_path}/chaussures_homme.csv", "Chaussures Homme"),
                (f"{base_path}/vetements_enfants.csv", "Vêtements Enfants"),
                (f"{base_path}/chaussures_enfants.csv", "Chaussures Enfants"),
                (f"{base_path}/vetements_homme_cleaned.csv", "Vêtements Homme (Nettoyées)"),
                (f"{base_path}/chaussures_homme_cleaned.csv", "Chaussures Homme (Nettoyées)"),
                (f"{base_path}/vetements_enfants_cleaned.csv", "Vêtements Enfants (Nettoyées)"),
                (f"{base_path}/chaussures_enfants_cleaned.csv", "Chaussures Enfants (Nettoyées)")
            ]

            
            for filepath, category in possible_files:
                df = load_data_from_csv(filepath)
                if not df.empty:
                    all_sources.append(df)
                    st.info(f'✅ {category}: {len(df)} articles chargés')
            
            if all_sources:
                combined_df = pd.concat(all_sources, ignore_index=True)
                # Supprimer les doublons
                combined_df = combined_df.drop_duplicates()
                cleaned_combined = clean_scraped_data(combined_df)
                
                st.success(f'🎉 Dashboard généré avec {len(cleaned_combined)} articles uniques')
                create_dashboard(cleaned_combined)
            else:
                st.warning('⚠️ Aucune donnée trouvée. Veuillez d\'abord scraper des données.')

else:  # Formulaire d'évaluation
    st.markdown("""
        <div style='background-color: #f8d7da; padding: 1rem; border-radius: 10px; margin: 1rem 0;'>
            <h3 style='color: #721c24; margin-bottom: 1rem;'>📝 Formulaire d'évaluation</h3>
            <p>Donnez votre avis sur cette application via KoboToolbox.</p>
        </div>
    """, unsafe_allow_html=True)
    
    
# 🔁 Section d'évaluation externe avec iframe + fallback
st.markdown("---")
st.markdown("### 🌐 Formulaire KoboToolbox")

try:
    components.html("""
        <div style='text-align: center; margin: 2rem 0;'>
            <h4>Évaluez cette application sur KoboToolbox</h4>
            <p>Votre feedback détaillé nous aide à améliorer l'application.</p>
            <iframe src='https://ee.kobotoolbox.org/i/fBmPGz9P' width="800" height="600"></iframe>
        </div>
    """, height=650)
except:
    st.warning("⚠️ Le formulaire intégré n'a pas pu s'afficher. Cliquez ci-dessous pour y accéder :")
    st.markdown("[📝 Accéder au formulaire KoboToolbox](https://ee.kobotoolbox.org/i/fBmPGz9P)", unsafe_allow_html=True)


# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; padding: 2rem; margin-top: 3rem; border-top: 1px solid #ddd;'>
        <p style='color: #666; margin: 0;'>
            🚀 Coinafrique Scraper - Développé avec Streamlit et BeautifulSoup
        </p>
        <p style='color: #999; font-size: 0.8rem; margin: 0.5rem 0 0 0;'>
            Scraping BeautifulSoup (nettoyage) | Web Scraper (données brutes) | Dashboard interactif | Évaluation
        </p>
        <p style='color: #999; font-size: 0.8rem; margin: 0.5rem 0 0 0;'>
            Pour toute question ou suggestion, contactez l'équipe de développement
        </p>
    </div>
""", unsafe_allow_html=True)
