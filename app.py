from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agent import handle_incident, resolve_incident, reflect_on_service

app = FastAPI(title="Incident Response Agent")


class IncidentRequest(BaseModel):
    description: str


class ResolveRequest(BaseModel):
    description: str
    resolution: str
    worked: bool = True


class ReflectRequest(BaseModel):
    service: str


@app.post("/api/incident")
async def post_incident(req: IncidentRequest):
    return await handle_incident(req.description)


@app.post("/api/resolve")
async def post_resolve(req: ResolveRequest):
    await resolve_incident(req.description, req.resolution, req.worked)
    return {"status": "ok"}


@app.post("/api/reflect")
async def post_reflect(req: ReflectRequest):
    return {"insight": await reflect_on_service(req.service)}


app.mount("/", StaticFiles(directory="static", html=True), name="static")