from pydantic import BaseModel
from typing import Dict, List, Optional


class Step(BaseModel):
    name: str
    command: str
    cwd: Optional[str] = None
    env: Optional[Dict[str, str]] = None


class ParameterDef(BaseModel):
    description: str
    type: str = "string"
    required: bool = False
    default: Optional[str] = None


class Secret(BaseModel):
    source: str
    target: str


class Tool(BaseModel):
    name: str
    description: Optional[str] = None
    steps: List[Step]
    parameters: Optional[Dict[str, ParameterDef]] = None
    secrets: Optional[List[Secret]] = None
    cwd: Optional[str] = None
    timeout: Optional[int] = None


class ConfigFile(BaseModel):
    version: str
    tools: List[Tool]
