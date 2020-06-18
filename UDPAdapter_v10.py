import socket
import select

# PC software port configurarion
# PC(IP:Port)
# CU_Bind
codemap = {0: ("127.0.0.1", 50001),
           1: ("127.0.0.1", 50002),
           2: ("127.0.0.1", 50003),
           3: ("127.0.0.1", 50004),
           4: ("127.0.0.1", 50005),
           5: ("127.0.0.1", 50006),
           6: ("127.0.0.1", 50007),
           7: ("127.0.0.1", 50008),
           8: ("127.0.0.1", 50009),
           9: ("127.0.0.1", 50010),
           10: ("127.0.0.1", 60001),
           11: ("127.0.0.1", 60002),
           12: ("127.0.0.1", 60003),
           13: ("127.0.0.1", 60004),
           14: ("127.0.0.1", 60005),
           15: ("127.0.0.1", 60006),
           16: ("127.0.0.1", 60007),
           17: ("127.0.0.1", 60008),
           18: ("127.0.0.1", 60009),
           19: ("127.0.0.1", 60010)
           }

# Proxy port configuration
# Proxy port CU_Connect 127.0.0.1:<port>
portmap = {20001: 0,
           20002: 1,
           20003: 2,
           20004: 3,
           20005: 4,
           20006: 5,
           20007: 6,
           20008: 7,
           20009: 8,
           20010: 9,
           30001: 10,
           30002: 11,
           30003: 12,
           30004: 13,
           30005: 14,
           30006: 15,
           30007: 16,
           30008: 17,
           30009: 18,
           30010: 19
           }


numTotalPorts = 20
usedMask = numTotalPorts * [0]
swapList = list(range(numTotalPorts))

Flagstart = b'\x7e\x00'
Flagend = b'\x7e'
Flagzero = b'\x0a\x00\x00'
Flage = b'\x8e\x45'

FPGA_IP = "192.168.2.100"
FPGA_PORT = 20482
# Debug print
print_FPGA_packet = 0
print_PC_packet = 0


def swapCodeMap(i, j):
    tmp = codemap[i]
    codemap[i] = codemap[j]
    codemap[j] = tmp

    for k in portmap:
        if portmap[k] == i:
            ii = k
            break
    for k in portmap:
        if portmap[k] == j:
            jj = k
            break
    portmap[ii] = j
    portmap[jj] = i

    swapList[i], swapList[j] = swapList[j], swapList[i]
    print("+++++++ swapList = {0}".format(swapList))


def sendtoPC(data, codesockmap):
    while (len(data) > 0):
        if data[0:2] != Flagstart:
            s = data.find(Flagstart)
            if s == -1:
                return b''
            else:
                data = data[s:]

        end = data.find(Flagend, 2)
        if end != -1:
            pack = data[:end + 1]
            newpack = pack

            for i in range(len(newpack)):
                if newpack[i] == '7d' and newpack[i + 1] == '5e':
                    newpack[i] = b'\x7e'
                    newpack[i + 1] = b''
                if newpack[i] == '7d' and newpack[i + 1] == '5d':
                    newpack[i] = b'\x7d'
                    newpack[i + 1] = b''

            code = pack[2]
            addr = codemap.get(code, None)
            send = codesockmap.get(swapList[code], None)
            if addr != None and send != None:
                send.sendto(Flagstart + pack[3:],  addr)
            if addr != None and send != None and newpack.hex()[6:8] == '8f' and newpack.hex()[38:40] == '49':   
                fra = int(newpack.hex()[14:16],16) + int(newpack.hex()[16:18],16)*256 + int(newpack.hex()[18:20],16)*256*256
                num = fra % 8
                supnum = fra//64
                supnum_h = supnum//256
                supnum_l = supnum % 256
                franum = fra % 64
                if num == 0:
                   send.sendto(Flagstart + Flage + chr(supnum_h).encode() + chr(supnum_l).encode()[len(chr(supnum_l).encode())-1:] + chr(franum).encode() + Flagzero + Flagend,  addr)  
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
        else:
            if data.hex()[4:6] == '02' or data.hex()[4:6] == '12' or data.hex()[4:6] == '0a' or data.hex()[4:6] == '03':
                print("Receive from PC: {0}. Port {1}".format(data.hex(), port))

        # Process 02 packet: 02 should be mapped to code number 4n
        if data.hex()[4:6] == '02' and (data.hex()[6:8] != '00' or data.hex()[8:10] != '00'):
            if code % 4 == 0:
                usedMask[code] = 1
            else:
                for unusedIdx in range(0, numTotalPorts, 4):
                    if usedMask[unusedIdx] == 0:
                        usedMask[unusedIdx] = 1
                        swapCodeMap(code, unusedIdx)
                        print("codemap after 0x02 = {0}".format(codemap))
                        print("portmap after 0x02 = {0}".format(portmap))
                        break
            print("####### usedMask after 0x02 = {0}".format(usedMask))

        # Process 03 packet: 03 is used for UL RACH/TCH allocation
        if data.hex()[4:6] == '03' and (data.hex()[6:8] != '00' or data.hex()[8:10] != '00'):
            LinkType = data.hex()[10:12]

            if LinkType == '00':        # DL TCH mapped to code number 4n+2
                if code % 4 == 1:
                    usedMask[code] = 1
                else:
                    for unusedIdx in range(1, numTotalPorts, 4):
                        if usedMask[unusedIdx] == 0:
                            usedMask[unusedIdx] = 1
                            swapCodeMap(code, unusedIdx)
                            print("codemap after 0x03 (DL) = {0}".format(codemap))
                            print("portmap after 0x03 (DL) = {0}".format(portmap))
                            break
                print("####### usedMask after 0x03 (DL) = {0}".format(usedMask))

            if LinkType == '01':        # RACH mapped to code number 4n+2
                if code % 4 == 2 and code < 4:
                    usedMask[code] = 1
                else:
                    for unusedIdx in range(2, numTotalPorts, 4):
                        if usedMask[unusedIdx] == 0:
                            usedMask[unusedIdx] = 1
                            swapCodeMap(code, unusedIdx)
                            print("codemap after 0x03 (RACH) = {0}".format(codemap))
                            print("portmap after 0x03 (RACH) = {0}".format(portmap))
                            break
                print("####### usedMask after 0x03 (RACH) = {0}".format(usedMask))

            if LinkType == '02':        # UL TCH mapped to code number 4n+3
                if code % 4 == 3:
                    usedMask[code] = 1
                else:
                    for unusedIdx in range(3, numTotalPorts, 4):
                        if usedMask[unusedIdx] == 0:
                            usedMask[unusedIdx] = 1
                            swapCodeMap(code, unusedIdx)
                            print("codemap after 0x03 (UL) = {0}".format(codemap))
                            print("portmap after 0x03 (UL) = {0}".format(portmap))
                            break
                print("####### usedMask after 0x03 (UL) = {0}".format(usedMask))

        # # Process 0A packet: 0A should be mapped to code number 4n+1(DL) or 4n+3(UL)
        # if data.hex()[4:6] == '0a':
        #     if port < 30000:  # DL
        #         if code % 4 == 1:
        #             usedMask[code] = 1
        #         else:
        #             for unusedIdx in range(1, numTotalPorts, 4):
        #                 if usedMask[unusedIdx] == 0:
        #                     usedMask[unusedIdx] = 1
        #                     swapCodeMap(code, unusedIdx)
        #                     print("codemap after DL 0x0A = {0}".format(codemap))
        #                     print("portmap after DL 0x0A = {0}".format(portmap))
        #                     break
        #         print("####### usedMask after DL 0x0A = {0}".format(usedMask))
        #     else:  # UL
        #         if code % 4 == 3:
        #             usedMask[code] = 1
        #         else:
        #             for unusedIdx in range(3, numTotalPorts, 4):
        #                 if usedMask[unusedIdx] == 0:
        #                     usedMask[unusedIdx] = 1
        #                     swapCodeMap(code, unusedIdx)
        #                     print("codemap after UL 0x0A = {0}".format(codemap))
        #                     print("portmap after UL 0x0A = {0}".format(portmap))
        #                     break
        #         print("####### usedMask after UL 0x0A = {0}".format(usedMask))
        #
        # # Process 09 packet: 09 should be mapped to code number 4n+2
        # if data.hex()[4:6] == '09':
        #     if code % 4 == 2 and code < 4:
        #         usedMask[code] = 1
        #     else:
        #         for unusedIdx in range(2, numTotalPorts, 4):
        #             if usedMask[unusedIdx] == 0:
        #                 usedMask[unusedIdx] = 1
        #                 swapCodeMap(code, unusedIdx)
        #                 print("codemap after 0x09 = {0}".format(codemap))
        #                 print("portmap after 0x09 = {0}".format(portmap))
        #                 break
        #     print("####### usedMask after 0x09 = {0}".format(usedMask))

        # Process 12 packet: 12 should reset usedMask
        if data.hex()[4:6] == '12':
            usedMask[code] = 0
            print("####### usedMask after 0x12 = {0}".format(usedMask))

        code = portmap.get(port, -1)
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
    while (1):
        try:
            FPGA_connection.connect((FPGA_IP, FPGA_PORT))
            print("FPGA_connected")
            break
        except:
            continue
    sockets.append(FPGA_connection)

    remaindata = b''
    while (1):
        read = select.select(sockets, [], [])
        for m in read:
            for s in m:
                if s.type == socket.SOCK_STREAM:
                    newdata = FPGA_connection.recv(128)
                    if print_FPGA_packet:
                        if newdata.hex()[6:8] != '8f':  # don't print 0x8F packet
                            print("Receive from FPGA:" + newdata.hex())
                    remaindata = sendtoPC(remaindata + newdata, codesockmap)
                else:
                    newdata = s.recv(32)
                    sendtoFPGA(s.getsockname()[1], newdata, FPGA_connection)


while (1):
    try:
        mainloop()
    except:
        continue
