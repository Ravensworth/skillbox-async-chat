#
# Серверное приложение для соединений
#
import asyncio
from asyncio import transports
import time

class ServerProtocol(asyncio.Protocol):
    login: str = None
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server


    def data_received(self, data: bytes):
        print(data)

        decoded = data.decode()

        if self.login in self.server.logins:
            self.send_message(decoded.strip("\r\n"))
        else:
            if decoded.startswith("login:"):
                self.login = decoded.replace("login:", "").replace("\r\n", "")

                if self.login not in self.server.logins:
                    self.server.logins.append(self.login)
                    self.transport.write(
                        f"Привет, {self.login}!\n".encode()
                    )
                    if len(self.server.history) > 1:
                        self.transport.write(
                            f"История последних сообщений: {self.server.send_history()}\n".encode()
                        )
                    else:
                        self.transport.write(
                            f"Введите первое сообщение >>>\n".encode()
                        )
                else:
                    self.transport.write(
                        f"Логин {self.login} занят, попробуйте другой\n".encode()
                    )
                    self.countdown(2)
            else:
                self.transport.write("Неправильный логин\n".encode())

    def countdown(self, t):
        while t > 0:
            t -= 1
            time.sleep(1)
        self.transport.close()

    def connection_made(self, transport: transports.Transport):
        self.server.clients.append(self)
        self.transport = transport
        print("Пришел новый клиент")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Клиент вышел")

    def send_message(self, content: str):
        message = f"{self.login}: {content}\r\n"
        self.server.history.append(message)

        for user in self.server.clients:
            user.transport.write(message.encode())


class Server:
    clients: list
    logins: list
    history: list

    def __init__(self):
        self.clients = []
        self.logins = []
        self.history = []

    def build_protocol(self):
        return ServerProtocol(self)

    def send_history(self):
        latest_history = self.history[-10:]
        return ', '.join(latest_history)

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
