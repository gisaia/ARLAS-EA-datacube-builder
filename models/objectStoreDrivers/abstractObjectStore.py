import abc


class AbstractObjectStore(abc.ABC):
    client: any

    def __init__(self):
        pass
