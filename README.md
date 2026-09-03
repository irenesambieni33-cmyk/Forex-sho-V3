# Forex AI Analyst

Dashboard Streamlit d'analyse technique multi-timeframe pour EUR/USD et XAU/USD. L'application est un **outil d'aide à la décision** : elle ne se connecte à aucun broker et n'envoie aucun ordre.

## Fonctionnalités

- D1, H4, H1, M15, M5 avec pondérations 3/3/2/1/1.
- H4 construit à partir de bougies H1.
- EMA20, EMA50, SMA200, RSI14, MACD 12/26/9, ATR14, ADX14, DI+/DI-, Bollinger 20/2, Stochastic 14/3.
- Swings confirmés, HH/HL/LH/LL, BOS/CHoCH.
- Supports/résistances regroupés par distance ATR.
- Fibonacci 23.6/38.2/50/61.8/78.6/127.2/161.8 et confluence.
- Score multi-timeframe et décisions ACHAT / VENTE / ATTENDRE / AUCUN SETUP.
- Entry, SL, TP1, TP2 et contrôle du R:R.
- Gestion du risque informative : 1% par trade, 2% maximum configuré.
- Graphique Plotly interactif.
- Tolérance aux timeframes manquants et aux erreurs Yahoo Finance.
- Fallback GC=F pour XAU/USD lorsque le spot est largement indisponible, avec avertissement explicite.

## Architecture

`app.py` orchestre ; `data.py` récupère les données ; `indicators.py` calcule les indicateurs ; `structure.py` analyse la structure ; `fibonacci.py` calcule Fibonacci/confluence ; `support_resistance.py` détecte les zones ; `analysis.py` décide ; `risk.py` calcule le setup et le risque ; `interface.py` affiche ; `config.py` centralise les paramètres.

## Installation locale

```bash
python -m venv .venv
# Windows : .venv\Scripts\activate
# Linux/macOS : source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## GitHub

1. Créez un dépôt `forex-ai-analyst`.
2. Copiez tous les fichiers du projet à la racine.
3. Committez puis poussez vers GitHub.
4. Sur Streamlit Community Cloud, créez une application et sélectionnez `app.py` comme fichier principal.

## Test

Avant déploiement :

```bash
python -m py_compile app.py config.py data.py indicators.py structure.py fibonacci.py support_resistance.py analysis.py risk.py interface.py
streamlit run app.py
```

Testez séparément : EUR/USD, XAU/USD, absence de données sur un timeframe, marché fermé, réponse Yahoo vide, et fallback GC=F.

## Limites professionnelles

- Yahoo Finance est une source pratique mais pas une source institutionnelle de trading ; des retards, trous ou changements de disponibilité sont possibles.
- Les signaux sont des évaluations techniques, pas des garanties de rendement.
- La taille affichée est une **quantité théorique en unités de prix**. La conversion en lots réels dépend du contrat, de la valeur du point, de la devise du compte et du broker.
- Aucun code d'exécution d'ordre n'est présent.

## Contraintes de coût et utilisation Android

Cette version est conçue pour rester gratuite à ton niveau :
- aucune API OpenAI ou autre API IA payante ;
- aucune API Forex payante ;
- aucune connexion à un broker ;
- aucune commande d'achat/vente automatique ;
- données via `yfinance` ;
- calculs locaux avec Python, pandas et numpy ;
- interface Streamlit ;
- déploiement possible gratuitement avec GitHub + Streamlit Community Cloud.

### Travail depuis un téléphone Android

Le projet peut être créé, modifié et déployé depuis un navigateur Android avec GitHub/Codespaces puis Streamlit Community Cloud. Aucun PC n'est requis pour le workflow prévu.

### Limite importante

« Gratuit » ne signifie pas « données institutionnelles temps réel ». Yahoo Finance peut fournir des données retardées, incomplètes ou indisponibles sur certains intervalles. L'application doit afficher une analyse prudente lorsqu'une donnée manque.

**Analyse uniquement. Aucun ordre automatique.**
