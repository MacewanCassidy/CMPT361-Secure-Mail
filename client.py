import socket
import sys
import time
import json

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


def client_program():
    # Server Information
    server_name = '127.0.0.1'  # 'localhost'
    server_port = 13000

    # Create client socket that using IPv4 and TCP protocols
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error as e:
        print('Error in client socket creation:', e)
        sys.exit(1)

    try:
        # Client connect with the server
        client.connect((server_name, server_port))

        # SERVICE START

        # Client sends username and password to server (SEND 1)
        username = input("Enter your username: ")
        password = input("Enter your password: ")
        client.send(f"{username}\n{password}".encode())  # Encrypt this string before sending

        # Client receives authorization result. (RECV 2)
        access = client.recv(1).decode()
        if access == '1':
            running = True
        else:
            running = False

        # Email Service Loop
        while running:
            # Receive menu from server (RECV 3)
            menu = client.recv(500).decode()  # Decrypt this
            print(menu)

            # Operation menu selection (SEND 4)
            selection = input("Choice: ")
            client.send(selection.encode())  # Encrypt this

            match selection:

                # Create and send email. (SEND 5a)
                case '1':
                    destinations, email = create_email(username)
                    client.send(destinations.encode())
                    time.sleep(0.25)
                    client.send(email.encode())
                    print("Message has been sent to the server.")

                # Display inbox contents. (SEND 5b)
                case '2':
                    # Receiving and printing the header.
                    print(client.recv(30).decode())

                    # Getting number of emails
                    email_num = client.recv(1).decode()

                    for num in range(0, int(email_num)):
                            
                        
                        mail = client.recv(10000).decode()

                        dict_email = json.loads(mail)
                        print(f"{num+1}\t\t{dict_email.get('From')}\t{dict_email.get('Time and Date Received')}\t {dict_email.get('Title')}")

                        time.sleep(0.2)

                # Read indexed email. (SEND 5c/RECV 5c)
                case '3':
                    # Client sends email index
                    email_index = input("Enter the email index you wish to view: ")
                    client.send(email_index.encode())
                    
                    # Print recieved string.
                    print()
                    print(client.recv(10000).decode())

                # Terminate the connection.
                case '4':
                    break

        # Client terminates connection with the server
        client.close()

    except socket.error as e:
        print('An error occurred:', e)
        client.close()
        sys.exit(1)


def create_email(username):

    # Gather email information.
    destinations = input(" Enter destinations (separated by ;): ")
    title = input("Enter title: ")

    load = input("Would you like to load contents from a file? (Y/N): ")

    # Entering message contents.
    if load.lower() == 'y':
        while True:

            filename = input("Enter filename: ")

            try:
                f = open(filename, 'r')
                message = f.read()
                f.close()
                break

            except:
                answer = input("Invalid file name, would you like to try again? (Y/N): ")
                if answer.lower() == 'y':
                    pass
                else:
                    message = input("Enter message contents: ")
                    break

    else:
        message = input("Enter message contents: ")

    # Creation of email dictionary.
    email = {"From": username, "To": destinations, "Title": title, "Content Length": len(message), "Contents": message}
    email = json.dumps(email)
    return destinations, email


client_program()
