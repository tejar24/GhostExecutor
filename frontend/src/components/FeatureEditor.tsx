import { useState, useCallback } from 'react';

const API_BASE = '/api/v1';

const PLACEHOLDER_FEATURE = `Feature: Your Test Feature

  Scenario: Describe your test scenario
    Given I am on the application page at https://your-app-url.com/
    When I perform some action
    Then I should see the expected result

# Select a feature from the "Saved Features" list below, or write your own test above.`;

interface FeatureEditorProps {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}

export function FeatureEditor({ value, onChange, disabled }: FeatureEditorProps) {
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');

  const saveFeature = useCallback(async () => {
    setSaveStatus('saving');
    try {
      const filename = prompt('Enter filename (e.g., my_test.feature):', 'new_test.feature');
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

  const handleClear = useCallback(() => {
    onChange('');
  }, [onChange]);

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-ghost-blue font-semibold">Feature Editor</h2>
        <div className="flex gap-2">
          <button
            onClick={handleClear}
            disabled={disabled || !value}
            className="text-xs px-2 py-1 bg-ghost-surface text-ghost-text-muted hover:text-ghost-text rounded disabled:opacity-50"
          >
            Clear
          </button>
          <button
            onClick={saveFeature}
            disabled={disabled || saveStatus === 'saving' || !value}
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
        placeholder={PLACEHOLDER_FEATURE}
        spellCheck={false}
      />
    </div>
  );
}
