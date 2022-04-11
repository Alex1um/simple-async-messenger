import asyncio

from serverd import *
import socket
from websockets import server as wss
from websockets.server import WebSocketServerProtocol
import websockets


class SockListener(Listener):

    class SockConnection(Connection):

        def __init__(self, sock: socket.socket, max_bytes: int, server: Server):
            Connection.__init__(self, server)
            self.sock = sock
            self.is_serving = True
            self.max_bytes = max_bytes
            print("Raw socket connection created")

        async def serve(self):
            print("Starting raw socket serving...")
            try:
                while self.is_serving:
                    msg = (await self.__recv(self.max_bytes)).decode("utf-8")
                    if not msg:
                        raise ConnectionAbortedError
                    print(f"New raw socket message: <{msg}>")
                    await self._server.on_message(self, msg)
            except Exception as f:
                print(f"Raw Socket connection error: {f}")
            finally:
                print("Raw Socket connection closed")
                await self.close()
#
        async def __recv(self, byte_count: int):
            return await asyncio.get_event_loop().sock_recv(self.sock, self.max_bytes)

        async def write(self, msg: str):
            return await asyncio.get_event_loop().sock_sendall(self.sock, msg.encode("utf-8"))

        async def close(self):
            await Connection.close(self)

    def __init__(self, server: Server, host: str, port: str, max_cons: int,
                 max_bytes: int, *args, **kwargs):
        super().__init__(server, host, port, *args, **kwargs)
        self._connection_set = server.connections
        self.server_sock = socket.create_server((host, int(port)), family=socket.AF_INET)
        self.server_sock.listen(max_cons)
        self.server_sock.setblocking(False)
        self._recv_max_bytes = max_bytes
        self._server = server

    async def listen(self):
        loop = asyncio.get_event_loop()
        while 1:
            new_con, _ = await loop.sock_accept(self.server_sock)
            loop.create_task(self.__handle(new_con))

    async def __handle(self, raw_con: socket.socket):
        # loop = asyncio.get_event_loop()
        # await loop.sock_recv(raw_con, self._recv_max_bytes)
        # await loop.sock_sendall(raw_con, "+".encode("utf-8"))
        con = SockListener.SockConnection(raw_con, self._recv_max_bytes, self._server)
        await self.add_connection(con)
        await con.serve()


class WebSockListener(Listener):

    class WebSockConnection(Connection):

        _wssp: WebSocketServerProtocol

        def __init__(self, wssp: WebSocketServerProtocol, server: Server):
            Connection.__init__(self, server)
            self._wssp: WebSocketServerProtocol = wssp

            self.close = self._wssp.close
            self.__recv = self._wssp.recv
            # self.write = self._wssp.send

        async def write(self, msg: str):
            return await self._wssp.send(msg.encode("utf-8"))

        async def serve(self):
            print("Websocket serving started")
            while 1:
                try:
                    msg = (await self._wssp.recv()).decode("utf-8")
                    print(f"new message from websocket: <{msg}>")
                    await self._server.on_message(self, msg)
                except websockets.ConnectionClosedOK:
                    print("Websocket emit closing")
                    break
                except Exception as e:
                    print(f"Websocket connection Error: {e}")
                    break
            try:
                await self.close()
            except Exception as e:
                print("Websocket closing error:", e)
            print("WebSocket connection closed")

        async def close(self):
            await Connection.close(self)

    def __init__(self, server: Server, host: Ip="localhost", port: Port="48666", *args, **kwargs):
        Listener.__init__(self, server, host, port, *args, **kwargs)
        self._host = host
        self._port = int(port)
        self._server_args = args
        self._server_kwargs = kwargs

    async def __handle(self, con: WebSocketServerProtocol):
        print("New websocket connection")
        connection = WebSockListener.WebSockConnection(con, self._server)
        print("Websocket connection created")
        await self.add_connection(connection)
        await connection.serve()

    async def listen(self):
        async with wss.serve(self.__handle, self._host, self._port, *self._server_args, **self._server_kwargs):
            await asyncio.Future()


class SockWebsockServer(Server):

    def __init__(self, *args, **kwargs):
        Server.__init__(self, *args, **kwargs)
        self.con_id = 1
        self.con_ids = dict()

    async def on_connect(self, con: Connection):
        # self.con_ids[con] = self.con_id
        con.id = self.con_id
        await con.write(f"{con.id}|0-")
        print(f"Id <{con.id}> sent")
        self.con_id += 1

    async def on_message(self, connection: Connection, msg: str):
        con: Connection
        for con in self.connections:
            await con.write(f"{connection.id}|{msg}")


if __name__ == "__main__":
    sv = SockWebsockServer(
        (SockListener, "0.0.0.0", "48666", [16, 1024], {}),
        (WebSockListener, "0.0.0.0", "48667", [], {})
    )
    asyncio.run(sv.start())