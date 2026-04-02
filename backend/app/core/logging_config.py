import logging
import sys
import structlog

def setup_logging():
    # 1. On nettoie les loggers par défaut pour éviter les doublons
    logging.basicConfig(level=logging.INFO, stream=sys.stdout, format="%(message)s")
    
    # On désactive la propagation des logs d'Uvicorn pour ne pas polluer
    logging.getLogger("uvicorn.access").handlers = []
    logging.getLogger("uvicorn").handlers = []

    processors = [
        # Ajoute le niveau de log (info, error...)
        structlog.processors.add_log_level,
        # Ajoute l'horodatage
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    # 💡 L'ASTUCE : Si on est sur un terminal (local), on fait du joli texte coloré.
    # Sinon (dans un conteneur / fichier), on sort du JSON pur !
    if sys.stdout.isatty():
        processors.append(structlog.dev.ConsoleRenderer(colors=True))
    else:
        processors.append(structlog.processors.JSONRenderer())

    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )