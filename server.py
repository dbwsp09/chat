#
# Серверное приложение для соединений
#
import asyncio
from asyncio import transports


class ServerProtocol(asyncio.Protocol):
    login: str = None
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server

    def data_received(self, data: bytes):
        print(data)

        decoded = data.decode()

        if self.login is not None:
            self.send_message(decoded)
        else:
            if decoded.startswith("login:"):
                if len(self.server.users) != 0:
                    for user in self.server.users:
                        if user == decoded.replace("login:", "").replace("\r\n", ""):
                            self.transport.write(
                                f"Логин, {user} занят, попробуйте другой.\n".encode()
                            )
                            self.server.clients.remove(self)
                            self.transport.close()
                        else:
                            self.server.users.append(decoded.replace("login:", "").replace("\r\n", ""))
                            self.login = decoded.replace("login:", "").replace("\r\n", "")
                            for msg in self.server.msgs:
                                self.transport.write(msg.encode())
                else:
                    self.server.users.append(decoded.replace("login:", "").replace("\r\n", ""))
                    self.login = decoded.replace("login:", "").replace("\r\n", "")

                self.login = decoded.replace("login:", "").replace("\r\n", "")
                self.transport.write(
                    f"Привет, {self.login}!\n".encode()
                )

            else:
                self.transport.write("Неправильный логин\n".encode())

    def connection_made(self, transport: transports.Transport):
        self.server.clients.append(self)
        self.transport = transport
        print("Пришел новый клиент")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Клиент вышел")

    def send_message(self, content: str):
        message = f"{self.login}: {content}\n"
        self.server.msgs.append(message)

        for user in self.server.clients:
            user.transport.write(message.encode())


class Server:
    clients: list
    users: list
    msgs: list

    def __init__(self):
        self.clients = []
        self.users = []
        self.msgs = []

    def build_protocol(self):
        return ServerProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.build_protocol,
            '127.0.0.1',
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()

try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
