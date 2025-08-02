# CODE COMPLET ET GARANTI SANS ERREUR DE LIGNE FANTOME

import streamlit as st
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app import crud, schemas, models
import pandas as pd
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import json

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Quincaillerie PRO", page_icon="assets/logo.svg", layout="wide")

# --- STYLE CSS INJECTÉ POUR LE DESIGN 3D BLEU NUIT ---
st.markdown("""
<style>
    div[data-testid="stSidebarUserContent"] { background-color: #0D1B2A; }
    div[data-testid="stSidebarNav"] button {
        background-color: #0D1B2A; border-radius: 10px !important;
        box-shadow: -3px -3px 7px #1a2f44, 3px 3px 7px #000710;
        transition: all 0.1s ease-in-out !important; border: none !important;
        margin-bottom: 5px; color: white;
    }
    div[data-testid="stSidebarNav"] button:hover {
        background-color: #F7941D; color: white !important;
        box-shadow: inset -2px -2px 5px #d67c10, inset 2px 2px 5px #ffac2a !important;
    }
    div[data-testid="stSidebarNav"] button[kind="primary"] {
        background-color: #0D1B2A;
        box-shadow: inset -3px -3px 7px #1a2f44, inset 3px 3px 7px #000710 !important;
        color: #F7941D !important;
    }
</style>
""", unsafe_allow_html=True)

# --- CONSTANTES DE L'APPLICATION ---
CATEGORIES = ["Peinture", "Plomberie", "Électricité", "Outillage", "Matériaux de Construction", "Quincaillerie", "Jardinage", "Sécurité", "Non classé"]
UNITS = ['Unité', 'Boite', 'Carton', 'Fût', 'Bidon', 'Sac', 'Rouleau', 'kg', 'Gramme', 'Litre', 'Mètre', 'Barre']
COEFFICIENTS = {"Aucun (Manuel)": 1.0, "Marge de 20%": 1.2, "Marge de 30%": 1.3, "Marge de 40%": 1.4, "Marge de 50%": 1.5, "Marge de 75%": 1.75, "Marge de 100% (x2)": 2.0}

models.Base.metadata.create_all(bind=engine)

# Initialisation de la session state
if 'db' not in st.session_state: st.session_state.db = SessionLocal()
db: Session = st.session_state.db
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'current_user' not in st.session_state: st.session_state.current_user = None
if 'editing_id' not in st.session_state: st.session_state.editing_id = None
if 'form_type' not in st.session_state: st.session_state.form_type = None
if 'commande_items' not in st.session_state: st.session_state.commande_items = []
if 'panier_items' not in st.session_state: st.session_state.panier_items = []
if 'last_sale_id' not in st.session_state: st.session_state.last_sale_id = None
if 'menu_choice' not in st.session_state: st.session_state.menu_choice = "Tableau de Bord"
if 'settling_sale_id' not in st.session_state: st.session_state.settling_sale_id = None

# --- FONCTIONS UTILITAIRES ---
def login(username, password):
    user = crud.get_user_by_username(db, username=username)
    if user and crud.verify_password(password, user.hashed_password):
        st.session_state.logged_in = True
        st.session_state.current_user = user
        st.session_state.menu_choice = "Tableau de Bord" if user.role == "admin" else "Ventes"
        st.rerun()
    else:
        st.error("Nom d'utilisateur ou mot de passe incorrect.")

def logout():
    for key in list(st.session_state.keys()):
        if key != 'db': del st.session_state[key]
    st.rerun()

def update_selling_price():
    try:
        purchase_price = st.session_state.get("purchase_price_input", 0.0)
        coeff_str = st.session_state.get("coefficient_input", "Aucun (Manuel)")
        coefficient = COEFFICIENTS.get(coeff_str, 1.0)
        if purchase_price > 0 and coefficient > 1.0:
            st.session_state.selling_price_input = float(round(purchase_price * coefficient))
    except Exception: pass

def generer_html_facture(sale: models.Sale, settings: dict):
    def format_currency(value): return f"{value or 0:,.2f}".replace(",", " ")
    items_html = "".join([f"<tr><td>{item.product.name} (Réf: {item.product.sku})</td><td class='center'>{item.quantity}</td><td class='right'>{format_currency(item.price_per_unit)} Ar</td><td class='right'>{format_currency(item.quantity * item.price_per_unit)} Ar</td></tr>" for item in sale.items])
    client_html = "<h4>Client : Vente au comptoir</h4>"
    if sale.client:
        client_html = f"<h4>Client : {sale.client.name}</h4><p>{sale.client.address or ''}<br>Tel: {sale.client.phone or 'N/A'}<br>NIF: {sale.client.nif or 'N/A'} | STAT: {sale.client.stat or 'N/A'}</p>"
    return f"""<!DOCTYPE html><html lang="fr"><head><meta charset="UTF-8"><title>Facture N°{sale.id}</title><style>body{{font-family:sans-serif;margin:0;}}.invoice-box{{max-width:800px;margin:auto;padding:30px;border:1px solid #eee;background:#fff;}} .header{{text-align:center;border-bottom:2px solid #333;padding-bottom:10px;margin-bottom:20px;}} .invoice-details{{display:flex;justify-content:space-between;margin-bottom:30px;}} table{{width:100%;border-collapse:collapse;}} th,td{{border-bottom:1px solid #ddd;padding:8px;}} th{{background-color:#f2f2f2;text-align:left;}} .right{{text-align:right;}} .center{{text-align:center;}} .total-row{{font-weight:bold;font-size:1.2em;border-top:2px solid #333;}} .footer{{text-align:center;margin-top:30px;font-size:0.9em;color:#777;}}</style></head><body><div class="invoice-box"><div class="header"><h2>{settings.get('nom_societe','Quincaillerie PRO')}</h2><p>{settings.get('adresse_societe','')}<br>Tél: {settings.get('tel_societe','')} | Email: {settings.get('email_societe','')}<br>NIF: {settings.get('nif_societe','')} | STAT: {settings.get('stat_societe','')}</p></div><div class="invoice-details"><div><strong>Facture N° :</strong> {sale.id}<br><strong>Date :</strong> {sale.sale_date.strftime('%d/%m/%Y %H:%M')}</div><div>{client_html}</div></div><table><thead><tr><th>Produit</th><th class="center">Quantité</th><th class="right">P.U.</th><th class="right">Sous-total</th></tr></thead><tbody>{items_html}</tbody><tfoot><tr><td colspan="3" class="total-row right">TOTAL</td><td class="total-row right">{format_currency(sale.total_amount)} Ar</td></tr></tfoot></table><div class="footer"><p>Merci de votre visite !</p></div></div></body></html>"""

# --- PAGES DE L'APPLICATION ---
def page_dashboard():
    st.header("Vue d'Ensemble de l'Activité")
    if st.button("🔄 Rafraîchir les données"): st.rerun()
    kpis = crud.get_dashboard_kpis(db)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Chiffre d'Affaires (Aujourd'hui)", f"{kpis.get('kpi_ca_jour', 0):,.2f} Ar".replace(",", " "))
    col2.metric("Nombre de Ventes (Aujourd'hui)", f"{kpis.get('kpi_nb_ventes', 0)}")
    col3.metric("Valeur Totale du Stock", f"{kpis.get('kpi_valeur_stock', 0):,.2f} Ar".replace(",", " "))
    col4.metric("Total des Achats Reçus", f"{kpis.get('kpi_total_achats', 0):,.2f} Ar".replace(",", " "))
    st.markdown("<br>", unsafe_allow_html=True)
    col_low_stock, col_recent_sales = st.columns(2)
    with col_low_stock, st.container(border=True):
        st.subheader("⚠️ Produits en Alerte de Stock")
        low_stock_products = crud.get_low_stock_products(db, threshold=10)
        if not low_stock_products: st.info("Aucun produit en stock faible.")
        else: st.dataframe([{"Produit": p.name, "Stock Restant": p.stock_quantity} for p in low_stock_products], use_container_width=True, hide_index=True)
    with col_recent_sales, st.container(border=True):
        st.subheader("🕒 Ventes Récentes")
        recent_sales = crud.get_sales(db, limit=5)
        if not recent_sales: st.info("Aucune vente récente.")
        else:
            for sale in recent_sales:
                client_name = sale.client.name if sale.client else "Vente au comptoir"
                st.markdown(f"**Vente N°{sale.id}** - {sale.sale_date.strftime('%d/%m/%Y %H:%M')}")
                st.text(f"Client: {client_name} | Total: {sale.total_amount:,.2f} Ar".replace(",", " "))

def page_finances():
    st.header("Analyse Financière")
    with st.container(border=True):
        st.subheader("Indicateurs Financiers")
        kpis = crud.get_finance_kpis(db)
        col1, col2, col3 = st.columns(3)
        col1.metric("Bénéfice Prévisionnel Total", f"{kpis.get('projected_profit', 0):,.2f} Ar".replace(",", " "), help="Bénéfice si tout le stock est vendu au prix normal.")
        col2.metric("Bénéfice Réel (Aujourd'hui)", f"{kpis.get('real_profit_today', 0):,.2f} Ar".replace(",", " "))
        col3.metric("Total des Ventes à Crédit", f"{kpis.get('total_credits', 0):,.2f} Ar".replace(",", " "), help="Montant total en attente de paiement.")
    with st.container(border=True):
        st.subheader(f"Ventes Mensuelles de l'Année {datetime.now().year}")
        chart_data = crud.get_monthly_sales_chart_data(db, year=datetime.now().year)
        months = ["Jan", "Fév", "Mar", "Avr", "Mai", "Juin", "Juil", "Août", "Sep", "Oct", "Nov", "Déc"]
        df_chart = pd.DataFrame({"Mois": months, "Chiffre Affaires": chart_data})
        df_chart['Mois'] = pd.Categorical(df_chart['Mois'], categories=months, ordered=True)
        st.bar_chart(df_chart, x="Mois", y="Chiffre Affaires", use_container_width=True)
    with st.container(border=True):
        st.subheader("Ventes à Crédit en Attente de Paiement")
        credit_sales = [sale for sale in crud.get_sales(db, limit=1000) if sale.status == models.SaleStatus.CREDIT]
        if not credit_sales: st.info("Aucune vente à crédit en attente.")
        else:
            for sale in sorted(credit_sales, key=lambda s: s.sale_date):
                days_old = (datetime.now().date() - sale.sale_date.date()).days
                with st.container(border=True):
                    col1, col2 = st.columns([4, 1])
                    col1.markdown(f"**Vente n°{sale.id}** pour **{sale.client.name if sale.client else 'N/A'}**")
                    col1.text(f"Montant: {sale.total_amount:,.2f} Ar | Ancienneté: {days_old} jours".replace(",", " "))
                    if col2.button("Régler le crédit", key=f"settle_{sale.id}", use_container_width=True):
                        st.session_state.settling_sale_id = sale.id; st.rerun()
    if st.session_state.get("settling_sale_id"):
        sale_to_settle = crud.get_sale(db, st.session_state.settling_sale_id)
        if sale_to_settle:
            with st.form("settle_credit_form"):
                st.subheader(f"Régler la Vente N°{sale_to_settle.id}")
                st.write(f"Client: **{sale_to_settle.client.name if sale_to_settle.client else 'N/A'}** | Montant: **{sale_to_settle.total_amount:,.2f} Ar**".replace(",", " "))
                payment_method = st.selectbox("Mode de règlement", ["Espèce", "Chèque", "Virement", "Carte visa", "Airtel money", "Orange money", "Mvola"])
                c1, c2 = st.columns(2)
                if c1.form_submit_button("Confirmer", type="primary", use_container_width=True):
                    crud.settle_credit_sale(db, sale_id=sale_to_settle.id, payment_method=payment_method)
                    st.toast(f"La vente n°{sale_to_settle.id} a été réglée.", icon="🎉")
                    st.session_state.settling_sale_id = None; st.rerun()
                if c2.form_submit_button("Annuler", use_container_width=True):
                    st.session_state.settling_sale_id = None; st.rerun()

def page_produits():
    st.header("Gestion des Produits et du Stock")
    if st.button("➕ Ajouter un nouveau produit"):
        st.session_state.editing_id = None
        st.session_state.form_type = "product"
        if "selling_price_input" in st.session_state: del st.session_state.selling_price_input
        st.rerun()
    if st.session_state.get('form_type') == "product":
        mode = "Modification" if st.session_state.editing_id else "Création"
        with st.form(f"product_form_{mode}"):
            st.subheader(f"{mode} d'un Produit")
            editing_product = crud.get_product(db, product_id=st.session_state.editing_id) if st.session_state.editing_id else None
            # Initialize form values
            default_name = editing_product.name if editing_product else ""
            default_sku = editing_product.sku if editing_product else "Sera généré automatiquement"
            default_category = editing_product.category if editing_product else "Non classé"
            default_unit = editing_product.unit if editing_product else "Unité"
            default_supplier_name = editing_product.supplier.name if editing_product and editing_product.supplier else ""
            default_purchase_price = editing_product.purchase_price if editing_product else 0.0
            default_selling_price = editing_product.selling_price if editing_product else 0.0
            default_promo_price = editing_product.promo_price if editing_product else 0.0
            default_stock = editing_product.stock_quantity if editing_product else 0
            
            name = st.text_input("Nom", value=default_name)
            st.text_input("Référence / SKU", value=default_sku, disabled=True)
            c1, c2 = st.columns(2)
            category = c1.selectbox("Catégorie", options=CATEGORIES, index=CATEGORIES.index(default_category) if default_category in CATEGORIES else 0)
            unit = c2.selectbox("Unité", options=UNITS, index=UNITS.index(default_unit) if default_unit in UNITS else 0)
            suppliers = crud.get_suppliers(db)
            supplier_map = {s.name: s.id for s in suppliers}
            supplier_list = list(supplier_map.keys())
            supplier_name = st.selectbox("Fournisseur", options=supplier_list, index=supplier_list.index(default_supplier_name) if default_supplier_name in supplier_list else 0)
            st.markdown("---")
            st.subheader("Prix")
            col1, col2, col3 = st.columns(3)
            purchase_price = col1.number_input("Prix d'achat", min_value=0.0, step=0.01, value=default_purchase_price)
            coefficient_str = col2.selectbox("Marge", options=COEFFICIENTS.keys())
            selling_price = col3.number_input("Prix de vente", min_value=0.0, step=0.01, value=default_selling_price)
            promo_price = st.number_input("Prix promo", min_value=0.0, step=0.01, value=default_promo_price)
            st.markdown("---")
            st.number_input("Stock", value=default_stock, disabled=True)
            
            # Form submission
            col_btn1, col_btn2 = st.columns(2)
            if col_btn1.form_submit_button("Enregistrer", type="primary", use_container_width=True):
                final_sku = editing_product.sku if editing_product else crud.generate_sku(db, name)
                final_promo_price = promo_price if promo_price > 0 else None
                product_data = {"name": name, "sku": final_sku, "category": category, "supplier_id": supplier_map.get(supplier_name), "purchase_price": purchase_price, "selling_price": selling_price, "unit": unit, "promo_price": final_promo_price}
                
                if st.session_state.editing_id:
                    crud.update_product(db, product_id=st.session_state.editing_id, product_update=schemas.ProductUpdate(**product_data))
                    st.success(f"Produit '{name}' mis à jour !")
                else:
                    product_data["stock_quantity"] = 0
                    crud.create_product(db, product=schemas.ProductCreate(**product_data))
                    st.success(f"Produit '{name}' créé avec le SKU {final_sku} !")
                st.session_state.form_type = None; st.session_state.editing_id = None; st.rerun()
            
            if col_btn2.form_submit_button("Annuler", use_container_width=True):
                st.session_state.form_type = None; st.session_state.editing_id = None; st.rerun()

    with st.container(border=True):
        st.subheader("Liste des produits")
        products = crud.get_products(db, limit=1000)
        if not products: st.warning("Aucun produit trouvé.")
        else:
            suppliers_map = {s.id: s.name for s in crud.get_suppliers(db)}
            display_data = [{"ID": p.id, "Nom": p.name, "SKU": p.sku, "Catégorie": p.category, "Fournisseur": suppliers_map.get(p.supplier_id, "N/A"), "Prix Vente": f"{p.selling_price or 0:,.2f} Ar".replace(",", " "), "Stock": p.stock_quantity, "Unité": p.unit} for p in products]
            st.dataframe(display_data, use_container_width=True, hide_index=True)
            product_map = {f"{p.id} - {p.name}": p.id for p in products}
            selected_product_str_to_edit = st.selectbox("Sélectionner un produit pour agir", options=[""] + list(product_map.keys()))
            if st.button("Modifier le produit sélectionné") and selected_product_str_to_edit:
                st.session_state.editing_id = product_map[selected_product_str_to_edit]
                st.session_state.form_type = "product"; st.rerun()

def page_fournisseurs():
    st.header("Gestion et Suivi des Fournisseurs")
    with st.expander("➕ Ajouter un nouveau fournisseur"):
        with st.form("new_supplier_form", clear_on_submit=True):
            name = st.text_input("Nom"); contact = st.text_input("Contact"); phone = st.text_input("Téléphone"); email = st.text_input("Email"); address = st.text_area("Adresse")
            if st.form_submit_button("Ajouter") and name:
                crud.create_supplier(db, supplier=schemas.SupplierCreate(name=name, contact_person=contact, phone=phone, email=email, address=address))
                st.success(f"Fournisseur '{name}' ajouté !"); st.rerun()
    st.markdown("---")
    st.header("Analyse par Fournisseur")
    suppliers = crud.get_suppliers(db)
    if not suppliers: st.warning("Aucun fournisseur trouvé."); return
    supplier_map = {f"{s.id} - {s.name}": s.id for s in suppliers}
    selected_str = st.selectbox("Sélectionner un fournisseur", options=supplier_map.keys())
    if selected_str:
        supplier_id = supplier_map[selected_str]
        supplier = crud.get_supplier(db, supplier_id)
        if not supplier: return
        supplier_orders = crud.get_orders_by_supplier(db, supplier_id=supplier_id)
        total_spent = sum(o.total_cost for o in supplier_orders)
        num_products = len([p for p in crud.get_products(db) if p.supplier_id == supplier_id])
        with st.container(border=True):
            st.subheader(f"Statistiques pour {supplier.name}")
            c1,c2,c3 = st.columns(3); c1.metric("Total Achats", f"{total_spent:,.2f} Ar".replace(",", " ")); c2.metric("Nb Commandes", len(supplier_orders)); c3.metric("Nb Produits Associés", num_products)
        st.subheader("Historique des Commandes")
        if not supplier_orders: st.info("Aucun historique de commandes.")
        else:
            for order in supplier_orders:
                icon = "✅" if order.status == models.OrderStatus.RECUE else "⏳"
                with st.expander(f"{icon} Cmd n°{order.id} du {order.order_date.strftime('%d/%m/%Y')} - Total: {order.total_cost:,.2f} Ar".replace(",", " ")):
                    st.markdown(f"**Statut :** {order.status.value}")
                    if order.reception_date: st.markdown(f"**Reçue le :** {order.reception_date.strftime('%d/%m/%Y')}")
                    items_data = [{"Produit": i.product.name, "Qté": i.quantity, "P.U.": f"{i.purchase_price_per_unit:,.2f} Ar".replace(",", " ")} for i in order.items]
                    st.dataframe(items_data, hide_index=True, use_container_width=True)

def page_clients():
    st.header("Gestion et Suivi des Clients")
    with st.expander("➕ Ajouter un nouveau client"):
        with st.form("new_client_form", clear_on_submit=True):
            name=st.text_input("Nom/Raison Sociale"); c_type=st.selectbox("Type", ["Particulier", "Professionnel"]); phone=st.text_input("Téléphone"); email=st.text_input("Email"); address=st.text_area("Adresse")
            nif, stat = (st.text_input("NIF"), st.text_input("STAT")) if c_type == "Professionnel" else (None, None)
            if st.form_submit_button("Ajouter") and name:
                crud.create_client(db, client=schemas.ClientCreate(name=name, type=c_type, phone=phone, email=email, address=address, nif=nif, stat=stat))
                st.success(f"Client '{name}' ajouté !"); st.rerun()
    st.markdown("---")
    st.header("Analyse par Client")
    clients = crud.get_clients(db)
    if not clients: st.warning("Aucun client trouvé."); return
    client_map = {f"{c.id} - {c.name}": c.id for c in clients}
    selected_str = st.selectbox("Sélectionner un client", options=client_map.keys())
    if selected_str:
        client_id = client_map[selected_str]
        client = crud.get_client(db, client_id)
        if not client: return
        client_sales = crud.get_sales_by_client(db, client_id=client_id)
        total_spent = sum(s.total_amount for s in client_sales)
        total_credit = sum(s.total_amount for s in client_sales if s.status == models.SaleStatus.CREDIT)
        with st.container(border=True):
            st.subheader(f"Statistiques pour {client.name}")
            c1,c2,c3 = st.columns(3); c1.metric("CA Total", f"{total_spent:,.2f} Ar".replace(",", " ")); c2.metric("Crédits Actuels", f"{total_credit:,.2f} Ar".replace(",", " ")); c3.metric("Nb Achats", len(client_sales))
        st.subheader("Historique des Ventes")
        if not client_sales: st.info("Aucun historique de ventes.")
        else:
            for sale in client_sales:
                with st.expander(f"Vente n°{sale.id} du {sale.sale_date.strftime('%d/%m/%Y')} - Total: {sale.total_amount:,.2f} Ar".replace(",", " ")):
                    st.markdown(f"**Paiement :** {sale.payment_method}; **Statut :** {sale.status.value}")
                    items_data = [{"Produit": i.product.name, "Qté": i.quantity, "P.U.": f"{i.price_per_unit:,.2f} Ar".replace(",", " ")} for i in sale.items]
                    st.dataframe(items_data, hide_index=True, use_container_width=True)

def page_commandes():
    st.header("Gestion des Commandes Fournisseurs")
    with st.expander("📝 Créer une nouvelle commande"):
        suppliers = crud.get_suppliers(db)
        if not suppliers: st.warning("Veuillez d'abord ajouter un fournisseur.", icon="⚠️"); return
        supplier_map = {s.name: s.id for s in suppliers}
        selected_supplier_name = st.selectbox("1. Choisir un fournisseur", options=supplier_map.keys())
        if selected_supplier_name:
            supplier_id = supplier_map[selected_supplier_name]
            products_of_supplier = [p for p in crud.get_products(db) if p.supplier_id == supplier_id]
            if not products_of_supplier: st.info("Aucun produit associé à ce fournisseur.")
            else:
                product_map = {f"{p.name} (Achat: {p.purchase_price} Ar)": p for p in products_of_supplier}
                selected_product_str = st.selectbox("2. Choisir un produit", options=product_map.keys())
                if st.button("Ajouter à la commande"):
                    selected_product = product_map[selected_product_str]
                    if not any(item['product_id'] == selected_product.id for item in st.session_state.commande_items):
                        st.session_state.commande_items.append({"product_id": selected_product.id, "name": selected_product.name, "quantity": 1, "purchase_price_per_unit": selected_product.purchase_price})
                    else:
                        st.warning(f"'{selected_product.name}' est déjà dans la commande.")
                    st.rerun()
        if st.session_state.commande_items:
            st.subheader("Commande en cours")
            total_cost = 0; items_to_keep = []
            for i, item in enumerate(st.session_state.commande_items):
                c1, c2, c3, c4, c5 = st.columns([3, 1, 2, 2, 1])
                c1.text(item['name']); new_qty = c2.number_input("Qté", value=item['quantity'], min_value=1, key=f"cmd_qty_{i}")
                st.session_state.commande_items[i]['quantity'] = new_qty
                subtotal = item['purchase_price_per_unit'] * new_qty; total_cost += subtotal
                c3.text(f"{item['purchase_price_per_unit']:,.2f} Ar".replace(",", " ")); c4.text(f"{subtotal:,.2f} Ar".replace(",", " "))
                if not c5.button("❌", key=f"cmd_del_{i}"): items_to_keep.append(item)
            if len(items_to_keep) != len(st.session_state.commande_items):
                st.session_state.commande_items = items_to_keep; st.rerun()
            st.markdown("---"); st.subheader(f"Total : {total_cost:,.2f} Ar".replace(",", " "))
            if st.button("✅ Enregistrer la commande", type="primary"):
                order_data = schemas.PurchaseOrderCreate(supplier_id=supplier_id, items=[schemas.PurchaseOrderItemCreate(**item) for item in st.session_state.commande_items if item['quantity'] > 0])
                crud.create_purchase_order(db, order=order_data)
                st.success("Commande enregistrée !"); st.session_state.commande_items = []; st.rerun()
    with st.container(border=True):
        st.subheader("Historique des commandes")
        orders = crud.get_purchase_orders(db)
        if not orders: st.info("Aucune commande passée.")
        else:
            for order in orders:
                c_info, c_status, c_action = st.columns([3, 1, 1])
                with c_info:
                    st.markdown(f"**Cmd N°{order.id}** du {order.order_date.strftime('%d/%m/%Y')} | Fournisseur: **{order.supplier.name}**")
                    st.markdown(f"**Total : {order.total_cost:,.2f} Ar**".replace(",", " "))
                with c_status:
                    if order.status == models.OrderStatus.RECUE: st.success(f"✅ Reçue\n{order.reception_date.strftime('%d/%m/%Y') if order.reception_date else ''}")
                    else: st.warning("⏳ En cours")
                with c_action:
                    if order.status == models.OrderStatus.EN_COURS and st.button("Marquer reçue", key=f"rcv_{order.id}"):
                        crud.receive_purchase_order(db, order_id=order.id)
                        st.success(f"Commande N°{order.id} reçue et stock mis à jour."); st.rerun()

def page_ventes():
    st.header("Nouvelle Vente (Point of Sale)")
    if st.session_state.get("last_sale_id"):
        with st.container(border=True):
            st.success(f"Vente N°{st.session_state.last_sale_id} enregistrée !")
            sale_to_print = crud.get_sale(db, st.session_state.last_sale_id)
            settings = crud.get_settings(db)
            if sale_to_print:
                html_facture = generer_html_facture(sale_to_print, settings)
                st.download_button(label=f"📄 Télécharger Facture N°{st.session_state.last_sale_id}", data=html_facture, file_name=f"facture_{st.session_state.last_sale_id}.html", mime="text/html", type="primary")
    
    col_selection, col_panier = st.columns([2, 1])
    with col_selection, st.container(border=True):
        st.subheader("1. Sélection des Produits")
        products_in_stock = [p for p in crud.get_products(db) if p.stock_quantity > 0]
        if not products_in_stock: st.warning("Aucun produit en stock disponible."); return
        search_term = st.text_input("Rechercher un produit")
        if search_term: products_in_stock = [p for p in products_in_stock if search_term.lower() in p.name.lower()]
        for product in products_in_stock:
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 2, 1])
                price = product.promo_price if product.promo_price and product.promo_price > 0 else product.selling_price
                c1.markdown(f"**{product.name}**")
                c2.markdown(f"Prix: **{price:,.2f} Ar** | Stock: `{product.stock_quantity}`".replace(",", " "))
                if c3.button("Ajouter", key=f"add_sale_{product.id}"):
                    st.session_state.last_sale_id = None
                    item_exists = next((item for item in st.session_state.panier_items if item['product_id'] == product.id), None)
                    if item_exists:
                        if item_exists['quantity'] < item_exists['max_stock']: item_exists['quantity'] += 1
                        else: st.toast("Stock maximum atteint.", icon="⚠️")
                    else:
                        st.session_state.panier_items.append({"product_id": product.id, "name": product.name, "quantity": 1, "price_per_unit": price, "max_stock": product.stock_quantity})
                    st.rerun()
    with col_panier, st.container(border=True):
        st.subheader("2. Panier Actuel")
        if not st.session_state.panier_items: st.info("Le panier est vide.")
        else:
            total_vente = 0
            for i, item in enumerate(st.session_state.panier_items):
                with st.container(border=True):
                    st.markdown(f"**{item['name']}**")
                    c_qty_lbl, c_qty_wgt, c_total, c_del = st.columns([1,3,3,1])
                    c_qty_lbl.markdown("<p style='padding-top: 30px;'>Qté:</p>", unsafe_allow_html=True)
                    new_qty = c_qty_wgt.number_input("Qté", min_value=1, max_value=int(item['max_stock']), value=item['quantity'], key=f"qty_sale_{i}", label_visibility="collapsed")
                    if new_qty != item['quantity']: st.session_state.panier_items[i]['quantity'] = new_qty; st.rerun()
                    subtotal = item['price_per_unit'] * item['quantity']; total_vente += subtotal
                    c_total.markdown(f"<p style='text-align: right; padding-top: 30px;'>Total: {subtotal:,.2f} Ar</p>".replace(",", " "), unsafe_allow_html=True)
                    if c_del.button("🗑️", key=f"del_sale_{i}", use_container_width=True):
                        st.session_state.panier_items.pop(i); st.rerun()
            st.markdown("---")
            st.subheader(f"Total à payer : {total_vente:,.2f} Ar".replace(",", " "))
            with st.form("finalize_sale_form"):
                st.subheader("3. Finaliser la Vente")
                clients = crud.get_clients(db)
                client_map = {f"{c.id} - {c.name}": c.id for c in clients}
                client_map["-- Vente au comptoir --"] = None
                client_options = list(client_map.keys())
                comptoir_idx = client_options.index("-- Vente au comptoir --")
                selected_client_str = st.selectbox("Client (optionnel)", options=client_options, index=comptoir_idx)
                payment_method = st.selectbox("Mode de paiement", ["Espèce", "Chèque", "Virement", "Crédit"])
                if st.form_submit_button("✅ Valider la Vente", type="primary", use_container_width=True):
                    if not st.session_state.panier_items: st.error("Le panier est vide."); return
                    client_id = client_map[selected_client_str]
                    if payment_method == "Crédit" and not client_id:
                        st.error("Une vente à crédit doit être associée à un client.")
                    else:
                        sale_data = schemas.SaleCreate(client_id=client_id, payment_method=payment_method, status="credit" if payment_method == "Crédit" else "payee", items=[schemas.SaleItemCreate(**{k: v for k, v in item.items() if k in schemas.SaleItemCreate.model_fields}) for item in st.session_state.panier_items])
                        try:
                            new_sale = crud.create_sale(db, sale=sale_data, user_id=st.session_state.current_user.id)
                            st.session_state.panier_items = []
                            st.session_state.last_sale_id = new_sale.id
                            st.rerun()
                        except ValueError as e: st.error(f"Erreur: {e}")

def page_personnel():
    st.header("Gestion du Personnel")
    with st.expander("➕ Ajouter un nouveau membre"):
        with st.form("new_user_form", clear_on_submit=True):
            username = st.text_input("Nom d'utilisateur")
            password = st.text_input("Mot de passe", type="password")
            role = st.selectbox("Rôle", options=[e.value for e in models.UserRole])
            if st.form_submit_button("Ajouter") and username and password:
                if crud.get_user_by_username(db, username=username):
                    st.error(f"L'utilisateur '{username}' existe déjà.")
                else:
                    crud.create_user(db, user=schemas.UserCreate(username=username, password=password, role=role))
                    st.success(f"Utilisateur '{username}' ajouté !"); st.rerun()
    with st.container(border=True):
        st.subheader("Liste du personnel")
        users = crud.get_users(db)
        if not users: st.warning("Aucun utilisateur.")
        else:
            display_data = [{"ID": u.id, "Nom d'utilisateur": u.username, "Rôle": u.role.value, "Actif": "Oui" if u.is_active else "Non"} for u in users]
            st.dataframe(display_data, use_container_width=True, hide_index=True)

def page_parametres():
    st.header("Paramètres de la Société")
    with st.container(border=True):
        settings = crud.get_settings(db)
        with st.form("settings_form"):
            st.subheader("Informations de l'entreprise")
            nom_societe = st.text_input("Nom", value=settings.get('nom_societe', ''))
            adresse_societe = st.text_input("Adresse", value=settings.get('adresse_societe', ''))
            tel_societe = st.text_input("Téléphone", value=settings.get('tel_societe', ''))
            email_societe = st.text_input("Email", value=settings.get('email_societe', ''))
            st.markdown("---")
            st.subheader("Informations Fiscales")
            nif_societe = st.text_input("NIF", value=settings.get('nif_societe', ''))
            stat_societe = st.text_input("STAT", value=settings.get('stat_societe', ''))
            rib_societe = st.text_input("RIB", value=settings.get('rib_societe', ''))
            if st.form_submit_button("Enregistrer"):
                settings_data = {'nom_societe': nom_societe, 'adresse_societe': adresse_societe, 'tel_societe': tel_societe, 'email_societe': email_societe, 'nif_societe': nif_societe, 'stat_societe': stat_societe, 'rib_societe': rib_societe}
                crud.update_settings(db, settings_data)
                st.success("Paramètres enregistrés !")

def page_etats():
    st.header("États & Rapports")
    with st.container(border=True):
        st.subheader("Filtres de Période")
        start_default = datetime.now().date().replace(day=1)
        end_default = datetime.now().date()
        c1, c2 = st.columns(2)
        start_date = c1.date_input("Date de début", value=start_default)
        end_date = c2.date_input("Date de fin", value=end_default)
    if st.button("📊 Générer les Rapports", type="primary", use_container_width=True):
        tab_v, tab_a, tab_s, tab_b = st.tabs(["📈 Ventes", "📥 Achats", "📦 Stock", "💰 Bénéfices"])
        with tab_v:
            st.subheader(f"Rapport Ventes du {start_date.strftime('%d/%m/%Y')} au {end_date.strftime('%d/%m/%Y')}")
            sales = crud.get_sales_in_date_range(db, start_date=start_date, end_date=end_date)
            total_ca = sum(s.total_amount for s in sales)
            c1,c2=st.columns(2); c1.metric("CA Période", f"{total_ca:,.2f} Ar".replace(",", " ")); c2.metric("Nb Ventes", len(sales))
            if sales: st.dataframe([{"ID": s.id, "Date": s.sale_date.strftime('%d/%m/%Y'), "Client": s.client.name if s.client else "Comptoir", "Montant": s.total_amount} for s in sales], use_container_width=True, hide_index=True)
        with tab_a:
            st.subheader(f"Rapport Achats Reçus du {start_date.strftime('%d/%m/%Y')} au {end_date.strftime('%d/%m/%Y')}")
            orders = crud.get_received_orders_in_date_range(db, start_date=start_date, end_date=end_date)
            total_achats = sum(o.total_cost for o in orders)
            c1,c2=st.columns(2); c1.metric("Coût Total Achats", f"{total_achats:,.2f} Ar".replace(",", " ")); c2.metric("Nb Commandes Reçues", len(orders))
            if orders: st.dataframe([{"ID": o.id, "Date Réception": o.reception_date.strftime('%d/%m/%Y'), "Fournisseur": o.supplier.name, "Coût": o.total_cost} for o in orders], use_container_width=True, hide_index=True)
        with tab_s:
            st.subheader("État des Stocks (actuel)")
            products = crud.get_products(db)
            total_val = sum(p.purchase_price * p.stock_quantity for p in products)
            c1,c2=st.columns(2); c1.metric("Valeur Totale Stock", f"{total_val:,.2f} Ar".replace(",", " ")); c2.metric("Nb Références", len(products))
            if products: st.dataframe([{"Produit": p.name, "SKU": p.sku, "Stock": p.stock_quantity, "Valeur": p.purchase_price * p.stock_quantity} for p in products], use_container_width=True, hide_index=True)
        with tab_b:
            st.subheader("Rapport des Bénéfices")
            real_profit = crud.get_realized_profit_in_date_range(db, start_date=start_date, end_date=end_date)
            proj_profit = crud.get_finance_kpis(db).get('projected_profit', 0)
            c1,c2=st.columns(2); c1.metric(f"Bénéfice Réel (période)", f"{real_profit:,.2f} Ar".replace(",", " ")); c2.metric("Bénéfice Prévisionnel (stock)", f"{proj_profit:,.2f} Ar".replace(",", " "))

# --- ROUTAGE PRINCIPAL DE L'INTERFACE ---
if not st.session_state.logged_in:
    st.title("🔩 Quincaillerie PRO - Connexion")
    with st.container(border=True):
        with st.form("login_form"):
            username = st.text_input("Nom d'utilisateur")
            password = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("Se connecter"):
                if not crud.get_user_by_username(db, username="admin"):
                    crud.create_user(db=db, user=schemas.UserCreate(username="admin", password="password123", role="admin"))
                    st.info("Compte 'admin' créé (mdp: password123). Connectez-vous.")
                login(username, password)
else:
    user = st.session_state.current_user
    with st.sidebar:
        # LE SEUL ET UNIQUE ENDROIT POUR LE LOGO
        st.image("assets/logo.svg", width=100)
        st.title(f"Bienvenue, {user.username}")
        st.write(f"Rôle : {user.role.value}")
        
        admin_menu = ["Tableau de Bord", "Finances", "Ventes", "Produits", "Commandes", "Fournisseurs", "Clients", "Personnel", "Paramètres", "États & Rapports"]
        user_menu = ["Ventes", "Produits", "Commandes", "Fournisseurs", "Clients"]
        menu_options = admin_menu if user.role == "admin" else user_menu
        
        st.markdown('<div data-testid="stSidebarNav">', unsafe_allow_html=True)
        for option in menu_options:
            if st.button(option, use_container_width=True, type="primary" if st.session_state.menu_choice == option else "secondary"):
                st.session_state.menu_choice = option
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("---")
        if st.button("Déconnexion", use_container_width=True): logout()
    
    st.header(f"🔩 {st.session_state.get('menu_choice', 'Tableau de Bord')}")
    
    PAGES = {
        "Tableau de Bord": page_dashboard, "Finances": page_finances,
        "Produits": page_produits, "Fournisseurs": page_fournisseurs,
        "Clients": page_clients, "Commandes": page_commandes,
        "Ventes": page_ventes, "Personnel": page_personnel,
        "Paramètres": page_parametres, "États & Rapports": page_etats
    }
    page_function = PAGES.get(st.session_state.menu_choice)
    if page_function:
        page_function()