from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.pool import StaticPool

# Configuração robusta para SQLite suportar múltiplas threads no FastAPI sem travar
db = create_engine(
    "sqlite:///banco.db",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
Base = declarative_base()


class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column("id", Integer, nullable=False, primary_key=True, autoincrement=True)
    nome = Column("nome", String, nullable=False)
    email = Column("email", String, nullable=False, unique=True, index=True)
    senha = Column("senha", String, nullable=False)
    ativo = Column("ativo", Boolean, default=True)
    admin = Column("admin", Boolean, default=False)

    # Relacionamento 1 para Muitos
    pedidos = relationship("Pedido", back_populates="dono", cascade="all, delete-orphan")

    def __init__(self, nome, email, senha, ativo=True, admin=False):
        self.nome = nome
        self.email = email
        self.senha = senha
        self.ativo = ativo
        self.admin = admin


class Pedido(Base):
    __tablename__ = "pedidos"
    id = Column("id", Integer, nullable=False, primary_key=True, autoincrement=True)
    status = Column("status", String, nullable=False, default="pendente") 
    usuario = Column("usuario", Integer, ForeignKey("usuarios.id")) 
    preco = Column("preco", Float, nullable=False, default=0.0)

    # O pedido sabe quem é o seu dono
    dono = relationship("Usuario", back_populates="pedidos")

    # O pedido pode ter vários itens
    itens = relationship("ItemPedido", back_populates="pedido_rel", cascade="all, delete-orphan")

    def __init__(self, status, usuario, preco=0.0):
        self.status = status
        self.usuario = usuario
        self.preco = preco


class ItemPedido(Base):
    __tablename__ = "itens_pedido"
    id = Column("id", Integer, nullable=False, primary_key=True, autoincrement=True)
    quantidade = Column("quantidade", Integer, nullable=False)
    sabor = Column("sabor", String, nullable=True)
    tamanho = Column("tamanho", String, nullable=False)
    preco_unitario = Column("preco_unitario", Float, nullable=False)
    pedido = Column("pedido", Integer, ForeignKey("pedidos.id"))

    # O item sabe a qual pedido ele pertence
    pedido_rel = relationship("Pedido", back_populates="itens")

    def __init__(self, quantidade, sabor, tamanho, preco_unitario, pedido):
        self.quantidade = quantidade
        self.sabor = sabor
        self.tamanho = tamanho
        self.preco_unitario = preco_unitario
        self.pedido = pedido