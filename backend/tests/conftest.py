# backend/test/conftest.py

import sys
import os
import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Ce script récupère le dossier parent (backend) et dit à Python d'aller chercher dedans !
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))