import httpx
from fastmcp import FastMCP
from fastmcp.server.middleware import Middleware, MiddlewareContext
from fastmcp.tools.base import ToolResult
from pydantic import BaseModel
from database_classes import Mail, Mailbox
from typing import Any
from classes import RequestAuthenticate, RequestCreateMailbox, RequestReadInbox, RequestSendMail, RequestReadMessage, ResponseHealthDataWrapper, ResponseAuthenticateDataWrapper, ResponseBase
import threading
import time


class ElmAStatus(BaseModel):
    online: bool
    authenticated: bool
    address: str

    def is_connected(self) -> bool:
        return (self.online and self.authenticated)


class ElmAMiddleWare(Middleware):

    def __init__(self, elma_status: ElmAStatus):
        super().__init__()
        self.elma_status = elma_status

    async def on_message(self, context: MiddlewareContext, call_next):
        if (not self.elma_status.is_connected()):
            return ToolResult(content="rate limit exceeded", is_error=True)
        result = await call_next(context)
        return result


class ElmA():
    def __init__(self) -> None:
        self.mailbox_address: str = "agentA"
        self.password: str = "password"
        self.address: str = "http://127.0.0.1:8000"
        self.jwt: str = ""
        self.status = ElmAStatus(
            online=False, authenticated=False, address=self.mailbox_address)
        self._app = FastMCP("ElmA")

        self._thread_lock = threading.Lock()

        self._middleware = ElmAMiddleWare(self.status)
        self._status_thread = threading.Thread(target=self._status_loop)

        self._app.add_tool(self.create_mailbox)
        self._app.add_tool(self.read_inbox)
        self._app.add_tool(self.send_message)
        self._app.add_tool(self.authenticate_mailbox)
        self._app.add_tool(self.read_message)
        self._app.add_tool(self.get_status)

    def get_health(self) -> bool:

        health_response = self._get_request("/health")

        health_response_formatted = ResponseBase[ResponseHealthDataWrapper].model_validate(
            health_response)

        if (health_response_formatted.success and health_response_formatted.data):

            return health_response_formatted.data.status == "ok"

        return False

    def _status_loop(self) -> None:
        while True:
            with self._thread_lock:
                self.status.online = self.get_health()
                self.status.authenticated = (len(self.jwt) != 0)
            time.sleep(2)

    def _post_request(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        response = httpx.post(f"{self.address}{path}", json=payload)

        return response.json()

    def _get_request(self, path: str) -> dict[str, Any]:
        response = httpx.get(f"{self.address}{path}")

        return response.json()

    def run(self):

        self._status_thread.start()

        self._app.run(transport="streamable-http",port=8001)

    def get_status(self):
        with self._thread_lock:
            status: ElmAStatus = self.status
        return status.model_dump()

    def create_mailbox(self):

        payload = RequestCreateMailbox(
            address=self.mailbox_address, password=self.password).model_dump()

        print(payload)

        response = self._post_request("/create-mailbox", payload=payload)
        
        print(response)
        
        response_formatted = ResponseBase[Mailbox].model_validate(
            response)
        
        return response_formatted.model_dump()

    def authenticate_mailbox(self):

        response = self._post_request("/authenticate", payload=RequestAuthenticate(
            address=self.mailbox_address, password=self.password).model_dump())

        response_formatted = ResponseBase[ResponseAuthenticateDataWrapper].model_validate(
            response)

        print(response_formatted)

        if (response_formatted.success and response_formatted.data):

            self.jwt = response_formatted.data.jwt

        return response_formatted.model_dump()

    def read_inbox(self):

        response = self._post_request("read-inbox",
                                      payload=RequestReadInbox(address=self.mailbox_address, jwt=self.jwt).model_dump())

        response_formatted = ResponseBase[list[Mail]].model_validate(response)

        return response_formatted.model_dump()

    def send_message(self, recipient_address: str, subject: str, message: str):

        response = self._post_request("/send-message", payload=RequestSendMail(
            address=self.mailbox_address, jwt=self.jwt, subject=subject, recipient=recipient_address, content=message).model_dump())

        response_formatted = ResponseBase[Mail].model_validate(response)

        return response_formatted.model_dump()

    def read_message(self, message_id: str):

        response = self._post_request("/read-message", payload=RequestReadMessage(
            address=self.mailbox_address, jwt=self.jwt, message_id=message_id).model_dump())

        response_formatted = ResponseBase[Mail].model_validate(
            response)

        return response_formatted.model_dump()


elma = ElmA()

if __name__ == "__main__":
    elma.run()
