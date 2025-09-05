from typing import Optional, Iterable, List, Dict
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func

from db.models import Dataset, ParametersSet, ItemParameter, Execution, StudentResult


def create_dataset(session: Session, name: str, source_type: str, file_name: Optional[str]) -> Dataset:
    dataset = Dataset(name=name, source_type=source_type, file_name=file_name)
    session.add(dataset)
    session.commit()
    session.refresh(dataset)
    return dataset


def create_parameters_set(session: Session, name: Optional[str], is_anchor: bool, params_df: pd.DataFrame) -> ParametersSet:
    param_set = ParametersSet(name=name, is_anchor=is_anchor)
    session.add(param_set)
    session.flush()

    items = []
    for _, row in params_df.iterrows():
        items.append(
            ItemParameter(
                parameters_set_id=param_set.id,
                questao=int(row["Questao"]),
                a=float(row["a"]),
                b=float(row["b"]),
                c=float(row["c"]),
                is_anchor=bool(row["is_anchor"]) if "is_anchor" in params_df.columns else False,
            )
        )
    session.add_all(items)
    session.commit()
    session.refresh(param_set)
    return param_set


def list_parameter_sets(session: Session) -> List[Dict]:
    rows = (
        session.query(
            ParametersSet.id,
            ParametersSet.name,
            ParametersSet.created_at,
            func.count(ItemParameter.id).label("num_items")
        )
        .join(ItemParameter, ItemParameter.parameters_set_id == ParametersSet.id, isouter=True)
        .group_by(ParametersSet.id)
        .order_by(ParametersSet.created_at.desc())
        .all()
    )
    return [
        {
            "id": r.id,
            "name": r.name,
            "created_at": r.created_at,
            "num_items": int(r.num_items or 0),
        }
        for r in rows
    ]


def get_parameter_set_items(session: Session, parameters_set_id: int) -> pd.DataFrame:
    rows = (
        session.query(ItemParameter)
        .filter(ItemParameter.parameters_set_id == parameters_set_id)
        .all()
    )
    data = [
        {
            "Questao": r.questao,
            "a": r.a,
            "b": r.b,
            "c": r.c,
            "is_anchor": r.is_anchor,
        }
        for r in rows
    ]
    return pd.DataFrame(data)


def create_execution(session: Session, dataset_id: Optional[int], parameters_set_id: Optional[int], status: str = "completed", notes: Optional[str] = None) -> Execution:
    execution = Execution(dataset_id=dataset_id, parameters_set_id=parameters_set_id, status=status, notes=notes)
    session.add(execution)
    session.commit()
    session.refresh(execution)
    return execution


def bulk_insert_results(session: Session, execution_id: int, results_df: pd.DataFrame) -> int:
    records = []
    for _, row in results_df.iterrows():
        records.append(
            StudentResult(
                execution_id=execution_id,
                cod_pessoa=str(row["CodPessoa"]),
                theta=float(row["theta"]),
                enem_score=float(row["enem_score"]),
                acertos=int(row.get("acertos", 0)),
                total_itens=int(row.get("total_itens", 0)),
            )
        )
    session.add_all(records)
    session.commit()
    return len(records)


def get_execution_results(session: Session, execution_id: int) -> pd.DataFrame:
    rows = (
        session.query(StudentResult)
        .filter(StudentResult.execution_id == execution_id)
        .all()
    )
    data = [
        {
            "CodPessoa": r.cod_pessoa,
            "theta": r.theta,
            "enem_score": r.enem_score,
            "acertos": r.acertos,
            "total_itens": r.total_itens,
        }
        for r in rows
    ]
    df = pd.DataFrame(data)
    
    # Calcular percentual de acertos
    df['percentual_acertos'] = (df['acertos'] / df['total_itens'] * 100).round(2)
    
    return df


def list_executions(session: Session) -> List[Dict]:
    """Lista todas as execuções com informações resumidas"""
    rows = (
        session.query(
            Execution.id,
            Execution.name,
            Execution.status,
            Execution.created_at,
            Execution.dataset_id,
            Execution.parameters_set_id,
            func.count(StudentResult.id).label("total_students"),
            func.avg(StudentResult.theta).label("theta_mean"),
            func.avg(StudentResult.enem_score).label("enem_mean")
        )
        .join(StudentResult, StudentResult.execution_id == Execution.id, isouter=True)
        .group_by(Execution.id)
        .order_by(Execution.created_at.desc())
        .all()
    )
    
    return [
        {
            "id": r.id,
            "name": r.name,
            "status": r.status,
            "created_at": r.created_at,
            "dataset_id": r.dataset_id,
            "parameters_set_id": r.parameters_set_id,
            "total_students": int(r.total_students or 0),
            "theta_mean": float(r.theta_mean or 0),
            "enem_mean": float(r.enem_mean or 0),
            "num_items": 0  # Será calculado separadamente se necessário
        }
        for r in rows
    ]


def delete_execution(session: Session, execution_id: int) -> bool:
    try:
        execution = session.query(Execution).filter(Execution.id == execution_id).first()
        if execution:
            # Deletar resultados primeiro
            session.query(StudentResult).filter(StudentResult.execution_id == execution_id).delete()
            # Deletar execução
            session.delete(execution)
            session.commit()
            return True
        return False
    except Exception:
        session.rollback()
        return False


def update_execution_name(session: Session, execution_id: int, new_name: str) -> bool:
    """Atualiza o nome de uma execução"""
    try:
        execution = session.query(Execution).filter(Execution.id == execution_id).first()
        if execution:
            execution.name = new_name
            session.commit()
            return True
        return False
    except Exception:
        session.rollback()
        return False


def list_parameters_sets(session: Session) -> List[Dict]:
    """Lista todos os conjuntos de parâmetros salvos"""
    rows = (
        session.query(
            ParametersSet.id,
            ParametersSet.name,
            ParametersSet.created_at,
            ParametersSet.is_anchor,
            func.count(ItemParameter.id).label("total_items")
        )
        .join(ItemParameter, ItemParameter.parameters_set_id == ParametersSet.id, isouter=True)
        .group_by(ParametersSet.id)
        .order_by(ParametersSet.created_at.desc())
        .all()
    )
    
    return [
        {
            "id": r.id,
            "name": r.name,
            "created_at": r.created_at,
            "is_anchor": r.is_anchor,
            "total_items": int(r.total_items or 0)
        }
        for r in rows
    ]


def get_parameters_set(session: Session, parameters_set_id: int) -> pd.DataFrame:
    """Obtém os parâmetros de um conjunto específico"""
    rows = (
        session.query(ItemParameter)
        .filter(ItemParameter.parameters_set_id == parameters_set_id)
        .all()
    )
    
    data = [
        {
            "questao": r.questao,
            "a": r.a,
            "b": r.b,
            "c": r.c,
            "is_anchor": r.is_anchor
        }
        for r in rows
    ]
    
    df = pd.DataFrame(data)
    df = df.sort_values('questao')
    return df


def update_parameters_set_name(session: Session, parameters_set_id: int, new_name: str) -> bool:
    """Atualiza o nome de um conjunto de parâmetros"""
    try:
        params_set = session.query(ParametersSet).filter(ParametersSet.id == parameters_set_id).first()
        if params_set:
            params_set.name = new_name
            session.commit()
            return True
        return False
    except Exception:
        session.rollback()
        return False


