import asyncio
from typing import Type

Ip = str
Port = str
Args = list
Kwargs = dict


class Connection:
    address: str
    port: str
    ...

    def __init__(self, server):
        self._server = server
        self._server.connections.add(self)

    async def close(self):
        self._server.connections.remove(self)

    async def write(self, msg: str):
        ...

    async def __recv(self, byte_count: int):
        ...

    async def serve(self):
        ...


class ConnectionSet(set):

    def __init__(self, iterable=()):
        set.__init__(self, iterable)

    def add(self, element: Connection) -> None:
        set.add(self, element)


class ListenerList(list):

    _listeners_fut: asyncio.Future

    def __init__(self):
        list.__init__(self)
        self._is_started = None

    async def gather(self):
        self._listeners_fut = asyncio.gather(*(listener.listen() for listener in self))
        await self._listeners_fut


class Listener:
    ...


class Server:
    connections: ConnectionSet
    listeners: ListenerList
    is_working: bool = False

    def __init__(self,
                 *listeners: tuple[Type[Listener], Ip, Port, Args, Kwargs]):
        self.listeners = ListenerList()
        self.connections = ConnectionSet()

        for listener, ip, port, args, kwargs in listeners:
            self.listeners.append(listener(self, ip, port, *args, **kwargs))

    def add_connection(self, con: Connection):
        self.connections.add(con)

    async def start(self):
        #  add cli
        await self.listeners.gather()

    async def on_message(self, con: Connection, msg: str):
        pass

    async def on_connect(self, con: Connection):
        pass


class Listener:

    _connection_set: ConnectionSet
    _connection_t: type(Connection)

    def __init__(self, server: Server, host: Ip="localhost", port: Port="48666", *args, **kwargs):
        self._connection_set = server.connections
        self._server = server
        ...

    async def listen(self):
        ...

    async def add_connection(self, con: Connection):
        await self._server.on_connect(con)
        self._server.add_connection(con)

    async def stop(self):
        ...
