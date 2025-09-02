from pydantic import BaseModel
from typing import Optional, List


class ExecutionCreate(BaseModel):
    dataset_name: str
    parameters_set_id: Optional[int] = None


class ExecutionResponse(BaseModel):
    execution_id: int


class ResultRecord(BaseModel):
    CodPessoa: str
    theta: float
    enem_score: float
    acertos: int
    total_itens: int


class ResultsResponse(BaseModel):
    execution_id: int
    results: List[ResultRecord]


