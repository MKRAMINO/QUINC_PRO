from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from .models import UserRole, ClientType, SaleStatus, OrderStatus

# Schemas pour l'Authentification et les Utilisateurs
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserBase(BaseModel):
    username: str
    role: UserRole

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True

# Schemas pour les Fournisseurs
class SupplierBase(BaseModel):
    name: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None

class SupplierCreate(SupplierBase):
    pass

class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None

class Supplier(SupplierBase):
    id: int

    class Config:
        from_attributes = True

# Schemas pour les Clients
class ClientBase(BaseModel):
    name: str
    type: ClientType
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    nif: Optional[str] = None
    stat: Optional[str] = None

class ClientCreate(ClientBase):
    pass

class ClientUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[ClientType] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    nif: Optional[str] = None
    stat: Optional[str] = None

class Client(ClientBase):
    id: int

    class Config:
        from_attributes = True

# Schemas pour les Produits
class ProductBase(BaseModel):
    sku: str
    name: str
    category: Optional[str] = "Non classé"
    purchase_price: float = Field(..., gt=0)
    selling_price: float = Field(..., gt=0)
    promo_price: Optional[float] = Field(None, gt=0)
    stock_quantity: float = Field(..., ge=0)
    unit: Optional[str] = "Unité"
    image_url: Optional[str] = None
    supplier_id: Optional[int] = None

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    purchase_price: Optional[float] = Field(None, gt=0)
    selling_price: Optional[float] = Field(None, gt=0)
    promo_price: Optional[float] = Field(None, gt=0)
    stock_quantity: Optional[float] = Field(None, ge=0)
    unit: Optional[str] = None
    image_url: Optional[str] = None
    supplier_id: Optional[int] = None

class Product(ProductBase):
    id: int
    supplier: Optional[Supplier] = None # Afficher le fournisseur lié

    class Config:
        from_attributes = True

# Schemas pour les Ventes
class SaleItemBase(BaseModel):
    product_id: int
    quantity: float = Field(..., gt=0)
    price_per_unit: float

class SaleItemCreate(SaleItemBase):
    pass

class SaleItem(SaleItemBase):
    id: int
    product: Product # Afficher le produit détaillé dans l'item de vente

    class Config:
        from_attributes = True

class SaleBase(BaseModel):
    total_amount: float
    payment_method: str
    status: SaleStatus
    client_id: Optional[int] = None
    user_id: int

class SaleCreate(BaseModel):
    payment_method: str
    status: SaleStatus
    client_id: Optional[int] = None
    items: List[SaleItemCreate]

class Sale(SaleBase):
    id: int
    sale_date: datetime
    client: Optional[Client] = None
    user: User
    items: List[SaleItem] = []

    class Config:
        from_attributes = True
        
# Schemas pour les Commandes Fournisseurs
class PurchaseOrderItemBase(BaseModel):
    product_id: int
    quantity: float = Field(..., gt=0)
    purchase_price_per_unit: float

class PurchaseOrderItemCreate(PurchaseOrderItemBase):
    pass

class PurchaseOrderItem(PurchaseOrderItemBase):
    id: int
    product: Product

    class Config:
        from_attributes = True

class PurchaseOrderBase(BaseModel):
    total_cost: float
    status: OrderStatus
    supplier_id: int

class PurchaseOrderCreate(BaseModel):
    supplier_id: int
    items: List[PurchaseOrderItemCreate]

class PurchaseOrder(PurchaseOrderBase):
    id: int
    order_date: datetime
    reception_date: Optional[datetime] = None
    supplier: Supplier
    items: List[PurchaseOrderItem] = []

    class Config:
        from_attributes = True

# Schemas pour les Paramètres
class SettingBase(BaseModel):
    key: str
    value: Optional[str] = None

class SettingCreate(SettingBase):
    pass

class Setting(SettingBase):
    class Config:
        from_attributes = True
