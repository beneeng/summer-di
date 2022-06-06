class ValidationError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class AmbiguousBeanReference(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class CircularDependencyException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)