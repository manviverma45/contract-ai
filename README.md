\# Contract AI



A full-stack web app for analysing PDF and DOCX documents using AI.



Users can upload documents, ask questions about them, get answers with verified source passages, and compare two documents.



\## Features



\- PDF and DOCX upload

\- PDF text extraction with OCR fallback

\- Document library and delete

\- Duplicate file protection

\- Semantic search using embeddings + FAISS

\- Single and multi-document Q\&A

\- Streaming AI responses

\- Verified document quotations

\- Source passage and page viewing

\- Document comparison



\## Tech Stack



\*\*Frontend:\*\* Next.js, React, TypeScript, Tailwind CSS



\*\*Backend:\*\* Python, FastAPI



\*\*AI / Search:\*\* Google Gemini, Sentence Transformers, FAISS



\*\*Document Processing:\*\* PyMuPDF, python-docx, Tesseract OCR



\## How It Works



```text

Upload Document

&#x20;     ↓

Text Extraction / OCR

&#x20;     ↓

Chunking + Embeddings

&#x20;     ↓

FAISS Retrieval

&#x20;     ↓

Gemini

&#x20;     ↓

Quote Verification

&#x20;     ↓

Answer + Source





Project Structure

contract-ai/

├── backend/

│   ├── routes/

│   ├── services/

│   ├── database/

│   ├── main.py

│   └── requirements.txt

│

├── frontend/

│   ├── src/

│   │   ├── app/

│   │   ├── components/

│   │   └── lib/

│   └── package.json

│

└── README.md

Run Locally

Backend

cd backend

python -m venv venv

venv\\Scripts\\activate

pip install -r requirements.txt



Create backend/.env:



GEMINI\_API\_KEY=your\_api\_key

GEMINI\_MODEL=gemini-3.7-flash



Run:



uvicorn main:app --reload

Frontend

cd frontend

npm install

npm run dev



Open:



http://localhost:3000

Current Limitations



The current version focuses on the core document-analysis workflow.



Not implemented yet:



Tracked DOCX changes

Agentic research workflow

Full coordinate-level PDF highlighting

Persistent chat history

Author



Manvi Verma



GitHub: https://github.com/manviverma45

LinkedIn: https://www.linkedin.com/in/manvi-verma-145800259/





\*\*This is the one I'd use.\*\* It looks normal for a fresher take-home project, isn't unnecessarily verbose, and doesn't pretend you've implemented features you haven't.



Then:



```cmd

git add README.md

git commit -m "Add project README"

git push

