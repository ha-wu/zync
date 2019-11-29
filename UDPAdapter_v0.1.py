import socket
import select


codemap = {0: ("127.0.0.1", 50002),
           1: ("127.0.0.1", 50003)
           }

portmap = {20002: 0,
           20003: 1
           }

Flagstart = b'\x7e\x00'
Flagend = b'\x7e'

FPGA_IP = "192.168.2.100"
FPGA_PORT = 20482
#Debug print
print_FPGA_packet = 0
print_PC_packet = 1


def sendtoPC(data, codesockmap):

    while (len(data) > 0):
        if data[0:2] != Flagstart:
            s = data.find(Flagstart)
            if s == -1 :
                return b''
            else:
                data = data[s:]
        
        end = data.find(Flagend, 2)
        if end != -1:
            pack = data[:end + 1]  
            addr = codemap.get(pack[2],  None)
            send = codesockmap.get(pack[2],  None)
            if addr != None and send != None:
                send.sendto(Flagstart + pack[3:],  addr)
            if end + 1 != len(data):
                data = data[end:]
            else:
                return b''
            continue
        else:
            return data
   
def sendtoFPGA(port, data, FPGA_connection):
    code = portmap.get(port, -1)
    if code != -1:
        if print_PC_packet:
            if data.hex()[4:6] != '01':  # don't print 0x01 packet
                print("Receive from PC: " + data.hex() + "\n")
        FPGA_connection.send(data[0:2] + bytes([code]) + data[2:])

def mainloop():
    sockets = []
    codesockmap = {}
    for k in portmap:
        s = socket.socket(socket.AF_INET, type=socket.SOCK_DGRAM)
        s.bind(("127.0.0.1", k))
        sockets.append(s)
        codesockmap[portmap[k]] = s

    FPGA_connection = socket.socket()
    while(1):
        try:
            FPGA_connection.connect((FPGA_IP,  FPGA_PORT))
            print("FPGA_connected")
            break
        except:
            continue
    sockets.append(FPGA_connection)

    remaindata = b''
    while(1):
            read = select.select(sockets, [], [])
            for m in read:
                for s in m:
                    if s.type == socket.SOCK_STREAM:
                        newdata = FPGA_connection.recv(128)
                        if print_FPGA_packet:
                            print("Receive from FPGA:" + newdata.hex())
                        remaindata = sendtoPC(remaindata + newdata, codesockmap)
                    else :
                        newdata = s.recv(32)
                        sendtoFPGA(s.getsockname()[1], newdata, FPGA_connection)


while(1):
    try:
        mainloop()
    except:
        continue
