from datetime import timedelta
# Configuration pour JWT (JSON Web Tokens)
# En production, ces valeurs devraient venir de variables d'environnement.
SECRET_KEY = "a_very_secret_key_that_should_be_changed_and_be_longer"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8 # 8 heures
