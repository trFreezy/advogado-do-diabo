# ⚖️ Advogado do Diabo (Devil's Advocate AI)

Uma aplicação web Full-Stack impulsionada por Inteligência Artificial, concebida para atuar como um auditor lógico implacável. Em vez de agir como um assistente passivo, o sistema utiliza o modelo **Google Gemini 2.5 Flash** e técnicas avançadas de *Prompt Engineering* para detetar vieses cognitivos, apontar falácias estruturais e forçar o utilizador a refinar as suas ideias.

🔗 **[Live Demo (Vercel)](https://advogado-do-diabo.vercel.app/)**

## 🚀 Principais Funcionalidades

* **Arquitetura Multi-Sessão:** Capacidade de gerir múltiplos debates em simultâneo. O histórico é persistido num banco de dados relacional.
* **Upload de Ficheiros (RAG):** Suporte para anexar ficheiros PDF. O backend extrai e memoriza o conteúdo, permitindo à IA fazer auditorias baseadas em documentos privados do utilizador.
* **Exportação de Relatórios:** Geração client-side de ficheiros PDF (via `html2pdf.js`) com o resultado das auditorias para partilha ou arquivo.
* **Renderização Markdown:** Transformação de respostas complexas e estruturadas da IA num layout limpo e elegante (via `marked.js`).
* **Dark Mode UI:** Interface responsiva e otimizada para reduzir a fadiga visual.

## 🛠️ Stack Tecnológica

**Backend (Cérebro):**
* `Python 3`
* `FastAPI` (Roteamento assíncrono e RESTful API)
* `SQLAlchemy` (ORM) + `SQLite` (Persistência de Dados)
* `Google Generative AI SDK` (Integração LLM)
* `PyPDF2` (Extração e processamento de documentos)
* **Hospedagem:** Render.com

**Frontend (Interface):**
* `HTML5` & `CSS3` (Vanilla, sem frameworks pesados)
* `JavaScript ES6` (Gestão de estado, manipulação de DOM e FormData)
* **Hospedagem:** Vercel

## ⚙️ Como correr localmente

1. Clone este repositório:
   ```bash
   git clone [https://github.com/SEU_USUARIO/advogado-do-diabo.git](https://github.com/SEU_USUARIO/advogado-do-diabo.git)
