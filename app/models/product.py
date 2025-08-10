"""
Enterprise Product and Business Data Models
Separates structured business data from unstructured document content
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Float, ForeignKey, Boolean, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Product(Base):
    """
    Core product catalog for real-time data
    Used by RAG system for current pricing, availability, specifications
    """
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String, unique=True, index=True)        # "SAM-S24U-256-BLK"
    name = Column(String, index=True)                    # "Samsung Galaxy S24 Ultra 256GB"
    brand = Column(String, index=True)                   # "Samsung"
    category = Column(String, index=True)                # "Smartphones"
    subcategory = Column(String)                         # "Android Flagship"
    
    # Real-time business data
    price_jod = Column(Float)                           # 1299.00
    original_price_jod = Column(Float)                  # 1399.00
    discount_percentage = Column(Float, default=0)      # 7.14
    stock_quantity = Column(Integer, default=0)         # 15
    is_available = Column(Boolean, default=True)
    
    # Product details
    model_number = Column(String)                       # "SM-S928B/DS"
    specifications = Column(JSON)                       # Technical specs
    warranty_months = Column(Integer, default=12)
    
    # Business flags
    is_featured = Column(Boolean, default=False)
    is_promotion = Column(Boolean, default=False)
    promotion_text = Column(String)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    variants = relationship("ProductVariant", back_populates="product")
    supplier_relations = relationship("ProductSupplier", back_populates="product")

class ProductVariant(Base):
    """Product variations (colors, storage, etc.)"""
    __tablename__ = "product_variants"
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    variant_type = Column(String)                       # "color", "storage"
    variant_value = Column(String)                      # "Phantom Black", "256GB"
    sku_suffix = Column(String)                         # "-BLK-256GB"
    price_adjustment = Column(Float, default=0.0)       # +50 JOD for 512GB
    stock_quantity = Column(Integer, default=0)
    
    # Relationship
    product = relationship("Product", back_populates="variants")

class Supplier(Base):
    """Supplier information for business operations"""
    __tablename__ = "suppliers"
    
    id = Column(Integer, primary_key=True)
    name = Column(String)                               # "Samsung Gulf Electronics"
    contact_email = Column(String)
    contact_phone = Column(String)
    country = Column(String)                            # "UAE"
    lead_time_days = Column(Integer)                    # 14
    minimum_order_jod = Column(Float)                   # 50000.00
    payment_terms = Column(String)                      # "Net 45"
    
    # Relationships
    product_relations = relationship("ProductSupplier", back_populates="supplier")

class ProductSupplier(Base):
    """Many-to-many relationship between products and suppliers"""
    __tablename__ = "product_suppliers"
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    supplier_sku = Column(String)                       # Supplier's internal SKU
    cost_price_jod = Column(Float)                      # Our cost
    last_order_date = Column(DateTime(timezone=True))
    
    # Relationships
    product = relationship("Product", back_populates="supplier_relations")
    supplier = relationship("Supplier", back_populates="product_relations")

class ServiceOffering(Base):
    """Services provided by the store"""
    __tablename__ = "service_offerings"
    
    id = Column(Integer, primary_key=True)
    service_name = Column(String)                       # "AC Installation"
    category = Column(String)                           # "Installation"
    description = Column(Text)
    base_price_jod = Column(Float)                      # 120.00
    duration_hours = Column(Float)                      # 3.5
    requirements = Column(JSON)                         # Prerequisites
    available_for_products = Column(JSON)               # Product categories
    
class StoreLocation(Base):
    """Physical store information"""
    __tablename__ = "store_locations"
    
    id = Column(Integer, primary_key=True)
    name = Column(String)                               # "TechMart Nablus Main"
    address = Column(Text)
    phone = Column(String)
    email = Column(String)
    manager_name = Column(String)
    opening_hours = Column(JSON)                        # Structured hours
    services_offered = Column(JSON)                     # Available services
    delivery_zones = Column(JSON)                       # Coverage areas

class DocumentMetadata(Base):
    """Enhanced metadata for RAG document management"""
    __tablename__ = "document_metadata"
    
    id = Column(Integer, primary_key=True)
    
    # Document identification
    filename = Column(String, index=True)
    document_type = Column(String, index=True)          # "policy", "manual", "faq"
    title = Column(String)
    version = Column(String)                            # "2.1"
    document_id = Column(String, unique=True)           # "TMP-CS-POL-2.1"
    
    # Content classification
    department = Column(String)                         # "customer_service"
    audience = Column(String)                           # "customers"
    language = Column(String, index=True)               # "en", "ar", "bilingual"
    
    # Business context
    products_covered = Column(JSON)                     # ["smartphones", "laptops"]
    services_covered = Column(JSON)                     # ["delivery", "installation"]
    geographic_scope = Column(String)                   # "nablus"
    
    # Document lifecycle
    author = Column(String)
    reviewer = Column(String)
    approval_status = Column(String)                    # "approved"
    effective_date = Column(DateTime(timezone=True))
    expiry_date = Column(DateTime(timezone=True))
    
    # RAG optimization
    keyword_tags = Column(JSON)                         # ["return", "warranty"]
    content_summary = Column(Text)
    target_queries = Column(JSON)                       # Expected questions
    related_documents = Column(JSON)                    # Related doc IDs
    
    # Processing status
    indexing_status = Column(String, default="pending")
    total_chunks = Column(Integer)
    embedding_model = Column(String)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_indexed = Column(DateTime(timezone=True))

class QueryAnalytics(Base):
    """Track RAG performance and optimize responses"""
    __tablename__ = "query_analytics"
    
    id = Column(Integer, primary_key=True)
    
    # Query information
    user_query = Column(Text, index=True)
    normalized_query = Column(String)
    query_intent = Column(String)                       # "product_info", "policy"
    query_language = Column(String)
    
    # RAG response metrics
    documents_retrieved = Column(Integer)
    top_similarity_score = Column(Float)
    documents_used = Column(JSON)
    confidence_score = Column(Float)
    response_time_ms = Column(Integer)
    
    # Database queries made
    products_queried = Column(JSON)                     # Product IDs referenced
    services_queried = Column(JSON)                     # Service IDs referenced
    
    # User interaction
    session_id = Column(String, index=True)
    user_satisfaction = Column(Integer)                 # 1-5 rating
    follow_up_query = Column(Text)
    
    # Business context
    resulted_in_sale = Column(Boolean)
    product_categories_mentioned = Column(JSON)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())