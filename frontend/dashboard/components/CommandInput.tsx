/**
 * Command Input Component
 * =======================
 *
 * Command input with real-time intent preview, auto-complete,
 * and confidence indicators.
 *
 * Features:
 * - Debounced parsing (500ms)
 * - Real-time intent preview
 * - Confidence score visualization
 * - Auto-complete suggestions
 * - Recent commands history
 * - Keyboard shortcuts
 *
 * Author: PromptOps Team - Week 9-10
 * Date: 2026-04-28
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import './CommandInput.css';

// ============================================================================
// Type Definitions
// ============================================================================

export interface ParsedIntent {
  intent_type: string;
  target_service: string;
  target_env?: string;
  parameters: Record<string, any>;
  confidence: number;
  ambiguity_score: number;
  missing_params: string[];
  requires_approval: boolean;
  warnings?: string[];
}

export interface CommandSuggestion {
  text: string;
  description: string;
  type: 'recent' | 'template' | 'context';
}

export interface CommandInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: (command: string) => void;
  parsedIntent?: ParsedIntent | null;
  isLoading?: boolean;
  autoComplete?: boolean;
  showHistory?: boolean;
  placeholder?: string;
}

// ============================================================================
// Command Input Component
// ============================================================================

export function CommandInput({
  value,
  onChange,
  onSubmit,
  parsedIntent,
  isLoading = false,
  autoComplete = true,
  showHistory = true,
  placeholder = "Enter command (e.g., 'Deploy frontend v2.0 to staging')"
}: CommandInputProps): JSX.Element {
  const [suggestions, setSuggestions] = useState<CommandSuggestion[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedSuggestion, setSelectedSuggestion] = useState(0);
  const [recentCommands, setRecentCommands] = useState<string[]>([]);
  const [showIntentPreview, setShowIntentPreview] = useState(false);

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);

  // Load recent commands from localStorage
  useEffect(() => {
    if (showHistory) {
      const stored = localStorage.getItem('promptops_recent_commands');
      if (stored) {
        try {
          setRecentCommands(JSON.parse(stored));
        } catch (e) {
          console.error('Failed to parse recent commands:', e);
        }
      }
    }
  }, [showHistory]);

  // Generate suggestions based on input
  useEffect(() => {
    if (!autoComplete || !value || value.length < 2) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }

    const newSuggestions: CommandSuggestion[] = [];
    const lowerValue = value.toLowerCase();

    // Recent commands
    if (showHistory) {
      const matchingRecent = recentCommands.filter(cmd =>
        cmd.toLowerCase().includes(lowerValue)
      );
      matchingRecent.slice(0, 3).forEach(cmd => {
        newSuggestions.push({
          text: cmd,
          description: 'Recent command',
          type: 'recent'
        });
      });
    }

    // Template suggestions
    const templates = getTemplateSuggestions(value);
    templates.forEach(template => {
      newSuggestions.push(template);
    });

    setSuggestions(newSuggestions);
    setShowSuggestions(newSuggestions.length > 0);
    setSelectedSuggestion(0);
  }, [value, autoComplete, showHistory, recentCommands]);

  // Show/hide intent preview
  useEffect(() => {
    setShowIntentPreview(!!parsedIntent && value.length > 0);
  }, [parsedIntent, value]);

  // Handle keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (showSuggestions && suggestions.length > 0) {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedSuggestion(prev =>
          prev < suggestions.length - 1 ? prev + 1 : 0
        );
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedSuggestion(prev =>
          prev > 0 ? prev - 1 : suggestions.length - 1
        );
      } else if (e.key === 'Tab' || e.key === 'Enter') {
        if (e.key === 'Tab') {
          e.preventDefault();
        }
        if (selectedSuggestion >= 0 && selectedSuggestion < suggestions.length) {
          selectSuggestion(suggestions[selectedSuggestion].text);
        } else if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          handleSubmit();
        }
      } else if (e.key === 'Escape') {
        setShowSuggestions(false);
      }
    } else if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  // Select suggestion
  const selectSuggestion = useCallback((text: string) => {
    onChange(text);
    setShowSuggestions(false);
    textareaRef.current?.focus();
  }, [onChange]);

  // Handle submit
  const handleSubmit = () => {
    if (!value.trim() || isLoading) return;

    // Save to recent commands
    if (showHistory) {
      const updated = [value, ...recentCommands.filter(cmd => cmd !== value)].slice(0, 10);
      setRecentCommands(updated);
      localStorage.setItem('promptops_recent_commands', JSON.stringify(updated));
    }

    onSubmit(value);
  };

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  }, [value]);

  return (
    <div className="command-input-container">
      <div className="command-input-wrapper">
        <textarea
          ref={textareaRef}
          className="command-input-textarea"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          rows={1}
          disabled={isLoading}
          aria-label="Command input"
        />

        <button
          className="command-input-submit"
          onClick={handleSubmit}
          disabled={!value.trim() || isLoading}
          aria-label="Submit command"
        >
          {isLoading ? (
            <span className="button-spinner"></span>
          ) : (
            '→'
          )}
        </button>
      </div>

      {/* Suggestions Dropdown */}
      {showSuggestions && suggestions.length > 0 && (
        <div ref={suggestionsRef} className="command-suggestions">
          {suggestions.map((suggestion, index) => (
            <div
              key={index}
              className={`suggestion-item ${index === selectedSuggestion ? 'suggestion-item--selected' : ''}`}
              onClick={() => selectSuggestion(suggestion.text)}
              onMouseEnter={() => setSelectedSuggestion(index)}
            >
              <div className="suggestion-text">{suggestion.text}</div>
              <div className="suggestion-description">
                <span className={`suggestion-badge suggestion-badge--${suggestion.type}`}>
                  {suggestion.type}
                </span>
                {suggestion.description}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Intent Preview */}
      {showIntentPreview && parsedIntent && (
        <IntentPreview intent={parsedIntent} />
      )}
    </div>
  );
}

// ============================================================================
// Intent Preview Component
// ============================================================================

interface IntentPreviewProps {
  intent: ParsedIntent;
}

function IntentPreview({ intent }: IntentPreviewProps): JSX.Element {
  const confidencePercent = Math.round(intent.confidence * 100);
  const isHighConfidence = intent.confidence >= 0.8;
  const isMediumConfidence = intent.confidence >= 0.6;

  return (
    <div className="intent-preview">
      <div className="intent-preview-header">
        <span className="intent-preview-title">Intent Preview</span>
        <div className="intent-preview-confidence">
          <ConfidenceIndicator confidence={intent.confidence} />
          <span className="confidence-text">{confidencePercent}%</span>
        </div>
      </div>

      <div className="intent-preview-body">
        <div className="intent-field">
          <span className="intent-label">Type:</span>
          <span className="intent-value intent-value--type">{intent.intent_type}</span>
        </div>

        <div className="intent-field">
          <span className="intent-label">Service:</span>
          <span className="intent-value">{intent.target_service}</span>
        </div>

        {intent.target_env && (
          <div className="intent-field">
            <span className="intent-label">Environment:</span>
            <span className={`intent-value intent-value--env intent-value--env-${intent.target_env}`}>
              {intent.target_env}
            </span>
          </div>
        )}

        {Object.keys(intent.parameters).length > 0 && (
          <div className="intent-field">
            <span className="intent-label">Parameters:</span>
            <div className="intent-params">
              {Object.entries(intent.parameters).map(([key, value]) => (
                <span key={key} className="intent-param">
                  {key}: {String(value)}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Warnings */}
      {intent.missing_params.length > 0 && (
        <div className="intent-warning">
          <span className="warning-icon">⚠️</span>
          <span className="warning-text">
            Missing: {intent.missing_params.join(', ')}
          </span>
        </div>
      )}

      {intent.requires_approval && (
        <div className="intent-approval-required">
          <span className="approval-icon">🔒</span>
          <span className="approval-text">Approval required</span>
        </div>
      )}

      {/* Validation Status */}
      <div className="intent-preview-footer">
        {intent.missing_params.length === 0 ? (
          <span className="validation-status validation-status--success">
            ✓ All required parameters present
          </span>
        ) : (
          <span className="validation-status validation-status--warning">
            ⚠ Some parameters missing
          </span>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// Confidence Indicator Component
// ============================================================================

interface ConfidenceIndicatorProps {
  confidence: number;
}

function ConfidenceIndicator({ confidence }: ConfidenceIndicatorProps): JSX.Element {
  const percent = confidence * 100;
  let color = '#ef4444'; // red (low)

  if (confidence >= 0.8) {
    color = '#10b981'; // green (high)
  } else if (confidence >= 0.6) {
    color = '#f59e0b'; // yellow (medium)
  }

  return (
    <div className="confidence-indicator">
      <svg width="32" height="32" viewBox="0 0 32 32">
        <circle
          cx="16"
          cy="16"
          r="14"
          fill="none"
          stroke="#e5e7eb"
          strokeWidth="3"
        />
        <circle
          cx="16"
          cy="16"
          r="14"
          fill="none"
          stroke={color}
          strokeWidth="3"
          strokeDasharray={`${2 * Math.PI * 14}`}
          strokeDashoffset={`${2 * Math.PI * 14 * (1 - confidence)}`}
          strokeLinecap="round"
          transform="rotate(-90 16 16)"
        />
      </svg>
    </div>
  );
}

// ============================================================================
// Helper Functions
// ============================================================================

function getTemplateSuggestions(input: string): CommandSuggestion[] {
  const lowerInput = input.toLowerCase();
  const templates: CommandSuggestion[] = [];

  // Deploy templates
  if (lowerInput.includes('deploy')) {
    templates.push({
      text: 'Deploy frontend v2.0 to staging',
      description: 'Deploy service to environment',
      type: 'template'
    });
    templates.push({
      text: 'Deploy api v1.5 to production with canary rollout',
      description: 'Canary deployment',
      type: 'template'
    });
  }

  // Scale templates
  if (lowerInput.includes('scale')) {
    templates.push({
      text: 'Scale backend to 10 instances',
      description: 'Scale service instances',
      type: 'template'
    });
  }

  // Rollback templates
  if (lowerInput.includes('rollback')) {
    templates.push({
      text: 'Rollback frontend to previous version',
      description: 'Rollback to last stable',
      type: 'template'
    });
  }

  // Monitor templates
  if (lowerInput.includes('show') || lowerInput.includes('monitor')) {
    templates.push({
      text: 'Show me current AWS spending',
      description: 'Cost monitoring',
      type: 'template'
    });
  }

  return templates.slice(0, 3); // Limit to 3 templates
}

export default CommandInput;
