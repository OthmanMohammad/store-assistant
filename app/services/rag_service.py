"""
Enterprise RAG Service with Database Integration
Combines structured data (PostgreSQL) with unstructured content (Vector DB)
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import openai
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.config import settings
from app.database import get_db
from app.models.product import Product, ProductVariant, ServiceOffering, StoreLocation
from app.services.vector_service import vector_service

logger = logging.getLogger(__name__)

class EnterpriseRAGService:
    def __init__(self):
        self.vector_service = vector_service
        self.openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Enhanced configuration
        self.similarity_threshold = 0.65  # Lowered for better recall
        self.max_context_length = 4000
        self.max_products_returned = 10
        self.max_services_returned = 5
        
    async def generate_response(
        self,
        user_message: str,
        language: str = "auto",
        conversation_history: Optional[List[Dict[str, str]]] = None,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Generate enterprise-grade response combining database and vector data
        """
        try:
            logger.info(f"🔍 Enterprise RAG processing: {user_message[:50]}...")
            
            # Step 1: Analyze query intent and extract entities
            query_analysis = await self._analyze_query(user_message, language)
            
            # Step 2: Retrieve structured data from database
            structured_data = await self._retrieve_structured_data(
                query_analysis, db
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
                unstructured_data, response, db
            )
            
            logger.info(f"✅ Enterprise RAG response generated")
            return response
            
        except Exception as e:
            logger.error(f"❌ Enterprise RAG failed: {str(e)}")
            return self._fallback_response(user_message, language)
    
    async def _analyze_query(self, query: str, language: str) -> Dict[str, Any]:
        """
        Advanced query analysis to extract intent and entities
        """
        try:
            analysis_prompt = f"""
            Analyze this customer query and extract structured information:
            
            Query: "{query}"
            
            Extract and return as JSON:
            {{
                "intent": "product_inquiry|price_check|availability|policy|support|service|comparison|recommendation",
                "entities": {{
                    "products": ["samsung galaxy s24", "iphone 15"],
                    "brands": ["samsung", "apple"],
                    "categories": ["smartphones", "laptops"],
                    "price_range": {{"min": 500, "max": 1500}},
                    "services": ["delivery", "installation", "warranty"],
                    "attributes": ["price", "specifications", "availability"]
                }},
                "urgency": "low|medium|high",
                "requires_real_time_data": true/false
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": analysis_prompt}],
                max_tokens=300,
                temperature=0.1
            )
            
            import json
            analysis = json.loads(response.choices[0].message.content)
            
            # Add detected language
            analysis["language"] = self._detect_language(query) if language == "auto" else language
            
            return analysis
            
        except Exception as e:
            logger.error(f"Query analysis failed: {str(e)}")
            return {
                "intent": "general",
                "entities": {},
                "urgency": "medium",
                "requires_real_time_data": True,
                "language": language
            }
    
    async def _retrieve_structured_data(
        self, 
        query_analysis: Dict[str, Any], 
        db: Optional[Session]
    ) -> Dict[str, Any]:
        """
        Query PostgreSQL for real-time structured data
        """
        structured_data = {
            "products": [],
            "services": [],
            "store_info": {},
            "pricing": {},
            "availability": {}
        }
        
        if not db:
            return structured_data
        
        try:
            entities = query_analysis.get("entities", {})
            intent = query_analysis.get("intent", "")
            
            # Product queries
            if intent in ["product_inquiry", "price_check", "availability", "comparison"]:
                products = await self._query_products(entities, db)
                structured_data["products"] = products
            
            # Service queries
            if intent in ["service", "support"] or "services" in entities:
                services = await self._query_services(entities, db)
                structured_data["services"] = services
            
            # Store information queries
            if intent in ["policy", "support"] or any(term in query_analysis.get("user_message", "").lower() 
                for term in ["hours", "location", "contact", "address"]):
                store_info = await self._query_store_info(db)
                structured_data["store_info"] = store_info
            
            return structured_data
            
        except Exception as e:
            logger.error(f"Structured data retrieval failed: {str(e)}")
            return structured_data
    
    async def _query_products(self, entities: Dict, db: Session) -> List[Dict]:
        """Query product database with entity matching"""
        try:
            query = db.query(Product).filter(Product.is_available == True)
            
            # Apply filters based on extracted entities
            if "brands" in entities and entities["brands"]:
                brand_filters = [Product.brand.ilike(f"%{brand}%") for brand in entities["brands"]]
                query = query.filter(or_(*brand_filters))
            
            if "categories" in entities and entities["categories"]:
                category_filters = [Product.category.ilike(f"%{cat}%") for cat in entities["categories"]]
                query = query.filter(or_(*category_filters))
            
            if "products" in entities and entities["products"]:
                product_filters = [Product.name.ilike(f"%{prod}%") for prod in entities["products"]]
                query = query.filter(or_(*product_filters))
            
            if "price_range" in entities and entities["price_range"]:
                price_range = entities["price_range"]
                if "min" in price_range:
                    query = query.filter(Product.price_jod >= price_range["min"])
                if "max" in price_range:
                    query = query.filter(Product.price_jod <= price_range["max"])
            
            # Limit results and order by relevance
            products = query.limit(self.max_products_returned).all()
            
            # Format for RAG consumption
            return [
                {
                    "id": p.id,
                    "sku": p.sku,
                    "name": p.name,
                    "brand": p.brand,
                    "category": p.category,
                    "price_jod": p.price_jod,
                    "original_price_jod": p.original_price_jod,
                    "discount_percentage": p.discount_percentage,
                    "stock_quantity": p.stock_quantity,
                    "specifications": p.specifications,
                    "warranty_months": p.warranty_months,
                    "promotion_text": p.promotion_text,
                    "is_featured": p.is_featured
                }
                for p in products
            ]
            
        except Exception as e:
            logger.error(f"Product query failed: {str(e)}")
            return []
    
    async def _query_services(self, entities: Dict, db: Session) -> List[Dict]:
        """Query services database"""
        try:
            query = db.query(ServiceOffering)
            
            if "services" in entities and entities["services"]:
                service_filters = [
                    ServiceOffering.service_name.ilike(f"%{service}%") 
                    for service in entities["services"]
                ]
                query = query.filter(or_(*service_filters))
            
            services = query.limit(self.max_services_returned).all()
            
            return [
                {
                    "id": s.id,
                    "service_name": s.service_name,
                    "category": s.category,
                    "description": s.description,
                    "base_price_jod": s.base_price_jod,
                    "duration_hours": s.duration_hours,
                    "requirements": s.requirements
                }
                for s in services
            ]
            
        except Exception as e:
            logger.error(f"Service query failed: {str(e)}")
            return []
    
    async def _query_store_info(self, db: Session) -> Dict:
        """Get store information"""
        try:
            store = db.query(StoreLocation).first()
            if store:
                return {
                    "name": store.name,
                    "address": store.address,
                    "phone": store.phone,
                    "email": store.email,
                    "opening_hours": store.opening_hours,
                    "services_offered": store.services_offered
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
        Retrieve relevant context from vector database
        """
        try:
            # Create enhanced search query
            search_query = self._enhance_search_query(user_message, query_analysis)
            
            # Search vector database
            search_results = await self.vector_service.search_similar(
                query_text=search_query,
                top_k=8,  # Increased for better coverage
                filter_dict=self._build_metadata_filter(query_analysis)
            )
            
            # Filter and format results
            context_chunks = []
            sources = []
            
            for result in search_results:
                if result["score"] >= self.similarity_threshold:
                    chunk_text = result["metadata"].get("text", "")
                    source_name = result["metadata"].get("source", "Unknown")
                    
                    if chunk_text:
                        context_chunks.append({
                            "text": chunk_text,
                            "source": source_name,
                            "score": result["score"],
                            "metadata": result["metadata"]
                        })
                        sources.append(source_name)
            
            return {
                "chunks": context_chunks[:6],  # Limit for token management
                "sources": list(set(sources)),
                "total_found": len(search_results)
            }
            
        except Exception as e:
            logger.error(f"Unstructured data retrieval failed: {str(e)}")
            return {"chunks": [], "sources": [], "total_found": 0}
    
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
        Generate response combining structured and unstructured data
        """
        try:
            # Build comprehensive system prompt
            system_prompt = self._build_enterprise_system_prompt(language)
            
            # Build data context
            data_context = self._build_data_context(structured_data, unstructured_data)
            
            # Build conversation context
            history_context = self._build_conversation_context(conversation_history)
            
            # Create user prompt
            user_prompt = f"""
Customer Question: {user_message}

{data_context}
{history_context}

Please provide a comprehensive, accurate response using the available data. 
If you reference specific products, include current pricing and availability.
If you mention policies or procedures, cite the relevant sources.
Maintain a professional, helpful tone appropriate for customer service.
"""
            
            # Generate response
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=600,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Calculate confidence score
            confidence = self._calculate_hybrid_confidence(
                structured_data, unstructured_data, query_analysis
            )
            
            # Compile sources
            all_sources = unstructured_data.get("sources", [])
            if structured_data.get("products"):
                all_sources.append("Product Database")
            if structured_data.get("services"):
                all_sources.append("Service Database")
            
            return {
                "answer": ai_response,
                "language": query_analysis.get("language", language),
                "sources": list(set(all_sources)),
                "confidence": confidence,
                "data_sources": {
                    "structured": bool(structured_data.get("products") or structured_data.get("services")),
                    "unstructured": bool(unstructured_data.get("chunks")),
                    "hybrid": True
                },
                "products_found": len(structured_data.get("products", [])),
                "services_found": len(structured_data.get("services", [])),
                "context_chunks": len(unstructured_data.get("chunks", []))
            }
            
        except Exception as e:
            logger.error(f"Hybrid response generation failed: {str(e)}")
            return self._fallback_response(user_message, language)
    
    def _build_data_context(
        self, 
        structured_data: Dict[str, Any], 
        unstructured_data: Dict[str, Any]
    ) -> str:
        """Build comprehensive data context for AI"""
        context_parts = []
        
        # Add product information
        if structured_data.get("products"):
            context_parts.append("\n🛒 CURRENT PRODUCT INFORMATION:")
            for product in structured_data["products"][:5]:  # Limit for token management
                context_parts.append(f"""
Product: {product['name']}
SKU: {product['sku']}
Price: {product['price_jod']} JOD (Original: {product['original_price_jod']} JOD)
Stock: {product['stock_quantity']} units available
Warranty: {product['warranty_months']} months
{f"Promotion: {product['promotion_text']}" if product.get('promotion_text') else ""}
""")
        
        # Add service information
        if structured_data.get("services"):
            context_parts.append("\n🔧 AVAILABLE SERVICES:")
            for service in structured_data["services"]:
                context_parts.append(f"""
Service: {service['service_name']}
Category: {service['category']}
Price: {service['base_price_jod']} JOD
Duration: {service['duration_hours']} hours
Description: {service['description']}
""")
        
        # Add unstructured context
        if unstructured_data.get("chunks"):
            context_parts.append("\n📋 RELEVANT POLICIES & INFORMATION:")
            for i, chunk in enumerate(unstructured_data["chunks"], 1):
                context_parts.append(f"""
[Source {i}]: {chunk['source']}
{chunk['text']}
""")
        
        return "\n".join(context_parts)
    
    def _calculate_hybrid_confidence(
        self,
        structured_data: Dict[str, Any],
        unstructured_data: Dict[str, Any],
        query_analysis: Dict[str, Any]
    ) -> float:
        """Calculate confidence based on data quality and relevance"""
        base_confidence = 0.3
        
        # Boost for structured data matches
        if structured_data.get("products"):
            base_confidence += 0.3
        if structured_data.get("services"):
            base_confidence += 0.2
        
        # Boost for unstructured data quality
        chunks = unstructured_data.get("chunks", [])
        if chunks:
            avg_score = sum(chunk["score"] for chunk in chunks) / len(chunks)
            base_confidence += min(0.4, avg_score * 0.5)
        
        # Intent-based adjustments
        if query_analysis.get("requires_real_time_data") and structured_data.get("products"):
            base_confidence += 0.1
        
        return min(0.95, base_confidence)
    
    def _detect_language(self, text: str) -> str:
        """Enhanced language detection"""
        arabic_chars = len([c for c in text if '\u0600' <= c <= '\u06FF'])
        total_chars = len([c for c in text if c.isalpha()])
        
        if total_chars == 0:
            return "en"
        
        arabic_ratio = arabic_chars / total_chars
        return "ar" if arabic_ratio > 0.3 else "en"
    
    def _fallback_response(self, user_message: str, language: str) -> Dict[str, Any]:
        """Enhanced fallback response"""
        if language == "ar":
            message = "أعتذر، أواجه صعوبة في معالجة طلبك حالياً. يرجى المحاولة مرة أخرى أو الاتصال بفريق الدعم."
        else:
            message = "I apologize, but I'm having trouble processing your request right now. Please try again or contact our support team."
        
        return {
            "answer": message,
            "language": language,
            "sources": [],
            "confidence": 0.2,
            "data_sources": {"structured": False, "unstructured": False, "hybrid": False},
            "error": "system_error"
        }

# Global instance
enterprise_rag_service = EnterpriseRAGService()