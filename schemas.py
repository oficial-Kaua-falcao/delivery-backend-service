from pydantic import BaseModel, EmailStr
from typing import List, Optional

class UsuarioSchema(BaseModel):
    nome: str
    email: EmailStr
    senha: str
    ativo: Optional[bool] = True

    class Config:
        from_attributes = True


class loginSchema(BaseModel):
    email: EmailStr
    senha: str

    class Config:
        from_attributes = True


class RefreshTokenSchema(BaseModel):
    refresh_token: str


class PedidoSchema(BaseModel):
    preco: Optional[float] = 0.0
    status: Optional[str] = "pendente"

    class Config:
        from_attributes = True


class EditarPedidoSchema(BaseModel):
    preco: Optional[float] = None
    status: Optional[str] = None

    class Config:
        from_attributes = True


class ItemPedidoSchema(BaseModel):
    quantidade: int
    sabor: Optional[str] = None
    tamanho: str
    preco_unitario: float

    class Config:
        from_attributes = True


class DonoPedidoResponse(BaseModel):
    id: int
    nome: str
    email: str

    class Config:
        from_attributes = True


class ItemPedidoResponse(BaseModel):
    id: int
    quantidade: int
    sabor: Optional[str] = None
    tamanho: str
    preco_unitario: float

    class Config:
        from_attributes = True


class PedidoCompletoResponse(BaseModel):
    id: int
    status: str
    preco: float
    dono: DonoPedidoResponse
    itens: List[ItemPedidoResponse]

    class Config:
        from_attributes = True