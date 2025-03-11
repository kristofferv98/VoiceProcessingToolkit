import asyncio
import logging
from typing import Callable, List, Dict, Optional

from VoiceProcessingToolkit.interfaces import ActionManagerInterface

logger = logging.getLogger(__name__)


class ActionManager(ActionManagerInterface):
    """
    Manages a collection of actions (callbacks) to be executed upon wake word detection.
    
    This class implements a simplified approach to action management where actions
    are registered with names and can be retrieved and executed individually or as a group.
    """

    def __init__(self):
        """
        Initializes a new instance of ActionManager with an empty action registry.
        """
        self._actions: Dict[str, Callable] = {}
        self.__logger = logging.getLogger(__name__)

    def register_action(self, action_name: str, action_func: Callable) -> None:
        """
        Registers a new action function with a name.

        Args:
            action_name: Name of the action to register.
            action_func: Function to execute when the action is triggered.
        """
        self.__logger.info(f"Registering action: {action_name}")
        self._actions[action_name] = action_func
        
    def get_action(self, action_name: str) -> Optional[Callable]:
        """
        Retrieves a registered action by name.
        
        Args:
            action_name: Name of the action to retrieve
            
        Returns:
            The action function if found, None otherwise
        """
        return self._actions.get(action_name)
        
    def has_action(self, action_name: str) -> bool:
        """
        Checks if an action with the given name exists.
        
        Args:
            action_name: Name of the action to check
            
        Returns:
            True if the action exists, False otherwise
        """
        return action_name in self._actions

    def on_wake_word_detected(self) -> None:
        """
        Handle the wake word detection event by executing all registered actions.
        
        This method is called when a wake word is detected and runs all
        registered actions asynchronously.
        """
        self.__logger.info("Wake word detected, executing actions")
        asyncio.run(self.execute_actions())

    async def execute_actions(self):
        """
        Executes all registered actions asynchronously.
        
        This method creates tasks for each registered action and runs them
        concurrently using asyncio.
        """
        self.__logger.info(f"Executing {len(self._actions)} registered actions")
        
        if not self._actions:
            self.__logger.warning("No actions registered to execute")
            return
            
        tasks = []
        for name, action in self._actions.items():
            self.__logger.debug(f"Creating task for action: {name}")
            if asyncio.iscoroutinefunction(action):
                # If the action is already a coroutine function, create a task for it
                tasks.append(asyncio.create_task(action()))
            else:
                # If the action is a regular function, wrap it in a coroutine
                async def run_action(func, name):
                    self.__logger.debug(f"Running action: {name}")
                    try:
                        return func()
                    except Exception as e:
                        self.__logger.error(f"Error executing action {name}: {e}")
                        return None
                
                tasks.append(asyncio.create_task(run_action(action, name)))
                
        # Wait for all tasks to complete
        if tasks:
            await asyncio.gather(*tasks)
            self.__logger.info("All actions executed successfully")
        
    def execute_action(self, action_name: str) -> bool:
        """
        Execute a single action by name.
        
        Args:
            action_name: Name of the action to execute
            
        Returns:
            True if the action was found and executed, False otherwise
        """
        action = self.get_action(action_name)
        if not action:
            self.__logger.warning(f"Action not found: {action_name}")
            return False
            
        try:
            if asyncio.iscoroutinefunction(action):
                asyncio.run(action())
            else:
                action()
            self.__logger.debug(f"Action executed: {action_name}")
            return True
        except Exception as e:
            self.__logger.error(f"Error executing action {action_name}: {e}")
            return False
