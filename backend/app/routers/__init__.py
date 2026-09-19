from fastapi import APIRouter

from app.routers import dashboard, edges, fares, flat_fares, history, quote, settings, stations

api = APIRouter(prefix="/api")
for r in (dashboard, stations, edges, fares, flat_fares, quote, history, settings):
    api.include_router(r.router)
