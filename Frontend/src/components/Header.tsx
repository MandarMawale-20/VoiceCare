import React from 'react';
import { Heart, Bell, Mic, MicOff } from 'lucide-react';

interface HeaderProps {
  isListening: boolean;
  toggleListening: () => void;
}

const Header: React.FC<HeaderProps> = ({ isListening, toggleListening }) => {
  return (
    <header className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-4 shadow-lg">
      <div className="container mx-auto flex justify-between items-center">
        <div className="flex items-center space-x-2">
          <Heart className="text-red-300\" size={32} />
          <h1 className="text-2xl font-bold">VoiceCare Assistant</h1>
        </div>
        <div className="flex items-center space-x-4">
          <button 
            className="relative p-2"
            aria-label="Notifications"
          >
            <Bell size={24} />
            <span className="absolute top-0 right-0 bg-red-500 rounded-full w-4 h-4 text-xs flex items-center justify-center">
              3
            </span>
          </button>
          <button 
            onClick={toggleListening}
            className={`p-3 rounded-full transition-all ${isListening ? 'bg-red-500 animate-pulse' : 'bg-gray-700 hover:bg-gray-600'}`}
            aria-label={isListening ? "Stop listening" : "Start listening"}
          >
            {isListening ? <MicOff size={24} /> : <Mic size={24} />}
          </button>
        </div>
      </div>
    </header>
  );
};

export default Header;