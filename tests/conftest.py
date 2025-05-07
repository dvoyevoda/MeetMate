import sys
import os

# Add project root to path so that 'app' package can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Override DATABASE_URL for pytest to use in-memory SQLite
os.environ["DATABASE_URL"] = "sqlite:///:memory:" 