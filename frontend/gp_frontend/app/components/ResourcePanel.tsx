import React from 'react';
import { ResourceCard } from './ResourceCard';
import type { Resource } from '../lib/api';

interface ResourcePanelProps {
  resources?: Resource[];
  taskTitle?: string;
}

/** Map resource type → Material Symbol icon name */
function iconForType(type: string): string {
  switch (type) {
    case 'video':   return 'play_circle';
    case 'docs':    return 'description';
    default:        return 'article';
  }
}

export const ResourcePanel: React.FC<ResourcePanelProps> = ({
  resources = [],
  taskTitle = '',
}) => {
  console.log("[ResourcePanel] Rendering with resources:", resources);

  return (
    <aside className="hidden lg:block w-80 h-screen fixed right-0 top-0 bg-surface-container-low border-l border-outline-variant/10 p-8 z-50 overflow-y-auto">
      <h3 className="font-headline font-bold text-lg text-on-surface mb-1">
        Learning Resources
      </h3>
      {taskTitle && (
        <p className="text-xs text-on-surface-variant mb-6 truncate">{taskTitle}</p>
      )}

      {resources.length === 0 ? (
        <p className="text-xs text-on-surface-variant/50 mt-4">
          Resources will appear here once a lesson loads.
        </p>
      ) : (
        <div className="space-y-4">
          {resources.map((r, i) => (
            <ResourceCard
              key={r.url + i}
              title={r.title}
              description={
                r.type === 'video' && r.start_timestamp
                  ? `▶ Watch: ${r.start_timestamp} → ${r.end_timestamp}${r.reason ? `  •  ${r.reason}` : ''}`
                  : r.type === 'docs'
                    ? 'Official documentation'
                    : 'Article / tutorial'
              }
              url={r.url}
              type={r.type}
              iconName={iconForType(r.type)}
              colorType={i % 2 === 0 ? 'primary' : 'tertiary'}
            />
          ))}
        </div>
      )}
    </aside>
  );
};
