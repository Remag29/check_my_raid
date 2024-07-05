FROM python:3.13.0b2-slim

# Crée un répertoire de travail dans l'image
WORKDIR /app

# Copie le script Python dans le répertoire de travail
COPY main.py .

# Met à jour pip et installe les dépendances Python
RUN pip install --upgrade pip \
    && pip install python-dotenv requests schedule pytz

# Définit la commande par défaut à exécuter
CMD ["python", "-u", "./main.py"]
