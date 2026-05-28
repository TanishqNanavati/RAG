import logging
from typing import List
from sqlalchemy.orm import Session
from app.models.chat import ChatSession, ChatMessage
from openai import OpenAI
import os
from app.core.config import settings

logger = logging.getLogger(__name__)

class ConversationManager:
    """Manages chat sessions, persists conversation history, and rewrites follow-up queries."""

    def __init__(self) -> None:
        model_name = settings.gemini_model or "gpt-4o-mini"
        api_key = settings.gemini_api_key or os.environ.get("OPENAI_API_KEY", "dummy_key")
        base_url = settings.openai_base_url
        self.model_name = model_name
        
        try:
            self.client = OpenAI(api_key=api_key, base_url=base_url)
            logger.info("Initialized ConversationManager with LLM client.")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client in ConversationManager: {e}")
            self.client = None

    def get_or_create_session(self, db: Session, session_id: str, title: str = None, user_id: int = None) -> ChatSession:
        """Retrieves an existing session or creates a new one."""
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            session = ChatSession(id=session_id, title=title or f"Chat {session_id[:8]}", user_id=user_id)
            db.add(session)
            db.commit()
            db.refresh(session)
            logger.info(f"Created new chat session: {session_id}")
        elif user_id and session.user_id != user_id:
            # Bind to user if it was anonymous
            session.user_id = user_id
            db.commit()
        return session

    def add_message(self, db: Session, session_id: str, role: str, content: str, user_id: int = None) -> ChatMessage:
        """Saves a message to the database."""
        # Ensure session exists
        self.get_or_create_session(db, session_id, user_id=user_id)
        
        msg = ChatMessage(session_id=session_id, role=role, content=content)
        db.add(msg)
        db.commit()
        db.refresh(msg)
        logger.info(f"Added {role} message to session {session_id}")
        return msg

    def get_history(self, db: Session, session_id: str, limit: int = 10) -> List[ChatMessage]:
        """Retrieves recent messages in the conversation."""
        return db.query(ChatMessage)\
            .filter(ChatMessage.session_id == session_id)\
            .order_by(ChatMessage.created_at.asc())\
            .limit(limit)\
            .all()

    def rewrite_query(self, db: Session, session_id: str, new_query: str) -> str:
        """
        Uses LLM to rewrite user query based on recent chat history.
        If there is no history, returns the original query.
        """
        if not self.client:
            logger.warning("LLM client not available, returning original query.")
            return new_query
            
        history = self.get_history(db, session_id, limit=6)
        if not history:
            return new_query

        # Construct context transcript
        transcript = ""
        for msg in history:
            role_label = "User" if msg.role == "user" else "Assistant"
            transcript += f"{role_label}: {msg.content}\n"

        system_prompt = (
            "You are a helpful query rewriter for a RAG search system.\n"
            "Given the following conversation history and the new user query, rewrite the new query into a standalone search query "
            "that captures all the necessary context from the conversation.\n"
            "If the query is already standalone or does not refer to past messages, return the exact original query.\n"
            "Do NOT answer the question. Only return the rewritten query."
        )

        user_content = f"Conversation History:\n{transcript}\nNew Query: {new_query}\n\nRewritten standalone query:"

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.0
            )
            rewritten = response.choices[0].message.content or ""
            rewritten_clean = rewritten.strip()
            logger.info(f"Query rewritten: '{new_query}' -> '{rewritten_clean}'")
            return rewritten_clean
        except Exception as e:
            logger.error(f"Query rewriting failed, falling back to original: {e}")
            return new_query
