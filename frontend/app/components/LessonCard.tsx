import React from 'react';
import { Icon } from './Icon';

interface LessonCardProps {
  title: string;
  content: React.ReactNode;
  tags?: string[];
  codeSnippet?: string;
  keyTakeaway?: string;
}

export const LessonCard: React.FC<LessonCardProps> = ({
  title,
  content,
  tags = [],
  codeSnippet,
  keyTakeaway
}) => {
  return (
    <div className="flex flex-col items-start gap-4">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center text-primary">
          <Icon name="smart_toy" className="text-lg" />
        </div>
        <span className="font-headline font-bold text-lg text-primary">{title}</span>
      </div>

      <div className="w-full glass-panel rounded-xl p-6 lg:p-8 shadow-2xl space-y-6">
        <div className="prose prose-invert max-w-none">
          <div className="text-on-surface leading-relaxed">
            {content}
          </div>
          
          {tags.length > 0 && (
            <div className="flex flex-wrap gap-2 my-4">
              {tags.map((tag, idx) => {
                const colors = [
                  'bg-primary/10 text-primary border-primary/20',
                  'bg-secondary/10 text-secondary border-secondary/20',
                  'bg-tertiary/10 text-tertiary border-tertiary/20'
                ];
                const colorClass = colors[idx % colors.length];
                
                return (
                  <span key={idx} className={`px-3 py-1 text-xs rounded-full border ${colorClass}`}>
                    {tag}
                  </span>
                )
              })}
            </div>
          )}
        </div>

        {codeSnippet && (
          <div className="bg-surface-container-lowest rounded-xl p-6 font-mono text-sm border border-outline-variant/10 relative group overflow-x-auto">
            <div className="absolute top-4 right-4 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
              <button className="p-1 hover:text-primary">
                <Icon name="content_copy" className="text-sm" />
              </button>
            </div>
            <pre>
              {codeSnippet}
            </pre>
          </div>
        )}

        {keyTakeaway && (
          <div className="bg-primary/5 p-4 rounded-xl border-l-4 border-primary">
            <p className="text-sm italic text-on-surface-variant">
              <strong className="text-on-surface text-opacity-90">Key Takeaway: </strong> 
              {keyTakeaway}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
