import { useState, useEffect, useCallback } from 'react';

const API_BASE = '/api/v1';

const DEFAULT_FEATURE = `Feature: Edit Compliance Record

  Scenario: Navigate to Edit Compliance Record form using pencil icon
    Given I am on the Fleetlytics login page at https://fleetlytics-test.pages.dev/
    When I enter "Mg@trucking.com" in the email input field
    And I enter "Welcome2eox!" in the password input field
    And I click the Sign In button
    And I wait for 3 seconds for the page to load
    Then I should see the Home page
    Then I should click on Compliance tile
    When I click on the Edit pencil icon button for the first row in the compliance records table
    Then I should see the compliance record edit form
    And the form fields should be pre-filled with existing data
    And I should click on 'Next' button
    And I wait for 3 seconds for the page to load
    And I should click on 'Next' button
    And I wait for 3 seconds for the page to load
    And I should click on 'Next' button
    And I wait for 3 seconds for the page to load
    And I should click on 'Submit' button`;

interface FeatureEditorProps {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}

export function FeatureEditor({ value, onChange, disabled }: FeatureEditorProps) {
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');

  // Initialize with default or loaded content
  useEffect(() => {
    if (!value) {
      loadFeature();
    }
  }, []);

  const loadFeature = async () => {
    try {
      const res = await fetch(`${API_BASE}/features/read/edit_compliance_single.feature`);
      if (res.ok) {
        const data = await res.json();
        onChange(data.content);
      } else {
        onChange(DEFAULT_FEATURE);
      }
    } catch {
      onChange(DEFAULT_FEATURE);
    }
  };

  const saveFeature = useCallback(async () => {
    setSaveStatus('saving');
    try {
      const filename = prompt('Enter filename (e.g., my_test.feature):', 'edit_compliance_single.feature');
      if (!filename) {
        setSaveStatus('idle');
        return;
      }

      const res = await fetch(`${API_BASE}/features/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename, content: value }),
      });

      if (res.ok) {
        setSaveStatus('saved');
        setTimeout(() => setSaveStatus('idle'), 2000);
      } else {
        throw new Error('Save failed');
      }
    } catch {
      setSaveStatus('error');
      setTimeout(() => setSaveStatus('idle'), 3000);
    }
  }, [value]);

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-ghost-blue font-semibold">Feature Editor</h2>
        <div className="flex gap-2">
          <button
            onClick={loadFeature}
            disabled={disabled}
            className="text-xs px-2 py-1 bg-ghost-surface text-ghost-text-muted hover:text-ghost-text rounded disabled:opacity-50"
          >
            Reload
          </button>
          <button
            onClick={saveFeature}
            disabled={disabled || saveStatus === 'saving'}
            className="text-xs px-2 py-1 bg-ghost-surface text-ghost-text-muted hover:text-ghost-text rounded disabled:opacity-50"
          >
            {saveStatus === 'saving' ? 'Saving...' : saveStatus === 'saved' ? 'Saved!' : saveStatus === 'error' ? 'Error' : 'Save As'}
          </button>
        </div>
      </div>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        className="flex-1 w-full bg-ghost-bg text-ghost-green font-mono text-sm p-4 rounded-lg border border-ghost-border focus:border-ghost-blue focus:outline-none resize-none disabled:opacity-50"
        placeholder="Write your Gherkin feature here..."
        spellCheck={false}
      />
    </div>
  );
}
