from typing import Tuple
from Proxy import Proxy
import hashlib
import math

seg_size = 1024 * 4
win_size = 8

def get_count(count: int, size: int) -> int:
    a = count // size
    if count % size != 0:
        a += 1
    return a

class Tracker:
    def __init__(self, upload_rate=10000, download_rate=10000, port=None):
        self.proxy = Proxy(upload_rate, download_rate, port)
        self.file_window = {}  # file -> list of peer_list
        self.file_length = {}  # fid -> int
        self.peer_speed = {}

    def __send__(self, data: bytes, dst: Tuple[str, int]):
        """
        Do not modify this function!!!
        You must send all your packet by this function!!!
        :param data: The data to be send
        :param dst: The address of the destination
        """
        self.proxy.sendto(data, dst)

    def __recv__(self, timeout=None) -> Tuple[bytes, Tuple[str, int]]:
        """
        Do not modify this function!!!
        You must receive all data from this function!!!
        :param timeout: if its value has been set, it can raise a TimeoutError;
                        else it will keep waiting until receive a packet from others
        :return: a tuple x with packet data in x[0] and the source address(ip, port) in x[1]
        """
        return self.proxy.recvfrom(timeout)

    def start(self):
        """
        Start the Tracker and it will work forever
        :return: None
        """
        while True:
            msg, frm = self.__recv__()
            msg_list = msg.split(b'\r\n')
            
            if msg_list[0] == b'REGISTER':
                # Client can use this to REGISTER a file and record it on the tracker
                fid = msg_list[1]
                flength = int(msg_list[2].decode('utf-8'))
                rate = int(msg_list[3].decode('utf-8'))
                self.peer_speed[frm] = rate

                seg_count = get_count(flength, seg_size)
                win_count = get_count(seg_count, win_size)

                if fid not in self.file_length.keys():
                    self.file_length[fid] = flength
                    self.file_window[fid] = [None] * win_count
                    for i in range(win_count):
                        self.file_window[fid][i] = [frm]
                else:
                    for w in self.file_window[fid]:
                        w.append(frm)

                self.__send__(b'REGISTER SUCCESS', frm)

            elif msg_list[0] == b'REGISTER WIN':
                # pclient register a window
                fid = msg_list[1]
                win = int(msg_list[2].decode('utf-8'))
                rate = int(msg_list[3].decode('utf-8'))
                self.peer_speed[frm] = rate
                self.file_window[fid][win].append(frm)

                self.__send__(b'REGISTER SUCCESS', frm)

            elif msg_list[0] == b'QUERY':
                # pclient query a window
                # reply a list of peers of the window
                fid = msg_list[1]
                win = int(msg_list[2].decode('utf-8'))
                rate_list = [[self.peer_speed[i], i] for i in self.file_window[fid][win]]
                rate_list = sorted(rate_list, key=lambda i: -i[0])
                send_list = []
                mmax = rate_list[0][0]
                ssum = 0
                for i in range(min(4, len(rate_list))):
                    if rate_list[i][0] >= mmax/4:
                        ssum += rate_list[i][0]
                        send_list.append(rate_list[i])
                for i in send_list:
                    i[0] = math.ceil(i[0]/ssum*8)
                response_msg = f'{send_list}'
                self.__send__(response_msg.encode('utf-8'), frm)

            elif msg_list[0] == b'QUERYLENGTH':
                fid = msg_list[1]
                response_msg = f'{self.file_length[fid]}'
                self.__send__(response_msg.encode('utf-8'), frm)

            elif msg_list[0] == b'CANCEL':
                # Client can use this file to cancel the share of a file
                fid = msg_list[1]
                for w in self.file_window[fid]:
                    if frm in w:
                        w.remove(frm)

                self.__send__(b"CANCEL SUCCESS", frm)

            elif msg_list[0] == b'CLOSE':
                for f in self.file_window.keys():
                    for w in self.file_window[f]:
                        if frm in w:
                            w.remove(frm)

                self.__send__(b"CLOSE SUCCESS", frm)




if __name__ == '__main__':
    tracker = Tracker(port=10086)
    tracker.start()
