import React from 'react';
import { Icon } from './Icon';

interface ResourceCardProps {
  title: string;
  description: string;
  url: string;
  type?: string;
  iconName: string;
  colorType: 'primary' | 'tertiary';
}

function getYoutubeVideoId(url: string | undefined | null) {
  if (!url) return null;
  const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=)([^#&?]*).*/;
  const match = url.match(regExp);
  return (match && match[2].length === 11) ? match[2] : null;
}

export const ResourceCard: React.FC<ResourceCardProps> = ({ 
  title, 
  description, 
  url, 
  type,
  iconName, 
  colorType 
}) => {
  const isPrimary = colorType === 'primary';
  const iconBgClass = isPrimary ? 'bg-primary/10 text-primary' : 'bg-tertiary/10 text-tertiary';
  const hoverTextClass = isPrimary ? 'group-hover:text-primary' : 'group-hover:text-tertiary';
  const barColorClass = isPrimary ? 'bg-primary' : 'bg-tertiary';

  const videoId = type === 'video' ? getYoutubeVideoId(url) : null;

  return (
    <a 
      href={url} 
      target="_blank" 
      rel="noopener noreferrer"
      className="block bg-surface-container-highest rounded-xl overflow-hidden hover:shadow-lg transition-all group border border-outline-variant/10 shadow-sm"
    >
      {videoId ? (
        <div className="w-full h-40 bg-surface-container overflow-hidden relative">
          <img 
            src={`https://img.youtube.com/vi/${videoId}/hqdefault.jpg`} 
            alt="YouTube Thumbnail"
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
          <div className="absolute inset-0 bg-black/20 group-hover:bg-transparent transition-colors flex items-center justify-center">
            <Icon name="play_circle" className="text-4xl text-white opacity-80 group-hover:opacity-100 drop-shadow-md" fill />
          </div>
        </div>
      ) : (
        <div className="flex items-center justify-between p-5 pb-3">
          <div className={`p-2 rounded-lg ${iconBgClass}`}>
            <Icon name={iconName} className="text-xl" />
          </div>
          <Icon name="open_in_new" className={`text-on-surface-variant transition-colors ${hoverTextClass}`} />
        </div>
      )}
      
      <div className={videoId ? "p-4" : "px-5 pb-5"}>
        <h4 className="font-bold text-sm mb-1 line-clamp-2">{title}</h4>
        {videoId && <span className="text-[10px] font-bold uppercase text-primary mb-2 block">Watch on YouTube</span>}
        <p className="text-xs text-on-surface-variant leading-relaxed line-clamp-2">{description}</p>
        
        <div className={`mt-4 h-1 w-0 group-hover:w-full transition-all duration-300 ${barColorClass}`} />
      </div>
    </a>
  );
};
