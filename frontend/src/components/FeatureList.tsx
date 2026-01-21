import { useState, useEffect, useCallback } from 'react';
import { FeatureListItem } from '../types';

const API_BASE = '/api/v1';

interface FeatureListProps {
  onSelect: (content: string) => void;
}

export function FeatureList({ onSelect }: FeatureListProps) {
  const [features, setFeatures] = useState<FeatureListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadFeatures = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/features`);
      if (!res.ok) throw new Error('Failed to load features');

      const data = await res.json();
      const items: FeatureListItem[] = (data.features || []).map((f: { name: string; file_path: string }) => ({
        filename: f.file_path.split('/').pop() || f.file_path,
        name: f.name,
      }));
      setFeatures(items);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load features');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadFeatures();
  }, [loadFeatures]);

  const handleSelect = async (filename: string) => {
    try {
      const res = await fetch(`${API_BASE}/features/read/${encodeURIComponent(filename)}`);
      if (!res.ok) throw new Error('Failed to load feature');

      const data = await res.json();
      onSelect(data.content);
    } catch (e) {
      alert(`Error loading feature: ${e instanceof Error ? e.message : 'Unknown error'}`);
    }
  };

  const handleDelete = async (filename: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm(`Delete ${filename}?`)) return;

    try {
      // Note: Delete functionality would need a backend endpoint
      // For now, we'll just reload the list
      await loadFeatures();
    } catch {
      alert('Failed to delete feature');
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-ghost-blue font-semibold">Saved Features</h2>
        <button
          onClick={loadFeatures}
          disabled={loading}
          className="text-xs px-2 py-1 bg-ghost-surface text-ghost-text-muted hover:text-ghost-text rounded disabled:opacity-50"
        >
          {loading ? 'Loading...' : 'Refresh'}
        </button>
      </div>

      <div className="flex-1 overflow-y-auto space-y-1">
        {error ? (
          <p className="text-ghost-red text-sm p-2">{error}</p>
        ) : features.length === 0 ? (
          <p className="text-ghost-text-muted text-sm p-2">
            {loading ? 'Loading features...' : 'No features found'}
          </p>
        ) : (
          features.map((feature) => (
            <div
              key={feature.filename}
              onClick={() => handleSelect(feature.filename)}
              className="group flex items-center justify-between p-2 bg-ghost-bg hover:bg-ghost-surface rounded cursor-pointer transition-colors"
            >
              <div className="flex-1 truncate">
                <span className="text-ghost-text text-sm">{feature.filename}</span>
              </div>
              <button
                onClick={(e) => handleDelete(feature.filename, e)}
                className="opacity-0 group-hover:opacity-100 text-ghost-text-muted hover:text-ghost-red text-xs px-2 transition-opacity"
              >
                Delete
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
