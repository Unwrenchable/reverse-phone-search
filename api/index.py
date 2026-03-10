"""
Vercel serverless entry point.

Vercel's Python runtime detects the ``app`` WSGI object in this file and
uses it to serve every incoming request.  The database is stored in
``/tmp`` (the only writable location on Vercel) and seeded with sample
data on each cold start.
"""
import os
import sys

# Ensure the project root is on the path so ``app`` and ``database``
# can be imported regardless of where Vercel invokes this file from.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app  # noqa: E402  (Flask WSGI object)
from database import init_db  # noqa: E402

# Seed the database on cold start.  ``init_db`` uses INSERT OR IGNORE so
# it is safe to call multiple times on warm instances.
init_db()
