"""Configuracion de logging."""
import logging
import sys

FORMATO = "%(asctime)s | %(levelname)-7s | %(name)-20s | %(message)s"


def configurar_logger(nombre="SIES", nivel=None):
    """Retorna un logger con el formato estandar del proyecto."""
    if nivel is None:
        from src.config import LOG_LEVEL
        nivel = LOG_LEVEL
    logger = logging.getLogger(nombre)
    logger.setLevel(getattr(logging, str(nivel).upper(), logging.INFO))
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(FORMATO))
        logger.addHandler(handler)
    logger.propagate = False
    return logger
