"""
Prompt Service
Keeps prompts separate from business logic
"""

import logging
from typing import Dict, Any, List
from app.config import settings

logger = logging.getLogger(__name__)

class PromptService:
    """Simple service to manage all prompts in one place"""
    
    def __init__(self):
        # Store information - could be moved to config later
        self.store_info = {
            "name_ar": "تك مارت فلسطين",
            "name_en": "TechMart Palestine",
            "location_ar": "نابلس، فلسطين",
            "location_en": "Nablus, Palestine",
            "phone": "+970-9-234-5678",
            "email": "info@techmart-palestine.ps",
            "address_ar": "شارع الرفيدية، نابلس",
            "address_en": "Rafidia Street, Nablus",
            "hours_ar": {
                "sunday_thursday": "9:00 صباحاً - 8:00 مساءً",
                "friday": "9:00 صباحاً - 2:00 ظهراً",
                "saturday": "10:00 صباحاً - 8:00 مساءً"
            },
            "hours_en": {
                "sunday_thursday": "9:00 AM - 8:00 PM", 
                "friday": "9:00 AM - 2:00 PM",
                "saturday": "10:00 AM - 8:00 PM"
            }
        }
    
    def get_system_prompt(self, language: str) -> str:
        """Get system prompt for given language"""
        if language == "ar":
            return self._get_arabic_system_prompt()
        else:
            return self._get_english_system_prompt()
    
    def _get_arabic_system_prompt(self) -> str:
        """Arabic system prompt with strong language enforcement"""
        return f"""أنت مساعد ذكي لخدمة العملاء في {self.store_info['name_ar']}.

تعليمات إلزامية - لا يمكن تجاهلها:
1. يجب أن تكتب إجابتك بالعربية فقط
2. لا تستخدم أي كلمة بالإنجليزية في إجابتك
3. حتى لو كانت المعلومات باللغة الإنجليزية، اكتب الإجابة بالعربية
4. العميل يسأل بالعربية، فيجب أن تجيب بالعربية فقط

معلومات المتجر:
- الاسم: {self.store_info['name_ar']}
- الموقع: {self.store_info['location_ar']}
- الهاتف: {self.store_info['phone']}
- البريد: {self.store_info['email']}

ساعات العمل:
- الأحد - الخميس: {self.store_info['hours_ar']['sunday_thursday']}
- الجمعة: {self.store_info['hours_ar']['friday']}
- السبت: {self.store_info['hours_ar']['saturday']}

قواعد الإجابة:
- اذكر الأسعار بالدينار الأردني
- قدم معلومات دقيقة ومفيدة
- كن مهذباً ومهنياً
- إذا لم تعرف الإجابة، قل "لا أعرف هذه المعلومة، يرجى الاتصال بالمتجر"

تذكر: العميل يتحدث العربية، فاجب بالعربية فقط!"""

    def _get_english_system_prompt(self) -> str:
        """English system prompt with strong language enforcement"""
        return f"""You are a customer service assistant for {self.store_info['name_en']} in {self.store_info['location_en']}.

CRITICAL INSTRUCTIONS - Cannot be ignored:
1. You must write your response in English only
2. Do not use any Arabic words in your response
3. Even if information is in Arabic, write the answer in English
4. The customer is asking in English, so respond in English only

Store Information:
- Name: {self.store_info['name_en']}
- Location: {self.store_info['location_en']}
- Phone: {self.store_info['phone']}
- Email: {self.store_info['email']}

Store Hours:
- Sunday-Thursday: {self.store_info['hours_en']['sunday_thursday']}
- Friday: {self.store_info['hours_en']['friday']}
- Saturday: {self.store_info['hours_en']['saturday']}

Response Rules:
- Include prices in Jordanian Dinars (JOD)
- Provide accurate and helpful information
- Be polite and professional
- If you don't know something, say "I don't have that information, please contact the store"

Remember: Customer is asking in English, so respond in English only!"""

    def get_user_prompt(
        self,
        user_message: str,
        language: str,
        data_context: str = "",
        history_context: str = "",
        query_analysis: Dict[str, Any] = None
    ) -> str:
        """Get user prompt with context"""
        if language == "ar":
            return self._get_arabic_user_prompt(
                user_message, data_context, history_context, query_analysis
            )
        else:
            return self._get_english_user_prompt(
                user_message, data_context, history_context, query_analysis
            )
    
    def _get_arabic_user_prompt(
        self,
        user_message: str,
        data_context: str,
        history_context: str,
        query_analysis: Dict[str, Any] = None
    ) -> str:
        """Arabic user prompt with strong language enforcement"""
        prompt = f"""السؤال: {user_message}

{data_context}
{history_context}

تعليمات مهمة جداً:
- اكتب إجابتك بالعربية فقط
- لا تستخدم أي كلمة بالإنجليزية
- حتى لو كانت البيانات بالإنجليزية، اكتب الإجابة بالعربية
- إذا كان السؤال عن الساعات: {self.store_info['hours_ar']['sunday_thursday']}, الجمعة {self.store_info['hours_ar']['friday']}, السبت {self.store_info['hours_ar']['saturday']}
- إذا كان السؤال عن الاتصال: {self.store_info['phone']}
- اذكر الأسعار بالدينار الأردني

يجب أن تكون إجابتك بالعربية فقط!"""

        return prompt
    
    def _get_english_user_prompt(
        self,
        user_message: str,
        data_context: str,
        history_context: str,
        query_analysis: Dict[str, Any] = None
    ) -> str:
        """English user prompt with strong language enforcement"""
        prompt = f"""Question: {user_message}

{data_context}
{history_context}

IMPORTANT INSTRUCTIONS:
- Write your answer in English only
- Do not use any Arabic words
- Even if data is in Arabic, write the answer in English
- If asking about hours: {self.store_info['hours_en']['sunday_thursday']}, Friday {self.store_info['hours_en']['friday']}, Saturday {self.store_info['hours_en']['saturday']}
- If asking about contact: {self.store_info['phone']}
- Include prices in Jordanian Dinars (JOD)

Your response must be in English only!"""

        return prompt
    
    def get_fallback_response(self, language: str) -> str:
        """Get fallback response for errors"""
        if language == "ar":
            return f"""عذراً، أواجه صعوبة تقنية في معالجة طلبك حالياً.

للمساعدة:
📞 {self.store_info['phone']}
📧 {self.store_info['email']}
📍 {self.store_info['address_ar']}

ساعات العمل:
• الأحد - الخميس: {self.store_info['hours_ar']['sunday_thursday']}
• الجمعة: {self.store_info['hours_ar']['friday']}
• السبت: {self.store_info['hours_ar']['saturday']}"""
        else:
            return f"""I apologize, but I'm experiencing technical difficulties processing your request right now.

For assistance:
📞 {self.store_info['phone']}
📧 {self.store_info['email']}
📍 {self.store_info['address_en']}

Store Hours:
• Sunday-Thursday: {self.store_info['hours_en']['sunday_thursday']}
• Friday: {self.store_info['hours_en']['friday']}
• Saturday: {self.store_info['hours_en']['saturday']}"""
    
    def get_force_arabic_response(self, user_message: str) -> str:
        """Get forced Arabic response for common queries"""
        # Handle common store hours questions
        if any(word in user_message for word in ["ساعات", "العمل", "فتح", "مفتوح"]):
            return f"""ساعات عمل متجر {self.store_info['name_ar']}:

• الأحد - الخميس: {self.store_info['hours_ar']['sunday_thursday']}
• الجمعة: {self.store_info['hours_ar']['friday']}
• السبت: {self.store_info['hours_ar']['saturday']}

للاستفسارات: {self.store_info['phone']}
العنوان: {self.store_info['address_ar']}"""
        
        # Handle contact information requests
        if any(word in user_message for word in ["اتصال", "هاتف", "رقم", "تواصل"]):
            return f"""معلومات التواصل مع {self.store_info['name_ar']}:

📞 الهاتف: {self.store_info['phone']}
📧 البريد الإلكتروني: {self.store_info['email']}
📍 العنوان: {self.store_info['address_ar']}

ساعات العمل:
• الأحد - الخميس: {self.store_info['hours_ar']['sunday_thursday']}
• الجمعة: {self.store_info['hours_ar']['friday']}
• السبت: {self.store_info['hours_ar']['saturday']}"""
        
        # Generic Arabic fallback
        return f"""أهلاً وسهلاً بك في {self.store_info['name_ar']}.

للحصول على المساعدة:
📞 {self.store_info['phone']}
📧 {self.store_info['email']}
📍 {self.store_info['address_ar']}

نحن هنا لخدمتك!"""
    
    def get_simple_arabic_prompt(self, user_message: str) -> str:
        """Get simple Arabic prompt for forcing Arabic responses"""
        return f"""أجب على هذا السؤال بالعربية فقط:

السؤال: {user_message}

قواعد:
- اكتب بالعربية فقط
- لا تستخدم الإنجليزية
- كن مفيداً ومهذباً
- للمزيد من المعلومات: {self.store_info['phone']}

الإجابة بالعربية:"""

# Global instance
prompt_service = PromptService()