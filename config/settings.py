"""
Configurações centralizadas para o sistema TRI
"""
import os
from pathlib import Path
from typing import Dict, Any

# Diretórios base
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
INPUT_DIR = DATA_DIR / "input"
OUTPUT_DIR = DATA_DIR / "output"
LOGS_DIR = BASE_DIR / "logs"
REPORTS_DIR = BASE_DIR / "reports"

# Criar diretórios se não existirem
for dir_path in [DATA_DIR, INPUT_DIR, OUTPUT_DIR, LOGS_DIR, REPORTS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Banco de Dados
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{(BASE_DIR / 'tri.db').as_posix()}")

# Configurações TRI
TRI_CONFIG = {
    "default_a": 1.0,      # Discriminação padrão
    "default_b": 0.0,      # Dificuldade padrão
    "default_c": 0.2,      # Acerto casual padrão
    "theta_bounds": (-4, 4),  # Limites para estimação de theta
    "enem_base": 500,      # Nota base ENEM
    "enem_scale": 100,     # Escala ENEM
    "constant": 1.7,       # Constante do modelo 3PL
    "max_iterations": 1000,  # Máximo de iterações para otimização
    "tolerance": 1e-6      # Tolerância para convergência
}

# Configurações de arquivos
FILE_CONFIG = {
    "input_separator": ";",
    "encoding": "utf-8",
    "date_format": "%Y-%m-%d",
    "decimal_separator": ".",
    "thousands_separator": ","
}

# Configurações de validação
VALIDATION_CONFIG = {
    "min_students": 10,
    "max_students": 100000,
    "min_items": 5,
    "max_items": 100,
    "required_columns": ["CodPessoa", "Questao", "RespostaAluno", "Gabarito"],
    "param_columns": ["a", "b", "c"]
}

# Configurações de visualização
VISUALIZATION_CONFIG = {
    "figure_size": (12, 8),
    "dpi": 300,
    "style": "seaborn-v0_8",
    "color_palette": "viridis",
    "font_size": 12,
    "save_format": "png"
}

# Configurações de logging
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": LOGS_DIR / "tri_system.log",
    "max_size": 10 * 1024 * 1024,  # 10MB
    "backup_count": 5
}

# Configurações de editoras e séries
PUBLISHERS = {
    "compartilha": "Compartilha",
    "edusfera": "Edusfera", 
    "sfb": "SFB",
    "uno": "Uno"
}

GRADES = {
    "1": "1° ano",
    "2": "2° ano", 
    "3": "3° ano"
}

SUBJECTS = {
    "CH": "Ciências Humanas",
    "CN": "Ciências da Natureza",
    "LP": "Linguagens e Códigos",
    "MT": "Matemática"
}

def get_config() -> Dict[str, Any]:
    """Retorna todas as configurações em um dicionário"""
    return {
        "tri": TRI_CONFIG,
        "file": FILE_CONFIG,
        "validation": VALIDATION_CONFIG,
        "visualization": VISUALIZATION_CONFIG,
        "logging": LOGGING_CONFIG,
        "publishers": PUBLISHERS,
        "grades": GRADES,
        "subjects": SUBJECTS
        ,
        "database_url": DATABASE_URL
    }
