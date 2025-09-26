from pydantic import BaseModel

class IDResponse(BaseModel):
    id_generado: str
    mensaje: str