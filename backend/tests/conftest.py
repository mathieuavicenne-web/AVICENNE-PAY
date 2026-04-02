import sys
import os

# Ce script récupère le dossier parent (backend) et dit à Python d'aller chercher dedans !
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))