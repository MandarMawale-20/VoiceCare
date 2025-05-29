import React, { useState, useEffect, useCallback } from 'react';
import { Volume2, VolumeX } from 'lucide-react';

interface VoiceAssistantProps {
  isListening: boolean;
  transcript: string;
  processingCommand: boolean;
  lastResponse: string;
  muted: boolean;
  toggleMute: () => void;
}

const VoiceAssistant: React.FC<VoiceAssistantProps> = ({ 
  isListening, 
  transcript, 
  processingCommand,
  lastResponse,
  muted,
  toggleMute
}) => {
  const [showBubble, setShowBubble] = useState(false);
  
  useEffect(() => {
    if (isListening || processingCommand || lastResponse) {
      setShowBubble(true);
    } else {
      const timer = setTimeout(() => setShowBubble(false), 5000);
      return () => clearTimeout(timer);
    }
  }, [isListening, processingCommand, lastResponse]);

  if (!showBubble) return null;

  return (
    <div className="fixed bottom-6 right-6 z-40">
      <div className="bg-white rounded-lg shadow-xl p-4 max-w-xs">
        <div className="flex justify-between items-center mb-2">
          <h3 className="font-semibold text-gray-800">Voice Assistant</h3>
          <button 
            onClick={toggleMute}
            className="p-1 rounded-full hover:bg-gray-100"
            aria-label={muted ? "Unmute" : "Mute"}
          >
            {muted ? <VolumeX size={18} /> : <Volume2 size={18} />}
          </button>
        </div>
        
        {isListening && (
          <div className="mb-2">
            <div className="text-sm text-gray-500">Listening...</div>
            <div className="text-gray-800 italic">"{transcript}"</div>
          </div>
        )}
        
        {processingCommand && (
          <div className="flex items-center space-x-2 text-gray-600">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
            <span>Processing your request...</span>
          </div>
        )}
        
        {lastResponse && !processingCommand && (
          <div className="text-gray-800">{lastResponse}</div>
        )}
        
        <div className="mt-2 text-xs text-gray-500">
          Try saying: "Add a medication reminder" or "What are my reminders for today?"
        </div>
      </div>
    </div>
  );
};

export default VoiceAssistant;