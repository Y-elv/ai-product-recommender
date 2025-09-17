from sqlalchemy import Column, String, Float, Integer, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from .database import Base
import uuid
from datetime import datetime

class Product(Base):
    __tablename__ = "products"
    
    # Use UUID to match Node.js database structure
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    product_id = Column(String, index=True)  # Original product ID from Node.js system
    name = Column(String, index=True)
    description = Column(Text, nullable=True)
    price = Column(Float)
    stock = Column(Integer, default=0)
    category = Column(String, index=True)
    # User interaction fields
    user_id = Column(String, index=True)  # User ID from your Node.js app
    interaction_weight = Column(Float, default=1.0)  # Weight for different interaction types
    interaction_type = Column(String, index=True)  # 'view', 'click', 'add_to_cart', 'purchase'
    created_at = Column(DateTime, default=datetime.utcnow, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)

class ProductImage(Base):
    __tablename__ = "product_images"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    url = Column(String)
    alt = Column(String)
    is_default = Column(Integer, default=0)  # 0 = false, 1 = true
    product_id = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
