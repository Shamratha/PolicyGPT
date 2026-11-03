import os
import sys
import tempfile

# Run the whole suite against a throw-away SQLite DB + Chroma folder in offline AI mode,
# so tests never touch the real policygpt.db or call paid APIs.
_TMP = tempfile.mkdtemp(prefix="policygpt-tests-")
os.environ["OPENAI_API_KEY"] = "sk-mock-key-for-testing"
os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(_TMP, "test.db").replace("\\", "/")
os.environ["CHROMA_PERSIST_DIR"] = os.path.join(_TMP, "chroma")
os.environ["ENVIRONMENT"] = "development"
os.environ["CLERK_JWKS_URL"] = ""

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
