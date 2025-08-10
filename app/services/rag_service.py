"""
Enterprise RAG Service with Database Integration - Complete Production Version
Combines structured data (PostgreSQL) with unstructured content (Vector DB)
Supports bilingual operation (Arabic/English) with Palestinian business context
"""

import logging
import json
from typing import List, Dict, Any, Optional, Tuple, Union
import openai
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.config import settings
from app.database import get_db
from app.models.product import Product, ProductVariant, ServiceOffering, StoreLocation
from app.services.vector_service import vector_service

logger = logging.getLogger(__name__)

class EnterpriseRAGService:
    """
    Advanced RAG service that combines:
    - Real-time database queries (products, services, store info)
    - Vector similarity search (documents, policies, procedures)
    - Intelligent response generation with confidence scoring
    - Bilingual support (Arabic/English)
    - Conversation context management
    - Analytics and performance tracking
    """
    
    def __init__(self):
        self.vector_service = vector_service
        self.openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Enhanced configuration for production
        self.similarity_threshold = 0.60  # Balanced for precision/recall
        self.max_context_length = 5000   # Increased for richer context
        self.max_products_returned = 15  # More products for better selection
        self.max_services_returned = 8   # More services coverage
        self.max_vector_results = 10     # More document chunks
        
        # Response quality thresholds
        self.min_confidence_threshold = 0.25
        self.high_confidence_threshold = 0.75
        
        # Bilingual support
        self.supported_languages = ["en", "ar", "auto"]
        
    async def generate_response(
        self,
        user_message: str,
        language: str = "auto",
        conversation_history: Optional[List[Dict[str, str]]] = None,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Generate enterprise-grade response combining database and vector data
        
        Args:
            user_message: Customer's question or request
            language: Language preference ("en", "ar", "auto")
            conversation_history: Previous conversation context
            db: Database session (auto-created if None)
            
        Returns:
            Comprehensive response with answer, sources, confidence, and metadata
        """
        # Auto-create database session if not provided
        db_session = db or next(get_db())
        should_close_db = db is None
        
        try:
            logger.info(f"🔍 Enterprise RAG processing: {user_message[:50]}...")
            
            # Step 1: Analyze query intent and extract entities
            query_analysis = await self._analyze_query(user_message, language)
            
            # Step 2: Retrieve structured data from database
            structured_data = await self._retrieve_structured_data(
                query_analysis, db_session
            )
            
            # Step 3: Retrieve unstructured data from vector store
            unstructured_data = await self._retrieve_unstructured_data(
                user_message, query_analysis
            )
            
            # Step 4: Combine data sources and generate response
            response = await self._generate_hybrid_response(
                user_message=user_message,
                query_analysis=query_analysis,
                structured_data=structured_data,
                unstructured_data=unstructured_data,
                conversation_history=conversation_history or [],
                language=language
            )
            
            # Step 5: Log analytics for performance optimization
            await self._log_query_analytics(
                user_message, query_analysis, structured_data, 
                unstructured_data, response, db_session
            )
            
            logger.info(f"✅ Enterprise RAG response generated - Confidence: {response.get('confidence', 0):.2f}")
            return response
            
        except Exception as e:
            logger.error(f"❌ Enterprise RAG failed: {str(e)}", exc_info=True)
            return self._fallback_response(user_message, language)
            
        finally:
            if should_close_db and db_session:
                db_session.close()
    
    async def _analyze_query(self, query: str, language: str) -> Dict[str, Any]:
        """
        Advanced query analysis to extract intent and entities using GPT-4
        """
        try:
            analysis_prompt = f"""
            Analyze this customer service query for a Palestinian electronics store and extract structured information:
            
            Query: "{query}"
            
            Extract and return ONLY valid JSON in this exact format:
            {{
                "intent": "product_inquiry|price_check|availability|policy|support|service|comparison|recommendation|greeting|general",
                "entities": {{
                    "products": ["samsung galaxy s24", "iphone 15"],
                    "brands": ["samsung", "apple", "lg", "hp"],
                    "categories": ["smartphones", "laptops", "home_appliances", "gaming"],
                    "price_range": {{"min": 500, "max": 1500}},
                    "services": ["delivery", "installation", "warranty", "repair"],
                    "attributes": ["price", "specifications", "availability", "warranty"],
                    "store_info": ["hours", "location", "contact", "payment_methods"]
                }},
                "urgency": "low|medium|high",
                "requires_real_time_data": true,
                "complexity": "simple|moderate|complex"
            }}
            
            Guidelines:
            - For Arabic queries, translate entities to English for database matching
            - Extract Palestinian/regional context (JOD pricing, local preferences)
            - Identify if query needs current inventory/pricing vs policy information
            - Mark urgency as high for troubleshooting, medium for purchasing, low for general info
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": analysis_prompt}],
                max_tokens=400,
                temperature=0.1
            )
            
            # Parse JSON response
            analysis_text = response.choices[0].message.content.strip()
            
            # Clean up response to ensure valid JSON
            if analysis_text.startswith('```json'):
                analysis_text = analysis_text.replace('```json', '').replace('```', '').strip()
            
            analysis = json.loads(analysis_text)
            
            # Add detected language
            analysis["language"] = self._detect_language(query) if language == "auto" else language
            
            # Add query metadata
            analysis["original_query"] = query
            analysis["query_length"] = len(query)
            analysis["has_arabic"] = bool(self._count_arabic_chars(query))
            
            return analysis
            
        except Exception as e:
            logger.error(f"Query analysis failed: {str(e)}")
            # Fallback analysis
            return {
                "intent": "general",
                "entities": {
                    "products": [],
                    "brands": [],
                    "categories": [],
                    "services": [],
                    "attributes": [],
                    "store_info": []
                },
                "urgency": "medium",
                "requires_real_time_data": True,
                "complexity": "simple",
                "language": self._detect_language(query) if language == "auto" else language,
                "original_query": query,
                "query_length": len(query),
                "has_arabic": bool(self._count_arabic_chars(query))
            }
    
    async def _retrieve_structured_data(
        self, 
        query_analysis: Dict[str, Any], 
        db: Session
    ) -> Dict[str, Any]:
        """
        Query PostgreSQL for real-time structured data based on query analysis
        """
        structured_data = {
            "products": [],
            "services": [],
            "store_info": {},
            "suppliers": [],
            "analytics": {}
        }
        
        try:
            entities = query_analysis.get("entities", {})
            intent = query_analysis.get("intent", "")
            
            # Product queries - high priority for e-commerce
            if (intent in ["product_inquiry", "price_check", "availability", "comparison", "recommendation"] 
                or entities.get("products") or entities.get("brands") or entities.get("categories")):
                products = await self._query_products(entities, intent, db)
                structured_data["products"] = products
            
            # Service queries - important for customer support
            if (intent in ["service", "support"] or entities.get("services") 
                or any(service in query_analysis.get("original_query", "").lower() 
                       for service in ["install", "setup", "delivery", "repair", "warranty"])):
                services = await self._query_services(entities, db)
                structured_data["services"] = services
            
            # Store information - always available for context
            if (intent in ["policy", "support", "general"] 
                or entities.get("store_info")
                or any(term in query_analysis.get("original_query", "").lower() 
                       for term in ["hours", "location", "contact", "address", "phone", "email"])):
                store_info = await self._query_store_info(db)
                structured_data["store_info"] = store_info
            
            # Add query analytics
            structured_data["analytics"] = {
                "products_found": len(structured_data["products"]),
                "services_found": len(structured_data["services"]),
                "has_store_info": bool(structured_data["store_info"]),
                "query_complexity": query_analysis.get("complexity", "simple")
            }
            
            return structured_data
            
        except Exception as e:
            logger.error(f"Structured data retrieval failed: {str(e)}")
            return structured_data
    
    async def _query_products(self, entities: Dict, intent: str, db: Session) -> List[Dict]:
        """
        Advanced product database query with intelligent filtering and ranking
        """
        try:
            # Base query for available products
            query = db.query(Product).filter(Product.is_available == True)
            
            # Brand filtering with fuzzy matching
            if entities.get("brands"):
                brand_conditions = []
                for brand in entities["brands"]:
                    brand_conditions.append(Product.brand.ilike(f"%{brand}%"))
                query = query.filter(or_(*brand_conditions))
            
            # Category filtering
            if entities.get("categories"):
                category_conditions = []
                for category in entities["categories"]:
                    category_conditions.append(Product.category.ilike(f"%{category}%"))
                query = query.filter(or_(*category_conditions))
            
            # Product name matching
            if entities.get("products"):
                product_conditions = []
                for product in entities["products"]:
                    # Split product name for better matching
                    words = product.split()
                    for word in words:
                        if len(word) > 2:  # Skip very short words
                            product_conditions.append(Product.name.ilike(f"%{word}%"))
                if product_conditions:
                    query = query.filter(or_(*product_conditions))
            
            # Price range filtering
            if entities.get("price_range"):
                price_range = entities["price_range"]
                if price_range.get("min"):
                    query = query.filter(Product.price_jod >= price_range["min"])
                if price_range.get("max"):
                    query = query.filter(Product.price_jod <= price_range["max"])
            
            # Intent-based ordering
            if intent == "recommendation":
                # Prioritize featured and promoted products
                query = query.order_by(Product.is_featured.desc(), Product.is_promotion.desc())
            elif intent == "price_check":
                # Order by price for comparison
                query = query.order_by(Product.price_jod.asc())
            else:
                # Default: featured products first, then by name
                query = query.order_by(Product.is_featured.desc(), Product.name.asc())
            
            # Execute with limit
            products = query.limit(self.max_products_returned).all()
            
            # Format for RAG consumption with rich metadata
            return [
                {
                    "id": p.id,
                    "sku": p.sku,
                    "name": p.name,
                    "brand": p.brand,
                    "category": p.category,
                    "subcategory": p.subcategory,
                    "price_jod": float(p.price_jod) if p.price_jod else 0,
                    "original_price_jod": float(p.original_price_jod) if p.original_price_jod else 0,
                    "discount_percentage": float(p.discount_percentage) if p.discount_percentage else 0,
                    "stock_quantity": p.stock_quantity or 0,
                    "specifications": p.specifications or {},
                    "warranty_months": p.warranty_months or 12,
                    "promotion_text": p.promotion_text,
                    "is_featured": p.is_featured or False,
                    "is_promotion": p.is_promotion or False,
                    "model_number": p.model_number,
                    "availability_status": "In Stock" if (p.stock_quantity or 0) > 0 else "Out of Stock"
                }
                for p in products
            ]
            
        except Exception as e:
            logger.error(f"Product query failed: {str(e)}")
            return []
    
    async def _query_services(self, entities: Dict, db: Session) -> List[Dict]:
        """
        Query services database with intelligent matching
        """
        try:
            query = db.query(ServiceOffering)
            
            # Service name matching
            if entities.get("services"):
                service_conditions = []
                for service in entities["services"]:
                    service_conditions.extend([
                        ServiceOffering.service_name.ilike(f"%{service}%"),
                        ServiceOffering.category.ilike(f"%{service}%"),
                        ServiceOffering.description.ilike(f"%{service}%")
                    ])
                query = query.filter(or_(*service_conditions))
            
            # Order by category and price
            query = query.order_by(ServiceOffering.category.asc(), ServiceOffering.base_price_jod.asc())
            
            services = query.limit(self.max_services_returned).all()
            
            return [
                {
                    "id": s.id,
                    "service_name": s.service_name,
                    "category": s.category,
                    "description": s.description,
                    "base_price_jod": float(s.base_price_jod) if s.base_price_jod else 0,
                    "duration_hours": float(s.duration_hours) if s.duration_hours else 0,
                    "requirements": s.requirements or {},
                    "available_for_products": s.available_for_products or []
                }
                for s in services
            ]
            
        except Exception as e:
            logger.error(f"Service query failed: {str(e)}")
            return []
    
    async def _query_store_info(self, db: Session) -> Dict:
        """
        Get comprehensive store information
        """
        try:
            store = db.query(StoreLocation).first()
            if store:
                return {
                    "name": store.name,
                    "address": store.address,
                    "phone": store.phone,
                    "email": store.email,
                    "manager_name": getattr(store, 'manager_name', ''),
                    "opening_hours": store.opening_hours or {},
                    "services_offered": store.services_offered or [],
                    "delivery_zones": getattr(store, 'delivery_zones', {})
                }
            return {}
            
        except Exception as e:
            logger.error(f"Store info query failed: {str(e)}")
            return {}
    
    async def _retrieve_unstructured_data(
        self, 
        user_message: str, 
        query_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Retrieve relevant context from vector database with advanced filtering
        """
        try:
            # Create enhanced search query
            search_query = self._enhance_search_query(user_message, query_analysis)
            
            # Build metadata filter for targeted search
            metadata_filter = self._build_metadata_filter(query_analysis)
            
            # Search vector database
            search_results = await self.vector_service.search_similar(
                query_text=search_query,
                top_k=self.max_vector_results,
                filter_dict=metadata_filter
            )
            
            # Filter and format results with quality control
            context_chunks = []
            sources = []
            total_score = 0
            
            for result in search_results:
                score = result.get("score", 0)
                if score >= self.similarity_threshold:
                    chunk_text = result["metadata"].get("text", "")
                    source_name = result["metadata"].get("source", "Unknown")
                    
                    if chunk_text and len(chunk_text.strip()) > 20:  # Quality check
                        context_chunks.append({
                            "text": chunk_text,
                            "source": source_name,
                            "score": score,
                            "metadata": result["metadata"],
                            "chunk_index": result["metadata"].get("chunk_index", 0),
                            "language": result["metadata"].get("language", "unknown")
                        })
                        sources.append(source_name)
                        total_score += score
            
            # Calculate average quality score
            avg_score = total_score / len(context_chunks) if context_chunks else 0
            
            return {
                "chunks": context_chunks[:8],  # Limit for optimal token usage
                "sources": list(set(sources)),
                "total_found": len(search_results),
                "quality_chunks": len(context_chunks),
                "average_score": avg_score,
                "search_query": search_query
            }
            
        except Exception as e:
            logger.error(f"Unstructured data retrieval failed: {str(e)}")
            return {
                "chunks": [], 
                "sources": [], 
                "total_found": 0,
                "quality_chunks": 0,
                "average_score": 0,
                "search_query": user_message
            }
    
    def _enhance_search_query(self, user_message: str, query_analysis: Dict[str, Any]) -> str:
        """
        Enhance search query with extracted entities and context
        """
        query_parts = [user_message]
        entities = query_analysis.get("entities", {})
        
        # Add product-related terms
        for product in entities.get("products", []):
            query_parts.append(product)
        
        # Add brand terms
        for brand in entities.get("brands", []):
            query_parts.append(brand)
        
        # Add service terms
        for service in entities.get("services", []):
            query_parts.append(service)
        
        # Add store info terms
        for info in entities.get("store_info", []):
            query_parts.append(info)
        
        # Add intent-based keywords
        intent = query_analysis.get("intent", "")
        intent_keywords = {
            "policy": ["policy", "procedure", "rules"],
            "support": ["help", "support", "assistance"],
            "warranty": ["warranty", "guarantee", "coverage"],
            "delivery": ["delivery", "shipping", "transport"]
        }
        
        if intent in intent_keywords:
            query_parts.extend(intent_keywords[intent])
        
        # Create enhanced query
        enhanced_query = " ".join(set(query_parts))  # Remove duplicates
        return enhanced_query[:200]  # Limit length
    
    def _build_metadata_filter(self, query_analysis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Build intelligent metadata filter for vector search
        """
        filter_dict = {}
        
        # Language filtering
        language = query_analysis.get("language")
        if language and language in ["en", "ar"]:
            filter_dict["language"] = language
        
        # Category-based filtering
        entities = query_analysis.get("entities", {})
        if entities.get("categories"):
            # Map categories to document types
            category_mapping = {
                "smartphones": "product",
                "laptops": "product", 
                "home_appliances": "product",
                "policy": "policy",
                "support": "manual",
                "warranty": "policy"
            }
            
            categories = entities["categories"]
            for category in categories:
                if category in category_mapping:
                    filter_dict["document_type"] = category_mapping[category]
                    break
        
        return filter_dict if filter_dict else None
    
    async def _generate_hybrid_response(
        self,
        user_message: str,
        query_analysis: Dict[str, Any],
        structured_data: Dict[str, Any],
        unstructured_data: Dict[str, Any],
        conversation_history: List[Dict[str, str]],
        language: str
    ) -> Dict[str, Any]:
        """
        Generate comprehensive response combining all data sources
        """
        try:
            # Build comprehensive system prompt
            system_prompt = self._build_enterprise_system_prompt(language)
            
            # Build rich data context
            data_context = self._build_data_context(structured_data, unstructured_data)
            
            # Build conversation context
            history_context = self._build_conversation_context(conversation_history)
            
            # Create comprehensive user prompt
            user_prompt = f"""
Customer Question: {user_message}

{data_context}
{history_context}

Analysis Context:
- Intent: {query_analysis.get('intent', 'general')}
- Language: {query_analysis.get('language', 'en')}
- Complexity: {query_analysis.get('complexity', 'simple')}
- Urgency: {query_analysis.get('urgency', 'medium')}

Please provide a comprehensive, accurate response using the available data:
1. If referencing products: include current pricing (in JOD), availability, and key specifications
2. If mentioning services: include pricing, duration, and requirements
3. If citing policies: reference the specific source document
4. Maintain a professional, helpful tone appropriate for Palestinian customers
5. Use the customer's preferred language ({query_analysis.get('language', 'en')})
6. If insufficient information is available, clearly state limitations and suggest alternatives

Response Requirements:
- Be specific and actionable
- Include relevant prices in Jordanian Dinars (JOD)
- Mention warranty information when relevant
- Provide contact information for follow-up if needed
"""
            
            # Generate response with appropriate model and settings
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=800,  # Increased for detailed responses
                temperature=0.7,
                presence_penalty=0.1,
                frequency_penalty=0.1
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Calculate comprehensive confidence score
            confidence = self._calculate_hybrid_confidence(
                structured_data, unstructured_data, query_analysis, ai_response
            )
            
            # Compile comprehensive sources
            all_sources = unstructured_data.get("sources", [])
            if structured_data.get("products"):
                all_sources.append("Product Database")
            if structured_data.get("services"):
                all_sources.append("Service Database")
            if structured_data.get("store_info"):
                all_sources.append("Store Information")
            
            # Build comprehensive response
            response_data = {
                "answer": ai_response,
                "language": query_analysis.get("language", language),
                "sources": list(set(all_sources)),
                "confidence": confidence,
                "data_sources": {
                    "structured": bool(structured_data.get("products") or structured_data.get("services")),
                    "unstructured": bool(unstructured_data.get("chunks")),
                    "hybrid": True,
                    "store_info": bool(structured_data.get("store_info"))
                },
                "metadata": {
                    "products_found": len(structured_data.get("products", [])),
                    "services_found": len(structured_data.get("services", [])),
                    "context_chunks": len(unstructured_data.get("chunks", [])),
                    "vector_quality": unstructured_data.get("average_score", 0),
                    "intent": query_analysis.get("intent"),
                    "complexity": query_analysis.get("complexity"),
                    "urgency": query_analysis.get("urgency"),
                    "response_length": len(ai_response),
                    "processing_successful": True
                }
            }
            
            return response_data
            
        except Exception as e:
            logger.error(f"Hybrid response generation failed: {str(e)}")
            return self._fallback_response(user_message, language)
    
    def _build_enterprise_system_prompt(self, language: str) -> str:
        """
        Build comprehensive system prompt for enterprise RAG
        """
        if language == "ar":
            return """أنت مساعد ذكي متقدم لخدمة العملاء في تك مارت فلسطين، متجر الإلكترونيات الرائد في نابلس.

مهامك الأساسية:
1. مساعدة العملاء الفلسطينيين بأسئلتهم حول المنتجات والخدمات والسياسات
2. استخدام البيانات الحية من قاعدة البيانات (أسعار، توفر، مواصفات) مع المعلومات من الوثائق
3. تقديم إجابات دقيقة ومفصلة ومهنية باللغة العربية
4. ذكر الأسعار بالدينار الأردني (JOD) والتوفر الحالي
5. الإشارة إلى مصادر المعلومات والوثائق ذات الصلة
6. فهم السياق الفلسطيني والاحتياجات المحلية

إرشادات الاستجابة:
- كن مهذباً ومساعداً ودقيقاً
- استخدم اللغة العربية الفصحى مع المصطلحات التقنية المناسبة
- اذكر معلومات الاتصال عند الحاجة
- قدم بدائل إذا لم تكن المعلومات متوفرة
- احترم الثقافة والتقاليد الفلسطينية في التواصل"""
        
        else:
            return """You are an advanced AI customer service assistant for TechMart Palestine, the leading electronics store in Nablus, West Bank.

Your core responsibilities:
1. Help Palestinian customers with questions about products, services, and store policies
2. Use real-time database information (pricing, availability, specifications) combined with document knowledge
3. Provide accurate, detailed, and professional responses in English
4. Include current pricing in Jordanian Dinars (JOD) and availability status
5. Cite relevant sources and reference policy documents when applicable
6. Understand Palestinian context and local customer needs

Response guidelines:
- Maintain a friendly, professional, and helpful tone
- Include specific product details, pricing, and availability when discussing items
- Provide contact information for follow-up when appropriate
- Offer alternatives if requested information isn't available
- Be culturally sensitive to Palestinian business practices and customer expectations
- Always aim to be helpful while being honest about limitations

Store context: TechMart Palestine serves the Palestinian market with authentic products, competitive pricing, bilingual support, and comprehensive customer service including delivery, installation, and technical support."""
    
    def _build_data_context(
        self, 
        structured_data: Dict[str, Any], 
        unstructured_data: Dict[str, Any]
    ) -> str:
        """
        Build comprehensive data context for AI with rich formatting
        """
        context_parts = []
        
        # Add current product information with rich details
        if structured_data.get("products"):
            context_parts.append("\n🛒 CURRENT PRODUCT INFORMATION:")
            for i, product in enumerate(structured_data["products"][:6], 1):  # Limit for token management
                discount_info = ""
                if product.get('discount_percentage', 0) > 0:
                    discount_info = f" (🏷️ {product['discount_percentage']:.1f}% OFF - Save {product['original_price_jod'] - product['price_jod']:.0f} JOD)"
                
                stock_status = "✅ In Stock" if product.get('stock_quantity', 0) > 0 else "❌ Out of Stock"
                
                context_parts.append(f"""
{i}. {product['name']} ({product['brand']})
   • SKU: {product['sku']} | Category: {product['category']}
   • Price: {product['price_jod']:.0f} JOD{discount_info}
   • Stock: {product['stock_quantity']} units | Status: {stock_status}
   • Warranty: {product['warranty_months']} months
   • Model: {product.get('model_number', 'N/A')}
   {f"• Promotion: {product['promotion_text']}" if product.get('promotion_text') else ""}
""")
        
        # Add available services with detailed information
        if structured_data.get("services"):
            context_parts.append("\n🔧 AVAILABLE SERVICES:")
            for i, service in enumerate(structured_data["services"], 1):
                context_parts.append(f"""
{i}. {service['service_name']} ({service['category']})
   • Price: {service['base_price_jod']:.0f} JOD
   • Duration: {service['duration_hours']:.1f} hours
   • Description: {service['description']}
   • Requirements: {service.get('requirements', 'Standard requirements apply')}
""")
        
        # Add store information when available
        if structured_data.get("store_info"):
            store = structured_data["store_info"]
            context_parts.append(f"\n🏪 STORE INFORMATION:")
            context_parts.append(f"""
Store: {store.get('name', 'TechMart Palestine')}
Address: {store.get('address', 'Nablus, Palestine')}
Phone: {store.get('phone', '+970-9-234-5678')}
Email: {store.get('email', 'info@techmart-palestine.ps')}
""")
            
            # Add hours if available
            if store.get('opening_hours'):
                context_parts.append("Hours: Check opening_hours data for detailed schedule")
        
        # Add relevant policies and information from documents
        if unstructured_data.get("chunks"):
            context_parts.append("\n📋 RELEVANT POLICIES & INFORMATION:")
            for i, chunk in enumerate(unstructured_data["chunks"][:5], 1):  # Limit chunks
                context_parts.append(f"""
[Source {i}]: {chunk['source']} (Relevance: {chunk['score']:.2f})
{chunk['text']}
""")
        
        return "\n".join(context_parts)
    
    def _build_conversation_context(self, conversation_history: List[Dict[str, str]]) -> str:
        """
        Build conversation context with intelligent summarization
        """
        if not conversation_history:
            return ""
        
        context_parts = ["\n💬 CONVERSATION CONTEXT:"]
        
        # Show last 4 exchanges for context
        recent_history = conversation_history[-8:]  # Last 4 user-assistant pairs
        
        for i, msg in enumerate(recent_history):
            role = "Customer" if msg.get("role") == "user" else "Assistant"
            content = msg.get("content", "")[:150]  # Limit length
            if len(msg.get("content", "")) > 150:
                content += "..."
            context_parts.append(f"{role}: {content}")
        
        context_parts.append("")  # Add spacing
        return "\n".join(context_parts)
    
    def _calculate_hybrid_confidence(
        self,
        structured_data: Dict[str, Any],
        unstructured_data: Dict[str, Any],
        query_analysis: Dict[str, Any],
        response_text: str = ""
    ) -> float:
        """
        Calculate sophisticated confidence score based on multiple factors
        """
        base_confidence = 0.2  # Start with low base
        
        # Data availability boosts
        if structured_data.get("products"):
            base_confidence += 0.25  # Strong boost for product data
        if structured_data.get("services"):
            base_confidence += 0.15  # Good boost for service data
        if structured_data.get("store_info"):
            base_confidence += 0.10  # Moderate boost for store info
        
        # Vector search quality
        chunks = unstructured_data.get("chunks", [])
        if chunks:
            avg_score = unstructured_data.get("average_score", 0)
            chunk_quality_boost = min(0.35, avg_score * 0.4)
            base_confidence += chunk_quality_boost
        
        # Query complexity adjustment
        complexity = query_analysis.get("complexity", "simple")
        if complexity == "simple":
            base_confidence += 0.05
        elif complexity == "complex":
            base_confidence -= 0.05
        
        # Intent-specific adjustments
        intent = query_analysis.get("intent", "general")
        if intent in ["product_inquiry", "price_check"] and structured_data.get("products"):
            base_confidence += 0.10  # High confidence for product queries with data
        elif intent == "policy" and chunks:
            base_confidence += 0.08  # Good confidence for policy with documents
        
        # Response quality indicators
        if response_text:
            if len(response_text) > 100 and "JOD" in response_text:
                base_confidence += 0.05  # Boost for detailed responses with pricing
            if any(word in response_text.lower() for word in ["available", "stock", "warranty"]):
                base_confidence += 0.03  # Boost for specific product information
        
        # Language consistency bonus
        detected_lang = query_analysis.get("language", "en")
        if detected_lang in ["en", "ar"]:  # Supported languages
            base_confidence += 0.02
        
        # Ensure confidence is within reasonable bounds
        final_confidence = max(0.15, min(0.95, base_confidence))
        
        return round(final_confidence, 3)
    
    async def _log_query_analytics(
        self,
        user_message: str,
        query_analysis: Dict[str, Any],
        structured_data: Dict[str, Any],
        unstructured_data: Dict[str, Any],
        response: Dict[str, Any],
        db: Session
    ):
        """
        Log comprehensive analytics for performance optimization and business intelligence
        """
        try:
            # For now, log to application logs (can be extended to database)
            analytics_data = {
                "query": user_message[:100],  # Truncated for privacy
                "intent": query_analysis.get("intent"),
                "language": query_analysis.get("language"),
                "complexity": query_analysis.get("complexity"),
                "confidence": response.get("confidence"),
                "products_found": len(structured_data.get("products", [])),
                "services_found": len(structured_data.get("services", [])),
                "document_chunks": len(unstructured_data.get("chunks", [])),
                "vector_quality": unstructured_data.get("average_score", 0),
                "response_length": len(response.get("answer", "")),
                "sources_count": len(response.get("sources", []))
            }
            
            logger.info(f"RAG Analytics: {json.dumps(analytics_data)}")
            
            # Future: Store in QueryAnalytics table for business intelligence
            # analytics_record = QueryAnalytics(**analytics_data)
            # db.add(analytics_record)
            # db.commit()
            
        except Exception as e:
            logger.error(f"Analytics logging failed: {str(e)}")
    
    def _detect_language(self, text: str) -> str:
        """
        Enhanced language detection with better Arabic support
        """
        if not text:
            return "en"
        
        arabic_chars = self._count_arabic_chars(text)
        total_chars = len([c for c in text if c.isalpha()])
        
        if total_chars == 0:
            return "en"
        
        arabic_ratio = arabic_chars / total_chars
        
        # More sophisticated detection
        if arabic_ratio > 0.25:  # Lowered threshold for mixed content
            return "ar"
        elif arabic_ratio > 0.1 and any(word in text for word in ["ما", "هي", "كيف", "أين", "متى"]):
            return "ar"  # Common Arabic question words
        else:
            return "en"
    
    def _count_arabic_chars(self, text: str) -> int:
        """Count Arabic characters in text"""
        return len([c for c in text if '\u0600' <= c <= '\u06FF'])
    
    def _fallback_response(self, user_message: str, language: str) -> Dict[str, Any]:
        """
        Enhanced fallback response with helpful alternatives
        """
        if language == "ar":
            message = """أعتذر، أواجه صعوبة تقنية في معالجة طلبك حالياً. 

يرجى المحاولة مرة أخرى أو الاتصال بفريق الدعم:
📞 +970-9-234-5678
📧 info@techmart-palestine.ps

أو زيارة متجرنا في شارع الرفيدية، نابلس."""
        else:
            message = """I apologize, but I'm experiencing technical difficulties processing your request right now. 

Please try again in a moment or contact our support team:
📞 +970-9-234-5678
📧 info@techmart-palestine.ps

You can also visit our store at Rafidia Street, Nablus."""
        
        return {
            "answer": message,
            "language": language,
            "sources": ["Fallback Response"],
            "confidence": 0.15,
            "data_sources": {
                "structured": False, 
                "unstructured": False, 
                "hybrid": False,
                "store_info": True
            },
            "metadata": {
                "products_found": 0,
                "services_found": 0,
                "context_chunks": 0,
                "vector_quality": 0,
                "intent": "system_error",
                "complexity": "error",
                "urgency": "high",
                "response_length": len(message),
                "processing_successful": False,
                "error_type": "technical_difficulty"
            }
        }
    
    async def get_suggested_questions(self, language: str = "en") -> List[str]:
        """
        Get intelligent suggested questions based on language and context
        """
        if language == "ar":
            return [
                "ما هي ساعات عمل المتجر؟",
                "ما هي سياسة الإرجاع والاستبدال؟",
                "ما هي طرق الدفع المقبولة؟",
                "هل تقدمون خدمة التوصيل؟",
                "كم سعر آيفون 15؟",
                "ما هي خدمات التركيب المتاحة؟",
                "هل يوجد ضمان على المنتجات؟",
                "كيف يمكنني التواصل مع خدمة العملاء؟"
            ]
        else:
            return [
                "What are your store hours?",
                "What is your return and exchange policy?",
                "What payment methods do you accept?",
                "Do you offer delivery services?",
                "What's the price of iPhone 15?",
                "What installation services do you provide?",
                "What warranty do you offer on products?",
                "How can I contact customer service?"
            ]

# Global instance for the enterprise RAG service
enterprise_rag_service = EnterpriseRAGService()