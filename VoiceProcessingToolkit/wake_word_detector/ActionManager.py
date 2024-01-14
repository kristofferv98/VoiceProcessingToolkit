import asyncio
import logging
from VoiceProcessingToolkit.shared_resources import shutdown_flag


class ActionManager:
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

    def register_action(self, action_function):
        """
        Registers a new action function to the list of actions.

        Args:
            action_function (callable): The function to be added to the actions list.
        """
        self.__actions.append(action_function)

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


def register_action_decorator(action_manager):
    def decorator(action_function):
        action_manager.register_action(action_function)
        return action_function

    return decorator
