import socket
import sys
import time
import json
import datetime
import os

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


def server_program():
    server_port = 13000

    # Create server socket that uses IPv4 and TCP protocols
    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error as e:
        print('Error in server socket creation:', e)
        sys.exit(1)

    # Associate 13000 port number to the server socket
    try:
        server.bind(('', server_port))
    except socket.error as e:
        print('Error in server socket binding:', e)
        sys.exit(1)

    # Loading data from credentials file, these are our authorized users.
    file = open("user_pass.json", 'r')
    x = file.read()
    creds = json.loads(x)
    file.close()

    # Creation of inbox file.
    dict_inbox = {"client1": [], "client2": [], "client3": [], "client4": [], "client5": []}
    str_inbox = json.dumps(dict_inbox)
    inboxes = open("inboxes.json", 'w')
    inboxes.write(str_inbox)
    inboxes.close()

    # Creating a list of users with inboxes. Could be improved.
    global users 
    users = []
    for (uname, password) in creds.items():
        user = User(uname, password)
        users.append(user)


    print('The server is ready to accept connections')

    # The server can only have five connection in its queue waiting for acceptance
    server.listen(5)

    while True:
        try:
            # Server accepts client connection
            connection_socket, addr = server.accept()
            print(addr, '   ', connection_socket)

            pid = os.fork()

            # This is the child process.
            if pid <= 0:
                
                # Close the inital server 
                server.close()

                # Server receives credentials for authentication (RECV 1)
                username, password = connection_socket.recv(100).decode().split("\n")  # Decrypt information

                # Server sends result of authentication (SEND 2)
                if password == creds.get(username):
                    running = True
                    connection_socket.send('1'.encode())
                    index = 0
                    for user in users:
                        if user.username == username:
                            break
                        else:
                            index += 1

                # Authentication failure.
                else:
                    connection_socket.send('0'.encode())
                    running = False

                # Email Service Loop
                while running:
                    # Server sends menu (SEND 3)
                    connection_socket.send("\nSelect the Operation:"
                                        "\n\t1) Create and send an email"
                                        "\n\t2) Display the inbox list"
                                        "\n\t3) Display the email contents"
                                        "\n\t4) Terminate the connection\n".encode())  # Encrypt this

                    # Receive operation menu selection (RECV 4)
                    selection = connection_socket.recv(2).decode()  # Decrypt this

                    match selection:

                        # Create and send email operation.
                        case '1':

                            # (RECV 5a)
                            destinations = connection_socket.recv(100).decode()  # Decrypt these two
                            email = connection_socket.recv(10000).decode()
                            email = json.loads(email)

                            # Adds time to email string.
                            email = add_time(email)

                            # Convert to list, to iterate through destination users.
                            if ';' in destinations:
                                destinations = destinations.split(';')
                            else:
                                destinations = [destinations]

                            # Putting email in file.
                            inboxes = open("inboxes.json", 'r')
                            str_inbox = inboxes.read()
                            dict_inbox = json.loads(str_inbox)
                            for recipient in destinations:
                                inbox = dict_inbox.get(recipient)
                                inbox.append(email)
                            str_inbox = json.dumps(dict_inbox)
                            inboxes.close()
                            file = open("inboxes.json", 'w')
                            file.write(str_inbox)
                            file.close()

                        # Display inbox contents.       
                        case '2':

                            # Top of menu.
                            connection_socket.send("Index\tFrom\tDate and Time\tTitle".encode())

                            file = open("inboxes.json", 'r')
                            str_inbox = file.read()
                            file.close()
                            dict_inbox = json.loads(str_inbox)
                            user_inbox = dict_inbox.get(username)
                            
                            loop = str(len(user_inbox)).encode()
                            connection_socket.send(loop)
                            time.sleep(0.2)

                            for email in user_inbox:
                                str_mail =  json.dumps(email)
                                connection_socket.send(str_mail.encode())
                                time.sleep(0.2)

                        # Get indexed email. Grab email string from inbox to display. (RECV 5c/SEND)
                        case '3':
                            inbox_index = int(connection_socket.recv(5).decode())
                            
                            file = open("inboxes.json", 'r')
                            str_inbox = file.read()
                            file.close()
                            dict_inbox = json.loads(str_inbox)
                            inbox = dict_inbox.get(username)
                            dict_email = inbox[inbox_index-1]
                            email = dictionary_to_string(dict_email)
                            connection_socket.send(email.encode())
                            time.sleep(0.20)

                        # Terminate the connection.
                        case '4':
                            break

                # Ending message.
                print(f"Service for {username} ended, about to terminate.")
                time.sleep(1)

                # Server terminates client connection
                connection_socket.close()

            # Parent Process
            elif pid > 0:
                connection_socket.close()

        except socket.error as e:
            print('An error occurred:', e)
            server.close()
            sys.exit(1)


# Class to organize username, password and inbox in one piece of data.
class User:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.inbox = []  # List of email strings.

# Function to insert date and time received into email string.
def add_time(email):
    current = str(datetime.datetime.now())
    email.update({"Time and Date Received": current})
    return email


def read_string(message):
    read = ""
    for letter in message:
        if letter != "\n":
            read += letter
        else:
            break
    return read


def print_inbox(list):
    for i in list:
        print(i.inbox)

def dictionary_to_string(dictionary) -> str:
    string = ""
    string += f"From: {dictionary.get('From')}\n"
    string += f"To: {dictionary.get('To')}\n"
    string += f"Time and Date Received: {dictionary.get('Time and Date Received')}\n"
    string += f"Title: {dictionary.get('Title')}\n"
    string += f"Content Length: {dictionary.get('Content Length')}\n"
    string += f"Contents:\n"
    string += f"{dictionary.get('Contents')}"
    return string


server_program()
