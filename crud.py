from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract
from datetime import datetime, date
from . import models, schemas
from passlib.context import CryptContext

# ... (Toutes les fonctions jusqu'à get_sales_by_client sont identiques)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(username=user.username, hashed_password=hashed_password, role=user.role)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
    
def get_product(db: Session, product_id: int):
    return db.query(models.Product).filter(models.Product.id == product_id).first()

def get_products(db: Session, skip: int = 0, limit: int = 1000):
    return db.query(models.Product).order_by(models.Product.name).offset(skip).limit(limit).all()

def create_product(db: Session, product: schemas.ProductCreate):
    db_product = models.Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def update_product(db: Session, product_id: int, product_update: schemas.ProductUpdate):
    db_product = get_product(db, product_id)
    if not db_product: return None
    update_data = product_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            setattr(db_product, key, value)
    db.commit()
    db.refresh(db_product)
    return db_product

def get_supplier(db: Session, supplier_id: int):
    return db.query(models.Supplier).filter(models.Supplier.id == supplier_id).first()

def get_suppliers(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Supplier).order_by(models.Supplier.name).offset(skip).limit(limit).all()

def create_supplier(db: Session, supplier: schemas.SupplierCreate):
    db_supplier = models.Supplier(**supplier.model_dump())
    db.add(db_supplier)
    db.commit()
    db.refresh(db_supplier)
    return db_supplier
    
def update_supplier(db: Session, supplier_id: int, supplier_update: schemas.SupplierUpdate):
    db_supplier = get_supplier(db, supplier_id)
    if not db_supplier: return None
    update_data = supplier_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_supplier, key, value)
    db.commit()
    db.refresh(db_supplier)
    return db_supplier

def delete_supplier(db: Session, supplier_id: int):
    db_supplier = get_supplier(db, supplier_id)
    if not db_supplier: return None
    if db_supplier.products:
        raise ValueError("Impossible de supprimer. Ce fournisseur est lié à des produits.")
    db.delete(db_supplier)
    db.commit()
    return db_supplier

def get_client(db: Session, client_id: int):
    return db.query(models.Client).filter(models.Client.id == client_id).first()
    
def get_clients(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Client).order_by(models.Client.name).offset(skip).limit(limit).all()

def create_client(db: Session, client: schemas.ClientCreate):
    db_client = models.Client(**client.model_dump())
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client

def update_client(db: Session, client_id: int, client_update: schemas.ClientUpdate):
    db_client = get_client(db, client_id)
    if not db_client: return None
    update_data = client_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_client, key, value)
    db.commit()
    db.refresh(db_client)
    return db_client

def delete_client(db: Session, client_id: int):
    db_client = get_client(db, client_id)
    if not db_client: return None
    if db_client.sales:
        raise ValueError("Impossible de supprimer. Ce client est lié à des ventes.")
    db.delete(db_client)
    db.commit()
    return db_client

def create_sale(db: Session, sale: schemas.SaleCreate, user_id: int):
    total_amount = 0
    for item in sale.items:
        product = get_product(db, item.product_id)
        if not product or product.stock_quantity < item.quantity:
            raise ValueError(f"Stock insuffisant pour le produit: {product.name if product else 'ID inconnu'}")
        price_to_use = product.promo_price if product.promo_price and product.promo_price > 0 else product.selling_price
        total_amount += price_to_use * item.quantity
        item.price_per_unit = price_to_use
    db_sale = models.Sale(total_amount=total_amount, payment_method=sale.payment_method, status=sale.status, client_id=sale.client_id, user_id=user_id)
    db.add(db_sale)
    db.flush()
    for item in sale.items:
        db_sale_item = models.SaleItem(quantity=item.quantity, price_per_unit=item.price_per_unit, sale_id=db_sale.id, product_id=item.product_id)
        db.add(db_sale_item)
        product = get_product(db, item.product_id)
        product.stock_quantity -= item.quantity
    db.commit()
    db.refresh(db_sale)
    return db_sale

def get_sales(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Sale).order_by(models.Sale.sale_date.desc()).offset(skip).limit(limit).all()

def get_sale(db: Session, sale_id: int):
    return db.query(models.Sale).filter(models.Sale.id == sale_id).first()

def get_sales_by_client(db: Session, client_id: int):
    return db.query(models.Sale).filter(models.Sale.client_id == client_id).order_by(models.Sale.sale_date.desc()).all()

# --- MODIFICATION DE LA FONCTION ---
def settle_credit_sale(db: Session, sale_id: int, payment_method: str):
    db_sale = get_sale(db, sale_id)
    if not db_sale: return None
    db_sale.status = models.SaleStatus.PAYEE
    db_sale.payment_method = payment_method # On met à jour le mode de paiement
    db.commit()
    db.refresh(db_sale)
    return db_sale

def create_purchase_order(db: Session, order: schemas.PurchaseOrderCreate):
    total_cost = sum(item.purchase_price_per_unit * item.quantity for item in order.items)
    db_order = models.PurchaseOrder(total_cost=total_cost, supplier_id=order.supplier_id, status=models.OrderStatus.EN_COURS)
    db.add(db_order)
    db.flush()
    for item in order.items:
        db_order_item = models.PurchaseOrderItem(quantity=item.quantity, purchase_price_per_unit=item.purchase_price_per_unit, order_id=db_order.id, product_id=item.product_id)
        db.add(db_order_item)
    db.commit()
    db.refresh(db_order)
    return db_order

def get_purchase_orders(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.PurchaseOrder).order_by(models.PurchaseOrder.order_date.desc()).offset(skip).limit(limit).all()

def get_orders_by_supplier(db: Session, supplier_id: int):
    return db.query(models.PurchaseOrder).filter(models.PurchaseOrder.supplier_id == supplier_id).order_by(models.PurchaseOrder.order_date.desc()).all()

def receive_purchase_order(db: Session, order_id: int):
    db_order = db.query(models.PurchaseOrder).filter(models.PurchaseOrder.id == order_id).first()
    if not db_order or db_order.status == models.OrderStatus.RECUE: return None
    for item in db_order.items:
        product = get_product(db, item.product_id)
        if product: product.stock_quantity += item.quantity
    db_order.status = models.OrderStatus.RECUE
    db_order.reception_date = datetime.now()
    db.commit()
    db.refresh(db_order)
    return db_order

def get_settings(db: Session):
    settings = db.query(models.Setting).all()
    return {s.key: s.value for s in settings}

def update_settings(db: Session, settings_data: dict):
    for key, value in settings_data.items():
        db_setting = db.query(models.Setting).filter(models.Setting.key == key).first()
        if db_setting:
            db_setting.value = str(value)
        else:
            db_setting = models.Setting(key=key, value=str(value))
            db.add(db_setting)
    db.commit()
    return get_settings(db)

def get_dashboard_kpis(db: Session):
    today = date.today()
    start_of_today = datetime.combine(today, datetime.min.time())
    ca_jour = db.query(func.sum(models.Sale.total_amount)).filter(models.Sale.sale_date >= start_of_today).scalar() or 0
    nb_ventes = db.query(func.count(models.Sale.id)).filter(models.Sale.sale_date >= start_of_today).scalar() or 0
    valeur_stock_query = db.query(func.sum(models.Product.purchase_price * models.Product.stock_quantity)).scalar()
    valeur_stock = valeur_stock_query or 0
    total_achats = db.query(func.sum(models.PurchaseOrder.total_cost)).filter(models.PurchaseOrder.status == models.OrderStatus.RECUE).scalar() or 0
    return {"kpi_ca_jour": ca_jour, "kpi_nb_ventes": nb_ventes, "kpi_valeur_stock": valeur_stock, "kpi_total_achats": total_achats}

def get_low_stock_products(db: Session, threshold: int = 10):
    return db.query(models.Product).filter(and_(models.Product.stock_quantity > 0, models.Product.stock_quantity < threshold)).all()

def get_finance_kpis(db: Session):
    today = date.today()
    start_of_today = datetime.combine(today, datetime.min.time())
    projected_profit_query = db.query(func.sum((models.Product.selling_price - models.Product.purchase_price) * models.Product.stock_quantity)).scalar()
    projected_profit = projected_profit_query or 0
    today_sales_items = db.query(models.SaleItem).join(models.Sale).filter(models.Sale.sale_date >= start_of_today).all()
    real_profit_today = sum((item.price_per_unit - item.product.purchase_price) * item.quantity for item in today_sales_items if item.product)
    total_credits_query = db.query(func.sum(models.Sale.total_amount)).filter(models.Sale.status == models.SaleStatus.CREDIT).scalar()
    total_credits = total_credits_query or 0
    return {"projected_profit": projected_profit, "real_profit_today": real_profit_today, "total_credits": total_credits}

def get_monthly_sales_chart_data(db: Session, year: int):
    sales_data = db.query(extract('month', models.Sale.sale_date).label('month'), func.sum(models.Sale.total_amount).label('total')).filter(extract('year', models.Sale.sale_date) == year).group_by('month').all()
    monthly_totals = [0.0] * 12
    for row in sales_data:
        monthly_totals[int(row.month) - 1] = float(row.total)
    return monthly_totals

def get_sales_in_date_range(db: Session, start_date: date, end_date: date):
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    return db.query(models.Sale).filter(models.Sale.sale_date.between(start_datetime, end_datetime)).all()

def get_received_orders_in_date_range(db: Session, start_date: date, end_date: date):
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    return db.query(models.PurchaseOrder).filter(
        models.PurchaseOrder.status == models.OrderStatus.RECUE,
        models.PurchaseOrder.reception_date.between(start_datetime, end_datetime)
    ).all()

def get_realized_profit_in_date_range(db: Session, start_date: date, end_date: date):
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    sales_items = db.query(models.SaleItem).join(models.Sale).filter(
        models.Sale.sale_date.between(start_datetime, end_datetime)
    ).all()
    real_profit = sum(
        (item.price_per_unit - (item.product.purchase_price if item.product else 0)) * item.quantity
        for item in sales_items
    )
    return real_profit
