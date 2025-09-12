"""
CRUD operations para o Sistema TRI Profissional
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from db.models_v2 import (
    User, Assessment, Dataset, ParametersSet, 
    ItemParameter, Execution, StudentResult
)
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class UserCRUD:
    """CRUD para usuários"""
    
    @staticmethod
    def get_user_by_username(session: Session, username: str) -> Optional[User]:
        """Busca usuário por username"""
        return session.query(User).filter(User.username == username).first()
    
    @staticmethod
    def get_user_by_id(session: Session, user_id: str) -> Optional[User]:
        """Busca usuário por ID"""
        return session.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def create_user(session: Session, name: str, username: str, password_hash: str) -> User:
        """Cria novo usuário"""
        user = User(name=name, username=username, password=password_hash)
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
    
    @staticmethod
    def list_users(session: Session) -> List[User]:
        """Lista todos os usuários"""
        return session.query(User).order_by(asc(User.name)).all()


class AssessmentCRUD:
    """CRUD para avaliações"""
    
    @staticmethod
    def create_assessment(session: Session, year: int, cicle: str, 
                         level: str, area: str, description: str) -> Assessment:
        """Cria nova avaliação"""
        assessment = Assessment(
            year=year,
            cicle=cicle,
            level=level,
            area=area,
            description=description
        )
        session.add(assessment)
        session.commit()
        session.refresh(assessment)
        return assessment
    
    @staticmethod
    def get_assessment_by_id(session: Session, assessment_id: str) -> Optional[Assessment]:
        """Busca avaliação por ID"""
        return session.query(Assessment).filter(Assessment.id == assessment_id).first()
    
    @staticmethod
    def get_assessment(session: Session, assessment_id: str) -> Optional[Assessment]:
        """Busca avaliação por ID (alias para get_assessment_by_id)"""
        return AssessmentCRUD.get_assessment_by_id(session, assessment_id)
    
    @staticmethod
    def list_assessments(session: Session) -> List[Assessment]:
        """Lista todas as avaliações"""
        return session.query(Assessment).order_by(desc(Assessment.created_at)).all()
    
    @staticmethod
    def update_assessment(session: Session, assessment_id: str, **kwargs) -> Optional[Assessment]:
        """Atualiza avaliação"""
        assessment = session.query(Assessment).filter(Assessment.id == assessment_id).first()
        if assessment:
            for key, value in kwargs.items():
                if hasattr(assessment, key):
                    setattr(assessment, key, value)
            session.commit()
            session.refresh(assessment)
        return assessment
    
    @staticmethod
    def delete_assessment(session: Session, assessment_id: str) -> bool:
        """Remove avaliação"""
        assessment = session.query(Assessment).filter(Assessment.id == assessment_id).first()
        if assessment:
            session.delete(assessment)
            session.commit()
            return True
        return False


class DatasetCRUD:
    """CRUD para datasets"""
    
    @staticmethod
    def create_dataset(session: Session, name: str, source_type: str, 
                      file_name: str = None) -> Dataset:
        """Cria novo dataset"""
        dataset = Dataset(
            name=name,
            source_type=source_type,
            file_name=file_name
        )
        session.add(dataset)
        session.commit()
        session.refresh(dataset)
        return dataset
    
    @staticmethod
    def get_dataset_by_id(session: Session, dataset_id: int) -> Optional[Dataset]:
        """Busca dataset por ID"""
        return session.query(Dataset).filter(Dataset.id == dataset_id).first()
    
    @staticmethod
    def list_datasets(session: Session) -> List[Dataset]:
        """Lista todos os datasets"""
        return session.query(Dataset).order_by(desc(Dataset.created_at)).all()
    
    @staticmethod
    def delete_dataset(session: Session, dataset_id: int) -> bool:
        """Remove dataset"""
        dataset = session.query(Dataset).filter(Dataset.id == dataset_id).first()
        if dataset:
            session.delete(dataset)
            session.commit()
            return True
        return False


class ParametersSetCRUD:
    """CRUD para conjuntos de parâmetros"""
    
    @staticmethod
    def create_parameters_set(session: Session, name: str, is_anchor: bool = False) -> ParametersSet:
        """Cria novo conjunto de parâmetros"""
        params_set = ParametersSet(name=name, is_anchor=is_anchor)
        session.add(params_set)
        session.commit()
        session.refresh(params_set)
        return params_set
    
    @staticmethod
    def get_parameters_set_by_id(session: Session, params_id: int) -> Optional[ParametersSet]:
        """Busca conjunto de parâmetros por ID"""
        return session.query(ParametersSet).filter(ParametersSet.id == params_id).first()
    
    @staticmethod
    def list_parameters_sets(session: Session) -> List[ParametersSet]:
        """Lista todos os conjuntos de parâmetros"""
        return session.query(ParametersSet).order_by(desc(ParametersSet.created_at)).all()
    
    @staticmethod
    def add_item_parameter(session: Session, params_set_id: int, questao: int,
                          a: float, b: float, c: float, is_anchor: bool = False) -> ItemParameter:
        """Adiciona parâmetro de item ao conjunto"""
        item_param = ItemParameter(
            parameters_set_id=params_set_id,
            questao=questao,
            a=a,
            b=b,
            c=c,
            is_anchor=is_anchor
        )
        session.add(item_param)
        session.commit()
        session.refresh(item_param)
        return item_param
    
    @staticmethod
    def get_item_parameters(session: Session, params_set_id: int) -> List[ItemParameter]:
        """Busca parâmetros de itens de um conjunto"""
        return session.query(ItemParameter).filter(
            ItemParameter.parameters_set_id == params_set_id
        ).order_by(ItemParameter.questao).all()
    
    @staticmethod
    def delete_parameters_set(session: Session, params_id: int) -> bool:
        """Remove conjunto de parâmetros"""
        params_set = session.query(ParametersSet).filter(ParametersSet.id == params_id).first()
        if params_set:
            session.delete(params_set)
            session.commit()
            return True
        return False
    
    @staticmethod
    def get_parameters_by_assessment(session: Session, assessment_id: str) -> List[ParametersSet]:
        """Busca parâmetros por avaliação (implementação simplificada)"""
        # Por enquanto, retorna todos os parâmetros
        # TODO: Implementar relação direta com assessment quando necessário
        return session.query(ParametersSet).order_by(desc(ParametersSet.created_at)).all()


class ExecutionCRUD:
    """CRUD para execuções"""
    
    @staticmethod
    def create_execution(session: Session, assessment_id: str, dataset_id: int = None,
                        parameters_set_id: int = None, name: str = None,
                        notes: str = None) -> Execution:
        """Cria nova execução"""
        execution = Execution(
            assessment_id=assessment_id,
            dataset_id=dataset_id,
            parameters_set_id=parameters_set_id,
            name=name,
            notes=notes,
            status='pending'
        )
        session.add(execution)
        session.commit()
        session.refresh(execution)
        return execution
    
    @staticmethod
    def get_execution_by_id(session: Session, execution_id: int) -> Optional[Execution]:
        """Busca execução por ID"""
        return session.query(Execution).filter(Execution.id == execution_id).first()
    
    @staticmethod
    def list_executions_by_assessment(session: Session, assessment_id: str) -> List[Execution]:
        """Lista execuções de uma avaliação"""
        return session.query(Execution).filter(
            Execution.assessment_id == assessment_id
        ).order_by(desc(Execution.created_at)).all()
    
    @staticmethod
    def update_execution_status(session: Session, execution_id: int, status: str) -> Optional[Execution]:
        """Atualiza status da execução"""
        execution = session.query(Execution).filter(Execution.id == execution_id).first()
        if execution:
            execution.status = status
            session.commit()
            session.refresh(execution)
        return execution
    
    @staticmethod
    def delete_execution(session: Session, execution_id: int) -> bool:
        """Remove execução"""
        execution = session.query(Execution).filter(Execution.id == execution_id).first()
        if execution:
            session.delete(execution)
            session.commit()
            return True
        return False


class StudentResultCRUD:
    """CRUD para resultados dos estudantes"""
    
    @staticmethod
    def create_student_result(session: Session, execution_id: int, cod_pessoa: str,
                             theta: float, enem_score: float, acertos: int,
                             total_itens: int) -> StudentResult:
        """Cria resultado de estudante"""
        result = StudentResult(
            execution_id=execution_id,
            cod_pessoa=cod_pessoa,
            theta=theta,
            enem_score=enem_score,
            acertos=acertos,
            total_itens=total_itens
        )
        session.add(result)
        session.commit()
        session.refresh(result)
        return result
    
    @staticmethod
    def get_results_by_execution(session: Session, execution_id: int) -> List[StudentResult]:
        """Busca resultados de uma execução"""
        return session.query(StudentResult).filter(
            StudentResult.execution_id == execution_id
        ).order_by(desc(StudentResult.enem_score)).all()
    
    @staticmethod
    def bulk_create_results(session: Session, execution_id: int, results_data: List[Dict]) -> List[StudentResult]:
        """Cria múltiplos resultados em lote"""
        results = []
        for data in results_data:
            result = StudentResult(
                execution_id=execution_id,
                cod_pessoa=data['cod_pessoa'],
                theta=data['theta'],
                enem_score=data['enem_score'],
                acertos=data['acertos'],
                total_itens=data['total_itens']
            )
            results.append(result)
            session.add(result)
        
        session.commit()
        for result in results:
            session.refresh(result)
        
        return results
    
    @staticmethod
    def delete_results_by_execution(session: Session, execution_id: int) -> int:
        """Remove todos os resultados de uma execução"""
        deleted_count = session.query(StudentResult).filter(
            StudentResult.execution_id == execution_id
        ).delete()
        session.commit()
        return deleted_count
