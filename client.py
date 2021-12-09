import socket
import asyncio

NICK_MAX_LEN: int = 25


async def new_server(ip: str, port: int) -> None:
    clients: dict[socket.socket, str] = {}

    async def share_msg(encoded_msg: bytes, sender: bytes):
        for client, _ in clients.items():
            loop.create_task(
                loop.sock_sendall(client, sender + b': ' + encoded_msg))

    async def handle_client(client: socket.socket):

        def check_nickname(nick: str) -> str:
            if not nick:
                return "Nick is empty"
            if nick in clients.values():
                return 'Nickname already used'
            l = len(nick)
            if l > NICK_MAX_LEN:
                return "Nickname is too long"
            return "+"

        print(f"New connection: {client}")
        while True:
            nick = (await loop.sock_recv(client, 1024)).strip()
            nick_str = nick.decode("utf-8")
            checked_nick_message = check_nickname(nick_str)
            if checked_nick_message == "+":
                await loop.sock_sendall(client,
                                        f'+{" ".join(clients.values()) or "None"}'.encode(
                                            "utf-8"))
                clients[client] = nick_str
                break
            else:
                await loop.sock_sendall(client,
                                        checked_nick_message.encode("utf-8"))

        await share_msg(f"{nick_str} Connected".encode("utf-8"),
                        "system".encode("utf-8"))

        while True:
            try:
                msg = (await loop.sock_recv(client, 1024))
                if not msg:
                    client.close()
                    del clients[client]
                    print(f"connection with {client} closed")
                    await share_msg(f"{nick_str} Disconnected".encode("utf-8"),
                                    "system".encode("utf-8"))
                    break
                decoded = msg.decode("utf-8")
                print(
                    f"new message from {client}:\nmsg: <{decoded}>\nraw: <{msg}>\n--------------------------------------------\n")
                loop.create_task(share_msg(msg, nick))
            except Exception as e:
                print("Error with reciving message:", e)
                client.close()
                if client in clients.keys():
                    del clients[client]
                break

    async def connection_handler():
        while True:
            client, _ = await loop.sock_accept(server)
            loop.create_task(handle_client(client))

    server = socket.create_server((ip, port), family=socket.AF_INET)
    server.listen(16)
    loop = asyncio.get_event_loop()
    server.setblocking(False)
    loop.create_task(connection_handler())
    print("server is running...")
    while True:
        cmd = await loop.run_in_executor(None, input)
        if cmd == "exit":
            break


def new_client(addr, port):
    loop = asyncio.get_event_loop()

    async def input_msg(connection: socket.socket):
        while True:
            try:
                msg = await loop.run_in_executor(None, input)
                connection.sendall(msg.encode("utf-8"))
            except asyncio.CancelledError:
                print("input canceled")
                break
            except Exception as e:
                print("Error on input: ", e)
                connection.close()
                break

    async def print_msg(connection: socket.socket, self_nick: str):
        while True:
            recv = await loop.sock_recv(connection, 1024)
            if recv:
                decoded = recv.decode("utf-8")
                if decoded[:decoded.find(':')] != self_nick:
                    await loop.run_in_executor(None, print, decoded)
            else:
                print("Server connection closed")
                connection.close()
                break

    def upload_nickname(server_sock: socket.socket):
        try:
            while True:
                nick = input("Choose nickname: ")
                server_sock.sendall(nick.encode("utf-8"))
                recv = server_sock.recv(1024).decode("utf-8")
                if recv:
                    if recv[0] == '+':
                        print("Nickname submitted")
                        print("Users on server:", recv[1:])
                        break
                    else:
                        print("server: ", recv)
                else:
                    raise "Connection closed"
            return nick
        except Exception as e:
            print("Error occupied: ", e)
            server_sock.close()
            return 1

    try:
        client = socket.create_connection((addr, port))
        print("connected")
        nick = upload_nickname(client)
        client.setblocking(False)
        for pending in asyncio.get_event_loop().run_until_complete(
                asyncio.wait((input_msg(client), print_msg(client, nick)),
                             return_when=asyncio.FIRST_COMPLETED))[1]:
            pending.cancel()
    except Exception as e:
        print("Error occupied: ", e)


def main():
    mode = None
    while mode != '3':
        mode = input("Type? 1 - server; 2 - client; 3 - cancel\n")
        if mode == '1':
            asyncio.run(new_server(input("ip: ") or "localhost",
                                   int(input("port: ") or 48666)))
        if mode == '2':
            new_client(input("ip: ") or "localhost",
                       int(input("port: ") or 48666))


if __name__ == "__main__":
    main()
