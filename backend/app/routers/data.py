from fastapi import APIRouter, HTTPException
from app.models.schemas import DataItem
from app.services import data_service

router = APIRouter(prefix="/api/data", tags=["data"])

@router.post("")
def create(item: DataItem):
    return data_service.create_data(item.model_dump())

@router.get("")
def list_all():
    return data_service.list_data()

@router.get("/summary")
def summary():
    return data_service.get_summary()

@router.put("/{doc_id}")
def update(doc_id: str, item: DataItem):
    try:
        return data_service.update_data(doc_id, item.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{doc_id}")
def delete(doc_id: str):
    try:
        data_service.delete_data(doc_id)
        return {"deleted": doc_id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))