import threading
import hashlib
import time
from typing import List, Tuple
from Proxy import Proxy
import concurrent.futures

def debug(data):
    for i in range(len(data)):
        if data[i] is None:
            print(i)

class PClient:
    count  = 1
    def __init__(self, tracker_addr: Tuple[str, int], proxy=None, port=None, upload_rate=0, download_rate=0):
        if proxy:
            self.proxy = proxy
        else:
            self.proxy = Proxy(upload_rate, download_rate, port)  # Do not modify this line!
        self.tracker = tracker_addr
        """
        Start your additional code below!
        """
        self.num = PClient.count
        PClient.count += 1

        self.file = {}
        self.receive = {}
        self.datapool = {}
        self.avalible = {}
        self.state = {}
        self.packet_size = 1024
        threading.Thread(target=self.start_catch, daemon=True).start()
        threading.Thread(target=self.start_catch, daemon=True).start()
        # threading.Thread(target=self.start_catch, daemon=True).start()
        # threading.Thread(target=self.start_catch, daemon=True).start()
        


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

    def response(self, data: bytes, address: Tuple[str, int], need_re = True) -> bytes:
        
        self.__send__(data, address)

        msg = None
        while need_re:
            if address in self.receive.keys():
                msg = self.receive[address]
                del self.receive[address]
                break
        return msg

    def register(self, file_path: str):

        with open(file_path, mode="rb") as file_object:
            file_data = file_object.read()
            fid = hashlib.sha256(file_data).hexdigest()
            file_length = len(file_data)
            self.file[fid] = file_data
            print(f'{self.num} register {file_path} with fid: {fid}')
            send_msg = b"REGISTER\r\n" + fid.encode('utf-8') + b'\r\n' + str(file_length).encode('utf-8')

        get_msg = self.response(send_msg, self.tracker)

        if get_msg == b"REGISTER SUCCESS":
            print(f'{self.num} register {file_path} success')
        else:
            print("no tracker")

        self.avalible[fid] = True
        return fid

    def __register(self, fid: str, file_length: int):
        send_msg = b"REGISTER\r\n" + fid.encode('utf-8') + b'\r\n' + str(file_length).encode('utf-8')
        get_msg = self.response(send_msg, self.tracker)

        if get_msg == b"REGISTER SUCCESS":
            print(f'{self.num} register {fid} success')
        else:
            print("no tracker")

        self.avalible[fid] = True
        return fid

    def __download(self, fid: str, peer: Tuple[str, int], start: int, end: int):
        msg = b'QUERY\r\n' + fid.encode('utf-8') + b'\r\n'
        msg += str(start).encode('utf-8') + b'\r\n'
        msg += str(end).encode('utf-8')
        self.__send__(msg, peer)
        print(f'{self.num} download {fid} from {start} to {end} from {peer}')

    def download(self, fid: str) -> bytes:
        """
        Download a file from P2P network using its unique identification
        :param fid: the unique identification of the expected file, should be the same type of the return value of share()
        :return: the whole received file in bytes
        """
        data = b''
        seg_size = 1024
        """
        Start your code below!
        """
        self.state[fid] = ['downloading'] * 11
        send_msg = b"QUERY\r\n" + fid.encode('utf-8')
        print(f'{self.num} wants to download {fid} from to')
        get_msg = self.response(send_msg, self.tracker)
        length = int(eval(get_msg)[0])
        peer_list = eval(get_msg)[1:]
        first_peer = peer_list[0]
        seg_count = length // seg_size
        if length % seg_size != 0:
            seg_count += 1
        self.datapool[fid] = [None] * seg_count
        start, end = 0, seg_count//10
        for i in range(11):
            self.__download(fid, first_peer, start, end)

            while self.state[fid][i] != 'done':
                time.sleep(0.5)
                if self.state[fid][i] == 'cancel':
                    self.state[fid][i] = 'downloading'
                    for d in self.datapool[fid]:
                        if d is not None:
                            start += 1
                    get_msg = self.response(send_msg, self.tracker)
                    peer_list = eval(get_msg)[1:]
                    first_peer = peer_list[0]
                    self.__download(fid, first_peer, start, end)
            
            start = end
            end += seg_count//10


        # while self.state:
        #     start, end = 0, seg_count
        #     for d in self.datapool[fid]:
        #         if d is not None:
        #             start += 1
        #     time.sleep(1)
        
        for d in self.datapool[fid]:
            data += d
        
        self.file[fid] = data

        self.__register(fid, length)
    
        return data


    def cancel(self, fid: str):
        send_msg = b"CANCEL\r\n" + fid.encode('utf-8')
        get_msg = self.response(send_msg, self.tracker)

        if get_msg == b"CANCEL SUCCESS":
            print(f"{self.num} cancel {fid} success")
        else:
            print("no tracker")

        self.avalible[fid] = False

    def close(self):
        send_msg = b"CLOSE"
        get_msg = self.response(send_msg, self.tracker)
        print(f'{self.num} wants to close')

        if get_msg == b"CLOSE SUCCESS":
            print(f"{self.num} close success")
            self.proxy.close()
        else:
            print("no tracker")


    def start_catch(self):
        while True:

            msg, frm = self.__recv__()
            msg_list = msg.split(b'\r\n')

            if msg_list[0] == b'QUERY':
                fid = msg_list[1].decode('utf-8')
                start = int(msg_list[2].decode('utf-8'))
                end = int(msg_list[3].decode('utf-8'))
                flag = True
                for i in range(start, end):
                    if not self.avalible[fid]:
                        print(f'{self.num} canceled {fid}')
                        cancel_msg = b'CANCELED\r\n' + msg_list[1]
                        self.__send__(cancel_msg, frm)
                        flag = False
                        break

                    head = b'RETURN\r\n' + msg_list[1] + b'\r\n' + str(i).encode('utf-8') + b'\r\n'
                    self.__send__(head + self.file[fid][i*self.packet_size:(i+1)*self.packet_size], frm)
                    # print(f'{self.num} sends {i}')
                if flag:
                    print(f'{self.num} sends {frm} done')
                    done_msg = b'DONE\r\n' + msg_list[1]
                    self.__send__(done_msg, frm)
                    
            elif msg_list[0] == b'RETURN':
                fid = msg_list[1].decode('utf-8')
                index = int(msg_list[2].decode('utf-8'))
                data = msg.split(b'\r\n', 3)[3]
                self.datapool[fid][index] = data
                if index % 100 == 0:
                    print(f'{self.num} reveives {index} from {frm}')
            
            elif msg_list[0] == b'CANCELED':
                fid = msg_list[1].decode('utf-8')
                self.state[fid] = 'cancel'
            
            elif msg_list[0] == b'DONE':
                fid = msg_list[1].decode('utf-8')
                self.state[fid] = 'done'

            elif msg == b'CLOSE SUCCESS':
                self.receive[frm] = msg
                return
            else:
                self.receive[frm] = msg


if __name__ == '__main__':
    pass
    # tracker_address = ("127.0.0.1", 10086)
    # A = PClient(tracker_address)