import socket
import threading
import argparse
import base64

# Handle client connections and forward to HTTP target with Basic Authentication
def handle_client(client_socket, target_host, target_port, username, password):
    try:
        # Connect to the target HTTP server
        target_socket = socket.create_connection((target_host, target_port))
        
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
            target_socket.sendall(client_data_with_auth)

            # Receive data from the target server and send it back to the client
            target_data = target_socket.recv(4096)
            if not target_data:
                break
            client_socket.sendall(target_data)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Close connections
        client_socket.close()
        target_socket.close()

# Set up the proxy server
def start_proxy(proxy_host, proxy_port, target_host, target_port, username, password):
    # Create a TCP socket for the proxy
    proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    proxy_socket.bind((proxy_host, proxy_port))
    proxy_socket.listen(5)
    print(f"HTTP-to-HTTP proxy with Basic Auth running on {proxy_host}:{proxy_port}, forwarding to http://{target_host}:{target_port}...")

    # Accept client connections and handle them in separate threads
    while True:
        client_socket, addr = proxy_socket.accept()
        print(f"Connection received from {addr}")
        
        # Start a new thread to handle each client
        client_thread = threading.Thread(
            target=handle_client,
            args=(client_socket, target_host, target_port, username, password)
        )
        client_thread.start()

# Main function to parse arguments and start the proxy
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simple HTTP-to-HTTP Proxy with Basic Authentication")
    parser.add_argument("--proxy-host", type=str, default="127.0.0.1", help="Proxy server host (default: 127.0.0.1)")
    parser.add_argument("--proxy-port", type=int, default=8080, help="Proxy server port (default: 8080)")
    parser.add_argument("--target-host", type=str, required=True, help="Target HTTP server host")
    parser.add_argument("--target-port", type=int, required=True, help="Target HTTP server port")
    parser.add_argument("--username", type=str, required=True, help="Username for Basic Authentication")
    parser.add_argument("--password", type=str, required=True, help="Password for Basic Authentication")

    args = parser.parse_args()
    
    # Start the proxy with specified arguments
    start_proxy(args.proxy_host, args.proxy_port, args.target_host, args.target_port, args.username, args.password)