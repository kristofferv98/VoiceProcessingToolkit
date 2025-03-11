import logging
from typing import Callable, Dict, Optional, List

from VoiceProcessingToolkit.interfaces import ActionManagerInterface

logger = logging.getLogger(__name__)

class ActionManager(ActionManagerInterface):
    """
    Simplified action manager that manages callbacks to be executed on wake word detection.
    """
    
    def __init__(self):
        """
        Initialize with empty callback dictionary.
        """
        self._callbacks: Dict[str, Callable] = {}
        self._logger = logging.getLogger(__name__)
    
    def register_action(self, action_name: str, action_func: Callable) -> None:
        """
        Register a callback function to execute on wake word detection.
        
        Args:
            action_name: Name to identify the action
            action_func: Function to execute when triggered
        """
        self._logger.debug(f"Registering action: {action_name}")
        self._callbacks[action_name] = action_func
    
    def get_action(self, action_name: str) -> Optional[Callable]:
        """
        Get a registered action by name.
        
        Args:
            action_name: Name of the action to retrieve
        
        Returns:
            The action function if found, None otherwise
        """
        return self._callbacks.get(action_name)
    
    def has_action(self, action_name: str) -> bool:
        """
        Check if an action is registered.
        
        Args:
            action_name: Name of the action to check
        
        Returns:
            True if the action exists, False otherwise
        """
        return action_name in self._callbacks
    
    def on_wake_word_detected(self) -> None:
        """
        Handle wake word detection by executing all registered callbacks.
        """
        self._logger.info("Wake word detected, executing actions")
        self.execute_actions()
    
    def execute_actions(self) -> None:
        """
        Execute all registered callbacks sequentially.
        """
        self._logger.debug(f"Executing {len(self._callbacks)} registered actions")
        
        if not self._callbacks:
            self._logger.warning("No actions registered to execute")
            return
        
        for name, callback in self._callbacks.items():
            try:
                self._logger.debug(f"Executing action: {name}")
                callback()
                self._logger.debug(f"Action executed: {name}")
            except Exception as e:
                self._logger.error(f"Error executing action {name}: {e}")
    
    def execute_action(self, action_name: str) -> bool:
        """
        Execute a single action by name.
        
        Args:
            action_name: Name of the action to execute
            
        Returns:
            True if the action was executed successfully, False otherwise
        """
        action = self.get_action(action_name)
        if not action:
            self._logger.warning(f"Action not found: {action_name}")
            return False
        
        try:
            action()
            self._logger.debug(f"Action executed: {action_name}")
            return True
        except Exception as e:
            self._logger.error(f"Error executing action {action_name}: {e}")
            return False
