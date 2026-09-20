import httpx
from fastmcp import FastMCP
from typing import Any
from classes import RequestAuthenticate, ResponseAuthenticate, ResponseCreateMailbox, RequestCreateMailbox, ResponseReadInbox, RequestReadInbox, RequestSendMail, ResponseSendMail, RequestReadMessage, ResponseReadMessage, ResponseHealth


class ElmA():
    def __init__(self) -> None:
        self.address: str = "agentA"
        self.password: str = "password"
        self.address: str = "http://127.0.0.1:8000"
        self.jwt: str = ""
        self.authenticated: bool = False
        self._app = FastMCP("ElmA")

        self._app.add_tool(self.create_mailbox)
        self._app.add_tool(self.authenticate)
        self._app.add_tool(self.read_inbox)
        self._app.add_tool(self.send_message)
        self._app.add_tool(self.read_message)

    def _post_request(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        response = httpx.post(f"{self.address}{path}", json=payload)

        return response.json()

    def _get_request(self, path: str) -> dict[str, Any]:
        response = httpx.get(f"{self.address}{path}")

        return response.json()

    def get_health(self) -> bool:
        health_response = self._get_request("/health")

        health_response_formatted = ResponseHealth.model_validate(
            health_response)

        if (health_response_formatted.success and health_response_formatted.data):

            return health_response_formatted.data.status == "ok"

        return False

    def run(self):
        self._app.run(transport="stdio")

    def create_mailbox(self):
        response = self._post_request("/create-mailbox", payload=RequestCreateMailbox(
            address=self.address, password=self.password).model_dump())

        response_formatted: ResponseCreateMailbox = ResponseCreateMailbox.model_validate(
            response)

        return response_formatted.model_dump()

    def authenticate(self):

        response = self._post_request("/authenticate", payload=RequestAuthenticate(
            address=self.address, password=self.password).model_dump())

        response_formatted: ResponseAuthenticate = ResponseAuthenticate.model_validate(
            response)

        print(response_formatted)

        if (response_formatted.success and response_formatted.data):
            self.jwt = response_formatted.data.jwt
            self.authenticated = True

        return response_formatted.model_dump()

    def read_inbox(self):

        response = self._post_request("read-inbox",
                                      payload=RequestReadInbox(address=self.address, jwt=self.jwt).model_dump())

        response_formatted = ResponseReadInbox.model_validate(response)

        return response_formatted.model_dump()

    def send_message(self, recipient_address: str, subject: str, message: str):

        response = self._post_request("/send-message", payload=RequestSendMail(
            address=self.address, jwt=self.jwt, subject=subject, recipient=recipient_address, content=message).model_dump())

        response_formatted = ResponseSendMail.model_validate(response)

        return response_formatted.model_dump()

    def read_message(self, message_id: str):

        response = self._post_request("/read-message", payload=RequestReadMessage(
            address=self.address, jwt=self.jwt, message_id=message_id).model_dump())

        response_formatted = ResponseReadMessage.model_validate(
            response)

        return response_formatted.model_dump()


elma = ElmA()

print(elma.get_health())

if __name__ == "__main__":
    elma.run()
    pass
