import React from 'react';
import { Icon } from './Icon';
import { ProgressBar } from './ProgressBar';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  // Live data from the learning session
  roadmap?: string[];
  currentTaskIndex?: number;
  progressPct?: number;
  isFinished?: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({
  isOpen,
  onClose,
  roadmap = [],
  currentTaskIndex = 0,
  progressPct = 0,
  isFinished = false,
}) => {
  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar Content */}
      <aside
        className={`h-screen w-64 fixed left-0 top-0 flex flex-col py-6 px-4 bg-surface-container-low font-headline tracking-tight z-50 transition-transform duration-300 ${
          isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        <div className="mb-6 px-2 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <img src="/GyanPath.jpeg" alt="GyanPath Logo" className="w-10 h-10 rounded-xl object-cover border border-primary/20 shadow-sm" />
            <div>
              <h1 className="text-lg font-bold text-primary leading-tight">GyanPath</h1>
              <p className="text-[10px] text-on-surface/40 uppercase tracking-wider font-semibold">AI Learning</p>
            </div>
          </div>
          <button className="lg:hidden text-on-surface" onClick={onClose}>
            <Icon name="close" />
          </button>
        </div>

        {/* Roadmap task list */}
        {roadmap.length > 0 ? (
          <nav className="flex-1 overflow-y-auto space-y-1 pr-1">
            <p className="text-[10px] uppercase tracking-widest text-on-surface-variant font-semibold mb-3 px-3">
              Curriculum
            </p>
            {roadmap.map((title, i) => {
              const isDone    = isFinished || i < currentTaskIndex;
              const isCurrent = !isFinished && i === currentTaskIndex;
              return (
                <div
                  key={i}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-body transition-colors
                    ${isCurrent
                      ? 'text-primary font-bold bg-surface-container-high border-r-2 border-primary'
                      : isDone
                        ? 'text-secondary/60 line-through'
                        : 'text-on-surface/50'
                    }`}
                >
                  <Icon
                    name={isDone ? 'check_circle' : isCurrent ? 'menu_book' : 'radio_button_unchecked'}
                    className={`text-lg shrink-0 ${isDone ? 'text-secondary' : ''}`}
                    fill={isDone}
                  />
                  <span className="truncate">{title}</span>
                </div>
              );
            })}
          </nav>
        ) : (
          <nav className="flex-1 space-y-1">
            <a className="flex items-center gap-3 px-3 py-2.5 rounded-xl transition-colors text-on-surface/60 hover:text-on-surface hover:bg-surface-container-high" href="#">
              <Icon name="map" className="text-xl" />
              <span className="text-sm font-body">Topic Roadmap</span>
            </a>
            <a className="flex items-center gap-3 px-3 py-2.5 rounded-xl transition-colors text-primary font-bold border-r-2 border-primary bg-surface-container-high" href="#">
              <Icon name="menu_book" className="text-xl" />
              <span className="text-sm font-body">Current Lesson</span>
            </a>
            <a className="flex items-center gap-3 px-3 py-2.5 rounded-xl transition-colors text-on-surface/60 hover:text-on-surface hover:bg-surface-container-high" href="#">
              <Icon name="library_books" className="text-xl" />
              <span className="text-sm font-body">Resources</span>
            </a>
          </nav>
        )}

        <div className="mt-4 px-2">
          <ProgressBar progress={isFinished ? 100 : progressPct} />
        </div>
      </aside>
    </>
  );
};
