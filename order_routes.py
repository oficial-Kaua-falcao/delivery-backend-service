from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from dependencies import pegar_sessao, verificar_token
from schemas import (
    PedidoSchema, 
    EditarPedidoSchema, 
    ItemPedidoSchema, 
    PedidoCompletoResponse
)
from models import Pedido, Usuario, ItemPedido

order_router = APIRouter(prefix="/pedidos", tags=["pedidos"])


@order_router.get("/", response_model=List[PedidoCompletoResponse])
async def pedidos(
    limit: int = 10,
    skip: int = 0,
    session: Session = Depends(pegar_sessao), 
    usuario_logado: dict = Depends(verificar_token)
):
    id_do_usuario = usuario_logado["id"]
    
    todos_pedidos = (
        session.query(Pedido)
        .filter(Pedido.usuario == id_do_usuario)
        .limit(limit)
        .offset(skip)
        .all()
    )
    
    return todos_pedidos


@order_router.get("/listas", response_model=List[PedidoCompletoResponse])
async def listar_todos_os_pedidos_do_sistema(
    limit: int = 10,
    skip: int = 0,
    session: Session = Depends(pegar_sessao),
    usuario_logado: dict = Depends(verificar_token)
):
    id_do_usuario = usuario_logado["id"]

    user_logado_db = session.query(Usuario).filter(Usuario.id == id_do_usuario).first()

    if not user_logado_db or not user_logado_db.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado. Esta rota é exclusiva para administradores."
        )

    todos_os_pedidos = (
        session.query(Pedido)
        .limit(limit)
        .offset(skip)
        .all()
    )

    return todos_os_pedidos


@order_router.get("/usuario/{usuario_id}", response_model=List[PedidoCompletoResponse])
async def listar_pedidos_de_um_usuario_especifico(
    usuario_id: int,
    limit: int = 10,
    skip: int = 0,
    session: Session = Depends(pegar_sessao),
    usuario_logado: dict = Depends(verificar_token)
):
    id_do_usuario_logado = usuario_logado["id"]

    user_logado_db = session.query(Usuario).filter(Usuario.id == id_do_usuario_logado).first()

    if not user_logado_db or not user_logado_db.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado. Apenas administradores podem consultar o histórico de outros usuários."
        )

    pedidos_do_usuario = (
        session.query(Pedido)
        .filter(Pedido.usuario == usuario_id)
        .limit(limit)
        .offset(skip)
        .all()
    )

    return pedidos_do_usuario


@order_router.post("/pedido", status_code=status.HTTP_201_CREATED)
async def criar_pedido(
    pedido_schema: PedidoSchema, 
    session: Session = Depends(pegar_sessao),
    usuario_logado: dict = Depends(verificar_token)
):  
    id_do_usuario = usuario_logado["id"]
    
    user = session.query(Usuario).filter(Usuario.id == id_do_usuario).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Usuário do token não encontrado no sistema."
        )

    novo_pedido = Pedido(
        status=pedido_schema.status,
        usuario=id_do_usuario,
        preco=pedido_schema.preco
    )
    
    session.add(novo_pedido)
    session.commit()
    session.refresh(novo_pedido)
    
    return {
        "message": "Pedido criado com sucesso de forma segura!", 
        "id_do_pedido": novo_pedido.id,
        "dono_do_pedido": user.nome
    }


@order_router.put("/pedido/{pedido_id}")
async def editar_pedido(
    pedido_id: int,
    pedido_editado: EditarPedidoSchema,
    session: Session = Depends(pegar_sessao),
    usuario_logado: dict = Depends(verificar_token)
):
    id_do_usuario = usuario_logado["id"]

    pedido_existente = session.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido_existente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido não encontrado.")

    user_logado_db = session.query(Usuario).filter(Usuario.id == id_do_usuario).first()

    if pedido_existente.usuario != id_do_usuario and not user_logado_db.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Você não tem permissão para alterar o pedido de outro usuário."
        )

    if pedido_editado.preco is not None:
        pedido_existente.preco = pedido_editado.preco
    if pedido_editado.status is not None:
        pedido_existente.status = pedido_editado.status

    session.commit()
    session.refresh(pedido_existente)

    return {
        "message": "Pedido atualizado com sucesso!",
        "pedido": {
            "id": pedido_existente.id,
            "status": pedido_existente.status,
            "preco": pedido_existente.preco
        }
    }


@order_router.patch("/pedido/{pedido_id}/finalizar")
async def finalizar_pedido(
    pedido_id: int,
    session: Session = Depends(pegar_sessao),
    usuario_logado: dict = Depends(verificar_token)
):
    id_do_usuario = usuario_logado["id"]

    pedido_existente = session.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido_existente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido não encontrado.")

    user_logado_db = session.query(Usuario).filter(Usuario.id == id_do_usuario).first()

    if pedido_existente.usuario != id_do_usuario and not user_logado_db.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Você não tem permissão para finalizar o pedido de outra pessoa."
        )

    if pedido_existente.status == "cancelado":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível finalizar um pedido que já foi cancelado."
        )
    
    if pedido_existente.status == "finalizado":
        return {"message": "Este pedido já consta como finalizado.", "pedido_id": pedido_id}

    pedido_existente.status = "finalizado"
    
    session.commit()
    session.refresh(pedido_existente)

    return {
        "message": "Pedido finalizado e enviado com sucesso!",
        "pedido_id": pedido_existente.id,
        "status_atual": pedido_existente.status
    }


@order_router.patch("/pedido/{pedido_id}/cancelar")
async def cancelar_pedido(
    pedido_id: int,
    session: Session = Depends(pegar_sessao),
    usuario_logado: dict = Depends(verificar_token)
):
    id_do_usuario = usuario_logado["id"]

    pedido_existente = session.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido_existente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido não encontrado.")

    user_logado_db = session.query(Usuario).filter(Usuario.id == id_do_usuario).first()

    if pedido_existente.usuario != id_do_usuario and not user_logado_db.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Você não pode cancelar o pedido de outra pessoa."
        )

    if pedido_existente.status == "cancelado":
        return {"message": "Este pedido já consta como cancelado."}

    pedido_existente.status = "cancelado"
    
    session.commit()
    session.refresh(pedido_existente)

    return {
        "message": "Pedido cancelado com sucesso!",
        "pedido_id": pedido_existente.id,
        "novo_status": pedido_existente.status
    }


@order_router.post("/pedido/{pedido_id}/itens", status_code=status.HTTP_201_CREATED)
async def adicionar_item_ao_pedido(
    pedido_id: int,
    item_schema: ItemPedidoSchema,
    session: Session = Depends(pegar_sessao),
    usuario_logado: dict = Depends(verificar_token)
):
    id_do_usuario = usuario_logado["id"]

    pedido_existente = session.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido_existente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido não encontrado.")

    user_logado_db = session.query(Usuario).filter(Usuario.id == id_do_usuario).first()

    if pedido_existente.usuario != id_do_usuario and not user_logado_db.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para adicionar itens ao pedido de outro usuário."
        )

    novo_item = ItemPedido(
        quantidade=item_schema.quantidade,
        sabor=item_schema.sabor,
        tamanho=item_schema.tamanho,
        preco_unitario=item_schema.preco_unitario,
        pedido=pedido_id
    )

    session.add(novo_item)
    
    valor_do_item = item_schema.quantidade * item_schema.preco_unitario
    pedido_existente.preco += valor_do_item

    session.commit()
    session.refresh(novo_item)

    return {
        "message": f"Item '{novo_item.sabor}' adicionado ao pedido #{pedido_id} com sucesso!",
        "item_id": novo_item.id,
        "novo_preco_total_do_pedido": pedido_existente.preco
    }