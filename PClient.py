from os import sendfile
import threading
import hashlib
from time import time
from typing import List, Tuple
from Proxy import Proxy
import concurrent.futures

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
        t = threading.Thread(target=self.start_catch, daemon=True)
        t.start()


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
            send_msg = b"REGISTER\r\n" + fid.encode('utf-8') + b'\r\n' + file_length.to_bytes((file_length.bit_length() + 7) // 8, 'big')

        get_msg = self.response(send_msg, self.tracker)

        if get_msg == b"REGISTER SUCCESS":
            print(f'{self.num} register {file_path} success')
        else:
            print("no tracker")

        return fid

    def __download_seg(self, fid: str, peer: Tuple[str, int], i: int, seg_count: int, seg_size: int, last_seg: int ,data_segs: List[bytes]) -> bytes:
        print(f'{self.num} download {i} from {peer}')

        start = i * seg_size
        if i == seg_count - 1:
            offset = last_seg
        elif i < seg_count - 1:
            offset = seg_size
        else:
            return
        
        msg = b'QUERY\r\n' + fid.encode('utf-8') + b'\r\n'
        msg += start.to_bytes((start.bit_length() + 7) // 8, 'big') + b'\r\n'
        msg += offset.to_bytes((offset.bit_length() + 7) // 8, 'big') + b'\r\n'
        msg += i.to_bytes((i.bit_length() + 7) // 8, 'big')
        # data_segs[i] = self.response(msg, peer)
        self.__send__(msg, peer)
        return

    def download(self, fid: str) -> bytes:
        """
        Download a file from P2P network using its unique identification
        :param fid: the unique identification of the expected file, should be the same type of the return value of share()
        :return: the whole received file in bytes
        """
        data = b''
        seg_size = 4000
        """
        Start your code below!
        """
        send_msg = b"QUERY\r\n" + fid.encode('utf-8')
        print(f'{self.num} wants to download {fid}')
        get_msg = self.response(send_msg, self.tracker)
        length = int(eval(get_msg)[0])
        seg_count = length // seg_size
        last_seg = length % seg_size
        if last_seg != 0:
            seg_count += 1
        data_segs = [None] * seg_count
        self.datapool[fid] = [None] * seg_count
        i = 0
        while None in self.datapool[fid]:       
            get_msg = self.response(send_msg, self.tracker)
            peer_list = eval(get_msg)[1:]
            first_peer = peer_list[0]
            self.__download_seg(fid, first_peer, i, seg_count, seg_size, last_seg, data_segs)
            i += 1
        
        for d in self.datapool[fid]:
            data += d
        
        self.file[fid] = data

        self.response(f'REGISTER\r\n{fid}\r\n{length}'.encode('utf-8'), self.tracker)
    
        return data


    def cancel(self, fid: str):
        send_msg = b"CANCEL\r\n" + fid.encode('utf-8')
        get_msg = self.response(send_msg, self.tracker)

        if get_msg == b"CANCEL SUCCESS":
            print(f"{self.num} cancel {fid} success")
        else:
            print("no tracker")

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
            # print(str(self.num))

            msg, frm = self.__recv__()
            # print(f'{self.num} catch {msg}')
            msg_list = msg.split(b'\r\n')

            if msg_list[0] == b'QUERY':
                fid = msg_list[1].decode('utf-8')
                start = int.from_bytes(msg_list[2], 'big')
                offset = int.from_bytes(msg_list[3], 'big')
                index = msg_list[4]
                self.__send__(b'RETURN\r\n'+ msg_list[1] + b'\r\n' +index+b'\r\n'+self.file[fid][start:start+offset], frm)
                # self.__send__(self.file[fid][start:start+offset], frm)

            elif msg_list[0] == b'RETURN':
                fid = msg_list[1].decode('utf-8')
                index = int.from_bytes(msg_list[2], 'big')
                data = msg.split(b'\r\n', 3)[3]
                self.datapool[fid][index] = data

            elif msg == b'CLOSE SUCCESS':
                self.receive[frm] = msg
                return
            else:
                self.receive[frm] = msg


if __name__ == '__main__':
    pass
    # tracker_address = ("127.0.0.1", 10086)
    # A = PClient(tracker_address)