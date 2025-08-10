"""
RAG (Retrieval-Augmented Generation) Service
Combines vector search with AI generation for intelligent responses
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import openai
from app.config import settings
from app.services.vector_service import vector_service

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        self.vector_service = vector_service
        self.openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # RAG configuration
        self.default_top_k = 5
        self.similarity_threshold = 0.7
        self.max_context_length = 3000  # Characters for context
        
    async def generate_response(
        self,
        user_message: str,
        language: str = "auto",
        conversation_history: Optional[List[Dict[str, str]]] = None,
        use_knowledge_base: bool = True
    ) -> Dict[str, Any]:
        """
        Generate an intelligent response using RAG
        
        Args:
            user_message: User's input message
            language: Preferred language ("en", "ar", or "auto")
            conversation_history: Previous conversation context
            use_knowledge_base: Whether to use document retrieval
            
        Returns:
            Response with answer, sources, and metadata
        """
        try:
            logger.info(f"🤖 Generating RAG response for: {user_message[:50]}...")
            
            # Step 1: Detect language if auto
            detected_language = self._detect_language(user_message) if language == "auto" else language
            
            # Step 2: Retrieve relevant context from knowledge base
            context_chunks = []
            sources = []
            
            if use_knowledge_base:
                context_chunks, sources = await self._retrieve_context(
                    user_message, 
                    language=detected_language
                )
            
            # Step 3: Generate response using AI
            ai_response = await self._generate_ai_response(
                user_message=user_message,
                context_chunks=context_chunks,
                conversation_history=conversation_history or [],
                language=detected_language
            )
            
            # Step 4: Format final response
            response = {
                "answer": ai_response,
                "language": detected_language,
                "sources": sources,
                "context_used": len(context_chunks) > 0,
                "confidence": self._calculate_confidence(context_chunks),
                "metadata": {
                    "query_length": len(user_message),
                    "context_chunks": len(context_chunks),
                    "total_sources": len(set(sources))
                }
            }
            
            logger.info(f"✅ RAG response generated successfully")
            return response
            
        except Exception as e:
            logger.error(f"❌ RAG response generation failed: {str(e)}")
            
            # Fallback response
            return {
                "answer": "I apologize, but I'm having trouble processing your request right now. Please try again or contact our support team.",
                "language": language if language != "auto" else "en",
                "sources": [],
                "context_used": False,
                "confidence": 0.0,
                "error": str(e)
            }
    
    async def _retrieve_context(
        self, 
        query: str, 
        language: str = "en"
    ) -> Tuple[List[str], List[str]]:
        """
        Retrieve relevant context from vector database
        
        Args:
            query: Search query
            language: Language filter
            
        Returns:
            Tuple of (context_chunks, source_names)
        """
        try:
            # Create language filter if specified
            filter_dict = None
            if language in ["en", "ar"]:
                filter_dict = {"language": language}
            
            # Search for similar content
            search_results = await self.vector_service.search_similar(
                query_text=query,
                top_k=self.default_top_k,
                filter_dict=filter_dict
            )
            
            # Filter by similarity threshold and extract context
            context_chunks = []
            sources = []
            
            for result in search_results:
                if result["score"] >= self.similarity_threshold:
                    chunk_text = result["metadata"].get("text", "")
                    source_name = result["metadata"].get("source", "Unknown")
                    
                    if chunk_text:
                        context_chunks.append(chunk_text)
                        sources.append(source_name)
            
            # Limit total context length
            context_chunks = self._limit_context_length(context_chunks)
            
            logger.info(f"🔍 Retrieved {len(context_chunks)} relevant chunks")
            return context_chunks, sources
            
        except Exception as e:
            logger.error(f"❌ Context retrieval failed: {str(e)}")
            return [], []
    
    def _limit_context_length(self, chunks: List[str]) -> List[str]:
        """Limit total context to stay within token limits"""
        total_length = 0
        limited_chunks = []
        
        for chunk in chunks:
            if total_length + len(chunk) <= self.max_context_length:
                limited_chunks.append(chunk)
                total_length += len(chunk)
            else:
                break
        
        return limited_chunks
    
    async def _generate_ai_response(
        self,
        user_message: str,
        context_chunks: List[str],
        conversation_history: List[Dict[str, str]],
        language: str = "en"
    ) -> str:
        """
        Generate AI response using OpenAI with retrieved context
        
        Args:
            user_message: User's question
            context_chunks: Retrieved context from documents
            conversation_history: Previous conversation
            language: Response language
            
        Returns:
            Generated response text
        """
        try:
            # Build system prompt
            system_prompt = self._build_system_prompt(language)
            
            # Build context section
            context_section = ""
            if context_chunks:
                context_section = "\n\nRelevant Information from Documents:\n"
                for i, chunk in enumerate(context_chunks, 1):
                    context_section += f"\n[Context {i}]: {chunk}\n"
            
            # Build conversation history
            history_section = ""
            if conversation_history:
                history_section = "\n\nRecent Conversation:\n"
                for msg in conversation_history[-3:]:  # Last 3 messages
                    role = "Customer" if msg.get("role") == "user" else "Assistant"
                    history_section += f"{role}: {msg.get('content', '')}\n"
            
            # Combine into user prompt
            user_prompt = f"""
Customer Question: {user_message}
{context_section}
{history_section}

Please provide a helpful, accurate response based on the available information. If the context doesn't contain relevant information, provide a general helpful response and suggest contacting customer service.
"""
            
            # Generate response
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content.strip()
            logger.info(f"✅ AI response generated: {len(ai_response)} characters")
            
            return ai_response
            
        except Exception as e:
            logger.error(f"❌ AI response generation failed: {str(e)}")
            return "I'm sorry, I'm having trouble generating a response right now. Please try again."
    
    def _build_system_prompt(self, language: str) -> str:
        """Build system prompt based on language"""
        
        if language == "ar":
            return """أنت مساعد ذكي لخدمة العملاء في متجر. مهمتك هي:

1. مساعدة العملاء بأسئلتهم حول المتجر والمنتجات والخدمات
2. استخدام المعلومات المتوفرة من وثائق المتجر عند الإجابة
3. كن مهذباً ومفيداً ودقيقاً في إجاباتك
4. إذا لم تكن متأكداً من الإجابة، اقترح على العميل الاتصال بخدمة العملاء
5. حافظ على نبرة ودية ومهنية

تذكر: أنت تمثل المتجر، لذا قدم خدمة عملاء ممتازة."""
        
        else:  # English
            return """You are an intelligent customer service assistant for a store. Your role is to:

1. Help customers with questions about the store, products, and services
2. Use information from store documents when available to provide accurate answers
3. Be polite, helpful, and accurate in your responses
4. If you're unsure about something, suggest the customer contact customer service
5. Maintain a friendly and professional tone

Remember: You represent the store, so provide excellent customer service while being honest about what you know and don't know."""
    
    def _detect_language(self, text: str) -> str:
        """Simple language detection for Arabic vs English"""
        # Count Arabic characters
        arabic_chars = len([c for c in text if '\u0600' <= c <= '\u06FF'])
        total_chars = len([c for c in text if c.isalpha()])
        
        if total_chars == 0:
            return "en"
        
        arabic_ratio = arabic_chars / total_chars
        return "ar" if arabic_ratio > 0.3 else "en"
    
    def _calculate_confidence(self, context_chunks: List[str]) -> float:
        """Calculate confidence score based on retrieved context"""
        if not context_chunks:
            return 0.3  # Low confidence without context
        
        # Base confidence on number and quality of chunks
        base_confidence = min(0.9, 0.5 + (len(context_chunks) * 0.1))
        
        return round(base_confidence, 2)
    
    async def get_suggested_questions(self, language: str = "en") -> List[str]:
        """Get suggested questions based on available content"""
        
        if language == "ar":
            return [
                "ما هي ساعات عمل المتجر؟",
                "ما هي سياسة الإرجاع؟",
                "ما هي طرق الدفع المقبولة؟",
                "هل تقدمون خدمة التوصيل؟",
                "كيف يمكنني التواصل مع خدمة العملاء؟"
            ]
        else:
            return [
                "What are your store hours?",
                "What is your return policy?",
                "What payment methods do you accept?",
                "Do you offer delivery services?",
                "How can I contact customer service?"
            ]

# Global instance
rag_service = RAGService()