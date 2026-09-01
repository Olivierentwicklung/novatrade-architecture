class CannotPlaceEmptyOrder(Exception):
    pass


class Order:
    def place(self):
        raise CannotPlaceEmptyOrder
