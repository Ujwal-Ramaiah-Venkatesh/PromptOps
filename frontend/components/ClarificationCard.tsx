/**
 * Clarification Card Component for PromptOps
 * ==========================================
 *
 * Interactive UI component that displays clarification questions when the
 * NLP parser detects ambiguity (confidence < 85%).
 *
 * Features:
 * - Clean, accessible card design
 * - Radio button or card-style options
 * - Mobile responsive
 * - Keyboard navigation support
 * - Integrates with parser clarification_questions output
 *
 * Example Usage:
 * ```tsx
 * <ClarificationCard
 *   question="Which version would you like to deploy?"
 *   options={[
 *     { id: "1", label: "v2.1.0 (latest)", badge: "Latest", value: "v2.1.0" },
 *     { id: "2", label: "v2.0.9 (stable)", badge: "Stable", value: "v2.0.9" }
 *   ]}
 *   onSelect={(value) => handleClarification(value)}
 *   onCancel={() => handleCancel()}
 * />
 * ```
 *
 * Author: PromptOps Team - Week 3-4
 * Date: 2026-04-20
 */

import React, { useState } from 'react';
import './ClarificationCard.css';

// ============================================================================
// Types
// ============================================================================

export interface ClarificationOption {
  id: string;
  label: string;
  description?: string;
  badge?: string;
  value: any;
  icon?: string;
}

export interface ClarificationCardProps {
  question: string;
  options: ClarificationOption[];
  onSelect: (value: any) => void;
  onCancel?: () => void;
  variant?: 'radio' | 'cards';  // Display style
  defaultSelected?: string;      // Default option ID
}

// ============================================================================
// Main Component
// ============================================================================

export const ClarificationCard: React.FC<ClarificationCardProps> = ({
  question,
  options,
  onSelect,
  onCancel,
  variant = 'cards',
  defaultSelected
}) => {
  const [selectedId, setSelectedId] = useState<string | null>(defaultSelected || null);

  const handleOptionClick = (option: ClarificationOption) => {
    setSelectedId(option.id);
  };

  const handleConfirm = () => {
    const selectedOption = options.find(opt => opt.id === selectedId);
    if (selectedOption) {
      onSelect(selectedOption.value);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent, option: ClarificationOption) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleOptionClick(option);
    }
  };

  return (
    <div className="clarification-card">
      <div className="clarification-card__header">
        <div className="clarification-card__icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M9.09 9C9.3251 8.33167 9.78915 7.76811 10.4 7.40913C11.0108 7.05016 11.7289 6.91894 12.4272 7.03871C13.1255 7.15848 13.7588 7.52152 14.2151 8.06353C14.6713 8.60553 14.9211 9.29152 14.92 10C14.92 12 11.92 13 11.92 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M12 17H12.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </div>
        <h3 className="clarification-card__title">Clarification Needed</h3>
      </div>

      <p className="clarification-card__question">{question}</p>

      <div className={`clarification-card__options clarification-card__options--${variant}`}>
        {options.map((option) => (
          <div
            key={option.id}
            className={`clarification-option clarification-option--${variant} ${
              selectedId === option.id ? 'clarification-option--selected' : ''
            }`}
            onClick={() => handleOptionClick(option)}
            onKeyDown={(e) => handleKeyDown(e, option)}
            role="radio"
            aria-checked={selectedId === option.id}
            tabIndex={0}
          >
            {variant === 'radio' ? (
              <div className="clarification-option__radio">
                <input
                  type="radio"
                  name="clarification"
                  value={option.id}
                  checked={selectedId === option.id}
                  onChange={() => handleOptionClick(option)}
                  tabIndex={-1}
                />
              </div>
            ) : (
              <div className="clarification-option__check">
                {selectedId === option.id && (
                  <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M16.6667 5L7.50004 14.1667L3.33337 10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                )}
              </div>
            )}

            <div className="clarification-option__content">
              <div className="clarification-option__header">
                {option.icon && (
                  <span className="clarification-option__icon">{option.icon}</span>
                )}
                <span className="clarification-option__label">{option.label}</span>
                {option.badge && (
                  <span className="clarification-option__badge">{option.badge}</span>
                )}
              </div>
              {option.description && (
                <p className="clarification-option__description">{option.description}</p>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="clarification-card__actions">
        {onCancel && (
          <button
            type="button"
            className="clarification-card__button clarification-card__button--secondary"
            onClick={onCancel}
          >
            Cancel
          </button>
        )}
        <button
          type="button"
          className="clarification-card__button clarification-card__button--primary"
          onClick={handleConfirm}
          disabled={!selectedId}
        >
          Continue
        </button>
      </div>
    </div>
  );
};

// ============================================================================
// Helper Component: Environment Option
// ============================================================================

export const EnvironmentOption: React.FC<{ env: string }> = ({ env }) => {
  const envConfig = {
    production: { icon: '🔴', badge: 'High Risk', color: 'red' },
    staging: { icon: '🟡', badge: 'Medium Risk', color: 'yellow' },
    dev: { icon: '🟢', badge: 'Low Risk', color: 'green' },
  };

  const config = envConfig[env as keyof typeof envConfig] || { icon: '⚪', badge: '', color: 'gray' };

  return (
    <span className={`env-option env-option--${config.color}`}>
      <span className="env-option__icon">{config.icon}</span>
      <span className="env-option__name">{env}</span>
      {config.badge && <span className="env-option__badge">{config.badge}</span>}
    </span>
  );
};

// ============================================================================
// Helper Component: Service Option
// ============================================================================

export const ServiceOption: React.FC<{ service: string; status?: string }> = ({ service, status }) => {
  return (
    <span className="service-option">
      <span className="service-option__name">{service}</span>
      {status && <span className={`service-option__status service-option__status--${status}`}>{status}</span>}
    </span>
  );
};

// ============================================================================
// Example Usage Component
// ============================================================================

export const ClarificationCardExample: React.FC = () => {
  const [result, setResult] = useState<any>(null);

  const handleSelect = (value: any) => {
    console.log('Selected:', value);
    setResult(value);
  };

  const handleCancel = () => {
    console.log('Cancelled');
    setResult(null);
  };

  // Example 1: Version selection
  const versionOptions: ClarificationOption[] = [
    {
      id: '1',
      label: 'v2.1.0',
      badge: 'Latest',
      value: { version: 'v2.1.0' },
      description: 'Latest production release with new features'
    },
    {
      id: '2',
      label: 'v2.0.9',
      badge: 'Stable',
      value: { version: 'v2.0.9' },
      description: 'Current stable version in production'
    },
    {
      id: '3',
      label: 'v2.0.8',
      value: { version: 'v2.0.8' },
      description: 'Previous stable release'
    },
    {
      id: '4',
      label: 'Other version...',
      value: { version: 'custom' },
      description: 'Specify a different version'
    }
  ];

  // Example 2: Environment selection
  const environmentOptions: ClarificationOption[] = [
    {
      id: '1',
      label: 'Production',
      badge: 'High Risk',
      icon: '🔴',
      value: { target_env: 'production' },
      description: 'Deploy to live production environment'
    },
    {
      id: '2',
      label: 'Staging',
      badge: 'Medium Risk',
      icon: '🟡',
      value: { target_env: 'staging' },
      description: 'Deploy to staging for testing'
    },
    {
      id: '3',
      label: 'Development',
      badge: 'Low Risk',
      icon: '🟢',
      value: { target_env: 'dev' },
      description: 'Deploy to development environment'
    }
  ];

  // Example 3: Service selection
  const serviceOptions: ClarificationOption[] = [
    {
      id: '1',
      label: 'API Service',
      value: { target_service: 'api' },
      description: 'Backend REST API'
    },
    {
      id: '2',
      label: 'Frontend',
      value: { target_service: 'frontend' },
      description: 'React web application'
    },
    {
      id: '3',
      label: 'Database',
      badge: 'Critical',
      value: { target_service: 'database' },
      description: 'PostgreSQL database'
    }
  ];

  return (
    <div style={{ padding: '20px', maxWidth: '600px', margin: '0 auto' }}>
      <h2>Clarification Card Examples</h2>

      <div style={{ marginBottom: '40px' }}>
        <h3>Example 1: Version Selection (Card Style)</h3>
        <ClarificationCard
          question="Which version would you like to deploy?"
          options={versionOptions}
          onSelect={handleSelect}
          onCancel={handleCancel}
          variant="cards"
        />
      </div>

      <div style={{ marginBottom: '40px' }}>
        <h3>Example 2: Environment Selection (Radio Style)</h3>
        <ClarificationCard
          question="Which environment should we deploy to?"
          options={environmentOptions}
          onSelect={handleSelect}
          onCancel={handleCancel}
          variant="radio"
        />
      </div>

      <div style={{ marginBottom: '40px' }}>
        <h3>Example 3: Service Selection</h3>
        <ClarificationCard
          question="Which service do you want to restart?"
          options={serviceOptions}
          onSelect={handleSelect}
          variant="cards"
          defaultSelected="1"
        />
      </div>

      {result && (
        <div style={{ padding: '20px', background: '#f0f0f0', borderRadius: '8px' }}>
          <h4>Result:</h4>
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};

export default ClarificationCard;
