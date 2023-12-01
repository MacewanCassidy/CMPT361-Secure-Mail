import socket
import sys
import time
import json
import datetime

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

    # Creating a list of users with inboxes. Could be improved.
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

            # SERVICE START

            # Server receives credentials for authentication (RECV 1)
            username, password = connection_socket.recv(100).decode().split("\n")  # Decrypt information

            # Server sends result of authentication (SEND 2)
            if password == creds.get(username):
                running = True
                connection_socket.send('1'.encode())
                for user in users:
                    if user.username == username:
                        active_user = user

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

                        # THIS COULD BE IMPROVED BY USING A DICTIONARY TO SEARCH FOR USERS.
                        # However, execution speed  for this assignment is not high priority.
                        # This finds the recipient from users and adds the email string to their inbox.
                        for recipient in destinations:
                            for user in users:
                                if recipient == user.username:
                                    user.inbox.append(email)

                    # Display inbox contents.
                    case '2':

                        # Top of menu.
                        connection_socket.send("Index\tFrom\tDate and Time\tTitle".encode())

                        loop = str(len(active_user.inbox))
                        connection_socket.send(loop.encode())

                        for email in active_user.inbox:

                            string_email = json.dumps(email)
                            header = str(len(string_email)).encode()
                            connection_socket.send(header + string_email.encode())

                    # Get indexed email. Grab email string from inbox to display. (RECV 5c/SEND)
                    case '3':
                        inbox_index = int(connection_socket.recv(5).decode())
                        email = active_user.inbox[inbox_index-1]
                        email = dictionary_to_string(email)
                        connection_socket.send(email.encode())

                    # Terminate the connection.
                    case '4':
                        break

            # Ending message.
            print("Service ended, about to terminate.")
            time.sleep(1)

            # Server terminates client connection
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
        if letter is not "\n":
            read += letter
        else:
            break
    return read


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
