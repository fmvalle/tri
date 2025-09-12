"""
Modelos SQLAlchemy para o Sistema TRI Profissional
Baseado no schema PostgreSQL fornecido
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from datetime import datetime
import uuid

Base = declarative_base()


class User(Base):
    """Modelo de usuário para autenticação"""
    __tablename__ = 'user'
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=True)
    username = Column(String, nullable=True, unique=True)
    password = Column(String, nullable=True)  # MD5 hash
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', name='{self.name}')>"


class Assessment(Base):
    """Modelo de avaliação - nível hierárquico superior"""
    __tablename__ = 'assessment'
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    year = Column(Integer, nullable=True)
    cicle = Column(String, nullable=True)
    level = Column(String, nullable=True)
    area = Column(String, nullable=True)  # Área do conhecimento
    description = Column(String, nullable=True)
    
    # Relacionamentos
    executions = relationship("Execution", back_populates="assessment", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Assessment(id={self.id}, year={self.year}, level='{self.level}')>"


class Dataset(Base):
    """Modelo de dataset - arquivos de dados"""
    __tablename__ = 'datasets'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    source_type = Column(String, nullable=False)  # 'csv', 'excel', 'anchor'
    file_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    executions = relationship("Execution", back_populates="dataset")
    
    def __repr__(self):
        return f"<Dataset(id={self.id}, name='{self.name}', type='{self.source_type}')>"


class ParametersSet(Base):
    """Modelo de conjunto de parâmetros"""
    __tablename__ = 'parameters_sets'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_anchor = Column(Boolean, nullable=False, default=False)
    
    # Relacionamentos
    item_parameters = relationship("ItemParameter", back_populates="parameters_set", cascade="all, delete-orphan")
    executions = relationship("Execution", back_populates="parameters_set")
    
    def __repr__(self):
        return f"<ParametersSet(id={self.id}, name='{self.name}', is_anchor={self.is_anchor})>"


class ItemParameter(Base):
    """Modelo de parâmetros de itens"""
    __tablename__ = 'item_parameters'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    parameters_set_id = Column(Integer, ForeignKey('parameters_sets.id'), nullable=False)
    questao = Column(Integer, nullable=False)
    a = Column(Float, nullable=False)  # Parâmetro de discriminação
    b = Column(Float, nullable=False)  # Parâmetro de dificuldade
    c = Column(Float, nullable=False)  # Parâmetro de acerto casual
    is_anchor = Column(Boolean, default=False)
    
    # Relacionamentos
    parameters_set = relationship("ParametersSet", back_populates="item_parameters")
    
    def __repr__(self):
        return f"<ItemParameter(questao={self.questao}, a={self.a}, b={self.b}, c={self.c})>"


class Execution(Base):
    """Modelo de execução - processamento TRI"""
    __tablename__ = 'executions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    dataset_id = Column(Integer, ForeignKey('datasets.id'), nullable=True)
    parameters_set_id = Column(Integer, ForeignKey('parameters_sets.id'), nullable=True)
    assessment_id = Column(PostgresUUID(as_uuid=True), ForeignKey('assessment.id'), nullable=True)
    status = Column(String, nullable=False)  # 'pending', 'running', 'completed', 'failed'
    notes = Column(Text, nullable=True)
    name = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    dataset = relationship("Dataset", back_populates="executions")
    parameters_set = relationship("ParametersSet", back_populates="executions")
    assessment = relationship("Assessment", back_populates="executions")
    student_results = relationship("StudentResult", back_populates="execution", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Execution(id={self.id}, status='{self.status}', assessment_id={self.assessment_id})>"


class StudentResult(Base):
    """Modelo de resultados dos estudantes"""
    __tablename__ = 'student_results'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    execution_id = Column(Integer, ForeignKey('executions.id'), nullable=False)
    cod_pessoa = Column(String, nullable=False)
    theta = Column(Float, nullable=False)
    enem_score = Column(Float, nullable=False)
    acertos = Column(Integer, nullable=False)
    total_itens = Column(Integer, nullable=False)
    
    # Relacionamentos
    execution = relationship("Execution", back_populates="student_results")
    
    def __repr__(self):
        return f"<StudentResult(cod_pessoa='{self.cod_pessoa}', theta={self.theta}, enem_score={self.enem_score})>"
