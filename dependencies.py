import os
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import bcrypt
import jwt
from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker
from models import db

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "uma_chave_super_secreta_caso_nao_tenha_env")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


class BcryptHasher:
    def hash(self, password: str) -> str:
        pwd_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(pwd_bytes, salt)
        return hashed.decode('utf-8')

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

bcrypt_context = BcryptHasher()


def pegar_sessao():
    Session = sessionmaker(bind=db)
    session = Session()
    try:
        yield session
    finally:
        session.close()


def criar_access_token(usuario_id: int, email: str):
    tempo_expiracao = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    dados = {
        "sub": str(usuario_id),
        "email": email,
        "type": "access",
        "exp": tempo_expiracao
    }
    return jwt.encode(dados, SECRET_KEY, algorithm=ALGORITHM)


def criar_refresh_token(usuario_id: int):
    tempo_expiracao = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    dados = {
        "sub": str(usuario_id),
        "type": "refresh",
        "exp": tempo_expiracao
    }
    return jwt.encode(dados, SECRET_KEY, algorithm=ALGORITHM)


def verificar_token(token: str = Depends(oauth2_scheme)) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Tipo de token inválido para esta operação."
            )
            
        usuario_id: str = payload.get("sub")
        email: str = payload.get("email")
        
        if usuario_id is None or email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido: informações de usuário ausentes."
            )
            
        return {"id": int(usuario_id), "email": email}

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="O seu token de acesso expirou. Use o seu refresh token ou faça login novamente.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação inválido ou corrompido.",
            headers={"WWW-Authenticate": "Bearer"},
        )