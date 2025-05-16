"""State management utilities for AG-UI protocol.

This module provides tools for managing state in AG-UI protocol implementations,
particularly for handling state snapshots and deltas.
"""

import copy
import json
import logging
from typing import Any, Dict, List, Optional, Union

import jsonpatch

from ailf.schemas.ag_ui import (
    EventType,
    StateSnapshotEvent,
    StateDeltaEvent,
)

logger = logging.getLogger(__name__)


class AGUIStateManager:
    """State manager for AG-UI protocol.
    
    Handles state tracking, snapshots, and deltas for AG-UI integration.
    """
    
    def __init__(self, initial_state: Optional[Dict[str, Any]] = None):
        """Initialize the state manager.
        
        Args:
            initial_state: Optional initial state dictionary
        """
        self.state = initial_state or {}
        self.previous_state = copy.deepcopy(self.state)
    
    def get_state(self) -> Dict[str, Any]:
        """Get a copy of the current state.
        
        Returns:
            A copy of the current state dictionary
        """
        return copy.deepcopy(self.state)
    
    def update_state(self, new_state: Dict[str, Any]) -> Dict[str, Any]:
        """Update the state with a new state dictionary.
        
        Args:
            new_state: New state dictionary
            
        Returns:
            The updated state dictionary
        """
        self.previous_state = copy.deepcopy(self.state)
        self.state = new_state
        return self.state
    
    def patch_state(self, patch: Union[List[Dict[str, Any]], jsonpatch.JsonPatch]) -> Dict[str, Any]:
        """Apply a JSON patch to the state.
        
        Args:
            patch: JSON patch to apply, either as a list or JsonPatch object
            
        Returns:
            The updated state dictionary
            
        Raises:
            jsonpatch.JsonPatchException: If the patch cannot be applied
        """
        self.previous_state = copy.deepcopy(self.state)
        
        if isinstance(patch, list):
            patch_obj = jsonpatch.JsonPatch(patch)
        else:
            patch_obj = patch
            
        self.state = patch_obj.apply(self.state)
        return self.state
    
    def get_state_delta(self) -> List[Dict[str, Any]]:
        """Get a JSON patch representing changes since the last update.
        
        Returns:
            JSON patch as a list of operations
        """
        return jsonpatch.make_patch(self.previous_state, self.state).patch
    
    def create_snapshot_event(
        self, 
        timestamp: Optional[int] = None,
        custom_state: Optional[Dict[str, Any]] = None,
    ) -> StateSnapshotEvent:
        """Create a StateSnapshotEvent with the current state.
        
        Args:
            timestamp: Optional timestamp to use
            custom_state: Optional custom state to use instead of the current state
            
        Returns:
            A StateSnapshotEvent
        """
        return StateSnapshotEvent(
            type=EventType.STATE_SNAPSHOT,
            state=custom_state if custom_state is not None else self.get_state(),
            timestamp=timestamp,
        )
    
    def create_delta_event(
        self,
        timestamp: Optional[int] = None,
        custom_delta: Optional[List[Dict[str, Any]]] = None,
    ) -> StateDeltaEvent:
        """Create a StateDeltaEvent with changes since the last update.
        
        Args:
            timestamp: Optional timestamp to use
            custom_delta: Optional custom delta to use instead of calculating one
            
        Returns:
            A StateDeltaEvent
        """
        return StateDeltaEvent(
            type=EventType.STATE_DELTA,
            delta=custom_delta if custom_delta is not None else self.get_state_delta(),
            timestamp=timestamp,
        )
