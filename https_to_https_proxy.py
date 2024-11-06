import socket
import ssl
import threading
import argparse
import base64

# Handle client connections and forward to HTTPS target with Basic Authentication
def handle_client(client_socket, target_host, target_port, target_context, username, password):
    try:
        # Connect to the target HTTPS server
        target_socket = socket.create_connection((target_host, target_port))
        
        # Wrap the target connection with SSL to communicate with the target over HTTPS
        secure_target_socket = target_context.wrap_socket(target_socket, server_hostname=target_host)
        
        # Prepare the Basic Authentication header
        credentials = f"{username}:{password}"
        auth_header = f"Authorization: Basic {base64.b64encode(credentials.encode()).decode()}\r\n"
        
        # Relay data between client and target with authentication
        while True:
            # Receive data from the client
            client_data = client_socket.recv(4096)
            if not client_data:
                break

            # Add the Basic Authentication header to client data before forwarding to the target
            client_data_with_auth = client_data + auth_header.encode()
            secure_target_socket.sendall(client_data_with_auth)

            # Receive data from the target server and send it back to the client
            target_data = secure_target_socket.recv(4096)
            if not target_data:
                break
            client_socket.sendall(target_data)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Close connections
        client_socket.close()
        secure_target_socket.close()

# Set up the proxy server
def start_proxy(proxy_host, proxy_port, target_host, target_port, certfile, keyfile, username, password):
    # SSL context for incoming client HTTPS connection
    client_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    client_context.load_cert_chain(certfile=certfile, keyfile=keyfile)
    
    # SSL context for outgoing target HTTPS connection
    target_context = ssl.create_default_context()

    # Create a TCP socket and wrap it with SSL for client-side HTTPS
    proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    proxy_socket.bind((proxy_host, proxy_port))
    proxy_socket.listen(5)
    print(f"HTTPS-to-HTTPS proxy with Basic Auth running on {proxy_host}:{proxy_port}, forwarding to https://{target_host}:{target_port}...")

    # Accept client connections and handle them in separate threads
    while True:
        client_socket, addr = proxy_socket.accept()
        print(f"Connection received from {addr}")
        
        # Wrap the client socket with SSL for HTTPS
        secure_client_socket = client_context.wrap_socket(client_socket, server_side=True)
        
        # Start a new thread to handle each client
        client_thread = threading.Thread(
            target=handle_client,
            args=(secure_client_socket, target_host, target_port, target_context, username, password)
        )
        client_thread.start()

# Main function to parse arguments and start the proxy
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simple HTTPS-to-HTTPS Proxy with Basic Authentication")
    parser.add_argument("--proxy-host", type=str, default="127.0.0.1", help="Proxy server host (default: 127.0.0.1)")
    parser.add_argument("--proxy-port", type=int, default=443, help="Proxy server port (default: 443)")
    parser.add_argument("--target-host", type=str, required=True, help="Target HTTPS server host")
    parser.add_argument("--target-port", type=int, required=True, help="Target HTTPS server port")
    parser.add_argument("--certfile", type=str, required=True, help="Path to SSL certificate file for proxy")
    parser.add_argument("--keyfile", type=str, required=True, help="Path to SSL private key file for proxy")
    parser.add_argument("--username", type=str, required=True, help="Username for Basic Authentication")
    parser.add_argument("--password", type=str, required=True, help="Password for Basic Authentication")

    args = parser.parse_args()
    
    # Start the proxy with specified arguments
    start_proxy(args.proxy_host, args.proxy_port, args.target_host, args.target_port, args.certfile, args.keyfile, args.username, args.password)