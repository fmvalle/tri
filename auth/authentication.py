"""
Sistema de autenticação para o Sistema TRI Profissional
"""

import hashlib
import streamlit as st
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from db.models_v2 import User
from db.session_v2 import get_db_session_context
import logging

logger = logging.getLogger(__name__)


class AuthenticationManager:
    """Gerenciador de autenticação"""
    
    def __init__(self):
        self.session_timeout = 3600  # 1 hora em segundos
    
    def hash_password_md5(self, password: str) -> str:
        """Gera hash MD5 da senha"""
        return hashlib.md5(password.encode()).hexdigest()
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verifica se a senha está correta"""
        return self.hash_password_md5(password) == hashed_password
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Autentica usuário com username e senha"""
        try:
            with get_db_session_context() as session:
                user = session.query(User).filter(User.username == username).first()
                
                if user and self.verify_password(password, user.password):
                    # Retornar dados do usuário como dicionário para evitar problemas de sessão
                    return {
                        'id': str(user.id),
                        'username': user.username,
                        'name': user.name,
                        'created_at': user.created_at
                    }
                return None
                
        except Exception as e:
            logger.error(f"Erro na autenticação: {e}")
            return None
    
    def login_user(self, user_data: Dict[str, Any]) -> None:
        """Realiza login do usuário no Streamlit"""
        st.session_state['authenticated'] = True
        st.session_state['user_id'] = user_data['id']
        st.session_state['username'] = user_data['username']
        st.session_state['user_name'] = user_data['name']
        st.session_state['login_time'] = datetime.now()
        
        logger.info(f"Usuário {user_data['username']} logado com sucesso")
    
    def logout_user(self) -> None:
        """Realiza logout do usuário"""
        username = st.session_state.get('username', 'Unknown')
        st.session_state.clear()
        logger.info(f"Usuário {username} deslogado")
    
    def is_authenticated(self) -> bool:
        """Verifica se o usuário está autenticado"""
        if not st.session_state.get('authenticated', False):
            return False
        
        # Verificar timeout da sessão
        login_time = st.session_state.get('login_time')
        if login_time:
            if datetime.now() - login_time > timedelta(seconds=self.session_timeout):
                self.logout_user()
                return False
        
        return True
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Retorna informações do usuário atual"""
        if not self.is_authenticated():
            return None
        
        return {
            'id': st.session_state.get('user_id'),
            'username': st.session_state.get('username'),
            'name': st.session_state.get('user_name'),
            'login_time': st.session_state.get('login_time')
        }
    
    def require_auth(self, func):
        """Decorator para exigir autenticação"""
        def wrapper(*args, **kwargs):
            if not self.is_authenticated():
                st.error("🔒 Acesso negado. Faça login para continuar.")
                st.stop()
            return func(*args, **kwargs)
        return wrapper


def show_login_form() -> bool:
    """Exibe formulário de login e retorna True se login foi bem-sucedido"""
    st.title("🔐 Sistema TRI - Login")
    st.markdown("---")
    
    with st.form("login_form"):
        st.subheader("Acesso ao Sistema")
        
        username = st.text_input("👤 Usuário", placeholder="Digite seu username")
        password = st.text_input("🔑 Senha", type="password", placeholder="Digite sua senha")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            login_button = st.form_submit_button("🚀 Entrar", use_container_width=True)
        
        if login_button:
            if not username or not password:
                st.error("❌ Por favor, preencha todos os campos.")
                return False
            
            auth_manager = AuthenticationManager()
            user_data = auth_manager.authenticate_user(username, password)
            
            if user_data:
                auth_manager.login_user(user_data)
                st.success(f"✅ Bem-vindo, {user_data['name'] or user_data['username']}!")
                st.rerun()
                return True
            else:
                st.error("❌ Usuário ou senha incorretos.")
                return False
    
    return False


def show_logout_button():
    """Exibe botão de logout"""
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        user_info = AuthenticationManager().get_current_user()
        if user_info:
            st.write(f"👤 **{user_info['name'] or user_info['username']}**")
    
    with col3:
        if st.button("🚪 Sair", use_container_width=True, key="btn_logout"):
            AuthenticationManager().logout_user()
            st.rerun()


def require_authentication():
    """Função principal para verificar autenticação"""
    if not AuthenticationManager().is_authenticated():
        show_login_form()
        st.stop()
    # Removido show_logout_button() para evitar duplicação
