class ActionManager:
    """
    Manages a list of actions (functions) to be executed.

    Attributes:
        _actions (list): A list of action functions to be executed.
    """

    def __init__(self):
        """
        Initializes a new instance of ActionManager with an empty list of actions.
        """
        self._actions = []

    def register_action(self, action_function):
        """
        Registers a new action function to the list of actions.

        Args:
            action_function (callable): The function to be added to the actions list.
        """
        self._actions.append(action_function)

    async def execute_actions(self):
        """
        Executes all registered action functions concurrently.
        """
        await asyncio.gather(*(action() for action in self._actions))

def register_action_decorator(action_manager):
    def decorator(action_function):
        action_manager.register_action(action_function)
        return action_function
    return decorator
