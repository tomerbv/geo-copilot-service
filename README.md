# geo-copilot-service

## Prereqs
- Python 3.10+
- [Ollama](https://ollama.com) running locally
- Pull a model: `ollama pull llama3.1:8b`

## Run
```
python -m venv .venv
. .venv/Scripts/activate      # Windows PowerShell
pip install -r requirements.txt
copy .env.example .env        # adjust if needed
python app.py
```
Service listens on `http://localhost:8080`.
