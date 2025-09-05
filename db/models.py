from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    Boolean,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column

from db.session import Base


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)  # csv|excel|streamlit
    file_name: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    executions: Mapped[list["Execution"]] = relationship("Execution", back_populates="dataset")


class ParametersSet(Base):
    __tablename__ = "parameters_sets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    is_anchor: Mapped[bool] = mapped_column(Boolean, default=False)

    items: Mapped[list["ItemParameter"]] = relationship("ItemParameter", back_populates="parameters_set", cascade="all, delete-orphan")
    executions: Mapped[list["Execution"]] = relationship("Execution", back_populates="parameters_set")


class ItemParameter(Base):
    __tablename__ = "item_parameters"
    __table_args__ = (UniqueConstraint("parameters_set_id", "questao", name="uq_paramset_questao"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    parameters_set_id: Mapped[int] = mapped_column(ForeignKey("parameters_sets.id", ondelete="CASCADE"), nullable=False)
    questao: Mapped[int] = mapped_column(Integer, nullable=False)
    a: Mapped[float] = mapped_column(Float, nullable=False)
    b: Mapped[float] = mapped_column(Float, nullable=False)
    c: Mapped[float] = mapped_column(Float, nullable=False)
    is_anchor: Mapped[bool] = mapped_column(Boolean, default=False)

    parameters_set: Mapped[ParametersSet] = relationship("ParametersSet", back_populates="items")


class Execution(Base):
    __tablename__ = "executions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[Optional[str]] = mapped_column(String(255))  # Nome personalizado para a execução
    dataset_id: Mapped[Optional[int]] = mapped_column(ForeignKey("datasets.id", ondelete="SET NULL"), nullable=True)
    parameters_set_id: Mapped[Optional[int]] = mapped_column(ForeignKey("parameters_sets.id", ondelete="SET NULL"))
    status: Mapped[str] = mapped_column(String(50), default="completed")  # completed|failed|running
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    dataset: Mapped[Dataset] = relationship("Dataset", back_populates="executions")
    parameters_set: Mapped[ParametersSet] = relationship("ParametersSet", back_populates="executions")
    results: Mapped[list["StudentResult"]] = relationship("StudentResult", back_populates="execution", cascade="all,delete-orphan")


class StudentResult(Base):
    __tablename__ = "student_results"
    __table_args__ = (UniqueConstraint("execution_id", "cod_pessoa", name="uq_execution_student"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    execution_id: Mapped[int] = mapped_column(ForeignKey("executions.id", ondelete="CASCADE"), nullable=False)
    cod_pessoa: Mapped[str] = mapped_column(String(64), nullable=False)
    theta: Mapped[float] = mapped_column(Float, nullable=False)
    enem_score: Mapped[float] = mapped_column(Float, nullable=False)
    acertos: Mapped[int] = mapped_column(Integer, nullable=False)
    total_itens: Mapped[int] = mapped_column(Integer, nullable=False)

    execution: Mapped[Execution] = relationship("Execution", back_populates="results")


