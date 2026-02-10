"""
Configuración de logging para la aplicación Fantasy Valorant.
"""
import logging

# Logger por defecto
logger = logging.getLogger("fantasy_valorant")
logger.setLevel(logging.INFO)

# Handler para consola si no hay handlers
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
