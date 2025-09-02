"""
Módulo core do Sistema TRI
Contém os componentes principais do sistema
"""

from .tri_engine import TRIEngine
from .data_processor import DataProcessor
from .validators import DataValidator
from .item_calibration import ItemCalibrator

# Exposição de serviços de persistência opcional
try:
    from db.session import get_session
except Exception:
    # Ignora durante inicialização sem DB
    def get_session():
        return None

__all__ = ['TRIEngine', 'DataProcessor', 'DataValidator', 'ItemCalibrator']

