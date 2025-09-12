#!/usr/bin/env python3
"""
Script para atualizar o schema do banco de dados
Adiciona o campo 'area' à tabela assessment
"""

import os
import sys
from sqlalchemy import text
from db.session_v2 import get_db_session_context, test_connection

def update_database_schema():
    """Atualiza o schema do banco de dados"""
    print("🔄 Atualizando schema do banco de dados...")
    
    try:
        # Testar conexão
        if not test_connection():
            print("❌ Erro na conexão com o banco de dados")
            return False
        
        with get_db_session_context() as session:
            # Verificar se a coluna 'area' já existe
            result = session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'assessment' 
                AND column_name = 'area'
            """))
            
            if result.fetchone():
                print("✅ Coluna 'area' já existe na tabela 'assessment'")
                return True
            
            # Adicionar coluna 'area'
            print("➕ Adicionando coluna 'area' à tabela 'assessment'...")
            session.execute(text("""
                ALTER TABLE assessment 
                ADD COLUMN area VARCHAR
            """))
            
            session.commit()
            print("✅ Coluna 'area' adicionada com sucesso!")
            
            # Atualizar registros existentes com valor padrão
            print("🔄 Atualizando registros existentes...")
            session.execute(text("""
                UPDATE assessment 
                SET area = 'Linguagens e suas Tecnologias' 
                WHERE area IS NULL
            """))
            
            session.commit()
            print("✅ Registros existentes atualizados!")
            
            return True
            
    except Exception as e:
        print(f"❌ Erro ao atualizar schema: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando atualização do schema do banco de dados...")
    
    if update_database_schema():
        print("✅ Schema atualizado com sucesso!")
        sys.exit(0)
    else:
        print("❌ Falha na atualização do schema")
        sys.exit(1)

