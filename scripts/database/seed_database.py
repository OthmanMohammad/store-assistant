"""
Comprehensive Database Seeding Script
Populates database with realistic business data matching PDF documents
"""

import sys
import os
import json
from datetime import datetime, timedelta
from decimal import Decimal

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database import SessionLocal, create_tables
from app.models.product import (
    Product, ProductVariant, Supplier, ProductSupplier, 
    ServiceOffering, StoreLocation, DocumentMetadata
)

def create_suppliers_data():
    """Create supplier data matching the PDF documents"""
    return [
        {
            "name": "Samsung Gulf Electronics LLC",
            "contact_email": "palestine@samsung-gulf.com",
            "contact_phone": "+971-4-123-4567",
            "country": "UAE",
            "lead_time_days": 12,
            "minimum_order_jod": 50000.0,
            "payment_terms": "Net 45 days, 2% early payment discount"
        },
        {
            "name": "Apple Middle East FZE",
            "contact_email": "palestine@apple-me.com",
            "contact_phone": "+971-4-567-8901", 
            "country": "UAE",
            "lead_time_days": 18,
            "minimum_order_jod": 75000.0,
            "payment_terms": "Net 30 days, LC required"
        },
        {
            "name": "LG Electronics Levant",
            "contact_email": "palestine@lge.com",
            "contact_phone": "+962-6-123-4567",
            "country": "Jordan",
            "lead_time_days": 8,
            "minimum_order_jod": 25000.0,
            "payment_terms": "Net 60 days"
        },
        {
            "name": "Sony Gulf FZE",
            "contact_email": "palestine@sony-gulf.com",
            "contact_phone": "+971-4-789-0123",
            "country": "UAE", 
            "lead_time_days": 10,
            "minimum_order_jod": 30000.0,
            "payment_terms": "Net 30 days"
        },
        {
            "name": "HP Gulf LLC",
            "contact_email": "palestine@hp-gulf.com",
            "contact_phone": "+971-4-456-7890",
            "country": "UAE",
            "lead_time_days": 7,
            "minimum_order_jod": 40000.0,
            "payment_terms": "Net 30 days"
        }
    ]

def create_products_data():
    """Create comprehensive product catalog matching PDF specifications"""
    return [
        # SMARTPHONES
        {
            "sku": "APL-IP15PM-256-TIT",
            "name": "iPhone 15 Pro Max 256GB Natural Titanium",
            "brand": "Apple",
            "category": "Smartphones",
            "subcategory": "iOS Flagship",
            "price_jod": 1899.00,
            "original_price_jod": 1999.00,
            "discount_percentage": 5.0,
            "stock_quantity": 12,
            "model_number": "A3108",
            "specifications": {
                "display": "6.7\" Super Retina XDR OLED, 2796×1290, 120Hz ProMotion",
                "processor": "A17 Pro chip (3nm), 6-core CPU, 6-core GPU",
                "ram": "8GB unified memory",
                "storage": "256GB (non-expandable)",
                "camera": "48MP main (f/1.78) + 12MP ultra-wide (f/2.2) + 12MP telephoto (f/2.8, 3x zoom)",
                "battery": "4441mAh, MagSafe wireless charging, USB-C",
                "os": "iOS 17 (upgradeable to iOS 21)",
                "features": ["Face ID", "IP68", "5G", "WiFi 6E", "Bluetooth 5.3"],
                "dimensions": "159.9 × 76.7 × 8.25 mm, 221g",
                "colors": ["Natural Titanium", "Blue Titanium", "White Titanium", "Black Titanium"]
            },
            "warranty_months": 12,
            "is_featured": True,
            "is_promotion": True,
            "promotion_text": "Trade-in your old iPhone and save up to 300 JOD"
        },
        {
            "sku": "APL-IP15-128-PNK", 
            "name": "iPhone 15 128GB Pink",
            "brand": "Apple",
            "category": "Smartphones",
            "subcategory": "iOS Standard",
            "price_jod": 1299.00,
            "original_price_jod": 1299.00,
            "discount_percentage": 0.0,
            "stock_quantity": 18,
            "model_number": "A3090",
            "specifications": {
                "display": "6.1\" Super Retina XDR OLED, 2556×1179, 60Hz",
                "processor": "A16 Bionic chip, 6-core CPU, 5-core GPU",
                "ram": "6GB",
                "storage": "128GB",
                "camera": "48MP main (f/1.6) + 12MP ultra-wide (f/2.4)",
                "battery": "3349mAh, MagSafe/Qi wireless charging",
                "colors": ["Pink", "Yellow", "Green", "Blue", "Black"]
            },
            "warranty_months": 12,
            "is_featured": True,
            "is_promotion": False
        },
        {
            "sku": "SAM-S24U-512-TBK",
            "name": "Samsung Galaxy S24 Ultra 512GB Titanium Black", 
            "brand": "Samsung",
            "category": "Smartphones",
            "subcategory": "Android Flagship",
            "price_jod": 1599.00,
            "original_price_jod": 1699.00,
            "discount_percentage": 5.88,
            "stock_quantity": 15,
            "model_number": "SM-S928B/DS",
            "specifications": {
                "display": "6.8\" Dynamic AMOLED 2X, 3120×1440, 120Hz adaptive",
                "processor": "Snapdragon 8 Gen 3 for Galaxy (4nm)",
                "ram": "12GB LPDDR5X",
                "storage": "512GB UFS 4.0",
                "camera": "200MP main (f/1.7, OIS) + 50MP periscope (f/3.4, 5x zoom) + 10MP telephoto (f/2.4, 3x zoom) + 12MP ultra-wide (f/2.2)",
                "battery": "5000mAh, 45W fast charging, 15W wireless",
                "os": "Android 14, One UI 6.1, 7 years updates",
                "features": ["S Pen included", "IP68", "5G", "WiFi 7", "Bluetooth 5.3"],
                "dimensions": "162.3 × 79.0 × 8.6 mm, 232g"
            },
            "warranty_months": 24,
            "is_featured": True,
            "is_promotion": True,
            "promotion_text": "Back to School: Free Galaxy Buds2 Pro + S Pen Case"
        },
        
        # LAPTOPS
        {
            "sku": "HP-EB840-G10-I7",
            "name": "HP EliteBook 840 G10 Business Laptop",
            "brand": "HP", 
            "category": "Laptops",
            "subcategory": "Business",
            "price_jod": 1899.00,
            "original_price_jod": 1899.00,
            "discount_percentage": 0.0,
            "stock_quantity": 8,
            "model_number": "5Y2K8EA",
            "specifications": {
                "display": "14\" WUXGA (1920×1200) IPS, anti-glare",
                "processor": "Intel Core i7-1355U (10-core, up to 5.0GHz)",
                "ram": "16GB DDR5-5600",
                "storage": "512GB PCIe Gen4 NVMe SSD",
                "graphics": "Intel Iris Xe integrated",
                "ports": ["2x Thunderbolt 4", "2x USB-A 3.2", "HDMI 2.1", "RJ45"],
                "battery": "51Wh, up to 12.5 hours",
                "os": "Windows 11 Pro",
                "security": ["TPM 2.0", "fingerprint reader", "IR camera"],
                "weight": "1.36kg"
            },
            "warranty_months": 36,
            "is_featured": True,
            "is_promotion": False
        },
        {
            "sku": "ASUS-ROGG18-RTX4070",
            "name": "ASUS ROG Strix G18 Gaming Laptop RTX 4070",
            "brand": "ASUS",
            "category": "Laptops", 
            "subcategory": "Gaming",
            "price_jod": 2799.00,
            "original_price_jod": 2999.00,
            "discount_percentage": 6.67,
            "stock_quantity": 6,
            "model_number": "G814JV-N6022W",
            "specifications": {
                "display": "18\" QHD+ (2560×1600) IPS, 240Hz, 3ms",
                "processor": "Intel Core i7-13650HX (14-core, up to 4.9GHz)",
                "ram": "16GB DDR5-4800 (expandable to 32GB)",
                "storage": "1TB PCIe 4.0 NVMe SSD",
                "graphics": "NVIDIA GeForce RTX 4070 8GB GDDR6",
                "cooling": "ROG Intelligent Cooling with liquid metal",
                "keyboard": "Per-key RGB, 1.7mm travel",
                "audio": "Dolby Atmos, quad speakers",
                "ports": ["USB 3.2 Gen2 Type-C", "3x USB 3.2 Type-A", "HDMI 2.1"],
                "weight": "3.0kg"
            },
            "warranty_months": 24,
            "is_featured": True,
            "is_promotion": True,
            "promotion_text": "Gaming Bundle: Free gaming mouse + headset worth 200 JOD"
        },
        
        # HOME APPLIANCES
        {
            "sku": "SAM-RF28T-SS",
            "name": "Samsung RF28T5001SR French Door Refrigerator",
            "brand": "Samsung",
            "category": "Home Appliances",
            "subcategory": "Refrigerators",
            "price_jod": 2199.00,
            "original_price_jod": 2199.00,
            "discount_percentage": 0.0,
            "stock_quantity": 4,
            "model_number": "RF28T5001SR/AA",
            "specifications": {
                "capacity": "28 cubic feet (793 liters)",
                "configuration": "French door with bottom freezer",
                "cooling": "Twin Cooling Plus technology",
                "features": ["Ice maker", "water dispenser", "LED lighting"],
                "energy_rating": "Energy Star certified",
                "dimensions": "91.4 × 70.5 × 177.8 cm",
                "finish": "Stainless steel with fingerprint-resistant coating"
            },
            "warranty_months": 24,
            "is_featured": False,
            "is_promotion": False
        },
        {
            "sku": "GRE-LIVO18-INV",
            "name": "Gree Livo+ 18,000 BTU Split AC with WiFi",
            "brand": "Gree",
            "category": "Home Appliances",
            "subcategory": "Air Conditioners",
            "price_jod": 899.00,
            "original_price_jod": 999.00,
            "discount_percentage": 10.01,
            "stock_quantity": 25,
            "model_number": "GWH18AAD-K6DNA1A",
            "specifications": {
                "cooling_capacity": "18,000 BTU/hr (5.27 kW)",
                "technology": "Inverter technology for energy efficiency",
                "energy_rating": "A++ energy class",
                "refrigerant": "R32 eco-friendly gas",
                "features": ["WiFi control", "self-cleaning function"],
                "operating_range": "-15°C to +50°C outdoor temperature",
                "indoor_unit_dimensions": "84.5 × 30.5 × 20.6 cm",
                "outdoor_unit_dimensions": "84.8 × 70.0 × 30.0 cm"
            },
            "warranty_months": 24,
            "is_featured": True,
            "is_promotion": True,
            "promotion_text": "Summer Ready: 100 JOD off + Free Installation"
        },
        
        # AUDIO & GAMING
        {
            "sku": "SON-WH1000XM5-BLK",
            "name": "Sony WH-1000XM5 Wireless Noise Canceling Headphones",
            "brand": "Sony",
            "category": "Audio",
            "subcategory": "Headphones",
            "price_jod": 549.00,
            "original_price_jod": 549.00,
            "discount_percentage": 0.0,
            "stock_quantity": 20,
            "model_number": "WH-1000XM5/B",
            "specifications": {
                "driver": "30mm dynamic drivers",
                "noise_canceling": "Industry-leading dual noise sensor technology",
                "battery": "Up to 30 hours with ANC, 40 hours without",
                "quick_charge": "3 minutes charge = 3 hours playback",
                "connectivity": "Bluetooth 5.2, multipoint connection",
                "codec_support": ["LDAC", "AAC", "SBC"],
                "features": ["Speak-to-Chat", "adaptive sound control"],
                "weight": "250g",
                "colors": ["Black", "Silver"]
            },
            "warranty_months": 24,
            "is_featured": True,
            "is_promotion": False
        },
        {
            "sku": "SON-PS5-SLIM-825",
            "name": "Sony PlayStation 5 Slim Console",
            "brand": "Sony",
            "category": "Gaming",
            "subcategory": "Consoles",
            "price_jod": 799.00,
            "original_price_jod": 799.00,
            "discount_percentage": 0.0,
            "stock_quantity": 10,
            "model_number": "CFI-2000A01",
            "specifications": {
                "processor": "Custom AMD Zen 2 8-core CPU @ 3.5GHz",
                "graphics": "Custom AMD RDNA 2 GPU, 10.28 TFLOPs",
                "memory": "16GB GDDR6",
                "storage": "825GB custom NVMe SSD (expandable)",
                "optical_drive": "4K UHD Blu-ray drive",
                "connectivity": ["WiFi 6", "Bluetooth 5.1", "Gigabit Ethernet"],
                "ports": ["USB-A (2x)", "USB-C (1x)", "HDMI 2.1"],
                "controller": "DualSense wireless controller included",
                "dimensions": "35.8 × 21.6 × 9.6 cm (30% smaller than original)",
                "features": ["3D audio", "haptic feedback", "ray tracing"]
            },
            "warranty_months": 12,
            "is_featured": True,
            "is_promotion": False
        }
    ]

def create_services_data():
    """Create service offerings matching the PDF procedures"""
    return [
        {
            "service_name": "Split AC Installation",
            "category": "Installation",
            "description": "Professional installation of split AC units including wall mounting, electrical connections, refrigerant line setup, and system testing with 2-year installation warranty",
            "base_price_jod": 120.00,
            "duration_hours": 3.5,
            "requirements": {
                "wall_type": "concrete or brick wall capable of supporting unit weight",
                "electrical": "220V 20A dedicated circuit with proper grounding",
                "access": "clear access path for equipment and 3-meter standard piping",
                "preparation": "customer must ensure clear work area and remove obstacles"
            },
            "available_for_products": ["Air Conditioners"]
        },
        {
            "service_name": "Washing Machine Setup & Installation",
            "category": "Installation",
            "description": "Complete washing machine installation including water supply connection, drain hose setup, machine leveling, and test cycle with old unit removal service available",
            "base_price_jod": 50.00,
            "duration_hours": 1.5,
            "requirements": {
                "water_supply": "standard 3/4 inch hot and cold water connections",
                "drainage": "floor drain or utility sink within 2 meters",
                "electrical": "standard 110V grounded outlet",
                "space": "minimum 60cm clearance on all sides"
            },
            "available_for_products": ["Washing Machines", "Washer-Dryer Combos"]
        },
        {
            "service_name": "Smart TV Wall Mounting",
            "category": "Installation",
            "description": "Professional TV wall mounting service including bracket installation, cable management, and setup of smart features with tilt and swivel adjustment",
            "base_price_jod": 45.00,
            "duration_hours": 2.0,
            "requirements": {
                "wall_type": "drywall with studs or concrete/brick wall",
                "bracket": "wall mount bracket sold separately or customer provided",
                "electrical": "nearby power outlet and cable access",
                "tools": "all mounting hardware and tools provided by technician"
            },
            "available_for_products": ["Televisions", "Smart Displays"]
        },
        {
            "service_name": "Smartphone Data Transfer & Setup",
            "category": "Setup",
            "description": "Complete data transfer from old device including contacts, photos, apps, and settings configuration with cloud backup setup and security features activation",
            "base_price_jod": 25.00,
            "duration_hours": 1.0,
            "requirements": {
                "old_device": "functional device with access to unlock code",
                "accounts": "Apple ID, Google account, or Samsung account credentials",
                "backup": "sufficient cloud storage or local backup option",
                "time": "1-3 hours depending on data volume"
            },
            "available_for_products": ["Smartphones", "Tablets"]
        },
        {
            "service_name": "Gaming Setup & Optimization",
            "category": "Setup",
            "description": "Complete gaming system setup including hardware assembly, software installation, performance optimization, and gaming account configuration with accessories setup",
            "base_price_jod": 40.00,
            "duration_hours": 2.0,
            "requirements": {
                "internet": "high-speed internet required for downloads and updates",
                "space": "adequate ventilation and setup space for equipment",
                "accounts": "gaming platform accounts (Steam, PlayStation, Xbox)",
                "games": "customer provided game titles and subscriptions"
            },
            "available_for_products": ["Gaming Laptops", "Gaming Consoles", "Gaming PCs"]
        },
        {
            "service_name": "TechProtect Extended Warranty",
            "category": "Protection",
            "description": "Comprehensive extended warranty coverage including accidental damage protection, technical support, and priority repair service with genuine parts guarantee",
            "base_price_jod": 0.00,  # Calculated as percentage of product price
            "duration_hours": 0.0,
            "requirements": {
                "timing": "must be purchased within 30 days of product purchase",
                "inspection": "device inspection required for high-value items over 1000 JOD",
                "registration": "product registration and serial number verification",
                "terms": "subject to terms and conditions document"
            },
            "available_for_products": ["All Electronics"]
        },
        {
            "service_name": "Home Delivery Service",
            "category": "Delivery",
            "description": "Professional delivery service with scheduled time windows, careful handling, and white-glove service available for large appliances with assembly service",
            "base_price_jod": 15.00,
            "duration_hours": 0.5,
            "requirements": {
                "access": "clear delivery path and accessible entrance",
                "recipient": "adult recipient must be present for delivery",
                "inspection": "immediate inspection and acceptance required",
                "scheduling": "24-48 hour advance scheduling required"
            },
            "available_for_products": ["All Products"]
        }
    ]

def create_store_location_data():
    """Create store location information matching PDF details"""
    return {
        "name": "TechMart Palestine - Nablus Main Store",
        "address": "123 Rafidia Street, near Arab Bank intersection, Nablus, West Bank, Palestine",
        "phone": "+970-9-234-5678",
        "email": "info@techmart-palestine.ps",
        "manager_name": "Ahmad Khalil",
        "opening_hours": {
            "sunday": {"open": "09:00", "close": "20:00"},
            "monday": {"open": "09:00", "close": "20:00"},
            "tuesday": {"open": "09:00", "close": "20:00"},
            "wednesday": {"open": "09:00", "close": "20:00"},
            "thursday": {"open": "09:00", "close": "20:00"},
            "friday": {"open": "09:00", "close": "14:00", "prayer_break": "12:00-13:00"},
            "saturday": {"open": "10:00", "close": "20:00"},
            "ramadan_schedule": {
                "hours": "10:00-16:00 and 20:00-01:00",
                "note": "Split schedule during holy month"
            }
        },
        "services_offered": [
            "retail_sales", "installation", "repair", "delivery", 
            "financing", "trade_in", "technical_support", "warranty_service"
        ],
        "delivery_zones": {
            "zone_a_nablus_city": {
                "name": "Nablus City Center",
                "coverage": "Old City, Downtown, Rafidia, Ras al-Ein",
                "delivery_fee": 0,
                "minimum_order": 200,
                "delivery_time": "Same day for orders before 2 PM"
            },
            "zone_b_greater_nablus": {
                "name": "Greater Nablus Area", 
                "coverage": "Askar Camp, Balata Camp, Tell, Rujeib",
                "delivery_fee": 25,
                "minimum_order": 0,
                "delivery_time": "Next day delivery"
            },
            "zone_c_governorate": {
                "name": "Nablus Governorate",
                "coverage": "Huwara, Asira al-Shamaliya, Beita, Madama",
                "delivery_fee": 35,
                "minimum_order": 500,
                "delivery_time": "2-3 business days"
            }
        }
    }

def create_document_metadata():
    """Create document metadata for uploaded PDFs"""
    return [
        {
            "filename": "techmart_product_catalog_2025.pdf",
            "document_type": "catalog",
            "title": "TechMart Palestine - Complete Product Catalog & Technical Specifications",
            "version": "3.2",
            "document_id": "TMP-SALES-CAT-3.2",
            "department": "sales",
            "audience": "customers",
            "language": "en",
            "products_covered": ["smartphones", "laptops", "home_appliances", "audio", "gaming"],
            "services_covered": ["delivery", "installation", "warranty"],
            "geographic_scope": "palestine",
            "keyword_tags": ["products", "specifications", "pricing", "features", "warranty"],
            "content_summary": "Comprehensive product catalog featuring smartphones, laptops, home appliances, and gaming equipment with detailed specifications, pricing, and warranty information",
            "target_queries": [
                "iPhone 15 price",
                "Samsung Galaxy S24 specifications", 
                "laptop prices",
                "PlayStation 5 availability",
                "AC installation cost"
            ],
            "approval_status": "approved",
            "effective_date": datetime(2025, 8, 10),
            "indexing_status": "completed"
        },
        {
            "filename": "supplier_relations_inventory_procedures.pdf",
            "document_type": "procedures",
            "title": "TechMart Palestine - Supplier Relations & Inventory Control Procedures",
            "version": "2.8",
            "document_id": "TMP-SCM-INV-2.8",
            "department": "operations",
            "audience": "staff",
            "language": "en",
            "products_covered": ["all_categories"],
            "services_covered": ["procurement", "inventory", "logistics"],
            "geographic_scope": "palestine",
            "keyword_tags": ["suppliers", "inventory", "procurement", "logistics", "operations"],
            "content_summary": "Comprehensive supplier relationship management and inventory control procedures covering procurement processes, supplier performance, and logistics coordination",
            "target_queries": [
                "supplier information",
                "delivery timeframes",
                "procurement procedures",
                "inventory management",
                "supplier contact details"
            ],
            "approval_status": "approved", 
            "effective_date": datetime(2025, 8, 10),
            "indexing_status": "completed"
        }
    ]

def seed_database():
    """Main function to seed the database with all data"""
    print("🌱 Starting database seeding process...")
    
    db = SessionLocal()
    
    try:
        # Ensure tables exist
        print("📋 Creating database tables...")
        create_tables()
        
        # Clear existing data (for testing)
        print("🧹 Clearing existing data...")
        db.query(ProductSupplier).delete()
        db.query(ProductVariant).delete() 
        db.query(Product).delete()
        db.query(Supplier).delete()
        db.query(ServiceOffering).delete()
        db.query(StoreLocation).delete()
        db.query(DocumentMetadata).delete()
        db.commit()
        
        # 1. Create Suppliers
        print("🏭 Creating suppliers...")
        suppliers_data = create_suppliers_data()
        suppliers = []
        for supplier_data in suppliers_data:
            supplier = Supplier(**supplier_data)
            db.add(supplier)
            suppliers.append(supplier)
        db.commit()
        print(f"✅ Created {len(suppliers)} suppliers")
        
        # 2. Create Products
        print("📱 Creating products...")
        products_data = create_products_data()
        products = []
        for product_data in products_data:
            product = Product(**product_data)
            db.add(product)
            products.append(product)
        db.commit()
        print(f"✅ Created {len(products)} products")
        
        # 3. Create Product-Supplier Relationships
        print("🔗 Creating supplier relationships...")
        relationships = [
            {"product_idx": 0, "supplier_idx": 1, "supplier_sku": "A3108-256-TIT", "cost_price": 1520.00},  # iPhone - Apple
            {"product_idx": 1, "supplier_idx": 1, "supplier_sku": "A3090-128-PNK", "cost_price": 1040.00},  # iPhone 15 - Apple
            {"product_idx": 2, "supplier_idx": 0, "supplier_sku": "SM-S928B-512", "cost_price": 1280.00},  # Galaxy S24U - Samsung
            {"product_idx": 3, "supplier_idx": 4, "supplier_sku": "5Y2K8EA-HP", "cost_price": 1520.00},    # HP EliteBook - HP
            {"product_idx": 4, "supplier_idx": 0, "supplier_sku": "G814JV-ASUS", "cost_price": 2240.00},   # ASUS Gaming - Samsung dist
            {"product_idx": 5, "supplier_idx": 0, "supplier_sku": "RF28T5001SR", "cost_price": 1760.00},   # Samsung Fridge - Samsung
            {"product_idx": 6, "supplier_idx": 2, "supplier_sku": "GWH18AAD-GREE", "cost_price": 720.00}, # Gree AC - LG dist
            {"product_idx": 7, "supplier_idx": 3, "supplier_sku": "WH-1000XM5-B", "cost_price": 440.00},  # Sony Headphones - Sony
            {"product_idx": 8, "supplier_idx": 3, "supplier_sku": "CFI-2000A01", "cost_price": 640.00}    # PS5 - Sony
        ]
        
        for rel in relationships:
            if rel["product_idx"] < len(products) and rel["supplier_idx"] < len(suppliers):
                product_supplier = ProductSupplier(
                    product_id=products[rel["product_idx"]].id,
                    supplier_id=suppliers[rel["supplier_idx"]].id,
                    supplier_sku=rel["supplier_sku"],
                    cost_price_jod=rel["cost_price"],
                    last_order_date=datetime.now() - timedelta(days=15)
                )
                db.add(product_supplier)
        db.commit()
        print(f"✅ Created {len(relationships)} supplier relationships")
        
        # 4. Create Services
        print("🔧 Creating services...")
        services_data = create_services_data()
        for service_data in services_data:
            service = ServiceOffering(**service_data)
            db.add(service)
        db.commit()
        print(f"✅ Created {len(services_data)} services")
        
        # 5. Create Store Location
        print("🏪 Creating store location...")
        store_data = create_store_location_data()
        store = StoreLocation(**store_data)
        db.add(store)
        db.commit()
        print("✅ Created store location")
        
        # 6. Create Document Metadata
        print("📄 Creating document metadata...")
        docs_metadata = create_document_metadata()
        for doc_data in docs_metadata:
            doc_metadata = DocumentMetadata(**doc_data)
            db.add(doc_metadata)
        db.commit()
        print(f"✅ Created {len(docs_metadata)} document metadata records")
        
        print("\n🎉 Database seeding completed successfully!")
        print("📊 Summary:")
        print(f"   - {len(suppliers)} suppliers")
        print(f"   - {len(products)} products")
        print(f"   - {len(relationships)} supplier relationships")
        print(f"   - {len(services_data)} services")
        print(f"   - 1 store location")
        print(f"   - {len(docs_metadata)} document metadata records")
        print("\n🚀 Ready for enterprise RAG testing!")
        
        # Save seed data to JSON for reference
        seed_summary = {
            "seeded_at": datetime.now().isoformat(),
            "suppliers": len(suppliers),
            "products": len(products),
            "services": len(services_data),
            "sample_products": [p.sku for p in products[:5]]
        }
        
        os.makedirs("data/exports", exist_ok=True)
        with open("data/exports/seed_summary.json", "w") as f:
            json.dump(seed_summary, f, indent=2)
        
    except Exception as e:
        print(f"❌ Error during seeding: {str(e)}")
        db.rollback()
        raise
        
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()