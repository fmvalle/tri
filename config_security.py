"""
Configurações de Segurança para o Sistema TRI Dashboard
Use este arquivo para configurar autenticação em ambiente de produção
"""

import hashlib
import os
from typing import Dict, Optional

class SecurityConfig:
    """Configurações de segurança do sistema"""
    
    def __init__(self):
        # Credenciais padrão (ALTERAR EM PRODUÇÃO!)
        self.default_credentials = {
            "admin": "tri2025",
        }
        
        # Configurações de segurança
        self.max_login_attempts = 3
        self.session_timeout = 3600  # 1 hora em segundos
        self.require_https = True
        self.enable_audit_log = True
    
    def hash_password(self, password: str) -> str:
        """Cria hash seguro da senha"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, username: str, password: str) -> bool:
        """Verifica credenciais do usuário"""
        if username in self.default_credentials:
            return self.default_credentials[username] == password
        return False
    
    def get_secure_credentials(self) -> Dict[str, str]:
        """Retorna credenciais com senhas hasheadas"""
        return {
            username: self.hash_password(password)
            for username, password in self.default_credentials.items()
        }

# Configurações de ambiente
class EnvironmentConfig:
    """Configurações por ambiente"""
    
    @staticmethod
    def is_production() -> bool:
        """Verifica se está em ambiente de produção"""
        return os.getenv('ENVIRONMENT', 'development') == 'production'
    
    @staticmethod
    def get_database_url() -> Optional[str]:
        """Retorna URL do banco de dados"""
        return os.getenv('DATABASE_URL')
    
    @staticmethod
    def get_secret_key() -> str:
        """Retorna chave secreta para sessões"""
        return os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')

# Instruções de uso
if __name__ == "__main__":
    print("🔐 Configurações de Segurança - Sistema TRI")
    print("=" * 50)
    
    config = SecurityConfig()
    
    print("📋 Credenciais Atuais:")
    for username, password in config.default_credentials.items():
        print(f"  👤 {username}: {password}")
    
    print("\n⚠️  IMPORTANTE PARA PRODUÇÃO:")
    print("1. Altere as credenciais padrão")
    print("2. Use senhas fortes e únicas")
    print("3. Implemente autenticação com banco de dados")
    print("4. Configure HTTPS")
    print("5. Ative logs de auditoria")
    print("6. Configure backup automático")
    
    print("\n🔧 Para alterar credenciais:")
    print("1. Edite o arquivo config_security.py")
    print("2. Altere o dicionário default_credentials")
    print("3. Reinicie o dashboard")
    
    print("\n🌐 Para ambiente de produção:")
    print("export ENVIRONMENT=production")
    print("export SECRET_KEY=your-secure-secret-key")
    print("export DATABASE_URL=your-database-url")
