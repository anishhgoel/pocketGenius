# PocketGenius: AI-Powered Personal Finance Assistant

PocketGenius is an AI-powered personal finance assistant designed to help users:

- **Categorize and analyze financial transactions**  
- **Assess portfolio performance** (ROI, volatility, Sharpe ratio)  
- **Generate tailored recommendations** (including GPT-based insights)  
- **Provide quick single-symbol analysis and macroeconomic outlook**  

This project combines **FastAPI**, **OpenAI GPT**, **Redis caching**, **yfinance** market data, and a **React frontend** to deliver an interactive financial analysis tool.

### 🌐 Live Demo  
👉 **[PocketGenius App](https://pocket-genius.vercel.app/)**  


## 📌 Features

✅ **Transaction Analysis:** Upload CSVs, categorize expenses, and get GPT-based budgeting suggestions.  
✅ **Portfolio Analysis:** Compute investment metrics and receive AI-powered investment recommendations.  
✅ **Single-Symbol Lookup:** Fetch stock fundamentals, ROI vs purchase, and AI investment advice.  
✅ **Sector Breakdown:** Get an overview of your portfolio’s sector diversification.  
✅ **Macro-Outlook:** AI-generated insights into the current macroeconomic environment.  



## 🛠 Tech Stack

- **Backend:** [FastAPI](https://fastapi.tiangolo.com/), [Uvicorn](https://www.uvicorn.org/), [Python 3.11+]  
- **APIs & Services:** [OpenAI](https://platform.openai.com/), [yfinance](https://pypi.org/project/yfinance/)  
- **Database & Caching:** [Redis](https://redis.io/) (optional)  
- **Frontend:** [React](https://react.dev/) + [Axios](https://axios-http.com/)  
- **Deployment:** [Render](https://render.com/) (Backend), [Vercel](https://vercel.com/) (Frontend)  


---

## 🚀 Installation & Setup

### 1️⃣ Clone the Repository

git clone https://github.com/yourusername/pocketGenius.git
cd pocketGenius

### 1️⃣ Clone the Repository

cd backend
python -m venv venv
source venv/bin/activate  # On Windows use: .\venv\Scripts\activate
pip install -r requirements.txt

#### Create a .env file in backend/ with your OpenAI API key:

OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxx
REDIS_HOST=localhost
REDIS_PORT=6379
CACHE_EXPIRATION_MINUTES=15

#### Start the backend:

uvicorn backend.main:app --host 0.0.0.0 --port 8000

### 3️⃣ Frontend Setup

cd frontend
npm install
npm start

Now, open http://localhost:3000 to view the frontend.