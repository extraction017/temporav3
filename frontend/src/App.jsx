import React from "react";
import "./App.css";
import Calendar from "./Calendar.jsx";
import Weather from "./Weather.jsx";
import Clock from "./Clock.jsx";
import logo from "/tempora_logo.jpg";

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <img src={logo} alt="Tempora Logo" className="app-logo" />
        <h1>Tempora</h1>
        <Clock />
        <Weather />
      </header>
      <Calendar />
    </div>
  );
}

export default App;
