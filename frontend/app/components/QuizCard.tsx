import React, { useState } from 'react';
import { Icon } from './Icon';

interface QuizOption {
  id: string;
  text: string;
  isCorrect: boolean;
}

interface QuizCardProps {
  question: string;
  options: QuizOption[];
  evaluationText?: string;
}

export const QuizCard: React.FC<QuizCardProps> = ({ question, options, evaluationText }) => {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);

  const handleSelect = (id: string) => {
    if (!submitted) {
      setSelectedId(id);
    }
  };

  const selectedOption = options.find(o => o.id === selectedId);
  const isCorrect = selectedOption?.isCorrect;

  return (
    <div className="flex flex-col items-start gap-4">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-secondary/20 flex items-center justify-center text-secondary">
          <Icon name="quiz" className="text-lg" />
        </div>
        <span className="font-headline font-bold text-lg text-secondary">Quiz: Knowledge Check</span>
      </div>

      <div className="w-full bg-surface-container-high rounded-xl p-6 border border-outline-variant/10">
        <p className="text-on-surface mb-4">{question}</p>
        
        <div className="space-y-3 mb-4">
          {options.map((option) => {
            const isSelected = selectedId === option.id;
            
            let btnClass = "w-full text-left px-5 py-4 rounded-xl transition-colors text-sm border flex items-center justify-between group ";
            let iconNode = <Icon name="radio_button_unchecked" className="opacity-0 group-hover:opacity-100 transition-opacity text-on-surface-variant" />;

            if (isSelected) {
              btnClass += "bg-primary-container text-on-primary-container font-medium border-primary/40";
              iconNode = <Icon name="check_circle" fill className="text-primary" />;
            } else {
              btnClass += "bg-surface-variant hover:bg-surface-bright border-outline-variant/20";
            }

            // Post-submission styling
            if (submitted) {
              if (option.isCorrect) {
                btnClass = "w-full text-left px-5 py-4 rounded-xl transition-colors text-sm border flex items-center justify-between bg-secondary-container text-on-surface font-medium border-secondary/40";
                iconNode = <Icon name="check_circle" fill className="text-secondary" />;
              } else if (isSelected && !option.isCorrect) {
                btnClass = "w-full text-left px-5 py-4 rounded-xl transition-colors text-sm border flex items-center justify-between bg-error-container text-on-error-container font-medium border-error/40";
                iconNode = <Icon name="cancel" fill className="text-error" />;
              } else {
                btnClass = "w-full text-left px-5 py-4 rounded-xl transition-colors text-sm border flex items-center justify-between bg-surface-variant text-on-surface/50 border-outline-variant/10";
                iconNode = <Icon name="radio_button_unchecked" className="opacity-0 text-on-surface-variant" />;
              }
            }

            return (
              <button 
                key={option.id}
                className={btnClass}
                onClick={() => handleSelect(option.id)}
                disabled={submitted}
              >
                <span>{option.text}</span>
                {iconNode}
              </button>
            );
          })}
        </div>

        {!submitted && selectedId && (
          <button 
            className="w-full py-3 bg-secondary text-on-secondary font-bold rounded-xl text-sm hover:brightness-110 transition-all font-body mt-2"
            onClick={() => setSubmitted(true)}
          >
            Submit Answer
          </button>
        )}
      </div>

      {submitted && (
        <div className="flex flex-col items-start gap-4 pb-12 w-full mt-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-tertiary/20 flex items-center justify-center text-tertiary">
              <Icon name="analytics" className="text-lg" />
            </div>
            <span className="font-headline font-bold text-lg text-tertiary">Evaluation</span>
          </div>

          <div className="w-full bg-surface-container rounded-xl p-6 flex gap-6 items-center border border-outline-variant/5">
            <div className={`w-16 h-16 rounded-full border-4 flex items-center justify-center shrink-0 ${isCorrect ? 'border-secondary/30 text-secondary' : 'border-error/30 text-error'}`}>
              <span className="text-lg font-bold">{isCorrect ? 'A+' : 'Try'}</span>
            </div>
            <div>
              <h4 className="font-bold text-on-surface">{isCorrect ? 'Concept Mastered' : 'Needs Review'}</h4>
              <p className="text-sm text-on-surface-variant mt-1">
                {isCorrect 
                  ? evaluationText || "Excellent work." 
                  : "Let's review this concept and try again."}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
