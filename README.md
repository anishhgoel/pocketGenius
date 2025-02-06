# PocketGenius: AI-Powered Personal Finance Assistant

PocketGenius is an AI-powered personal finance assistant designed to help users:

- **Categorize and analyze financial transactions**  
- **Assess portfolio performance** (ROI, volatility, Sharpe ratio)  
- **Generate tailored recommendations** (including GPT-based insights)  
- **Provide quick single-symbol analysis and macroeconomic outlook**  

This project combines **FastAPI**, **OpenAI GPT**, **Redis caching**, **yfinance** market data, and a **React frontend** to deliver an interactive financial analysis tool.


---


### 🌐 Live Demo  
👉 **[PocketGenius App](https://pocket-genius.vercel.app/)**  

---


## 📌 Features

✅ **Transaction Analysis:** Upload CSVs, categorize expenses, and get GPT-based budgeting suggestions.  
✅ **Portfolio Analysis:** Compute investment metrics and receive AI-powered investment recommendations.  
✅ **Single-Symbol Lookup:** Fetch stock fundamentals, ROI vs purchase, and AI investment advice.  
✅ **Sector Breakdown:** Get an overview of your portfolio’s sector diversification.  
✅ **Macro-Outlook:** AI-generated insights into the current macroeconomic environment.  

---

 
## 🛠 Tech Stack

- **Backend:**  FastAPI, OpenAI GPT, Redis, yfinance, Uvicorn

- **Frontend:** React, Vite, TailwindCSS

- **Database & Caching:** Redis Cache

- **Deployment:** Render (backend), Vercel (frontend)


---


## 🚀 Installation & Setup

### 1️⃣ Clone the Repository
```
git clone https://github.com/yourusername/pocketGenius.git
cd pocketGenius
```

### 1️⃣ Clone the Repository

```
cd backend
python -m venv venv
source venv/bin/activate  # On Windows use: .\venv\Scripts\activate
pip install -r requirements.txt
```

#### Create a .env file in backend/ with your OpenAI API key:

```

OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxx
REDIS_HOST=localhost
REDIS_PORT=6379
CACHE_EXPIRATION_MINUTES=15
```


#### Start the backend:

```
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```


### 3️⃣ Frontend Setup

```
cd frontend
npm install
npm start
```


Now, open http://localhost:3000 to view the frontend.


---


## 🚀 Endpoints

### 1️⃣ Welcome Message  
#### **GET** `/`
- **Description:** Returns a simple welcome message.
- **Response:**  
  ```json
  {
    "message": "Welcome to FinGenius API. Go to /docs for interactive API docs."
  }
  ```

### 2️⃣ Upload Transactions
### **POST** /upload-transactions
-	**Description:** Upload a CSV file containing transactions to analyze.
-	**Request Body:**
```
{
  "file": "CSV file containing transactions"
}
```
- **Response:**  
```
{
  "transactions": [
    {
      "description": "Coffee",
      "amount": 5.99,
      "date": "2024-02-01",
      "category": "Food & Beverage",
      "budget_recommendation": "Limit coffee expenses to $30/month",
      "savings_potential": "$10 savings possible"
    }
  ]
}
```