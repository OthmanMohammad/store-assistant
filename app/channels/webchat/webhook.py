"""
Webchat Webhook - Using the Updated RAG Service
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, List, Dict
import uuid
import json
import logging

from app.database import get_db
from app.models.user import User
from app.models.conversation import Conversation
from app.services.rag_service import enterprise_rag_service

logger = logging.getLogger(__name__)
router = APIRouter()

class WebMsg(BaseModel):
    text: str
    session_id: str | None = None
    locale: str | None = None

class ChatResponse(BaseModel):
    session_id: str
    text: str
    language: str
    sources: List[str] = []
    confidence: float = 0.0
    suggested_questions: List[str] = []

@router.post("/message", response_model=ChatResponse)
async def message(msg: WebMsg, db: Session = Depends(get_db)):
    """
    FIXED: Process chat message using Enterprise RAG Service
    """
    try:
        # Get or create session
        session_id = msg.session_id or str(uuid.uuid4())
        
        # Get or create user
        user = db.query(User).filter(User.session_id == session_id).first()
        if not user:
            user = User(
                session_id=session_id,
                preferred_language=msg.locale or "en"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # Get recent conversation history
        conversation_history = db.query(Conversation)\
            .filter(Conversation.session_id == session_id)\
            .order_by(Conversation.created_at.desc())\
            .limit(5)\
            .all()
        
        # Format conversation history for RAG
        formatted_history = []
        for conv in reversed(conversation_history):  # Reverse to get chronological order
            if conv.user_message:
                formatted_history.append({
                    "role": "user",
                    "content": conv.user_message
                })
            if conv.bot_response:
                formatted_history.append({
                    "role": "assistant", 
                    "content": conv.bot_response
                })
        
        logger.info(f"💬 Processing message for session {session_id}: {msg.text[:50]}...")
        
        # FIXED: Call the updated RAG service directly
        rag_response = await enterprise_rag_service.generate_response(
            user_message=msg.text,
            language=msg.locale or user.preferred_language or "auto",
            conversation_history=formatted_history,
            db=db  # Pass database session to RAG service
        )
        
        # Extract response components
        bot_response = rag_response["answer"]
        detected_language = rag_response["language"]
        sources = rag_response.get("sources", [])
        confidence = rag_response.get("confidence", 0.0)
        
        # Update user's preferred language if detected
        if detected_language != user.preferred_language:
            user.preferred_language = detected_language
            db.commit()
        
        # Save conversation to database
        conversation = Conversation(
            user_id=user.id,
            session_id=session_id,
            user_message=msg.text,
            bot_response=bot_response,
            language=detected_language,
            confidence=confidence,
            response_time_ms=0  # Could add timing here
        )
        db.add(conversation)
        db.commit()
        
        # Get suggested questions
        suggested_questions = await enterprise_rag_service.get_suggested_questions(detected_language)
        
        logger.info(f"✅ Response generated for session {session_id} - Confidence: {confidence:.2f}")
        
        return ChatResponse(
            session_id=session_id,
            text=bot_response,
            language=detected_language,
            sources=list(set(sources)),  # Remove duplicates
            confidence=confidence,
            suggested_questions=suggested_questions if not conversation_history else []
        )
        
    except Exception as e:
        logger.error(f"❌ Chat processing failed: {str(e)}", exc_info=True)
        
        # FIXED: Better error handling with proper fallback
        fallback_session = msg.session_id or str(uuid.uuid4())
        fallback_language = msg.locale or "en"
        
        # Use prompt service for fallback
        try:
            from app.services.prompt_service import prompt_service
            fallback_message = prompt_service.get_fallback_response(fallback_language)
        except:
            # Ultimate fallback
            if fallback_language == "ar":
                fallback_message = "عذراً، أواجه مشكلة تقنية. يرجى المحاولة مرة أخرى."
            else:
                fallback_message = "I apologize, but I'm experiencing technical difficulties. Please try again."
        
        return ChatResponse(
            session_id=fallback_session,
            text=fallback_message,
            language=fallback_language,
            sources=[],
            confidence=0.15,
            suggested_questions=[]
        )

@router.get("/suggestions")
async def get_suggestions(language: str = "en"):
    """Get suggested questions for the chat interface"""
    try:
        suggestions = await enterprise_rag_service.get_suggested_questions(language)
        return {
            "suggestions": suggestions,
            "language": language
        }
    except Exception as e:
        logger.error(f"❌ Failed to get suggestions: {str(e)}")
        return {"suggestions": [], "language": language}

@router.get("/history/{session_id}")
async def get_conversation_history(session_id: str, db: Session = Depends(get_db)):
    """Get conversation history for a session"""
    try:
        conversations = db.query(Conversation)\
            .filter(Conversation.session_id == session_id)\
            .order_by(Conversation.created_at.asc())\
            .limit(20)\
            .all()
        
        history = []
        for conv in conversations:
            history.append({
                "timestamp": conv.created_at.isoformat(),
                "user_message": conv.user_message,
                "bot_response": conv.bot_response,
                "language": conv.language,
                "confidence": conv.confidence
            })
        
        return {
            "session_id": session_id,
            "history": history,
            "total": len(history)
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get history: {str(e)}")
        return {"session_id": session_id, "history": [], "total": 0}

# ADDED: Debug endpoint to test RAG service directly
@router.post("/debug")
async def debug_message(msg: WebMsg, db: Session = Depends(get_db)):
    """Debug endpoint to test RAG service directly"""
    try:
        logger.info(f"🔍 Debug: Testing RAG with message: {msg.text}")
        
        # Call RAG service directly
        response = await enterprise_rag_service.generate_response(
            user_message=msg.text,
            language=msg.locale or "auto",
            conversation_history=[],
            db=db
        )
        
        return {
            "debug": True,
            "rag_response": response,
            "message": "RAG service working correctly",
            "confidence": response.get("confidence", 0)
        }
        
    except Exception as e:
        logger.error(f"❌ Debug endpoint failed: {str(e)}", exc_info=True)
        return {
            "debug": True,
            "error": str(e),
            "message": "RAG service failed",
            "confidence": 0
        }