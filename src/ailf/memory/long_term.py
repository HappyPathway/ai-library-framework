"""Long-term memory implementation for AILF agents."""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, TypeVar

from pydantic import BaseModel

from ailf.schemas.memory import MemoryItem, UserProfile, KnowledgeFact

# Generic type for Pydantic models used in LTM
M = TypeVar('M', bound=BaseModel)

class LongTermMemory:
    """
    Manages long-term memory for an agent, using file-based storage for Pydantic models.
    Each model type is stored in its own subdirectory.
    """

    def __init__(self, base_storage_path: str):
        """
        Initializes the long-term memory store.

        :param base_storage_path: The root directory where long-term memory files will be stored.
        :type base_storage_path: str
        """
        self.base_path = Path(base_storage_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_storage_path(self, model_cls: Type[M], item_id: str) -> Path:
        """
        Determines the storage path for a given model type and item ID.

        :param model_cls: The Pydantic model class (e.g., UserProfile, KnowledgeFact).
        :type model_cls: Type[M]
        :param item_id: The unique identifier for the item.
        :type item_id: str
        :return: The full path to the item's JSON file.
        :rtype: Path
        """
        # Use the class name for the subdirectory, preserving case
        model_dir_name = model_cls.__name__
        storage_dir = self.base_path / model_dir_name
        storage_dir.mkdir(parents=True, exist_ok=True)
        return storage_dir / f"{item_id}.json"

    async def store_item(self, item: M) -> None:
        """
        Stores a Pydantic model item (e.g., UserProfile, KnowledgeFact) in long-term memory.
        The item must have an 'item_id' or '{model_name}_id' attribute for use as filename.

        :param item: The Pydantic model instance to store.
        :type item: M
        :raises ValueError: If the item does not have a suitable ID attribute.
        """
        import sys
        print(f"DEBUG store_item: Storing item of type {type(item).__name__}", file=sys.stderr)
        
        try:
            item_id = self._extract_id(item)
            print(f"DEBUG store_item: Extracted ID: {item_id}", file=sys.stderr)
            
            file_path = self._get_storage_path(item.__class__, item_id)
            print(f"DEBUG store_item: File path: {file_path}", file=sys.stderr)
            
            # Pydantic v2 uses model_dump_json, v1 uses json()
            serialized_item = item.model_dump_json(indent=2) if hasattr(item, 'model_dump_json') else item.json(indent=2)
            print(f"DEBUG store_item: Serialized item: {serialized_item[:100]}...", file=sys.stderr)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(serialized_item)
                print(f"DEBUG store_item: Successfully wrote to {file_path}", file=sys.stderr)
            
            # Verify file exists after write
            import os
            if os.path.exists(file_path):
                print(f"DEBUG store_item: Verified file exists at {file_path}", file=sys.stderr)
            else:
                print(f"DEBUG store_item: ERROR - File does not exist after write: {file_path}", file=sys.stderr)
                
        except Exception as e:
            print(f"DEBUG store_item: Exception: {str(e)}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            raise

    async def retrieve_item(self, model_cls: Type[M], item_id: str) -> Optional[M]:
        """
        Retrieves an item of a specific Pydantic model type from long-term memory.

        :param model_cls: The Pydantic model class to retrieve (e.g., UserProfile).
        :type model_cls: Type[M]
        :param item_id: The ID of the item to retrieve.
        :type item_id: str
        :return: The deserialized Pydantic model instance if found, else None.
        :rtype: Optional[M]
        """
        import sys
        print(f"DEBUG retrieve_item: Looking for {model_cls.__name__} with ID {item_id}", file=sys.stderr)
        
        try:
            file_path = self._get_storage_path(model_cls, item_id)
            print(f"DEBUG retrieve_item: Path to check: {file_path}", file=sys.stderr)
            
            if not file_path.exists():
                print(f"DEBUG retrieve_item: File not found at {file_path}", file=sys.stderr)
                
                # Debug: List all files in the directory to check what's there
                dir_path = file_path.parent
                if dir_path.exists():
                    print(f"DEBUG retrieve_item: Files in directory {dir_path}:", file=sys.stderr)
                    for f in dir_path.iterdir():
                        print(f"  - {f.name}", file=sys.stderr)
                else:
                    print(f"DEBUG retrieve_item: Directory {dir_path} does not exist", file=sys.stderr)
                return None
            
            print(f"DEBUG retrieve_item: File found at {file_path}", file=sys.stderr)
            with open(file_path, 'r', encoding='utf-8') as f:
                data = f.read()
                print(f"DEBUG retrieve_item: Raw content: {data[:100]}...", file=sys.stderr)
                # Re-open the file for json.load
                f.seek(0)
                data_dict = json.load(f)
            
            # Pydantic v2 uses model_validate, v1 uses parse_obj
            if hasattr(model_cls, 'model_validate'):
                result = model_cls.model_validate(data_dict) 
            else:
                result = model_cls.parse_obj(data_dict)
                
            print(f"DEBUG retrieve_item: Successfully loaded {model_cls.__name__}: {result}", file=sys.stderr)
            return result
        except Exception as e:
            print(f"DEBUG retrieve_item: Exception: {str(e)}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            
            # Try parsing the JSON string directly
            try:
                print(f"DEBUG retrieve_item: Trying to parse from raw data", file=sys.stderr)
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = f.read()
                    data_dict = json.loads(data)
                    
                # Pydantic v2 uses model_validate, v1 uses parse_obj
                if hasattr(model_cls, 'model_validate'):
                    result = model_cls.model_validate(data_dict) 
                else:
                    result = model_cls.parse_obj(data_dict)
                    
                print(f"DEBUG retrieve_item: Successfully loaded from raw data: {result}", file=sys.stderr)
                return result
            except Exception as e2:
                print(f"DEBUG retrieve_item: Second attempt failed: {str(e2)}", file=sys.stderr)
                return None

    async def delete_item(self, model_cls: Type[M], item_id: str) -> bool:
        """
        Deletes an item of a specific Pydantic model type from long-term memory.

        :param model_cls: The Pydantic model class (e.g., UserProfile).
        :type model_cls: Type[M]
        :param item_id: The ID of the item to delete.
        :type item_id: str
        :return: True if the item was deleted, False if not found.
        :rtype: bool
        """
        file_path = self._get_storage_path(model_cls, item_id)
        if file_path.exists():
            os.remove(file_path)
            return True
        return False

    async def list_item_ids(self, model_cls: Type[M]) -> List[str]:
        """
        Lists all item IDs for a given Pydantic model type in long-term memory.

        :param model_cls: The Pydantic model class (e.g., UserProfile).
        :type model_cls: Type[M]
        :return: A list of item IDs (filenames without .json extension).
        :rtype: List[str]
        """
        model_dir_name = model_cls.__name__
        storage_dir = self.base_path / model_dir_name
        if not storage_dir.exists():
            return []
        return [f.stem for f in storage_dir.glob("*.json")]

    def _extract_id(self, item: M) -> str:
        """Helper to extract a suitable ID from a Pydantic model instance."""
        # Prioritize 'id' over legacy fields
        possible_id_fields = ['id', f'{item.__class__.__name__.lower()}_id', 'item_id']
        for field_name in possible_id_fields:
            if hasattr(item, field_name):
                item_id_val = getattr(item, field_name)
                if isinstance(item_id_val, str):
                    return item_id_val
        
        # Fallback for specific models if needed, or raise error
        if isinstance(item, UserProfile):
            return item.user_id # Already checked by 'userprofile_id' if class name is UserProfile

        raise ValueError(
            f"Item of type {item.__class__.__name__} must have a string ID attribute "
            f"(e.g., 'item_id', '{item.__class__.__name__.lower()}_id', or 'id')."
        )

# Example Usage (Illustrative - typically you'd call this from an agent service)
async def example_ltm_usage():
    ltm_store = LongTermMemory(base_storage_path="./agent_ltm_data")

    # --- UserProfile Example ---
    user_profile_id = "user_123_test"
    user_data = UserProfile(
        user_id=user_profile_id, 
        preferences={"theme": "dark", "notifications": "email"},
        history_summary="Started conversation about AILF development."
    )
    await ltm_store.store_item(user_data)
    print(f"Stored: {user_profile_id}")

    retrieved_user = await ltm_store.retrieve_item(UserProfile, user_profile_id)
    if retrieved_user:
        print(f"Retrieved UserProfile: {retrieved_user.user_id}, Prefs: {retrieved_user.preferences}")
    
    # --- KnowledgeFact Example ---
    fact_id = "ailf_is_cool_fact"
    fact_data = KnowledgeFact(
        id=fact_id,
        content="AILF is a framework for building AI agents.",
        source="Developer Documentation",
        metadata={"tags": ["ailf", "framework", "ai"]}
    )
    await ltm_store.store_item(fact_data)
    print(f"Stored: {fact_id}")

    retrieved_fact = await ltm_store.retrieve_item(KnowledgeFact, fact_id)
    if retrieved_fact:
        print(f"Retrieved KnowledgeFact: {retrieved_fact.id}, Content: {retrieved_fact.content}")

    # List items
    user_profiles = await ltm_store.list_item_ids(UserProfile)
    print(f"All UserProfile IDs: {user_profiles}")

    knowledge_facts = await ltm_store.list_item_ids(KnowledgeFact)
    print(f"All KnowledgeFact IDs: {knowledge_facts}")

    # Delete an item
    # await ltm_store.delete_item(UserProfile, user_profile_id)
    # print(f"Deleted UserProfile: {user_profile_id}")

if __name__ == "__main__":
    import asyncio
    # asyncio.run(example_ltm_usage()) # Commented out to prevent execution during tool use
