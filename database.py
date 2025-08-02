from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Configuration de la base de données SQLite
# Pour un déploiement en production, cette URL devra pointer vers une BDD PostgreSQL.
SQLALCHEMY_DATABASE_URL = "sqlite:///./quincaillerie_pro.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    # `connect_args` est nécessaire uniquement pour SQLite pour autoriser les connexions multithread.
    connect_args={"check_same_thread": False} 
)

# Création d'une usine de sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base déclarative pour les modèles SQLAlchemy
Base = declarative_base()

# Dépendance pour obtenir la session de la base de données dans les routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
