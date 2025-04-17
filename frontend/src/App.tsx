import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import DailyNews from './pages/DailyNews';
import Chat from './pages/Chat';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-100 flex justify-center">
        {/* Mobile container */}
        <div className="w-full max-w-[414px] min-h-screen bg-gradient-to-br from-purple-700 to-blue-500 shadow-2xl">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/news" element={<DailyNews />} />
            <Route path="/chat" element={<Chat />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App; 