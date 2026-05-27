import os

# Server-side bind configuration
SERVER_BIND_HOST = os.getenv("SECURECHAT_SERVER_BIND_HOST", "0.0.0.0")
SERVER_BIND_PORT = int(os.getenv("SECURECHAT_SERVER_BIND_PORT", "65432"))

# Client-side remote target configuration
CLIENT_SERVER_HOST = os.getenv("SECURECHAT_SERVER_HOST", "127.0.0.1")
CLIENT_SERVER_PORT = int(os.getenv("SECURECHAT_SERVER_PORT", "65432"))

BUFFER_SIZE = int(os.getenv("SECURECHAT_BUFFER_SIZE", "4096"))