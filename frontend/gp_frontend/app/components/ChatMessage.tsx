import React from 'react';

interface ChatMessageProps {
  role: 'user' | 'assistant';
  content: string;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ role, content }) => {
  if (role === 'user') {
    return (
      <div className="flex flex-col items-end gap-2">
        <div className="bg-surface-container-highest px-5 py-3 rounded-xl rounded-tr-none text-sm max-w-lg text-on-surface">
          {content}
        </div>
      </div>
    );
  }

  // Assistant message might just be plain text if it's not a lesson/quiz
  // For the sake of standard messages:
  return (
    <div className="flex flex-col items-start gap-2">
      <div className="bg-surface-variant px-5 py-3 rounded-xl rounded-tl-none text-sm max-w-lg text-on-surface">
        {content}
      </div>
    </div>
  );
};
