import socket
import time

s = socket.socket(socket.AF_INET, type=socket.SOCK_STREAM)
counter = 0
last_print_MB = 0
try:
    s.connect(("192.168.2.100", 8888))
    log = open(time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime()) + ".dat","wb");
    while(1):
        received = s.recv(1024)
        counter += len(received)
        log.write(received)
        if (counter >> 20) // 100 > last_print_MB:
            last_print_MB = (counter >> 20) // 100
            print("Received %d MB data" % counter)
finally:
    s.close()
