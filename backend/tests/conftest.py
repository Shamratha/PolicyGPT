import os

# Automatically intercept and mock environment variables for the test suite
# This guarantees that tests do not hit live billing endpoints and use local mock responses.
os.environ["OPENAI_API_KEY"] = "sk-mock-key-for-testing"
