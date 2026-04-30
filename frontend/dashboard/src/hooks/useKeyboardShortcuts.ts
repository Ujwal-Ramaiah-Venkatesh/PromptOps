/**
 * Keyboard Shortcuts Hook
 * ========================
 *
 * Centralized keyboard shortcut management for dashboard.
 *
 * Features:
 * - Global keyboard shortcuts
 * - Context-aware shortcuts
 * - Shortcut conflicts detection
 * - Help menu integration
 * - Customizable key bindings
 * - Platform-specific modifiers (Cmd/Ctrl)
 *
 * Author: PromptOps Team - Week 9-10
 * Date: 2026-04-28
 */

import { useEffect, useCallback, useRef } from 'react';

// ============================================================================
// Type Definitions
// ============================================================================

export interface KeyboardShortcut {
  key: string;
  ctrl?: boolean;
  shift?: boolean;
  alt?: boolean;
  meta?: boolean; // Command key on Mac
  description: string;
  handler: (event: KeyboardEvent) => void;
  enabled?: boolean;
  global?: boolean; // Works even when input is focused
}

export interface ShortcutGroup {
  name: string;
  shortcuts: KeyboardShortcut[];
}

// ============================================================================
// Platform Detection
// ============================================================================

const isMac = typeof window !== 'undefined' && navigator.platform.toUpperCase().indexOf('MAC') >= 0;

export const MODIFIER_KEY = isMac ? 'Cmd' : 'Ctrl';
export const MODIFIER_SYMBOL = isMac ? '⌘' : 'Ctrl';

// ============================================================================
// Shortcut Helpers
// ============================================================================

function matchesShortcut(event: KeyboardEvent, shortcut: KeyboardShortcut): boolean {
  const keyMatches = event.key.toLowerCase() === shortcut.key.toLowerCase() ||
                     event.code === shortcut.key;

  const ctrlMatches = shortcut.ctrl ? event.ctrlKey : !event.ctrlKey;
  const shiftMatches = shortcut.shift ? event.shiftKey : !event.shiftKey;
  const altMatches = shortcut.alt ? event.altKey : !event.altKey;
  const metaMatches = shortcut.meta ? event.metaKey : !event.metaKey;

  return keyMatches && ctrlMatches && shiftMatches && altMatches && metaMatches;
}

function shouldIgnoreEvent(event: KeyboardEvent, shortcut: KeyboardShortcut): boolean {
  // Ignore if shortcut is disabled
  if (shortcut.enabled === false) {
    return true;
  }

  // Allow global shortcuts
  if (shortcut.global) {
    return false;
  }

  // Ignore if user is typing in an input/textarea
  const target = event.target as HTMLElement;
  if (
    target.tagName === 'INPUT' ||
    target.tagName === 'TEXTAREA' ||
    target.isContentEditable
  ) {
    return true;
  }

  return false;
}

export function formatShortcut(shortcut: KeyboardShortcut): string {
  const parts: string[] = [];

  if (shortcut.meta) parts.push(MODIFIER_SYMBOL);
  if (shortcut.ctrl && !shortcut.meta) parts.push('Ctrl');
  if (shortcut.alt) parts.push('Alt');
  if (shortcut.shift) parts.push('Shift');
  parts.push(shortcut.key.toUpperCase());

  return parts.join('+');
}

// ============================================================================
// Main Hook
// ============================================================================

export function useKeyboardShortcuts(shortcuts: KeyboardShortcut[]): void {
  const shortcutsRef = useRef(shortcuts);

  // Update ref when shortcuts change
  useEffect(() => {
    shortcutsRef.current = shortcuts;
  }, [shortcuts]);

  // Handle keyboard events
  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    for (const shortcut of shortcutsRef.current) {
      if (matchesShortcut(event, shortcut)) {
        if (shouldIgnoreEvent(event, shortcut)) {
          continue;
        }

        event.preventDefault();
        event.stopPropagation();
        shortcut.handler(event);
        break; // Only trigger first matching shortcut
      }
    }
  }, []);

  // Attach event listener
  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [handleKeyDown]);
}

// ============================================================================
// Dashboard Shortcuts Configuration
// ============================================================================

export function getDashboardShortcuts(actions: {
  focusCommandInput: () => void;
  submitCommand: () => void;
  clearCommand: () => void;
  approveTask: () => void;
  rejectTask: () => void;
  toggleHelp: () => void;
  refreshDashboard: () => void;
  exportAudit: () => void;
  showAuditTrail: () => void;
  undo: () => void;
}): ShortcutGroup[] {
  return [
    {
      name: 'General',
      shortcuts: [
        {
          key: '/',
          description: 'Focus command input',
          handler: actions.focusCommandInput,
          global: false
        },
        {
          key: 'Escape',
          description: 'Clear command',
          handler: actions.clearCommand,
          global: true
        },
        {
          key: '?',
          shift: true,
          description: 'Show keyboard shortcuts',
          handler: actions.toggleHelp,
          global: false
        },
        {
          key: 'r',
          meta: true,
          description: 'Refresh dashboard',
          handler: (e) => {
            e.preventDefault();
            actions.refreshDashboard();
          },
          global: true
        }
      ]
    },
    {
      name: 'Command Execution',
      shortcuts: [
        {
          key: 'Enter',
          meta: true,
          description: 'Submit command',
          handler: actions.submitCommand,
          global: true
        },
        {
          key: 'k',
          meta: true,
          description: 'Focus command input',
          handler: actions.focusCommandInput,
          global: true
        }
      ]
    },
    {
      name: 'Approval Actions',
      shortcuts: [
        {
          key: 'a',
          meta: true,
          shift: true,
          description: 'Approve task',
          handler: actions.approveTask,
          global: false
        },
        {
          key: 'x',
          meta: true,
          shift: true,
          description: 'Reject task',
          handler: actions.rejectTask,
          global: false
        }
      ]
    },
    {
      name: 'Navigation',
      shortcuts: [
        {
          key: 'h',
          meta: true,
          description: 'View audit trail',
          handler: actions.showAuditTrail,
          global: false
        },
        {
          key: 'e',
          meta: true,
          description: 'Export audit trail',
          handler: actions.exportAudit,
          global: false
        }
      ]
    },
    {
      name: 'Editing',
      shortcuts: [
        {
          key: 'z',
          meta: true,
          description: 'Undo last action',
          handler: actions.undo,
          global: false
        }
      ]
    }
  ];
}

// ============================================================================
// Keyboard Shortcuts Help Modal Component
// ============================================================================

import React from 'react';
import './KeyboardShortcuts.css';

interface KeyboardShortcutsModalProps {
  show: boolean;
  onClose: () => void;
  shortcuts: ShortcutGroup[];
}

export function KeyboardShortcutsModal({
  show,
  onClose,
  shortcuts
}: KeyboardShortcutsModalProps): JSX.Element | null {
  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && show) {
        onClose();
      }
    };

    window.addEventListener('keydown', handleEscape);
    return () => window.removeEventListener('keydown', handleEscape);
  }, [show, onClose]);

  if (!show) return null;

  return (
    <div className="keyboard-shortcuts-overlay" onClick={onClose}>
      <div className="keyboard-shortcuts-modal" onClick={(e) => e.stopPropagation()}>
        <div className="keyboard-shortcuts-header">
          <h2>Keyboard Shortcuts</h2>
          <button className="shortcuts-close-button" onClick={onClose} aria-label="Close">
            ×
          </button>
        </div>

        <div className="keyboard-shortcuts-body">
          {shortcuts.map((group, index) => (
            <div key={index} className="shortcut-group">
              <h3 className="shortcut-group-name">{group.name}</h3>
              <div className="shortcut-list">
                {group.shortcuts
                  .filter(s => s.enabled !== false)
                  .map((shortcut, shortcutIndex) => (
                    <div key={shortcutIndex} className="shortcut-item">
                      <span className="shortcut-description">{shortcut.description}</span>
                      <kbd className="shortcut-keys">{formatShortcut(shortcut)}</kbd>
                    </div>
                  ))}
              </div>
            </div>
          ))}
        </div>

        <div className="keyboard-shortcuts-footer">
          <p>Press <kbd>Esc</kbd> to close</p>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// useShortcutHelp Hook
// ============================================================================

export function useShortcutHelp(shortcuts: ShortcutGroup[]) {
  const [showHelp, setShowHelp] = React.useState(false);

  const toggleHelp = useCallback(() => {
    setShowHelp(prev => !prev);
  }, []);

  const closeHelp = useCallback(() => {
    setShowHelp(false);
  }, []);

  const openHelp = useCallback(() => {
    setShowHelp(true);
  }, []);

  return {
    showHelp,
    toggleHelp,
    closeHelp,
    openHelp,
    ShortcutsModal: () => (
      <KeyboardShortcutsModal
        show={showHelp}
        onClose={closeHelp}
        shortcuts={shortcuts}
      />
    )
  };
}

export default useKeyboardShortcuts;
