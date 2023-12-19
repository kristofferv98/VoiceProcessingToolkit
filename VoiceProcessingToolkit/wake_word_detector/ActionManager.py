class ActionManager:
    def __init__(self):
        self._actions = []

    def register_action(self, action_function):
        self._actions.append(action_function)

    def execute_actions(self):
        for action in self._actions:
            action()
