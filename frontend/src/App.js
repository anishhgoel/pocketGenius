import React, { useState } from "react";
import axios from "axios";

function App() {
  // For each endpoint, we'll have some state to store input & results

  // 1) upload-transactions
  const [csvFile, setCsvFile] = useState(null);
  const [transactionsResult, setTransactionsResult] = useState(null);

  // 2) analyze-portfolio
  const [portfolio, setPortfolio] = useState({
    items: [{ symbol: "", quantity: 0, purchase_price: 0 }]
  });
  const [portfolioResult, setPortfolioResult] = useState(null);

  // advanced
  const [riskTolerance, setRiskTolerance] = useState("moderate");
  const [advancedResult, setAdvancedResult] = useState(null);

  // 4) sector breakdown
  const [sectorBreakdownResult, setSectorBreakdownResult] = useState(null);

  // 5) single symbol
  const [symbolData, setSymbolData] = useState({
    symbol: "AAPL",
    purchase_price: 150,
    quantity: 10,
    risk_tolerance: "moderate"
  });
  const [symbolResult, setSymbolResult] = useState(null);

  // 6) custom macros
  const [customData, setCustomData] = useState({
    portfolio: { items: [{ symbol: "AAPL", quantity: 10, purchase_price: 150 }] },
    risk_free_rate: 2.0,
    macro_inflation: 3.0,
    macro_interest_rate: 5.0,
    risk_tolerance: "moderate"
  });
  const [customResult, setCustomResult] = useState(null);

  // 7) macro-outlook
  const [macroResult, setMacroResult] = useState(null);

  const baseURL = "https://pocketgenius.onrender.com"; 

  // -----------------------------
  // 1) Upload CSV
  // -----------------------------
  const handleCsvChange = (e) => {
    setCsvFile(e.target.files[0]);
  };

  const uploadCsv = async () => {
    if (!csvFile) return;
    const formData = new FormData();
    formData.append("file", csvFile);

    try {
      const res = await axios.post(`${baseURL}/upload-transactions`, formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      setTransactionsResult(res.data);
    } catch (err) {
      console.error(err);
      setTransactionsResult({ error: err.message });
    }
  };

  // -----------------------------
  // 2) Analyze Portfolio
  // -----------------------------
  const handlePortfolioChange = (idx, field, rawValue) => {
    const newItems = [...portfolio.items];
  
    if (field === "symbol") {
      // symbol is a string
      newItems[idx].symbol = rawValue;
    } else {
      // quantity and purchase_price are numbers
      const numVal = parseFloat(rawValue);
      newItems[idx][field] = isNaN(numVal) ? 0 : numVal;
    }
  
    setPortfolio({ items: newItems });
  };

  const addPortfolioItem = () => {
    setPortfolio({
      items: [...portfolio.items, { symbol: "", quantity: 0, purchase_price: 0 }]
    });
  };
  const removePortfolioItem = (index) => {
    const newItems = [...portfolio.items];
    newItems.splice(index, 1);
    setPortfolio({ items: newItems });
  };

  const analyzePortfolio = async () => {
    try {
      const res = await axios.post(`${baseURL}/analyze-portfolio`, portfolio);
      setPortfolioResult(res.data);
    } catch (err) {
      console.error(err);
      setPortfolioResult({ error: err.message });
    }
  };

  // -----------------------------
  // 3) Advanced + riskTolerance
  // -----------------------------
  const analyzePortfolioAdvanced = async () => {
    try {
      const res = await axios.post(
        `${baseURL}/analyze-portfolio-advanced?risk_tolerance=${riskTolerance}`,
        portfolio
      );
      setAdvancedResult(res.data);
    } catch (err) {
      console.error(err);
      setAdvancedResult({ error: err.message });
    }
  };

  // -----------------------------
  // 4) Sector Breakdown
  // -----------------------------
  const portfolioSectorBreakdown = async () => {
    try {
      const res = await axios.post(`${baseURL}/portfolio-sector-breakdown`, portfolio);
      setSectorBreakdownResult(res.data);
    } catch (err) {
      console.error(err);
      setSectorBreakdownResult({ error: err.message });
    }
  };

  // -----------------------------
  // 5) Single Symbol
  // -----------------------------
  const analyzeSymbolCall = async () => {
    try {
      const res = await axios.post(`${baseURL}/analyze-symbol`, symbolData);
      setSymbolResult(res.data);
    } catch (err) {
      console.error(err);
      setSymbolResult({ error: err.message });
    }
  };

  // -----------------------------
  // 6) Portfolio custom
  // -----------------------------
  const analyzePortfolioCustom = async () => {
    try {
      const res = await axios.post(`${baseURL}/analyze-portfolio-custom`, customData);
      setCustomResult(res.data);
    } catch (err) {
      console.error(err);
      setCustomResult({ error: err.message });
    }
  };

  // -----------------------------
  // 7) Macro-outlook
  // -----------------------------
  const macroOutlook = async () => {
    try {
      const res = await axios.get(`${baseURL}/macro-outlook`);
      setMacroResult(res.data);
    } catch (err) {
      console.error(err);
      setMacroResult({ error: err.message });
    }
  };

  // Render
  return (
    <div style={{ padding: "1rem" }}>
      <h1>FinGenius - helping you with finances</h1>

      {/* 1) Upload CSV */}
      <section style={{ border: "1px solid #ccc", marginBottom: "1rem", padding: "1rem" }}>
        <h2>1) Upload Transactions</h2>
        <input type="file" accept=".csv" onChange={handleCsvChange} />
        <button onClick={uploadCsv}>Upload CSV</button>
        {transactionsResult && (
          <pre>{JSON.stringify(transactionsResult, null, 2)}</pre>
        )}
      </section>

      {/* 2) Analyze Portfolio */}
      <section style={{ border: "1px solid #ccc", marginBottom: "1rem", padding: "1rem" }}>
        <h2>2) Analyze Portfolio</h2>
        <div>
          {portfolio.items.map((item, idx) => (
            <div key={idx} style={{ marginBottom: "0.5rem" }}>
              <input
                placeholder="Symbol"
                value={item.symbol}
                onChange={(e) =>
                  handlePortfolioChange(idx, "symbol", e.target.value)
                }
              />
              <input
                type="number"
                placeholder="Quantity"
                value={item["quantity"] === "" ? "" : item["quantity"]}
                onChange={(e) =>
                  handlePortfolioChange(idx, "quantity", e.target.value)
                }
              />
              <input
                type="number"
                placeholder="Purchase Price"
                value={item["purchase_price"] === "" ? "" : item["purchase_price"]}
                onChange={(e) =>
                  handlePortfolioChange(idx, "purchase_price", e.target.value)
                }
              />
              <button onClick={() => removePortfolioItem(idx)}>Remove</button>
            </div>
          ))}
          <button onClick={addPortfolioItem}>+ Add Item</button>
        </div>
        <button onClick={analyzePortfolio}>Analyze Portfolio</button>
        {portfolioResult && (
          <pre>{JSON.stringify(portfolioResult, null, 2)}</pre>
        )}
      </section>

      {/* 3) Analyze Portfolio with Risk Tolerance */}
      <section style={{ border: "1px solid #ccc", marginBottom: "1rem", padding: "1rem" }}>
        <h2>3) Analyze Portfolio (Advanced)</h2>
        <p>Risk Tolerance:</p>
        <select value={riskTolerance} onChange={(e) => setRiskTolerance(e.target.value)}>
          <option value="conservative">Conservative</option>
          <option value="moderate">Moderate</option>
          <option value="aggressive">Aggressive</option>
        </select>
        <br />
        <button onClick={analyzePortfolioAdvanced}>Analyze w/ Risk Tolerance</button>
        {advancedResult && (
          <pre>{JSON.stringify(advancedResult, null, 2)}</pre>
        )}
      </section>

      {/* 4) Sector Breakdown */}
      <section style={{ border: "1px solid #ccc", marginBottom: "1rem", padding: "1rem" }}>
        <h2>4) Portfolio Sector Breakdown</h2>
        <p>Uses same portfolio inputs above</p>
        <button onClick={portfolioSectorBreakdown}>Get Sector Breakdown</button>
        {sectorBreakdownResult && (
          <pre>{JSON.stringify(sectorBreakdownResult, null, 2)}</pre>
        )}
      </section>

      {/* 5) Single Symbol */}
      <section style={{ border: "1px solid #ccc", marginBottom: "1rem", padding: "1rem" }}>
        <h2>5) Analyze Single Symbol</h2>
        <div>
          <input
            placeholder="Symbol"
            value={symbolData.symbol}
            onChange={(e) => setSymbolData({ ...symbolData, symbol: e.target.value })}
          />
          <input
            type="number"
            placeholder="Purchase Price"
            value={symbolData.purchase_price}
            onChange={(e) =>
              setSymbolData({ ...symbolData, purchase_price: parseFloat(e.target.value) })
            }
          />
          <input
            type="number"
            placeholder="Quantity"
            value={symbolData.quantity}
            onChange={(e) =>
              setSymbolData({ ...symbolData, quantity: parseFloat(e.target.value) })
            }
          />
          <select
            value={symbolData.risk_tolerance}
            onChange={(e) => setSymbolData({ ...symbolData, risk_tolerance: e.target.value })}
          >
            <option value="conservative">Conservative</option>
            <option value="moderate">Moderate</option>
            <option value="aggressive">Aggressive</option>
          </select>
        </div>
        <button onClick={analyzeSymbolCall}>Analyze Symbol</button>
        {symbolResult && (
          <pre>{JSON.stringify(symbolResult, null, 2)}</pre>
        )}
      </section>

      {/* 6) Custom macros/risk */}
      <section style={{ border: "1px solid #ccc", marginBottom: "1rem", padding: "1rem" }}>
        <h2>6) Analyze Portfolio (Custom Macros/Risk-Free)</h2>
        <p>Edit the JSON below or add more items:</p>
        <textarea
          rows={8}
          cols={50}
          value={JSON.stringify(customData, null, 2)}
          onChange={(e) => {
            // parse the user's JSON changes
            try {
              setCustomData(JSON.parse(e.target.value));
            } catch (err) {
              // ignore parse errors
            }
          }}
        />
        <br />
        <button onClick={analyzePortfolioCustom}>Analyze with custom macros</button>
        {customResult && (
          <pre>{JSON.stringify(customResult, null, 2)}</pre>
        )}
      </section>

      {/* 7) Macro-Outlook */}
      <section style={{ border: "1px solid #ccc", marginBottom: "1rem", padding: "1rem" }}>
        <h2>7) Macro-Outlook</h2>
        <button onClick={macroOutlook}>Get Macro Outlook</button>
        {macroResult && (
          <pre>{JSON.stringify(macroResult, null, 2)}</pre>
        )}
      </section>
    </div>
  );
}

export default App;