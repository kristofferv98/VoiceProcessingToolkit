import asyncio
import logging
import inspect
import threading
import time
from typing import List, Callable, Any, Coroutine, Union, Optional

from VoiceProcessingToolkit.interfaces import ActionManagerInterface
from VoiceProcessingToolkit.shared_resources import thread_manager

class ActionManager(ActionManagerInterface):
    """
    Manages a list of actions (functions) to be executed when triggered.
    Implements the ActionManagerInterface.
    
    Attributes:
        actions (List[Callable]): List of action functions to be executed.
        logger (logging.Logger): Logger for this class.
    """
    
    def __init__(self):
        """Initialize a new ActionManager instance."""
        self.actions: List[Callable] = []
        self.logger = logging.getLogger(__name__)
    
    def register_action(self, action_function: Callable) -> None:
        """
        Register a new action function to be executed when triggered.
        
        Args:
            action_function: The function to register as an action.
                             Can be a regular function or a coroutine function.
        
        Raises:
            TypeError: If action_function is not callable.
        """
        if not callable(action_function):
            raise TypeError("Action function must be callable")
        
        self.actions.append(action_function)
        self.logger.debug(f"Registered action: {action_function.__name__}")
    
    def register_actions(self, action_functions: List[Callable]) -> None:
        """
        Register multiple action functions at once.
        
        Args:
            action_functions: List of functions to register.
        
        Raises:
            TypeError: If any item in action_functions is not callable.
        """
        for action in action_functions:
            self.register_action(action)
    
    async def execute_actions(self) -> None:
        """
        Execute all registered action functions concurrently.
        
        If an action is a coroutine function, it will be awaited.
        If an action is a regular function, it will be run in a separate thread.
        
        Any exceptions during execution are caught and logged.
        """
        if not self.actions:
            self.logger.info("No actions registered to execute")
            return
        
        self.logger.info(f"Executing {len(self.actions)} registered actions")
        tasks = []
        
        for action in self.actions:
            if asyncio.iscoroutinefunction(action):
                # For coroutine functions, create a task
                tasks.append(self._execute_coroutine(action))
            else:
                # For regular functions, run in a thread
                tasks.append(self._execute_in_thread(action))
        
        # Wait for all tasks to complete
        await asyncio.gather(*tasks, return_exceptions=True)
        self.logger.info("All actions executed")
    
    async def _execute_coroutine(self, coro_func: Callable[[], Coroutine]) -> None:
        """
        Execute a coroutine function and handle exceptions.
        
        Args:
            coro_func: The coroutine function to execute.
        """
        try:
            self.logger.debug(f"Executing coroutine: {coro_func.__name__}")
            await coro_func()
            self.logger.debug(f"Completed coroutine: {coro_func.__name__}")
        except Exception as e:
            self.logger.error(f"Error in coroutine {coro_func.__name__}: {e}")
    
    async def _execute_in_thread(self, func: Callable) -> None:
        """
        Execute a regular function in a separate thread.
        
        Args:
            func: The function to execute.
        """
        loop = asyncio.get_event_loop()
        
        def thread_wrapper():
            try:
                self.logger.debug(f"Executing function in thread: {func.__name__}")
                result = func()
                self.logger.debug(f"Completed function: {func.__name__}")
                return result
            except Exception as e:
                self.logger.error(f"Error in function {func.__name__}: {e}")
                return None
        
        # Run the function in a thread pool
        self.logger.debug(f"Scheduling function: {func.__name__} in thread pool")
        result = await loop.run_in_executor(None, thread_wrapper)
        return result
    
    def clear_actions(self) -> None:
        """Remove all registered actions."""
        self.actions.clear()
        self.logger.debug("All actions cleared")
    
    def get_action_count(self) -> int:
        """
        Get the number of registered actions.
        
        Returns:
            int: Number of registered actions.
        """
        return len(self.actions)
