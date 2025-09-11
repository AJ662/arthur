from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class AgentConfig(BaseModel):
    name: str
    behavior: str
    health: int

@app.post("/agents/")
async def create_agent(config: AgentConfig):
    return {"message": f"Agent {config.name} created with behavior: {config.behavior}"}

@app.get("/")
async def root():
    return {"message": "Welcome to the Game Dev Kit Backend!"}
