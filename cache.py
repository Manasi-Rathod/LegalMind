import redis
import hashlib
from langchain_community.chat_message_histories import RedisChatMessageHistory


class RedisCache:
    """Handles query caching and chat history using Redis."""

    def __init__(self, redis_url="redis://localhost:6379/0"):
        try:
            self.client = redis.Redis.from_url(redis_url, decode_responses=True)
            self.client.ping()  # Check if Redis is reachable
            print("🔌 Redis connected successfully.")
        except Exception:
            print("⚠️ Redis not available! Falling back to in-memory cache.")
            self.client = None  # If Redis is unavailable

    # 🟢 Generate a unique cache key using query + session ID
    def make_cache_key(self, query, session_id):
        key_raw = f"{session_id}:{query}".encode()
        return "llm_cache:" + hashlib.sha256(key_raw).hexdigest()

    # 🟢 Save result in Redis (expires in 24h)
    def set(self, key, value):
        if self.client:
            self.client.set(key, value, ex=86400)  # 24 hours = 86400 sec

    # 🟢 Get cached result
    def get(self, key):
        return self.client.get(key) if self.client else None

    # 🟢 Chat history management
    def get_chat_history(self, session_id):
        if not self.client:
            print("📦 Using in-memory chat history.")
            return MemoryChatHistory()

        print("💾 Using Redis-based chat history.")
        return RedisChatMessageHistory(
            session_id=session_id,
            url=self.client.connection_pool.connection_kwargs.get("host", "localhost")
            + ":" + str(self.client.connection_pool.connection_kwargs.get("port", 6379))
        )


# 🔁 Fallback chat history (if Redis unavailable)
class MemoryChatHistory:
    def __init__(self):
        self.messages = []

    def add_user_message(self, text):
        self.messages.append({"role": "user", "content": text})

    def add_ai_message(self, text):
        self.messages.append({"role": "assistant", "content": text})
