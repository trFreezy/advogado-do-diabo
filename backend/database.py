from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime

SQLALCHEMY_DATABASE_URL = "sqlite:///./advogado.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class DebateDB(Base):
    __tablename__ = "debates"
    id = Column(String, primary_key=True, index=True)
    dono_id = Column(String, index=True) # <--- NOVA COLUNA: A CHAVE DA PRIVACIDADE
    titulo = Column(String, default="Novo Debate")
    data_criacao = Column(DateTime, default=datetime.utcnow)
    
    mensagens = relationship("MensagemDB", back_populates="debate", cascade="all, delete-orphan")

class MensagemDB(Base):
    __tablename__ = "mensagens"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    debate_id = Column(String, ForeignKey("debates.id"))
    role = Column(String)
    texto = Column(String)
    debate = relationship("DebateDB", back_populates="mensagens")

Base.metadata.create_all(bind=engine)