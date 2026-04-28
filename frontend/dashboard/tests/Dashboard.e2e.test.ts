/**
 * Dashboard End-to-End Tests (Cypress)
 * =====================================
 *
 * E2E tests for PM Dashboard user workflows.
 *
 * Test Scenarios:
 * - Command submission flow
 * - Approval workflow
 * - Audit trail navigation
 * - Drift handling
 * - Error recovery
 * - Mobile responsiveness
 *
 * Author: PromptOps Team - Week 9-10
 * Date: 2026-04-28
 */

/// <reference types="cypress" />

// ============================================================================
// Test Configuration
// ============================================================================

const DASHBOARD_URL = Cypress.env('DASHBOARD_URL') || 'http://localhost:3000/dashboard';

describe('PM Dashboard E2E Tests', () => {
  beforeEach(() => {
    // Login and navigate to dashboard
    cy.visit(DASHBOARD_URL);
    cy.get('[data-testid="dashboard"]').should('be.visible');
  });

  // ============================================================================
  // Basic Command Flow
  // ============================================================================

  describe('Command Submission', () => {
    it('should accept and parse a command', () => {
      // Type command
      cy.get('[data-testid="command-input"]')
        .type('Deploy frontend v2.0 to staging');

      // Wait for intent preview
      cy.get('[data-testid="intent-preview"]', { timeout: 1000 })
        .should('be.visible')
        .and('contain', 'deploy')
        .and('contain', 'frontend')
        .and('contain', 'staging');

      // Check confidence indicator
      cy.get('[data-testid="confidence-indicator"]')
        .should('be.visible');
    });

    it('should submit command and show task preview', () => {
      cy.get('[data-testid="command-input"]')
        .type('Deploy frontend v2.0 to staging');

      cy.get('[data-testid="submit-command"]').click();

      // Wait for decomposition
      cy.get('[data-testid="task-preview"]', { timeout: 5000 })
        .should('be.visible');

      // Check sub-tasks tab
      cy.get('[data-testid="tab-subtasks"]').should('be.visible');
      cy.get('[data-testid="subtask-list"]').children().should('have.length.gt', 0);
    });

    it('should show autocomplete suggestions', () => {
      cy.get('[data-testid="command-input"]').type('deploy');

      cy.get('[data-testid="suggestions-dropdown"]', { timeout: 1000 })
        .should('be.visible');

      cy.get('[data-testid="suggestion-item"]')
        .first()
        .click();

      cy.get('[data-testid="command-input"]')
        .should('not.have.value', 'deploy');
    });
  });

  // ============================================================================
  // Approval Workflow
  // ============================================================================

  describe('Approval Flow', () => {
    beforeEach(() => {
      // Submit high-risk command
      cy.get('[data-testid="command-input"]')
        .type('Deploy api v3.0 to production');

      cy.get('[data-testid="submit-command"]').click();

      // Wait for approval flow
      cy.get('[data-testid="approval-flow"]', { timeout: 5000 })
        .should('be.visible');
    });

    it('should require typed confirmation', () => {
      // Approve button should be disabled
      cy.get('[data-testid="approve-button"]').should('be.disabled');

      // Get required phrase
      cy.get('[data-testid="confirmation-code"]')
        .invoke('text')
        .then((phrase) => {
          // Type confirmation
          cy.get('[data-testid="confirmation-input"]').type(phrase);

          // Approve button should be enabled
          cy.get('[data-testid="approve-button"]').should('not.be.disabled');
        });
    });

    it('should show risk assessment', () => {
      cy.get('[data-testid="risk-assessment"]').should('be.visible');
      cy.get('[data-testid="risk-badge"]').should('be.visible');
      cy.get('[data-testid="risk-factors"]').should('be.visible');
    });

    it('should show countdown timer', () => {
      cy.get('[data-testid="approval-timer"]')
        .should('be.visible')
        .and('contain', '5:00');

      // Wait a second and check timer decreases
      cy.wait(1000);
      cy.get('[data-testid="approval-timer"]')
        .should('not.contain', '5:00');
    });

    it('should allow cancellation', () => {
      cy.get('[data-testid="cancel-button"]').click();

      cy.get('[data-testid="approval-flow"]').should('not.exist');
    });

    it('should approve and execute', () => {
      // Get and type confirmation
      cy.get('[data-testid="confirmation-code"]')
        .invoke('text')
        .then((phrase) => {
          cy.get('[data-testid="confirmation-input"]').type(phrase);
          cy.get('[data-testid="approve-button"]').click();
        });

      // Should show executing state
      cy.get('[data-testid="loading-overlay"]', { timeout: 1000 })
        .should('be.visible')
        .and('contain', 'Executing');

      // Should eventually complete
      cy.get('[data-testid="toast-success"]', { timeout: 30000 })
        .should('be.visible')
        .and('contain', 'completed');
    });
  });

  // ============================================================================
  // Task Preview Navigation
  // ============================================================================

  describe('Task Preview', () => {
    beforeEach(() => {
      cy.get('[data-testid="command-input"]')
        .type('Scale backend to 10 instances');

      cy.get('[data-testid="submit-command"]').click();

      cy.get('[data-testid="task-preview"]', { timeout: 5000 })
        .should('be.visible');
    });

    it('should navigate between tabs', () => {
      // Sub-tasks tab (default)
      cy.get('[data-testid="tab-subtasks"]').should('have.class', 'active');
      cy.get('[data-testid="subtask-list"]').should('be.visible');

      // Timeline tab
      cy.get('[data-testid="tab-timeline"]').click();
      cy.get('[data-testid="timeline-view"]').should('be.visible');

      // Dependencies tab
      cy.get('[data-testid="tab-dependencies"]').click();
      cy.get('[data-testid="dependency-graph"]').should('be.visible');

      // Rollback tab
      cy.get('[data-testid="tab-rollback"]').click();
      cy.get('[data-testid="rollback-plan"]').should('be.visible');
    });

    it('should show sub-task details', () => {
      cy.get('[data-testid="subtask-item"]')
        .first()
        .click();

      cy.get('[data-testid="subtask-details"]')
        .should('be.visible')
        .and('contain', 'Command')
        .and('contain', 'Timeout');
    });

    it('should display timeline correctly', () => {
      cy.get('[data-testid="tab-timeline"]').click();

      cy.get('[data-testid="timeline-bar"]').should('be.visible');
      cy.get('[data-testid="critical-path"]').should('be.visible');
    });
  });

  // ============================================================================
  // Audit Trail
  // ============================================================================

  describe('Audit Trail', () => {
    it('should display recent entries', () => {
      cy.get('[data-testid="audit-trail"]').should('be.visible');
      cy.get('[data-testid="audit-entry"]').should('have.length.gt', 0);
    });

    it('should filter by search', () => {
      cy.get('[data-testid="audit-search"]').type('deploy');

      cy.get('[data-testid="audit-entry"]').each(($entry) => {
        cy.wrap($entry).should('contain.text', 'deploy');
      });
    });

    it('should expand entry details', () => {
      cy.get('[data-testid="audit-entry"]').first().click();

      cy.get('[data-testid="audit-entry-details"]')
        .should('be.visible')
        .and('contain', 'Task Plan');
    });

    it('should filter by environment', () => {
      cy.get('[data-testid="filter-button"]').click();
      cy.get('[data-testid="filter-environment"]').select('production');

      cy.get('[data-testid="audit-entry"]').each(($entry) => {
        cy.wrap($entry).should('contain.text', 'production');
      });
    });

    it('should export to CSV', () => {
      cy.get('[data-testid="export-csv"]').click();

      // Check download happened (might need custom cypress plugin)
      cy.readFile('cypress/downloads/audit-trail-*.csv', { timeout: 5000 })
        .should('exist');
    });
  });

  // ============================================================================
  // Drift Monitoring
  // ============================================================================

  describe('Drift Alerts', () => {
    beforeEach(() => {
      // Mock drift event
      cy.intercept('GET', '/api/drift/recent', {
        statusCode: 200,
        body: {
          events: [
            {
              id: 'drift-1',
              timestamp: new Date().toISOString(),
              resource_type: 'ecs_service',
              resource_id: 'frontend-prod',
              field: 'desired_count',
              expected_value: 5,
              actual_value: 3,
              severity: 'critical',
              auto_fixable: true
            }
          ],
          unacknowledged_count: 1
        }
      }).as('getDrift');

      cy.reload();
      cy.wait('@getDrift');
    });

    it('should display drift alert', () => {
      cy.get('[data-testid="drift-alert"]').should('be.visible');
      cy.get('[data-testid="drift-count"]').should('contain', '1');
    });

    it('should expand drift details', () => {
      cy.get('[data-testid="drift-alert"]').click();

      cy.get('[data-testid="drift-event-list"]').should('be.visible');
      cy.get('[data-testid="drift-event"]').should('have.length', 1);
    });

    it('should acknowledge drift', () => {
      cy.get('[data-testid="drift-alert"]').click();
      cy.get('[data-testid="acknowledge-drift"]').first().click();

      cy.get('[data-testid="drift-alert"]').should('not.exist');
    });

    it('should revert drift', () => {
      cy.get('[data-testid="drift-alert"]').click();
      cy.get('[data-testid="revert-drift"]').first().click();

      cy.get('[data-testid="confirmation-modal"]').should('be.visible');
      cy.get('[data-testid="confirm-revert"]').click();

      cy.get('[data-testid="toast-success"]', { timeout: 10000 })
        .should('be.visible')
        .and('contain', 'reverted');
    });
  });

  // ============================================================================
  // Keyboard Shortcuts
  // ============================================================================

  describe('Keyboard Shortcuts', () => {
    it('should focus command input with Cmd+K', () => {
      cy.get('body').type('{meta}k');

      cy.get('[data-testid="command-input"]').should('have.focus');
    });

    it('should clear command with Escape', () => {
      cy.get('[data-testid="command-input"]').type('Deploy frontend');
      cy.get('body').type('{esc}');

      cy.get('[data-testid="command-input"]').should('have.value', '');
    });

    it('should show shortcuts help with Shift+?', () => {
      cy.get('body').type('?', { shiftKey: true });

      cy.get('[data-testid="shortcuts-modal"]').should('be.visible');
    });

    it('should close modal with Escape', () => {
      cy.get('body').type('?', { shiftKey: true });
      cy.get('[data-testid="shortcuts-modal"]').should('be.visible');

      cy.get('body').type('{esc}');
      cy.get('[data-testid="shortcuts-modal"]').should('not.exist');
    });
  });

  // ============================================================================
  // Error Handling
  // ============================================================================

  describe('Error Handling', () => {
    it('should show error toast on API failure', () => {
      cy.intercept('POST', '/api/parse-intent', {
        statusCode: 500,
        body: { error: 'Internal server error' }
      }).as('parseIntentError');

      cy.get('[data-testid="command-input"]').type('Deploy frontend');
      cy.get('[data-testid="submit-command"]').click();

      cy.wait('@parseIntentError');

      cy.get('[data-testid="toast-error"]')
        .should('be.visible')
        .and('contain', 'error');
    });

    it('should allow error dismissal', () => {
      cy.intercept('POST', '/api/parse-intent', {
        statusCode: 500,
        body: { error: 'Internal server error' }
      });

      cy.get('[data-testid="command-input"]').type('Deploy frontend');
      cy.get('[data-testid="submit-command"]').click();

      cy.get('[data-testid="toast-error"]').should('be.visible');
      cy.get('[data-testid="toast-dismiss"]').click();

      cy.get('[data-testid="toast-error"]').should('not.exist');
    });
  });

  // ============================================================================
  // Mobile Responsiveness
  // ============================================================================

  describe('Mobile Responsiveness', () => {
    beforeEach(() => {
      cy.viewport('iphone-x');
    });

    it('should render mobile layout', () => {
      cy.get('[data-testid="dashboard"]').should('be.visible');
      cy.get('[data-testid="command-input"]').should('be.visible');
    });

    it('should stack panels vertically', () => {
      cy.get('[data-testid="dashboard"]').then(($dashboard) => {
        const layout = window.getComputedStyle($dashboard[0]).flexDirection;
        expect(layout).to.equal('column');
      });
    });

    it('should show approval as modal on mobile', () => {
      cy.get('[data-testid="command-input"]')
        .type('Deploy api to production');

      cy.get('[data-testid="submit-command"]').click();

      cy.get('[data-testid="approval-flow"]', { timeout: 5000 })
        .should('have.class', 'modal-overlay');
    });
  });

  // ============================================================================
  // Accessibility
  // ============================================================================

  describe('Accessibility', () => {
    it('should have no detectable accessibility violations', () => {
      cy.injectAxe();
      cy.checkA11y();
    });

    it('should be keyboard navigable', () => {
      cy.get('body').tab();
      cy.focused().should('have.attr', 'data-testid', 'command-input');

      cy.focused().tab();
      cy.focused().should('have.attr', 'data-testid', 'submit-command');
    });

    it('should have proper ARIA labels', () => {
      cy.get('[data-testid="command-input"]')
        .should('have.attr', 'aria-label');

      cy.get('[data-testid="submit-command"]')
        .should('have.attr', 'aria-label');
    });
  });
});
