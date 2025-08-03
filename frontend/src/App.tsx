import React from 'react';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import './App.css';
import Query from './components/Query';
import Library from './components/Library';

function App() {
  return (
    <Router>
      <div className="App">
        <div className="sidebar">
          <div className="logo-container">
            <h2>PaperQA Discovery</h2>
          </div>
          <nav>
            <ul>
              <li><Link to="/">Query</Link></li>
              <li><Link to="/library">My Library</Link></li>
            </ul>
          </nav>
          <div className="history">
            <h3>History</h3>
            <ul>
              <li>GLP-1 agonists mechanism</li>
              <li>Osimertinib resistance</li>
              <li>CAR-T therapy side effects</li>
            </ul>
          </div>
        </div>
        <div className="main-content-wrapper">
          <Routes>
            <Route path="/" element={<Query />} />
            <Route path="/library" element={<Library />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;