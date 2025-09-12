from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
import pandas as pd
from typing import Optional

from db.session import Base, engine, get_session
from db import models, crud
from core.data_processor import DataProcessor
from core.tri_engine import TRIEngine
from core.item_calibration import ItemCalibrator
from core.validators import DataValidator
from api.schemas import ExecutionCreate, ExecutionResponse, ResultsResponse, ResultRecord


# Criar tabelas (auto-migrate simples)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="TRI System API", version="1.0.0")

data_processor = DataProcessor()
tri_engine = TRIEngine()
validator = DataValidator()
calibrator = ItemCalibrator()


@app.post("/upload", response_model=ExecutionResponse)
async def upload_and_process(
    dataset_name: str,
    file: UploadFile = File(...),
    params_file: Optional[UploadFile] = None,
    session: Session = Depends(get_session),
):
    # Detectar tipo de arquivo
    filename = file.filename
    content = await file.read()

    if filename.endswith(".csv"):
        df = pd.read_csv(pd.io.common.BytesIO(content), sep=';', encoding='utf-8')
        df = data_processor._clean_responses_data(df)
        source_type = "csv"
    elif filename.endswith(".xlsx"):
        # O fluxo Excel via API usa função síncrona load_responses_excel com caminho; aqui fazemos parsing direto
        # Para simplificar, obrigamos CSV neste endpoint
        raise HTTPException(status_code=400, detail="Suporte via API apenas para CSV neste endpoint")
    else:
        raise HTTPException(status_code=400, detail="Formato de arquivo não suportado")

    # Validar
    quality = data_processor.validate_data_quality(df)
    if not quality:
        raise HTTPException(status_code=400, detail="Falha na validação de qualidade")

    # Criar dataset
    dataset = crud.create_dataset(session, name=dataset_name, source_type=source_type, file_name=filename)

    # Carregar parâmetros opcionais
    params_df = None
    param_set_id = None
    if params_file is not None:
        pcontent = await params_file.read()
        if params_file.filename.endswith('.csv'):
            params_df = pd.read_csv(pd.io.common.BytesIO(pcontent), encoding='utf-8')
        elif params_file.filename.endswith('.xlsx'):
            params_df = pd.read_excel(pd.io.common.BytesIO(pcontent))
        else:
            raise HTTPException(status_code=400, detail="Formato de parâmetros não suportado")

        if not data_processor._validate_parameters(params_df):
            raise HTTPException(status_code=400, detail="Parâmetros inválidos")

        param_set = crud.create_parameters_set(session, name=f"params:{params_file.filename}", is_anchor=False, params_df=params_df)
        param_set_id = param_set.id

    # Executar TRI
    results_df = tri_engine.process_responses(df, params_df=params_df)

    # Salvar execução e resultados
    execution = crud.create_execution(session, dataset_id=dataset.id, parameters_set_id=param_set_id, status="completed")
    crud.bulk_insert_results(session, execution.id, results_df)

    return ExecutionResponse(execution_id=execution.id)


@app.get("/executions/{execution_id}/results", response_model=ResultsResponse)
def get_results(execution_id: int, session: Session = Depends(get_session)):
    df = crud.get_execution_results(session, execution_id)
    if df.empty:
        raise HTTPException(status_code=404, detail="Resultados não encontrados")
    return ResultsResponse(
        execution_id=execution_id,
        results=[ResultRecord(**row._asdict() if hasattr(row, "_asdict") else row) for row in df.to_dict(orient='records')]
    )


@app.post("/calibrate", response_model=ExecutionResponse)
async def calibrate_items(
    dataset_name: str,
    file: UploadFile = File(...),
    method: str = "ML",
    session: Session = Depends(get_session),
):
    filename = file.filename
    content = await file.read()
    if not filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Envie CSV com colunas padrão")

    df = pd.read_csv(pd.io.common.BytesIO(content), sep=';', encoding='utf-8')
    df = data_processor._clean_responses_data(df)

    # Validar método
    if method not in ["ML", "MLF"]:
        raise HTTPException(status_code=400, detail="Método deve ser 'ML' ou 'MLF'")

    params_df = calibrator.calibrate_items_3pl(df, method=method)
    validation = calibrator.validate_calibration(params_df)
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail=str(validation["errors"]))

    param_set = crud.create_parameters_set(session, name=f"calibrated:{dataset_name}", is_anchor=False, params_df=params_df)
    dataset = crud.create_dataset(session, name=dataset_name, source_type="csv", file_name=filename)
    execution = crud.create_execution(session, dataset_id=dataset.id, parameters_set_id=param_set.id, status="completed", notes=f"Calibração de itens usando método {method}")

    return ExecutionResponse(execution_id=execution.id)


