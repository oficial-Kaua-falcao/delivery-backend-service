from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import jwt
from models import Usuario
from dependencies import (
    pegar_sessao, 
    bcrypt_context, 
    criar_access_token, 
    criar_refresh_token, 
    SECRET_KEY, 
    ALGORITHM
)
from schemas import UsuarioSchema, RefreshTokenSchema

auth_router = APIRouter(prefix="/auth", tags=["auth"])

@auth_router.post("/criar_conta")
async def criar_conta(usuario_schema: UsuarioSchema, db_session: Session = Depends(pegar_sessao)):
    usuario_existente = db_session.query(Usuario).filter(Usuario.email == usuario_schema.email).first()

    if usuario_existente:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email já cadastrado")
    
    senha_criptografada = bcrypt_context.hash(usuario_schema.senha)
    
    # MEDIDA DE SEGURANÇA: 'admin' é definido como False explicitamente. 
    # Impede que usuários normais virem admins alterando o payload da requisição.
    novo_usuario = Usuario(
        nome=usuario_schema.nome, 
        email=usuario_schema.email, 
        senha=senha_criptografada, 
        ativo=usuario_schema.ativo, 
        admin=False
    )
    
    db_session.add(novo_usuario)
    db_session.commit()
    
    return {"message": "Conta criada com sucesso", "conta_criada": True}


@auth_router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db_session: Session = Depends(pegar_sessao)
):
    # O OAuth2PasswordRequestForm mapeia o campo de identificação como 'username'
    usuario_existente = db_session.query(Usuario).filter(Usuario.email == form_data.username).first()

    if not usuario_existente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
    
    if not usuario_existente.ativo:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Esta conta está desativada.")
        
    senha_valida = bcrypt_context.verify(form_data.password, usuario_existente.senha)
    
    if not senha_valida:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Senha incorreta")
    
    access_token = criar_access_token(usuario_id=usuario_existente.id, email=usuario_existente.email)
    refresh_token = criar_refresh_token(usuario_id=usuario_existente.id)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "message": "Login realizado com sucesso"
    }


@auth_router.post("/refresh")
async def renovar_fidelidade(payload: RefreshTokenSchema, db_session: Session = Depends(pegar_sessao)):
    try:
        dados = jwt.decode(payload.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        
        if dados.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido para esta operação")
            
        usuario_id = dados.get("sub")
        
        user = db_session.query(Usuario).filter(Usuario.id == usuario_id).first()
        if not user or not user.ativo:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado ou inativo")
            
        novo_access_token = criar_access_token(usuario_id=user.id, email=user.email)
        
        return {
            "access_token": novo_access_token,
            "token_type": "bearer"
        }

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="O seu Refresh Token expirou. Faça login novamente.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh Token inválido.")