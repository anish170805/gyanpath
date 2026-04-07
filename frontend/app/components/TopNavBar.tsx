import React from 'react';
import { Icon } from './Icon';

interface TopNavBarProps {
  onMenuClick: () => void;
  isResourcesOpen: boolean;
  onResourcesClick: () => void;
  showResources: boolean;
}

export const TopNavBar: React.FC<TopNavBarProps> = ({ 
  onMenuClick, 
  isResourcesOpen, 
  onResourcesClick,
  showResources
}) => {
  const rightOffset = (showResources && isResourcesOpen) ? "xl:right-80" : "right-0";
  
  return (
    <header className={`fixed top-0 lg:left-64 ${rightOffset} left-0 z-40 flex justify-between items-center h-16 px-4 lg:px-8 bg-surface/80 backdrop-blur-xl transition-all shadow-sm shadow-surface-container-lowest/20 border-b border-outline-variant/10 lg:border-none`}>
      <div className="flex items-center gap-4 lg:gap-6">
        <button 
          className="lg:hidden text-primary p-2 -ml-2"
          onClick={onMenuClick}
        >
          <Icon name="menu" />
        </button>
        <nav className="hidden sm:flex gap-6">
          <a className="font-headline text-sm font-medium text-primary border-b-2 border-primary transition-all pb-[22px] pt-[24px]" href="#">Curriculum</a>
        </nav>
      </div>
      
      <div className="flex items-center gap-2 lg:gap-4">
        {showResources && (
          <button 
            onClick={onResourcesClick}
            className={`p-2 rounded-full transition-all ${isResourcesOpen ? 'bg-primary/20 text-primary' : 'text-on-surface-variant hover:bg-surface-container-highest'}`}
            title={isResourcesOpen ? "Hide Resources" : "Show Resources"}
          >
            <Icon name={isResourcesOpen ? "visibility" : "visibility_off"} />
          </button>
        )}
      </div>
    </header>
  );
};
