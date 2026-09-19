from fastapi import APIRouter, HTTPException

from app.schemas.quote import FlatFareRequest
from app.services.metro_service import DuplicateFlatFareError, MetroService, ValidationError

router = APIRouter(tags=["flat-fares"])


@router.get("/flat-fares")
def list_flat_fares():
    with MetroService() as s:
        return {"items": s.flat_fares()}


@router.post("/flat-fares", status_code=201)
def create_flat_fare(body: FlatFareRequest):
    with MetroService() as s:
        try:
            return s.create_flat_fare(body.start, body.end, body.price)
        except DuplicateFlatFareError as e:
            raise HTTPException(409, str(e))
        except ValidationError as e:
            raise HTTPException(400, str(e))


@router.delete("/flat-fares/{start}/{end}")
def delete_flat_fare(start: str, end: str):
    with MetroService() as s:
        if not s.delete_flat_fare(start, end):
            raise HTTPException(404, f"未登记一口价: {start}->{end}")
        return {"ok": True}
