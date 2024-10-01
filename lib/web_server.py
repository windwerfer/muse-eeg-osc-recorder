import http.server
import os
import socketserver
import logging
import signal

def start_web_server(server_folder='.cache', port=9000):
    """
    Starts a simple HTTP server in a separate thread to serve files from the specified folder,
    with server logs redirected to 'server_errors.txt' and other prints to stdout.

    Args:
    server_folder (str): The directory from which to serve files.
    port (int): The port number on which the server will listen.
    """
    # Setup logging to file for server messages only

    print(f"\n  http://localhost:{port}/  ")  # This print will go to stdout

    try:
        kill_server_process(port)
    except Exception as e:
        pass

    logging.basicConfig(filename='server_errors.txt', level=logging.INFO,
                        format='%(asctime)s - %(message)s', datefmt='%d/%b/%Y %H:%M:%S')

    import os
    os.chdir(server_folder)

    class CustomHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            # Log server messages to file
            logging.info("%s - %s" % (self.client_address[0], format % args))

    Handler = CustomHandler

    with socketserver.TCPServer(("", port), Handler) as httpd:

        try:
            httpd.serve_forever()
        except Exception as e:
            httpd.server_close()
            return False


def kill_server_process(port):
    import psutil

    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if 'python' in proc.info['name'] or 'python.exe' in proc.info['name']:
                for conns in proc.connections():
                    if conns.laddr.port == port:
                        print(f"Killing process {proc.info['pid']} serving on port {port}")
                        os.kill(proc.info['pid'],
                                signal.SIGTERM)  # SIGTERM is a polite way to ask the process to terminate
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass