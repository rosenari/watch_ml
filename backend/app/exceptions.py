class NotFoundException(Exception):
    def __init__(self, message="요청한 리소스를 찾을 수 없습니다."):
        self.message = message

class ForbiddenException(Exception):
    def __init__(self, message="접근이 금지되었습니다."):
        self.message = message