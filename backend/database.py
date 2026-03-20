from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime

# 1. Configuração do banco de dados SQLite (vai criar um ficheiro chamado advogado.db na raiz)
SQLALCHEMY_DATABASE_URL = "sqlite:///./advogado.db"

# 2. Criando o "motor" que conecta o Python ao ficheiro do banco
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 3. Fábrica de sessões (é a "ponte" que usaremos para enviar comandos ao banco)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Classe base para criarmos as nossas tabelas
Base = declarative_base()

# --- DEFINIÇÃO DAS TABELAS ---

class DebateDB(Base):
    __tablename__ = "debates"

    # Colunas da tabela
    id = Column(String, primary_key=True, index=True) # Ex: 'debate_1710934...'
    titulo = Column(String, default="Novo Debate")
    data_criacao = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamento: Um debate possui várias mensagens. 
    # cascade="all, delete-orphan" garante que se apagarmos o debate, as mensagens também somem.
    mensagens = relationship("MensagemDB", back_populates="debate", cascade="all, delete-orphan")


class MensagemDB(Base):
    __tablename__ = "mensagens"

    # Colunas da tabela
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    debate_id = Column(String, ForeignKey("debates.id")) # Conecta com a tabela acima
    role = Column(String) # Quem enviou? Vai guardar 'user' (você) ou 'model' (IA)
    texto = Column(String)
    
    # Relacionamento reverso
    debate = relationship("DebateDB", back_populates="mensagens")

# 5. Comando mágico: Cria as tabelas fisicamente no ficheiro .db se elas ainda não existirem
Base.metadata.create_all(bind=engine)