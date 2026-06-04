class BaseAppError(Exception):
    """Базовый класс для всех кастомных ошибок приложения."""

    pass


class NotFoundError(BaseAppError):
    """Базовый класс для ошибок 404."""

    pass


class BusinessLogicError(BaseAppError):
    """Базовый класс для ошибок бизнес-логики (400, 409)."""

    pass


class EventNotFound(NotFoundError):
    def __init__(self) -> None:
        super().__init__("Event not found in Catalog")


class SeatNotFound(NotFoundError):
    def __init__(self) -> None:
        super().__init__("Seat not found")


class OrderNotFound(NotFoundError):
    def __init__(self) -> None:
        super().__init__("Order not found")


class SeatAlreadyReserved(BusinessLogicError):
    def __init__(self) -> None:
        super().__init__("This seat is already reserved or sold")


class InvalidRoleError(BusinessLogicError):
    def __init__(self) -> None:
        super().__init__("You do not have permission to perform this action")


class CommunicationError(BusinessLogicError):
    def __init__(self) -> None:
        super().__init__("Failed to communicate with internal service")
