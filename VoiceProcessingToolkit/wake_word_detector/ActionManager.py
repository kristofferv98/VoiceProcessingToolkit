import asyncio
import logging
from typing import Callable, List

from VoiceProcessingToolkit.interfaces import ActionManagerInterface
from VoiceProcessingToolkit.shared_resources import shutdown_flag


class ActionManager(ActionManagerInterface):
    """
    Manages a list of actions (functions) to be executed.

    Attributes:
        __actions (list): A list of action functions to be executed.
        __logger (logging.Logger): Logger for the ActionManager class.
    """

    def __init__(self):
        """
        Initializes a new instance of ActionManager with an empty list of actions.
        """
        self.__actions = []
        self.__logger = logging.getLogger(__name__)

    def register_action(self, action_name: str, action_func: Callable) -> None:
        """
        Registers a new action function to the list of actions.

        Args:
            action_name: Name of the action to register.
            action_func: Function to execute when the action is triggered.
        """
        self.__logger.info(f"Registering action: {action_name}")
        self.__actions.append(action_func)

    def on_wake_word_detected(self) -> None:
        """
        Handle the wake word detection event.
        This method is called when a wake word is detected.
        
        Implements the ActionManagerInterface.on_wake_word_detected method.
        """
        self.__logger.info("Wake word detected, executing actions")
        asyncio.run(self.execute_actions())

    async def execute_actions(self):
        """
        Executes all registered action functions concurrently.
        """
        if not shutdown_flag.is_set():
            # Ensure that each action is a coroutine before gathering
            coroutines = [action() if asyncio.iscoroutinefunction(action) else asyncio.to_thread(action) for action in
                          self.__actions]
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    self.__logger.exception("An exception occurred while executing an action: %s", result, exc_info=result)
