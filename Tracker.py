from typing import Tuple
from Proxy import Proxy
import hashlib

class Tracker:
    def __init__(self, upload_rate=10000, download_rate=10000, port=None):
        self.proxy = Proxy(upload_rate, download_rate, port)
        self.files = {}

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
                if fid not in self.files:
                    self.files[fid] = [flength]
                self.files[fid].append(frm)
                print(f'after register: {self.files}')
                # print(self.files)
                self.__send__(b'REGISTER SUCCESS', frm)
                # self.response("REGISTER Success", frm)

            elif msg_list[0] == b'QUERY':
                fid = msg_list[1]
                response_msg = f'{self.files[fid]}'
                # print(response_msg)
                self.__send__(response_msg.encode('utf-8'), frm)

            elif msg_list[0] == b'CANCEL':
                # Client can use this file to cancel the share of a file
                fid = msg_list[1]
                if frm in self.files[fid]:
                    self.files[fid].remove(frm)
                    print(f'after cancel: {self.files}')
                    # print(self.files)
                self.__send__(b"CANCEL SUCCESS", frm)

            elif msg_list[0] == b'CLOSE':
                for i in self.files.keys():
                    if frm in self.files[i]:
                        self.files[i].remove(frm)
                print(f'after close: {self.files}')
                self.__send__(b"CLOSE SUCCESS", frm)




if __name__ == '__main__':
    tracker = Tracker(port=10086)
    tracker.start()
