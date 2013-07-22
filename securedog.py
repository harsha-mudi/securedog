"""
RSA encryption 2048

json protocol:

recv -- "req_type" : "pubkey"
send -- "pubkey" : filestring

recv -- "req_type" : "message"
        "message" : string
        "signature": string
send -- "OK"
"""
import SocketServer
import socket
import json
import sys
import base64
import threading
import signal

from pubsub import pub
from Crypto.PublicKey import RSA

privatekey = sys.argv[1]
port = sys.argv[2]
port = int(port)
pubkey = privatekey + ".pub"
pubkey_text = open(pubkey).read()
privatekey_text = open(privatekey).read()
RSA_pubkey = RSA.importKey(pubkey_text)
RSA_privatekey = RSA.importKey(privatekey_text)


def listener_for_echo(arg, request):
    data = arg
    enc_msg = data["message"]
#    sig = data["signature"]
    msg = RSA_privatekey.decrypt(base64.b64decode(enc_msg))
    request.sendall(msg)


def listener_for_msg(arg, request):
    data = arg
    enc_msg = data["message"]
#    sig = data["signature"]
    RSA_privatekey.decrypt(base64.b64decode(enc_msg))
    request.sendall("OK")


def listener_for_pubkey(arg, request):
    global pubkey_text
    request.sendall(json.dumps({"pubkey": pubkey_text}))


def listener_for_new(arg, request):
    data = arg
    if data.get('req_type', "") == "pubkey":
        pub.sendMessage("pubkey", arg=data, request=request)
    elif data.get('req_type', "") == "message":
        pub.sendMessage("message", arg=data, request=request)
    elif data.get('req_type', "") == "echo":
        pub.sendMessage("echo", arg=data, request=request)
    else:
        request.sendall(json.dumps({"status": "OK"}))


pub.subscribe(listener_for_new, 'new')
pub.subscribe(listener_for_pubkey, 'pubkey')
pub.subscribe(listener_for_msg, 'message')
pub.subscribe(listener_for_echo, 'echo')


class RequestHandler(SocketServer.StreamRequestHandler):
    def handle(self):
        total_data = []
        while True:
            data = self.request.recv(1500)
            if not data:
                break
            total_data.append(data)
        data = ''.join(total_data)
        pub.sendMessage("new", arg=json.loads(data), request=self.request)


server = SocketServer.TCPServer(("127.0.0.1", port), RequestHandler)
print "Server Started"
t = threading.Thread(target=server.serve_forever)
t.start()


def handleSigTERM():
    print "Shutdown"
    server.socket.close()
    server.shutdown()
    exit(1)
signal.signal(signal.SIGTERM, handleSigTERM)

from PyQt4 import QtGui as qt

app = qt.QApplication([])
w = qt.QMainWindow()


def test_function():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(("127.0.0.1", port))
    sock.sendall(json.dumps({"req_type": "pubkey"}))
    sock.shutdown(socket.SHUT_WR)
    sock.recv(4096)
    sock.close()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(("127.0.0.1", port))
    enc_msg = RSA_pubkey.encrypt("Hello World", 32)
    sock.sendall(json.dumps({"req_type": "echo", "message": base64.b64encode(enc_msg[0])}))
    sock.shutdown(socket.SHUT_WR)
    msg = sock.recv(1024)
    qt.QMessageBox.about(w, "Received Data", msg)


from sets import Set
friends = Set([u"foo", u"Bar", u"baz"])


def new_friend():
    pass


def remove_friend():
    global friends
    friends.remove(str(cbox.currentText()))
    cbox.removeItem(cbox.currentIndex())


def compose_message():
    pass

# Menubar
menu = qt.QMenu("&Main", w)
add = qt.QAction("&Add Friend", menu)
compose = qt.QAction("&Compose", menu)
test = qt.QAction("Self test", menu)
add.triggered.connect(new_friend)
compose.triggered.connect(compose_message)
test.triggered.connect(test_function)
menu.addAction(add)
menu.addAction(compose)
menu.addAction(test)
w.menuBar().addMenu(menu)

# Centeral Widget
v = qt.QVBoxLayout(w)
cw = qt.QWidget(w)
cw.setLayout(v)
w.setCentralWidget(cw)

cbox = qt.QComboBox(w)
for friend in friends:
    cbox.addItem(friend)
h = qt.QHBoxLayout(w)
remove = qt.QPushButton("Remove")
remove.clicked.connect(remove_friend)
h.addWidget(remove)
new = qt.QPushButton("New")
new.clicked.connect(new_friend)
h.addWidget(new)
v.addLayout(h)
v.addWidget(cbox)

# Inbox
h1 = qt.QHBoxLayout(w)
ib = qt.QTreeWidget(w)
ib.resize(480, 280)
h1.addWidget(ib)
cb = qt.QTextEdit(w)
cb.resize(480, 440)
h1.addWidget(cb)
v.addLayout(h1)

# Status bar
w.statusBar().showMessage("I'm Listening")


w.resize(480, 720)
w.move(0, 0)
w.setWindowTitle('SecureDOG')
w.show()
app.exec_()

print "Shutdown"
server.socket.close()
server.shutdown()
exit(1)
