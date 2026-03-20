import os
import io
import PyPDF2 
from fastapi import FastAPI, Depends, UploadFile, File 
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import google.generativeai as genai
from sqlalchemy.orm import Session

# Importamos o nosso recém-criado Banco de Dados
from backend.database import SessionLocal, DebateDB, MensagemDB

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("Chave da API não encontrada! Verifique seu arquivo .env")

genai.configure(api_key=api_key)

instrucao_sistema = """
Você é o 'Advogado do Diabo Pessoal'. A sua missão é auditar premissas lógicas com rigor.
Você NUNCA deve enviar blocos de texto contínuos. Estruture SEMPRE a sua resposta no seguinte formato Markdown:

### 🔍 Análise da Premissa
(Parágrafo curto)

### ⚠️ Falhas e Vieses Lógicos
* **(Nome):** (Explicação)

### 🌪️ Cenário de Estresse
(Cenário extremo)

### ⚖️ Veredito
(Frase final de impacto)
"""

modelo_ia = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=instrucao_sistema
)

app = FastAPI(title="Advogado do Diabo API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Mensagem(BaseModel):
    texto: str
    debate_id: str

# --- DEPENDÊNCIA DO BANCO DE DADOS ---
# Esta função abre o cofre (banco de dados), deixa a rota usar, e fecha o cofre no final.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 1. ROTA PARA LER TODOS OS DEBATES SALVOS
@app.get("/debates")
def listar_debates(db: Session = Depends(get_db)):
    debates = db.query(DebateDB).order_by(DebateDB.data_criacao.desc()).all()
    return [{"id": d.id, "titulo": d.titulo} for d in debates]

# 2. ROTA PARA LER AS MENSAGENS DE UM DEBATE ESPECÍFICO
@app.get("/chat/{debate_id}")
def ler_historico(debate_id: str, db: Session = Depends(get_db)):
    mensagens = db.query(MensagemDB).filter(MensagemDB.debate_id == debate_id).order_by(MensagemDB.id).all()
    return [{"role": m.role, "texto": m.texto} for m in mensagens]

# 3. ROTA PRINCIPAL: RECEBER MENSAGEM, SALVAR E RESPONDER
@app.post("/chat")
def processar_chat(mensagem: Mensagem, db: Session = Depends(get_db)):
    try:
        # A. Verifica se o debate já existe no banco. Se não, cria um novo
        debate = db.query(DebateDB).filter(DebateDB.id == mensagem.debate_id).first()
        if not debate:
            debate = DebateDB(id=mensagem.debate_id, titulo=mensagem.texto[:25] + "...")
            db.add(debate)
            db.commit()

        # B. Salva a mensagem do usuário no banco
        nova_msg_user = MensagemDB(debate_id=mensagem.debate_id, role="user", texto=mensagem.texto)
        db.add(nova_msg_user)
        db.commit()

        # C. Reconstrói o histórico da conversa para a IA não sofrer de amnésia
        mensagens_anteriores = db.query(MensagemDB).filter(MensagemDB.debate_id == mensagem.debate_id).order_by(MensagemDB.id).all()
        historico_formatado = []
        for msg in mensagens_anteriores[:-1]: # Ignora a última (que acabamos de salvar)
            historico_formatado.append({"role": msg.role, "parts": [msg.texto]})

        # D. Inicia a IA com as memórias injetadas e pede a resposta
        sessao_chat = modelo_ia.start_chat(history=historico_formatado)
        resposta_ia = sessao_chat.send_message(mensagem.texto)
        
        # E. Salva a resposta do Advogado no banco
        nova_msg_ia = MensagemDB(debate_id=mensagem.debate_id, role="model", texto=resposta_ia.text)
        db.add(nova_msg_ia)
        db.commit()

        return {"resposta": resposta_ia.text}
        
    except Exception as e:
        return {"resposta": f"❌ Erro no servidor: {str(e)}"}

# 4. ROTA PARA APAGAR DO BANCO
@app.delete("/chat/{debate_id}")
def deletar_chat(debate_id: str, db: Session = Depends(get_db)):
    debate = db.query(DebateDB).filter(DebateDB.id == debate_id).first()
    if debate:
        db.delete(debate)
        db.commit() # O cascade="all" configurado no database.py apaga as mensagens automaticamente junto com o debate
        return {"status": "sucesso"}
    return {"status": "erro"}
# 5. NOVA ROTA: RECEBER PDF E EXTRAIR TEXTO
@app.post("/upload/{debate_id}")
async def upload_documento(debate_id: str, arquivo: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        # A. Verifica se o arquivo é um PDF
        if not arquivo.filename.endswith(".pdf"):
            return {"status": "erro", "mensagem": "Apenas arquivos PDF são suportados."}

        # B. Lê o conteúdo do PDF na memória RAM
        conteudo = await arquivo.read()
        leitor_pdf = PyPDF2.PdfReader(io.BytesIO(conteudo))
        
        texto_extraido = ""
        for pagina in leitor_pdf.pages:
            texto_extraido += pagina.extract_text() + "\n"

        if not texto_extraido.strip():
            return {"status": "erro", "mensagem": "Não foi possível extrair texto deste PDF (pode ser uma imagem escaneada)."}

        # C. Injeta o texto no banco de dados como uma mensagem secreta do usuário
        texto_contexto = f"[DOCUMENTO DE CONTEXTO ANEXADO PELO USUÁRIO. USE ESTES DADOS PARA EMBASAR A SUA AUDITORIA:]\n\n{texto_extraido}"
        
        # Cria o debate se não existir
        debate = db.query(DebateDB).filter(DebateDB.id == debate_id).first()
        if not debate:
            debate = DebateDB(id=debate_id, titulo=arquivo.filename[:25] + "...")
            db.add(debate)
            db.commit()

        nova_msg_contexto = MensagemDB(debate_id=debate_id, role="user", texto=texto_contexto)
        db.add(nova_msg_contexto)
        db.commit()

        return {"status": "sucesso", "mensagem": f"Documento '{arquivo.filename}' processado com sucesso! A IA já leu o conteúdo."}

    except Exception as e:
        return {"status": "erro", "mensagem": f"Falha ao ler o PDF: {str(e)}"}