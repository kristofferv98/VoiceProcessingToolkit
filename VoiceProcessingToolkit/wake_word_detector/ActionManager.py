class ActionManager:
    def __init__(self):
        self._actions = []

    def register_action(self, action_function):
        self._actions.append(action_function)

    def execute_actions(self):
        for action in self._actions:
            action()

def register_action_decorator(action_manager):
    def decorator(action_function):
        action_manager.register_action(action_function)
        return action_function
    return decorator
