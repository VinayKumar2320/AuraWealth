# AuraWealth

AuraWealth is a lightweight stock research and portfolio allocation demo built as a full-stack web app. It combines a modern frontend with a FastAPI backend to help users explore research-backed stock ideas and simulate portfolio allocation based on a chosen risk profile.

## What this project does

- Displays curated stock recommendations with sector, sentiment, and rationale
- Lets users enter an investment amount and risk level
- Calculates a simple portfolio allocation using fractional shares
- Supports live mock market updates through a WebSocket stream
- Exposes a backend API for allocation and investment simulation

## Tech stack

### Frontend
- Next.js
- React
- TypeScript
- Tailwind CSS

### Backend
- FastAPI
- Uvicorn
- Python
- WebSocket support

## Project structure

- frontend/ - Next.js frontend application
- backend/ - FastAPI backend API
- render.yaml - Render deployment configuration for the backend

## Local development

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The backend will run on http://localhost:8000

## Deployment

### Backend on Render
The backend is designed to be deployed on Render using the configuration in render.yaml.

### Frontend on Vercel
The frontend can be deployed on Vercel with the project root set to the frontend folder.

## Live demo

Frontend: https://aurawealth-lovat.vercel.app/

Backend: https://aurawealth-w54f.onrender.com/

## Notes

This project is intended as a demo and uses mock market data for the stock insights and live price stream.
