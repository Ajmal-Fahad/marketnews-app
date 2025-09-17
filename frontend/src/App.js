// frontend/src/App.js
import React, { useEffect, useState } from "react";
import "./App.css";

function App() {
  const [cards, setCards] = useState([]);

  useEffect(() => {
    fetch("http://127.0.0.1:8000/cards")
      .then((res) => res.json())
      .then((data) => setCards(data))
      .catch((err) => console.error("Error fetching cards:", err));
  }, []);

  return (
    <div className="app-container">
      <h1>Market News Cards</h1>
      {cards.length === 0 ? (
        <p>No cards found.</p>
      ) : (
        cards.map((card) => (
          <div key={card.id} className="card">
            <h3>
              <strong>{card.company}</strong>{" "}
              <span className="meta">- {card.event_type}</span>
            </h3>
            <p>{card.summary}</p>
            <a href={card.url} target="_blank" rel="noreferrer" className="source">
              Source
            </a>
          </div>
        ))
      )}
    </div>
  );
}

export default App;