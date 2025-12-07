"""Data persistence utilities for JSON file storage."""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import tempfile
import shutil
from .config import DATA_FILES

def load_json_data(file_key: str, default: Any = None) -> Any:
    """
    Load data from a JSON file.
    
    Args:
        file_key: Key from DATA_FILES config
        default: Default value if file doesn't exist or is invalid
        
    Returns:
        Loaded data or default value
    """
    if default is None:
        default = {} if file_key in ["bookings", "queue", "clients", "feedback", "barbers", "notifications"] else []
    
    file_path = DATA_FILES.get(file_key)
    if not file_path:
        return default
    
    try:
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data
        else:
            return default
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading {file_key}: {e}. Using default value.")
        return default

def save_json_data(file_key: str, data: Any) -> bool:
    """
    Save data to a JSON file using atomic write.
    
    Args:
        file_key: Key from DATA_FILES config
        data: Data to save
        
    Returns:
        True if successful, False otherwise
    """
    file_path = DATA_FILES.get(file_key)
    if not file_path:
        return False
    
    try:
        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Atomic write: write to temp file, then rename
        temp_file = file_path.with_suffix('.tmp')
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Atomic rename
        shutil.move(str(temp_file), str(file_path))
        return True
    except (IOError, OSError) as e:
        print(f"Error saving {file_key}: {e}")
        # Clean up temp file if it exists
        temp_file = file_path.with_suffix('.tmp')
        if temp_file.exists():
            try:
                temp_file.unlink()
            except:
                pass
        return False

def load_dict_data(file_key: str) -> Dict[str, Any]:
    """Load dictionary data from JSON file."""
    data = load_json_data(file_key, {})
    if isinstance(data, dict):
        return data
    return {}

def save_dict_data(file_key: str, data: Dict[str, Any]) -> bool:
    """Save dictionary data to JSON file."""
    return save_json_data(file_key, data)

def load_list_data(file_key: str) -> List[Any]:
    """Load list data from JSON file."""
    data = load_json_data(file_key, [])
    if isinstance(data, list):
        return data
    return []

def save_list_data(file_key: str, data: List[Any]) -> bool:
    """Save list data to JSON file."""
    return save_json_data(file_key, data)

