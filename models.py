import enum
from sqlalchemy import (
    Boolean, Column, ForeignKey, Integer, String, Float, DateTime, Enum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

# Définition des rôles et statuts en tant qu'Enums pour la cohérence
class UserRole(str, enum.Enum):
    ADMIN = "admin"
    PERSONNEL = "personnel"

class ClientType(str, enum.Enum):
    PARTICULIER = "Particulier"
    PROFESSIONNEL = "Professionnel"

class SaleStatus(str, enum.Enum):
    PAYEE = "payee"
    CREDIT = "credit"

class OrderStatus(str, enum.Enum):
    EN_COURS = "en-cours"
    RECUE = "recue"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.PERSONNEL)
    is_active = Column(Boolean, default=True)

    sales = relationship("Sale", back_populates="user")

class Supplier(Base):
    __tablename__ = "suppliers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    contact_person = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    address = Column(String, nullable=True)

    products = relationship("Product", back_populates="supplier")
    purchase_orders = relationship("PurchaseOrder", back_populates="supplier")

class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    type = Column(Enum(ClientType), nullable=False, default=ClientType.PARTICULIER)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    address = Column(String, nullable=True)
    nif = Column(String, nullable=True)
    stat = Column(String, nullable=True)

    sales = relationship("Sale", back_populates="client")

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, index=True, nullable=False)
    category = Column(String, index=True, nullable=True, default="Non classé")
    purchase_price = Column(Float, nullable=False)
    selling_price = Column(Float, nullable=False)
    promo_price = Column(Float, nullable=True)
    stock_quantity = Column(Float, nullable=False, default=0)
    unit = Column(String, nullable=True, default="Unité")
    image_url = Column(String, nullable=True)
    
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    
    supplier = relationship("Supplier", back_populates="products")
    sale_items = relationship("SaleItem", back_populates="product")
    purchase_order_items = relationship("PurchaseOrderItem", back_populates="product")

class Sale(Base):
    __tablename__ = "sales"
    id = Column(Integer, primary_key=True, index=True)
    sale_date = Column(DateTime(timezone=True), server_default=func.now())
    total_amount = Column(Float, nullable=False)
    payment_method = Column(String, nullable=False)
    status = Column(Enum(SaleStatus), nullable=False, default=SaleStatus.PAYEE)
    
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    client = relationship("Client", back_populates="sales")
    user = relationship("User", back_populates="sales")
    items = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")

class SaleItem(Base):
    __tablename__ = "sale_items"
    id = Column(Integer, primary_key=True, index=True)
    quantity = Column(Float, nullable=False)
    price_per_unit = Column(Float, nullable=False)
    
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    sale = relationship("Sale", back_populates="items")
    product = relationship("Product", back_populates="sale_items")

class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    id = Column(Integer, primary_key=True, index=True)
    order_date = Column(DateTime(timezone=True), server_default=func.now())
    reception_date = Column(DateTime(timezone=True), nullable=True)
    total_cost = Column(Float, nullable=False)
    status = Column(Enum(OrderStatus), nullable=False, default=OrderStatus.EN_COURS)
    
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    
    supplier = relationship("Supplier", back_populates="purchase_orders")
    items = relationship("PurchaseOrderItem", back_populates="order", cascade="all, delete-orphan")

class PurchaseOrderItem(Base):
    __tablename__ = "purchase_order_items"
    id = Column(Integer, primary_key=True, index=True)
    quantity = Column(Float, nullable=False)
    purchase_price_per_unit = Column(Float, nullable=False)
    
    order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    order = relationship("PurchaseOrder", back_populates="items")
    product = relationship("Product", back_populates="purchase_order_items")

class Setting(Base):
    __tablename__ = "settings"
    key = Column(String, primary_key=True, index=True)
    value = Column(String, nullable=True)
