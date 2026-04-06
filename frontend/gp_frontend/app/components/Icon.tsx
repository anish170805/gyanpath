import React from 'react';

interface IconProps extends React.HTMLAttributes<HTMLSpanElement> {
  name: string;
  className?: string;
  fill?: boolean;
}

export const Icon: React.FC<IconProps> = ({ name, className = '', fill = false, ...props }) => {
  return (
    <span
      className={`material-symbols-outlined ${className}`}
      {...(fill ? { 'data-weight': 'fill', style: { fontVariationSettings: "'FILL' 1" } } : {})}
      {...props}
    >
      {name}
    </span>
  );
};
