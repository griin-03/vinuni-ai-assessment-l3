class APIError(Exception):
    def __init__(self, status, message, details=None):
        self.status, self.message, self.details = status, message, details


def require(condition, message, status=400):
    if not condition:
        raise APIError(status, message)
