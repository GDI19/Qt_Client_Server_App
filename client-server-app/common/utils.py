import json
from logs.server_log_config import log


@log
def get_message(client):
    """
    Receive bytes and decode message.
    :param client: client
    :return: dict or ValueError
    """
    encoded_response = client.recv(1024)
    if isinstance(encoded_response, bytes):
        json_response = encoded_response.decode('utf-8')
        if isinstance(json_response, str):
            response = json.loads(json_response)
            if isinstance(response, dict):
                return response
            raise ValueError
        raise ValueError
    raise ValueError

@log
def send_message(sock, message):
    """
    Encode and send message.
    Receive dict convert it to str then to bytes.
    :param sock: socket
    :param message: dict
    :return: None
    """
    if not isinstance(message, dict):
        raise TypeError
    js_message = json.dumps(message)
    encoded_msg = js_message.encode('utf-8')
    sock.send(encoded_msg)
