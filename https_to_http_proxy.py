import socket
import ssl
import threading
import argparse

# Handle client connections
def handle_client(client_socket, target_host, target_port):
    # Connect to the target HTTP server
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.connect((target_host, target_port))
    
    # Receive data from client and send to the server
    while True:
        try:
            client_data = client_socket.recv(4096)
            if not client_data:
                break
            server_socket.sendall(client_data)

            # Receive data from the server and send it back to the client
            server_data = server_socket.recv(4096)
            if not server_data:
                break
            client_socket.sendall(server_data)
        except Exception as e:
            print(f"Error: {e}")
            break

    # Close sockets
    client_socket.close()
    server_socket.close()

# Set up the proxy server
def start_proxy(proxy_host, proxy_port, target_host, target_port, certfile, keyfile):
    # Create an SSL context for the HTTPS connection
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile=certfile, keyfile=keyfile)

    # Create a TCP socket and wrap it with SSL
    proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy_socket.bind((proxy_host, proxy_port))
    proxy_socket.listen(5)
    print(f"HTTPS proxy running on {proxy_host}:{proxy_port}, forwarding to http://{target_host}:{target_port}...")

    # Accept client connections and handle them in separate threads
    while True:
        client_socket, addr = proxy_socket.accept()
        print(f"Connection received from {addr}")
        
        # Wrap the client socket with SSL for HTTPS
        client_socket = context.wrap_socket(client_socket, server_side=True)
        
        # Start a new thread to handle each client
        client_thread = threading.Thread(target=handle_client, args=(client_socket, target_host, target_port))
        client_thread.start()

# Main function to parse arguments and start the proxy
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simple HTTPS-to-HTTP Proxy")
    parser.add_argument("--proxy-host", type=str, default="127.0.0.1", help="Proxy server host (default: 127.0.0.1)")
    parser.add_argument("--proxy-port", type=int, default=443, help="Proxy server port (default: 443)")
    parser.add_argument("--target-host", type=str, required=True, help="Target HTTP server host")
    parser.add_argument("--target-port", type=int, required=True, help="Target HTTP server port")
    parser.add_argument("--certfile", type=str, required=True, help="Path to SSL certificate file")
    parser.add_argument("--keyfile", type=str, required=True, help="Path to SSL private key file")

    args = parser.parse_args()
    
    # Start the proxy with specified arguments
    start_proxy(args.proxy_host, args.proxy_port, args.target_host, args.target_port, args.certfile, args.keyfile)