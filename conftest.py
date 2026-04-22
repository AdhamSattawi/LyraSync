import os
import sys

# Forces pytest to add the project root to PYTHONPATH so `from app.x import y` works
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Mock environment variables for testing
os.environ["DATABASE_URL"] = "postgresql+asyncpg://user:pass@localhost/testdb"
os.environ["OPENAI_API_KEY"] = "sk-test-key"
os.environ["TWILIO_ACCOUNT_SID"] = "ACtest"
os.environ["TWILIO_AUTH_TOKEN"] = "test-token"
os.environ["TWILIO_PHONE_NUMBER"] = "+1234567890"
os.environ["ADMIN_SECRET_KEY"] = "test-admin-key"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "60"
