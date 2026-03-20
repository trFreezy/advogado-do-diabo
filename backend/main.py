import os
import io
import PyPDF2
from fastapi import FastAPI, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import google.generativeai as genai
from sqlalchemy.orm import Session

from backend.database import SessionLocal, DebateDB, MensagemDB

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("Chave da API não encontrada!")

genai.configure(api_key=api_key)

instrucao_sistema = """
Você é o 'Advogado do Diabo Pessoal'. A sua missão é auditar premissas lógicas com rigor.
Estruture SEMPRE a sua resposta no seguinte formato Markdown:
### 🔍 Análise da Premissa
### ⚠️ Falhas e Vieses Lógicos
### 🌪️ Cenário de Estresse
### ⚖️ Veredito
"""

modelo_ia = genai.GenerativeModel(model_name="gemini-2.5-flash", system_instruction=instrucao_sistema)

app = FastAPI(title="Advogado do Diabo API")

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)

# A MENSAGEM AGORA EXIGE O ID DO UTILIZADOR
class Mensagem(BaseModel):
    texto: str
    debate_id: str
    user_id: str 

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ROTA 1: SÓ DEVOLVE OS DEBATES DO UTILIZADOR QUE PEDIU
@app.get("/debates")
def listar_debates(user_id: str, db: Session = Depends(get_db)):
    debates = db.query(DebateDB).filter(DebateDB.dono_id == user_id).order_by(DebateDB.data_criacao.desc()).all()
    return [{"id": d.id, "titulo": d.titulo} for d in debates]

# ROTA 2: LER HISTÓRICO
@app.get("/chat/{debate_id}")
def ler_historico(debate_id: str, db: Session = Depends(get_db)):
    mensagens = db.query(MensagemDB).filter(MensagemDB.debate_id == debate_id).order_by(MensagemDB.id).all()
    return [{"role": m.role, "texto": m.texto} for m in mensagens]

# ROTA 3: PROCESSAR E GUARDAR CHAT COM O DONO
@app.post("/chat")
def processar_chat(mensagem: Mensagem, db: Session = Depends(get_db)):
    try:
        debate = db.query(DebateDB).filter(DebateDB.id == mensagem.debate_id).first()
        if not debate:
            # ASSOCIA O DEBATE AO USER_ID
            debate = DebateDB(id=mensagem.debate_id, dono_id=mensagem.user_id, titulo=mensagem.texto[:25] + "...")
            db.add(debate)
            db.commit()

        nova_msg_user = MensagemDB(debate_id=mensagem.debate_id, role="user", texto=mensagem.texto)
        db.add(nova_msg_user)
        db.commit()

        mensagens_anteriores = db.query(MensagemDB).filter(MensagemDB.debate_id == mensagem.debate_id).order_by(MensagemDB.id).all()
        historico_formatado = [{"role": msg.role, "parts": [msg.texto]} for msg in mensagens_anteriores[:-1]]

        sessao_chat = modelo_ia.start_chat(history=historico_formatado)
        resposta_ia = sessao_chat.send_message(mensagem.texto)
        
        nova_msg_ia = MensagemDB(debate_id=mensagem.debate_id, role="model", texto=resposta_ia.text)
        db.add(nova_msg_ia)
        db.commit()

        return {"resposta": resposta_ia.text}
    except Exception as e:
        return {"resposta": f"❌ Erro no servidor: {str(e)}"}

# ROTA 4: UPLOAD SEGURO
@app.post("/upload/{debate_id}")
async def upload_documento(debate_id: str, user_id: str, arquivo: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        if not arquivo.filename.endswith(".pdf"):
            return {"status": "erro", "mensagem": "Apenas PDFs são suportados."}

        conteudo = await arquivo.read()
        leitor_pdf = PyPDF2.PdfReader(io.BytesIO(conteudo))
        texto_extraido = "".join([pagina.extract_text() + "\n" for pagina in leitor_pdf.pages])

        texto_contexto = f"[DOCUMENTO DE CONTEXTO ANEXADO PELO USUÁRIO:]\n\n{texto_extraido}"
        
        debate = db.query(DebateDB).filter(DebateDB.id == debate_id).first()
        if not debate:
            # ASSOCIA AO USER_ID AQUI TAMBÉM
            debate = DebateDB(id=debate_id, dono_id=user_id, titulo=arquivo.filename[:25] + "...")
            db.add(debate)
            db.commit()

        nova_msg_contexto = MensagemDB(debate_id=debate_id, role="user", texto=texto_contexto)
        db.add(nova_msg_contexto)
        db.commit()

        return {"status": "sucesso", "mensagem": f"Documento processado."}
    except Exception as e:
        return {"status": "erro", "mensagem": f"Falha: {str(e)}"}

# ROTA 5: APAGAR DEBATE (Verificando o dono)
@app.delete("/chat/{debate_id}")
def deletar_chat(debate_id: str, user_id: str, db: Session = Depends(get_db)):
    debate = db.query(DebateDB).filter(DebateDB.id == debate_id, DebateDB.dono_id == user_id).first()
    if debate:
        db.delete(debate)
        db.commit()
        return {"status": "sucesso"}
    return {"status": "erro"}