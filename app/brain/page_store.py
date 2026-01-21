"""
Page Brain Storage Manager

Persists and retrieves UI Brain data for pages, enabling
cross-session element intelligence and self-healing.
"""

import json
import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse


class PageBrainStore:
    """
    Storage manager for UI Brain page data.

    Stores one JSON file per unique page, enabling:
    - Cross-session persistence
    - Element history tracking
    - Self-healing selector resolution
    """

    def __init__(self, storage_dir: str = "brain_data"):
        """
        Initialize the page brain store.

        Args:
            storage_dir: Directory for storing brain JSON files
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._index_file = self.storage_dir / "brain_index.json"
        self._index: Dict[str, Dict[str, Any]] = self._load_index()

    def _load_index(self) -> Dict[str, Dict[str, Any]]:
        """Load the brain index file."""
        if self._index_file.exists():
            try:
                with open(self._index_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {}

    def _save_index(self) -> None:
        """Save the brain index file."""
        try:
            with open(self._index_file, "w", encoding="utf-8") as f:
                json.dump(self._index, f, indent=2)
        except IOError:
            pass

    def _generate_page_key(self, url: str, title: str = "") -> str:
        """
        Generate a unique key for a page.

        Args:
            url: Page URL
            title: Page title

        Returns:
            Unique page key
        """
        parsed = urlparse(url)
        # Use domain + path as base
        base = f"{parsed.netloc}{parsed.path}"
        # Add hash of title for differentiation
        if title:
            base += f"_{hashlib.md5(title.encode()).hexdigest()[:8]}"

        # Create safe filename
        safe_key = "".join(c if c.isalnum() or c in "-_" else "_" for c in base)
        return safe_key[:100]  # Limit length

    def _get_storage_path(self, page_key: str) -> Path:
        """Get the storage path for a page brain."""
        return self.storage_dir / f"{page_key}.json"

    def save_brain(self, brain_data: Dict[str, Any]) -> str:
        """
        Save a page brain to storage.

        Args:
            brain_data: Page brain dictionary (from PageBrain.to_dict())

        Returns:
            Page key used for storage
        """
        url = brain_data.get("url", "")
        title = brain_data.get("title", "")

        page_key = self._generate_page_key(url, title)
        storage_path = self._get_storage_path(page_key)

        # Add storage metadata
        brain_data["_storage"] = {
            "page_key": page_key,
            "stored_at": datetime.now().isoformat(),
            "version": 1
        }

        # Save to file
        try:
            with open(storage_path, "w", encoding="utf-8") as f:
                json.dump(brain_data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            raise RuntimeError(f"Failed to save brain: {e}")

        # Update index
        self._index[page_key] = {
            "url": url,
            "title": title,
            "dom_hash": brain_data.get("dom_hash", ""),
            "element_count": brain_data.get("element_count", 0),
            "last_updated": datetime.now().isoformat(),
            "file_path": str(storage_path)
        }
        self._save_index()

        return page_key

    def load_brain(self, url: str, title: str = "") -> Optional[Dict[str, Any]]:
        """
        Load a page brain from storage.

        Args:
            url: Page URL
            title: Page title (optional)

        Returns:
            Page brain dictionary or None if not found
        """
        page_key = self._generate_page_key(url, title)
        storage_path = self._get_storage_path(page_key)

        if not storage_path.exists():
            # Try without title
            page_key_no_title = self._generate_page_key(url, "")
            storage_path = self._get_storage_path(page_key_no_title)
            if not storage_path.exists():
                return None

        try:
            with open(storage_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

    def load_brain_by_key(self, page_key: str) -> Optional[Dict[str, Any]]:
        """
        Load a page brain by its key.

        Args:
            page_key: The page key

        Returns:
            Page brain dictionary or None
        """
        storage_path = self._get_storage_path(page_key)

        if not storage_path.exists():
            return None

        try:
            with open(storage_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

    def check_brain_valid(self, url: str, current_dom_hash: str, title: str = "") -> bool:
        """
        Check if stored brain is still valid for current DOM.

        Args:
            url: Page URL
            current_dom_hash: Current DOM hash
            title: Page title

        Returns:
            True if stored brain matches current DOM
        """
        brain = self.load_brain(url, title)
        if not brain:
            return False

        return brain.get("dom_hash") == current_dom_hash

    def get_element_by_id(self, url: str, element_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific element from stored brain.

        Args:
            url: Page URL
            element_id: Element ID to find

        Returns:
            Element data or None
        """
        brain = self.load_brain(url)
        if not brain:
            return None

        elements = brain.get("elements", [])
        for element in elements:
            if element.get("element_id") == element_id:
                return element

        return None

    def find_element_by_label(self, url: str, label: str) -> Optional[Dict[str, Any]]:
        """
        Find an element by its resolved label.

        Args:
            url: Page URL
            label: Label to search for

        Returns:
            Element data or None
        """
        brain = self.load_brain(url)
        if not brain:
            return None

        label_lower = label.lower()
        elements = brain.get("elements", [])

        for element in elements:
            resolved_label = element.get("resolved_label", "")
            if resolved_label and label_lower in resolved_label.lower():
                return element

        return None

    def find_elements_by_type(self, url: str, element_type: str) -> List[Dict[str, Any]]:
        """
        Find all elements of a specific type.

        Args:
            url: Page URL
            element_type: Element type to find

        Returns:
            List of matching elements
        """
        brain = self.load_brain(url)
        if not brain:
            return []

        elements = brain.get("elements", [])
        return [
            e for e in elements
            if e.get("element_type") == element_type or e.get("element_subtype") == element_type
        ]

    def get_all_selectors(self, url: str) -> Dict[str, str]:
        """
        Get all element selectors for a page.

        Args:
            url: Page URL

        Returns:
            Dict mapping element_id to logical_selector
        """
        brain = self.load_brain(url)
        if not brain:
            return {}

        selectors = {}
        for element in brain.get("elements", []):
            element_id = element.get("element_id")
            selector = element.get("logical_selector")
            if element_id and selector:
                selectors[element_id] = selector

        return selectors

    def list_stored_pages(self) -> List[Dict[str, Any]]:
        """
        List all stored page brains.

        Returns:
            List of page metadata
        """
        return [
            {
                "page_key": key,
                **data
            }
            for key, data in self._index.items()
        ]

    def delete_brain(self, url: str, title: str = "") -> bool:
        """
        Delete a stored page brain.

        Args:
            url: Page URL
            title: Page title

        Returns:
            True if deleted, False if not found
        """
        page_key = self._generate_page_key(url, title)
        storage_path = self._get_storage_path(page_key)

        if storage_path.exists():
            try:
                os.remove(storage_path)
                if page_key in self._index:
                    del self._index[page_key]
                    self._save_index()
                return True
            except IOError:
                return False

        return False

    def clear_all(self) -> int:
        """
        Clear all stored brains.

        Returns:
            Number of brains deleted
        """
        count = 0
        for path in self.storage_dir.glob("*.json"):
            if path.name != "brain_index.json":
                try:
                    os.remove(path)
                    count += 1
                except IOError:
                    pass

        self._index = {}
        self._save_index()

        return count

    def export_brain(self, url: str, output_path: str) -> bool:
        """
        Export a page brain to a specific path.

        Args:
            url: Page URL
            output_path: Output file path

        Returns:
            True if exported successfully
        """
        brain = self.load_brain(url)
        if not brain:
            return False

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(brain, f, indent=2, ensure_ascii=False)
            return True
        except IOError:
            return False

    def import_brain(self, input_path: str) -> Optional[str]:
        """
        Import a page brain from a file.

        Args:
            input_path: Input file path

        Returns:
            Page key if imported successfully, None otherwise
        """
        try:
            with open(input_path, "r", encoding="utf-8") as f:
                brain_data = json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

        if "url" not in brain_data:
            return None

        return self.save_brain(brain_data)

    def get_element_history(self, url: str, element_id: str) -> List[Dict[str, Any]]:
        """
        Get selector history for an element across brain versions.

        Note: This is a placeholder for future version tracking.

        Args:
            url: Page URL
            element_id: Element ID

        Returns:
            List of historical selector data
        """
        # Current implementation only returns current selector
        element = self.get_element_by_id(url, element_id)
        if element:
            return [{
                "selector": element.get("logical_selector"),
                "timestamp": datetime.now().isoformat(),
                "confidence": element.get("selector_confidence", 1.0)
            }]
        return []
