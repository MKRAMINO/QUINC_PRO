from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base, get_db
from . import models, crud
from .routers import auth, products, clients, suppliers, sales, orders, reports, settings
from sqlalchemy.orm import Session

# Crée les tables dans la base de données si elles n'existent pas
# Dans un environnement de production, on utiliserait un outil de migration comme Alembic.
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Quincaillerie PRO API",
    description="API pour le logiciel de gestion de quincaillerie.",
    version="1.0.0",
)

# Configuration CORS (Cross-Origin Resource Sharing)
# Permet au frontend (qui tourne sur une autre origine) de communiquer avec l'API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # À restreindre en production à l'URL du frontend !
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclure les routeurs des différents modules
app.include_router(auth.router, tags=["Authentication"])
app.include_router(products.router, prefix="/api", tags=["Products"])
app.include_router(clients.router, prefix="/api", tags=["Clients"])
app.include_router(suppliers.router, prefix="/api", tags=["Suppliers"])
app.include_router(sales.router, prefix="/api", tags=["Sales"])
app.include_router(orders.router, prefix="/api", tags=["Purchase Orders"])
app.include_router(reports.router, prefix="/api", tags=["Dashboard & Reports"])
app.include_router(settings.router, prefix="/api", tags=["Settings"])


@app.on_event("startup")
def startup_event():
    """
    Événement au démarrage de l'application pour créer un utilisateur admin par défaut
    et des paramètres de base.
    """
    db = next(get_db())
    try:
        # Vérifier si un utilisateur admin existe déjà
        admin_user = crud.get_user_by_username(db, username="admin")
        if not admin_user:
            # Créer l'utilisateur admin s'il n'existe pas
            from .schemas import UserCreate
            from .models import UserRole
            print("Création de l'utilisateur admin par défaut (admin/password123)")
            user_in = UserCreate(username="admin", password="password123", role=UserRole.ADMIN)
            crud.create_user(db=db, user=user_in)
        
        # Vérifier si les paramètres existent, sinon les initialiser
        current_settings = crud.get_settings(db)
        if not any(current_settings.values()): # Si tous les settings sont vides ou par défaut
             print("Initialisation des paramètres par défaut de la société.")
             default_settings = {
                'nom': 'Quincaillerie PRO', 'adresse': 'Lot II A 123 Ankorondrano, Antananarivo', 
                'tel': '034 00 123 45', 'email': 'contact@quincailleriepro.mg',
                'nif': '1000123456', 'stat': '123456789012345', 
                'rib': '00001 00002 0000300004 55', 'monnaie': 'Ar', 'tvaRate': '20'
             }
             # On ne met à jour que si les valeurs sont "vides"
             settings_to_update = {k: v for k, v in default_settings.items() if not current_settings.get(k)}
             if settings_to_update:
                crud.update_settings(db, settings_to_update)

    finally:
        db.close()

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Welcome to Quincaillerie PRO API"}
