from socket import *
from threading import Thread
import traceback
import random
import datetime
import os
import interactive_conditional_samples as gpt
from tensorflow.python.client import device_lib

print(device_lib.list_local_devices())

os.environ["CUDA_DEVICE_ORDER"]="PCI_BUS_ID"
os.environ["CUDA_VISIBLE_DEVICES"]="0"

class User:
    def __init__(self):
        self.c = 0
        self.addr = 0
        self.id = 0

    def __repr__(self):
        return str(self.id)

clients = []
request_base = open("server_requests.txt", "a", encoding="utf-8")

def handleMainProcess(toDel, c, strdata, jointpacketError, client):
    if len(jointpacketError) == 2:
        strdata = "/m" + jointpacketError[1]
    sds = strdata.split("\n")

    #parse and open params to send for gpt

    seed = int(sds[2])
    if sds[1] == "false":
        seed = random.randint(0, 2**32 - 1)

    lenth = int(sds[3])
    temp = float(sds[4])
    top_k = int(sds[5])

    
    output = gpt.interact_model(sds[6], sds[0][2:], seed, 1, 1, lenth if lenth != 0 else None, temp, top_k);
    
        
    newdata = output
    c.sendto(newdata.encode('utf-8'), client.addr)

    if toDel in clients:
        id = toDel.id
        clients.remove(toDel)
        print("Removed request " + str(id))
        

def clientHandler(toDel, c, addr):
    print(addr, "is Connected")
    try:
        while len(clients) > 0:

            try:
                data = c.recv(1024)
            except timeout:
                print("timeout, removing client")
                clients.remove(toDel)
                break
                
            if not data: 
                break 
            for client in clients:
                

                strdata = data.decode("utf-8")

                request_base.write(strdata.replace("\n", " : ") + "::TIME::" + str(datetime.datetime.now()) + ":: IP ADDR, "
                                    + str(addr) + "\n")
                request_base.flush()
                jointpacketError = strdata.split("/m");
                
                if(strdata.startswith("/m")):
                    handleMainProcess(toDel, c, strdata, jointpacketError, client)
                    
                            

                if(strdata.startswith("/connect")):
                   if client.id==0:                           
                       client.id = int(jointpacketError[0][8:])
                       print("New Request From: " + str(client.id))
                       if len(jointpacketError) == 2:
                           print("Packet came smacked together")
                           print("Resolving error...")
                           handleMainProcess(toDel, c, strdata, jointpacketError, client)
                           
                       
                   for other in clients:
                       if other.id == client.id and other != client:
                           clients.remove(other)


                           
                   
    except Exception:
        print(traceback.print_exc())

HOST = '192.168.1.15'
PORT = 2466

s = socket(AF_INET, SOCK_STREAM)
s.bind((HOST, PORT))
s.listen(10)

print("Server is running on "+ str(PORT))

#Thread(target=clientHandler).start()
#Thread(target=clientHandler).start()
#Thread(target=clientHandler).start()
trds = []

while True: 
    c, addr = s.accept()

    user = User()
    user.c = c
    user.addr = addr
    user.id = 0
    clients.append(user)


        
    t = Thread(target=clientHandler, args = (user, c, addr))
    trds.append(t)
    t.start()

for t in trds:
    t.join()

s.close()
