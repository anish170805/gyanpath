import React, { useState } from 'react';
import { Icon } from './Icon';

interface BottomInputBarProps {
  onSendMessage: (message: string) => void;
  onTakeQuiz?: () => void;
  onNextLesson?: () => void;
}

export const BottomInputBar: React.FC<BottomInputBarProps> = ({ 
  onSendMessage,
  onTakeQuiz,
  onNextLesson
}) => {
  const [input, setInput] = useState('');

  const handleSend = () => {
    if (input.trim()) {
      onSendMessage(input.trim());
      setInput('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSend();
    }
  };

  return (
    <div className="fixed bottom-0 lg:left-64 xl:right-80 left-0 right-0 p-4 lg:p-8 bg-gradient-to-t from-surface via-surface/90 to-transparent z-40">
      <div className="max-w-4xl mx-auto glass-panel p-2 rounded-full border border-outline-variant/10 shadow-xl flex flex-col sm:flex-row items-center gap-2">
        <input 
          className="flex-1 bg-transparent border-none focus:ring-0 focus:outline-none text-on-surface px-4 lg:px-6 py-2 text-sm placeholder:text-on-surface-variant/40 w-full" 
          placeholder="Type your answer here..." 
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          type="text"
        />
        <div className="flex justify-between sm:justify-end items-center gap-2 w-full sm:w-auto px-2 sm:px-0">
          <button 
            className="px-4 lg:px-6 py-2.5 rounded-full text-secondary font-bold text-sm hover:bg-secondary/10 transition-colors whitespace-nowrap"
            onClick={onTakeQuiz}
          >
            Take Quiz
          </button>
          <button 
            className="px-6 lg:px-8 py-2.5 rounded-full bg-secondary text-on-secondary font-bold text-sm shadow-[0_4px_12px_rgba(105,246,184,0.3)] hover:brightness-110 transition-all flex items-center gap-2 whitespace-nowrap"
            onClick={onNextLesson}
          >
            Next Lesson
            <Icon name="arrow_forward" className="text-lg" />
          </button>
        </div>
      </div>
    </div>
  );
};
