import React from 'react';

interface ProgressBarProps {
  progress: number;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({ progress }) => {
  return (
    <div className="bg-surface-container-high rounded-xl p-4 mb-4">
      <div className="flex justify-between items-center mb-2">
        <span className="text-[10px] uppercase tracking-widest text-on-surface-variant font-semibold">
          Course Progress
        </span>
        <span className="text-xs font-bold text-secondary">{progress}%</span>
      </div>
      <div className="w-full h-1.5 bg-secondary-container rounded-full overflow-hidden">
        <div
          className="h-full bg-secondary shadow-[0_0_8px_rgba(105,246,184,0.4)] transition-all duration-700 ease-out"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
};
