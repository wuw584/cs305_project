import threading

from Proxy import Proxy



class PClient:
    count  = 1
    def __init__(self, tracker_addr: (str, int), proxy=None, port=None, upload_rate=0, download_rate=0):
        if proxy:
            self.proxy = proxy
        else:
            self.proxy = Proxy(upload_rate, download_rate, port)  # Do not modify this line!
        self.tracker = tracker_addr
        """
        Start your additional code below!
        """
        self.num = PClient.count
        PClient.count +=1
        self.file={}
        self.receive = {}
        self.catching = True
        t = threading.Thread(target=self.start_catch,name=str(self.num))
        t.start()


    def __send__(self, data: bytes, dst: (str, int)):
        """
        Do not modify this function!!!
        You must send all your packet by this function!!!
        :param data: The data to be send
        :param dst: The address of the destination
        """
        self.proxy.sendto(data, dst)

    def __recv__(self, timeout=None) -> (bytes, (str, int)):
        """
        Do not modify this function!!!
        You must receive all data from this function!!!
        :param timeout: if its value has been set, it can raise a TimeoutError;
                        else it will keep waiting until receive a packet from others
        :return: a tuple x with packet data in x[0] and the source address(ip, port) in x[1]
        """
        return self.proxy.recvfrom(timeout)

    def response(self, data: str, address: (str, int), need_re = True):
        self.__send__(data.encode(), address)
        msg = None
        while need_re:
            if address in self.receive.keys():
                msg = self.receive[address]
                del self.receive[address]
                break
        return msg

    def register(self, file_path: str):
        """
        Share a file in P2P network
        :param file_path: The path to be shared, such as "./alice.txt"
        :return: fid, which is a unique identification of the shared file and can be used by other PClients to
                 download this file, such as a hash code of it
        """
        fid = 1
        """
        Start your code below!
        """
        self.file[fid] = file_path
        print("put in the list")
        send_msg = "REGISTER:"+str(fid)
        get_msg = self.response(send_msg,self.tracker)

        if get_msg == "REGISTER Success":
            print("Success register")
        else:
            print("no tracker")

        """
        End of your code
        """
        return fid

    def download(self, fid) -> bytes:
        """
        Download a file from P2P network using its unique identification
        :param fid: the unique identification of the expected file, should be the same type of the return value of share()
        :return: the whole received file in bytes
        """
        data = None
        """
        Start your code below!
        """
        send_msg = "QUERY:"+str(fid)
        get_msg = self.response(send_msg,self.tracker)
        peer_list = eval(get_msg[5:])
        print("get the peer list")
        for peer in peer_list:
            get_msg =self.response(send_msg,peer)
            if get_msg.startswith("FILE:"):
                print("got the file")
                data = get_msg[5:].encode
                self.response("REGISTER:"+str(fid),self.tracker)
                break

        # self.response(msg,self.tracker)
        # msg,frm = self.__recv__()
        # msg, client = msg.decode(), "(\"%s\", %d)" % frm

        """
        End of your code
        """
        return data

    def cancel(self, fid):
        """
        Stop sharing a specific file, others should be unable to get this file from this client any more
        :param fid: the unique identification of the file to be canceled register on the Tracker
        :return: You can design as your need
        """
        send_msg = "CANCEL:"+str(fid)
        get_msg = self.response(send_msg,self.tracker)

        if get_msg == "CANCEL Success":
            print("Success cancel")
        else:
            print("no tracker")


        """
        End of your code
        """

    def close(self):
        """
        Completely stop the client, this client will be unable to share or download files any more
        :return: You can design as your need
        """
        send_msg = "CLOSE"
        get_msg = self.response(send_msg,self.tracker)
        print("here")

        if get_msg == "CLOSE Success":
            print("Success close")
            self.catching = False
            self.proxy.close()
        else:
            print("no tracker")
        """
        End of your code
        """


    def start_catch(self):
        while self.catching:
            print(str(self.num))

            msg, frm = self.__recv__()
            msg, client = msg.decode(), "(\"%s\", %d)" % frm
            print(str(self.num)+" catch "+msg)

            if msg.startswith("QUERY:"):
                fid = int(msg[6:])
                if fid in self.file.keys():
                    file_object = open(self.file[fid])
                    try:
                        file_context = file_object.read()[:30]
                        file = "FILE:" + file_context
                        print("send the file")
                        self.response(file, eval(client),False)

                    finally:
                        file_object.close()
            else:
                self.receive[eval(client)] = msg


if __name__ == '__main__':
    pass
