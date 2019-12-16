import socket
import threading
from concurrent.futures import ThreadPoolExecutor
from os import system, name, path, walk, mkdir, remove
import subprocess
import re
import time
import atexit

transporterLogo = """
 _____                                      _            
/__   \_ __ __ _ _ __  ___ _ __   ___  _ __| |_ ___ _ __ 
  / /\/ '__/ _` | '_ \/ __| '_ \ / _ \| '__| __/ _ \ '__|
 / /  | | | (_| | | | \__ \ |_) | (_) | |  | ||  __/ |   
 \/   |_|  \__,_|_| |_|___/ .__/ \___/|_|   \__\___|_|   
                          |_|                            
"""


def clear():
    if name == 'nt':  # for windows
        system('cls')
    else:  # for mac and linux
        system('clear')


def print_options():
    print("1. Send message")
    print("2. Mailbox")
    print("3. Online people")
    print("4. Start video chat")
    print("5. Pending video calls")
    print("6. Manage Groups")
    print("7. Send message to a group")
    print("8. Attend video chat in a group")
    print("9. See group video chats going on. ")
    print("q. Quit")


def print_group_manage_options():
    print("1. List of all groups")
    print("2. List of groups I attended")
    print("3. Enter a group")
    print("4. Leave a group")
    print("c. Cancel")

def enter_group(groupname): #todo Enter a group
    pass

def leave_group(groupname): #todo Leave a group
    pass


def alphaNumericFilter(word):
    if re.fullmatch("^[a-zA-Z0-9_]+$", word):
        return True
    else: 
        return False


def sync_groups():
    global groups
    groups_isdir = path.isdir("groups")
    groups_isfile = path.isfile("groups")
    if groups_isfile:
        remove("groups")
        try:
            mkdir("groups")
        except OSError:
            print ("Creation of the directory 'groups' failed")
            time.sleep(2)
        else:
            print ("Successfully created the directory 'groups'")
            time.sleep(2)
    elif groups_isdir:
        for (root,dirs,files) in walk("groups"):
            groups = filter(alphaNumericFilter, files)

    else: 
        try:
            mkdir("groups")
        except OSError:
            print ("Creation of the directory 'groups' failed")
            time.sleep(2)
        else:
            print ("Successfully created the directory 'groups'")
            time.sleep(2)


def get_ip():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        try:
            # doesn't even have to be reachable
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except:
            IP = '127.0.0.1'
            print("You are not connected to a network chat application will not work.")
    return IP


def send_announce():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as announce_s:
        announce_s.settimeout(0.2)
        announce_s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        announce_s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        send_announce_packet_once(announce_s)
        time.sleep(1)
        send_announce_packet_once(announce_s)
        time.sleep(1)
        send_announce_packet_once(announce_s)


def send_announce_packet_once(_announce_socket):
    try:
        _announce_socket.sendto(("[" + str(username) + ", " + str(userip) + ", announce]").encode(
            "utf-8", errors="replace"), ('<broadcast>', 12345))
    except Exception as e:
        print("An error occured when broadcasting", e)
        time.sleep(1)


def send_response(_ip):  # _ip is ip of other guy
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as response_s:
        try:
            response_s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            response_s.connect((_ip, 12345))
            response_s.sendall(("[" + str(username) + ", " + str(userip) +
                               ", response]").encode("utf-8", errors="replace"))
            response_s.shutdown(socket.SHUT_RDWR)
        except Exception as e:
            print("An error occured when responding to an announce message", e)
            time.sleep(1)


def send_message(_ip, _payload):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as message_s:
        try:
            message_s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            message_s.connect((_ip, 12345))
            message_s.sendall(
                ("[" + str(username) + ", " + str(userip) + ", message, " + str(_payload) + "]").encode("utf-8", errors="replace"))
            message_s.shutdown(socket.SHUT_RDWR)
        except Exception as e:
            print("An error occured when message is sending", e)
            time.sleep(1)


def send_call(_ip):  # Call request
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as message_s:
        try:
            message_s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            message_s.connect((_ip, 12345))
            message_s.sendall(
                ("[" + str(username) + ", " + str(userip) + ", call]").encode("utf-8", errors="replace"))
            message_s.shutdown(socket.SHUT_RDWR)
        except Exception as e:
            print("An error occured when sending call message", e)
            time.sleep(1)


def send_accept_call(_ip):  # Ok to call request, sent after getting a call
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as message_s:
        try:
            message_s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            message_s.connect((_ip, 12345))
            message_s.sendall(
                ("[" + str(username) + ", " + str(userip) + ", acceptcall]").encode("utf-8", errors="replace"))
            message_s.shutdown(socket.SHUT_RDWR)
        except Exception as e:
            print("An error occured when sending accept call message", e)
            time.sleep(1)


def send_start_call(_ip):  # Starting response, sent after call is accepted by other party
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as message_s:
        try:
            message_s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            message_s.connect((_ip, 12345))
            message_s.sendall(
                ("[" + str(username) + ", " + str(userip) + ", startcall]").encode("utf-8", errors="replace"))
            message_s.shutdown(socket.SHUT_RDWR)
        except Exception as e:
            print("An error occured when sending start call message", e)
            time.sleep(1)


def send_cancel_call(_ip):  # Starting response, sent after call is accepted by other party
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as message_s:
        try:
            message_s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            message_s.connect((_ip, 12345))
            message_s.sendall(
                ("[" + str(username) + ", " + str(userip) + ", cancelcall]").encode("utf-8", errors="replace"))
            message_s.shutdown(socket.SHUT_RDWR)
        except Exception as e:
            print("An error occured when sending cancel call message", e)
            time.sleep(1)


def send_allgroups_request():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as allgroups_s:
        allgroups_s.settimeout(0.2)
        allgroups_s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        allgroups_s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        send_allgroups_req_packet_once(allgroups_s)
        time.sleep(1)
        send_allgroups_req_packet_once(allgroups_s)
        time.sleep(1)
        send_allgroups_req_packet_once(allgroups_s)



def send_allgroups_req_packet_once(_allgroups_socket):
    try:
        _allgroups_socket.sendto(("[" + str(username) + ", " + str(userip) + ", allgroups]").encode(
            "utf-8", errors="replace"), ('<broadcast>', 12345))
    except Exception as e:
        print("An error occured when broadcasting all groups request", e)
        time.sleep(1)


def send_my_groups_to(ip, groups):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as mygroups_s:
        try:
            mygroups_s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            mygroups_s.connect((_ip, 12345))
            mygroups_string = ", ".join(groups)
            mygroups_s.sendall(
                ("[" + str(username) + ", " + str(userip) + ", mygroups, " + mygroups_string + "]" ).encode("utf-8", errors="replace"))
            message_s.shutdown(socket.SHUT_RDWR)
        except Exception as e:
            print("An error occured when sending my groups", e)
            time.sleep(1)


def process_messages(_data):
    decoded = _data.decode("utf-8", errors="replace")
    # print(decoded)
    if decoded[0] == "[" and decoded[-1] == "]":
        decoded_striped = str(decoded[1:-1])  # Strip out square parantheses.
        decoded_splitted = decoded_striped.split(",")
        if len(decoded_splitted) < 3:
            print("Got an invalid message " + str(decode))
            return
        message_type = decoded_splitted[2].strip(' ')
        if message_type == 'announce':
            global lasttime, last_udp_packet
            lastip = last_udp_packet["ip"]
            lastname = last_udp_packet["name"]
            name = decoded_splitted[0].strip(' ')
            ip = decoded_splitted[1].strip(' ')
            if(time.time()-lasttime <= 3 and lastip == ip and lastname == name):
                pass
            # not me and also not in online list
            elif (name, ip) not in online_people and (name, ip) != (username, userip):
                try:
                    subprocess.run(["notify-send","New person online: " + name + ", Ip: " + ip])
                    online_people.add((name, ip))
                    executor.submit(send_response, ip)
                except Exception as e:
                    print(e)
            lasttime = time.time()
            last_udp_packet["ip"] = ip
            last_udp_packet["name"] = name
        elif message_type == 'response':
            name = decoded_splitted[0].strip(' ')
            ip = decoded_splitted[1].strip(' ')
            subprocess.run(["notify-send","New person online: " + name + ", Ip: " + ip])
            online_people.add((name, ip))
        elif message_type == 'call':
            name = decoded_splitted[0].strip(' ')
            ip = decoded_splitted[1].strip(' ')
            subprocess.run(["notify-send","New call from" + name + ".\n" + "To accept, go to calls."])
            if (name, ip) not in calls:
                calls.append((name, ip))
        elif message_type == 'acceptcall':
            name = decoded_splitted[0].strip(' ')
            ip = decoded_splitted[1].strip(' ')
            print("Call accepted by", name, "starting video chat...")
            send_start_call(ip)
            start_video_chat(ip)
        elif message_type == 'startcall':
            global start_call
            name = decoded_splitted[0].strip(' ')
            ip = decoded_splitted[1].strip(' ')
            if ip == accepted_call_ip:
                start_call = True
        elif message_type == "cancelcall":
            name = decoded_splitted[0].strip(' ')
            ip = decoded_splitted[1].strip(' ')
            subprocess.run(["notify-send",name + " canceled a call."], shellss)
            try:
                calls.remove((name, ip))
            except ValueError:
                pass
        elif message_type == "allgroups":
            ip = decoded_splitted[1].strip(' ')
            sync_groups()
            send_my_groups_to(ip, groups)
        elif message_type == 'message':
            if len(decoded_splitted) < 4:
                print("Got an invalid message " + str(decode))
                return
            name = decoded_splitted[0].strip(' ')
            ip = decoded_splitted[1].strip(' ')
            message = decoded_splitted[3].strip(' ')

            subprocess.run(["notify-send","New message from " + name + ", Message: " + message])
            # print(str(name) + ": " + str(message))
            if (name, ip) in messages:
                messages[(name, ip)].append(message)
            else:
                messages[(name, ip)] = [message]
            if (name, ip) not in online_people:
                subprocess.run(["notify-send","New person online: " + name + ", Ip: " + ip])
                online_people.add((name, ip))
        else:
            print("Got an invalid message " + str(decode))

    else:  # Invalid message
        print("Got an invalid message " + str(decode))


def listen_messages():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((get_ip(), 12345))
        sock.listen()
        while True:
            conn, addr = sock.accept()
            executor.submit(on_new_connection, conn, addr)


def listen_udp_messages():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        #sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 0)
        sock.bind(("", 12345))
        while True:
            data, addr = sock.recvfrom(1500)
            executor.submit(on_new_udp_connection, data, addr)


def on_new_connection(conn, addr):
    with conn:
        data = conn.recv(1500)
        if data:
            # time.sleep(0.1)
            process_messages(data)


def on_new_udp_connection(data, addr):
    if addr != (userip, 12345):
        # time.sleep(0.1)
        process_messages(data)


def start_video_chat(person_ip):
    global call_started
    call_started = True
    person_ip_splitted = person_ip.split(".")
    friend_ip = "234." + str(person_ip_splitted[1]) + "." + str(
        person_ip_splitted[2]) + "." + str(person_ip_splitted[3])

    user_ip_splitted = userip.split(".")

    own_ip = "234." + str(user_ip_splitted[1]) + "." + str(
        user_ip_splitted[2]) + "." + str(user_ip_splitted[3])

    streamVideoProcess = subprocess.Popen(
        ["bash", "streamVideo.sh", own_ip, "40000"], stdout=subprocess.DEVNULL)
    streamAudioProcess = subprocess.Popen(
        ["bash", "streamAudio.sh", own_ip, "50000"], stdout=subprocess.DEVNULL)
    renderOwnVideoProcess = subprocess.Popen(
        ["bash", "renderVideo.sh", own_ip, "40000"], stdout=subprocess.DEVNULL)
    renderVideoProcess = subprocess.Popen(
        ["bash", "renderVideo.sh", friend_ip, "40000"], stdout=subprocess.DEVNULL)
    renderAudioProcess = subprocess.Popen(
        ["bash", "renderAudio.sh", friend_ip, "50000"], stdout=subprocess.DEVNULL)
    print("Video chat started...")

    inp = input("Press c to close video chat")
    while inp != "c":
        inp = input("Press c to close video chat")

    print("Closing")
    call_started = False
    # streamVideoProcess.kill()
    # streamAudioProcess.kill()
    # renderOwnVideoProcess.kill()
    # renderVideoProcess.kill()
    # renderAudioProcess.kill()
    subprocess.run(["killall", "-9", "gst-launch-1.0"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def cleanup():
    subprocess.run(["killall", "-9", "gst-launch-1.0"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


last_udp_packet = {
    "ip": "",
    "name": ""
}

#!Main
lasttime = 0.0
messages = {}
sent_messages = {}


calls = []
start_call = False
accepted_call_ip = ""
call_started = False


online_people = set()
# online_people.add(("serkan", "192.168.43.224"))
username = input("What is your name? \n")
userip = get_ip()

tcplistener = threading.Thread(target=listen_messages, daemon=True)
tcplistener.start()

udplistener = threading.Thread(target=listen_udp_messages, daemon=True)
udplistener.start()


executor = ThreadPoolExecutor(255)

announcer = threading.Thread(target=send_announce, daemon=True)
announcer.start()

while not username:
    print("Please enter a name!")
    username = input("What is your name? \n")

all_groups = []
groups = []

sync_groups()

atexit.register(cleanup)

clear()
choice = None
flash_messages = ["Welcome to the transporter app. Have fun! \n"]
while choice != "q":
    clear()
    print(transporterLogo)
    if call_started:
        print("Press c to close video chat")
    for f_message in flash_messages:
        print(f_message)
    flash_messages.clear()
    print_options()
    choice = input("Select an option: \n")
    if choice == "1":  # Send message
        clear()
        print("------------------Send Message------------------ \n\n")
        if len(online_people) == 0:
            flash_messages.append("No one is online!\n")
            continue
        temp_dict = {}
        counter = 1
        print("Online people: \n")
        for person in online_people:
            print(str(counter) + ". Name: " +
                  str(person[0]) + " IP: " + str(person[1]))
            temp_dict[counter] = person
            counter += 1

        print()
        person_num = input(
            "Select a person by number. \nTo cancel, type 'c' \n")
        while not person_num.isdigit() or int(person_num) > (counter - 1) or int(person_num) < 1:
            if person_num == "c":
                break
            person_num = input("Invalid person number. Please enter again: \n")
        if person_num == "c":
            continue
        person_cho = temp_dict[int(person_num)]
        person_ip = person_cho[1]

        if person_cho in sent_messages:
            print("You wrote before: ")
            for message in sent_messages[person_cho]:
                print(">> " + str(message))

        message = input("Please enter your message:\n")
        if person_cho in sent_messages:
            sent_messages[person_cho].append(message)
        else:
            sent_messages[person_cho] = [message]
        executor.submit(send_message, person_ip, message)
        print("Message sent! \n")

        while True:
            sendAgain = input("Send again ? [y/n]:")
            while sendAgain.capitalize() != "Y" and sendAgain.capitalize() != "N":
                print("Invalid answer, try again.")
                sendAgain = input("Send again ? [y/n]:")
            if sendAgain.capitalize() == "Y":
                message = input("Please enter your message:\n")
                if person_cho in sent_messages:
                    sent_messages[person_cho].append(message)
                else:
                    sent_messages[person_cho] = [message]
                executor.submit(send_message, person_ip, message)
                print("Message sent! \n")
            elif sendAgain.capitalize() == "N":
                break

    elif choice == "2":  # Mailbox
        clear()
        print("------------------Mailbox------------------ \n\n")

        if len(messages.keys()) == 0:
            flash_messages.append("No message! \n")
            continue
        temp_dict = {}
        counter = 1
        for entry in messages:
            print(str(counter) + ". " + "Name: " +
                  entry[0] + " IP:" + entry[1])
            temp_dict[counter] = entry
            counter += 1
        entry_num = input("Select an entry.\nTo cancel, type 'c': \n")
        while not entry_num.isdigit() or int(entry_num) > (counter - 1) or int(entry_num) < 1:
            if entry_num == "c":
                break
            entry_num = input("Invalid. Select again \n")
        if entry_num == "c":
            continue
        entry_cho = temp_dict[int(entry_num)]
        flash_messages.append(str(entry_cho[0]) + " wrote: ")
        for message in messages[entry_cho]:
            flash_messages.append(">> " + str(message))
        flash_messages.append("\n")
    elif choice == "3":  # Online people
        flash_messages.append("Online People\n")

        if len(online_people) == 0:
            flash_messages.append("No one is online! \n")
            continue
        counter = 1
        for person in online_people:
            flash_messages.append(
                str(counter) + ". Name: " + str(person[0]) + " IP: " + str(person[1]))
            counter += 1
        flash_messages.append("\n")
    elif choice == "4":  # Video chat
        clear()
        print("------------------Video Chat------------------ \n\n")
        if len(online_people) == 0:
            flash_messages.append("No one is online!\n")
            continue
        temp_dict = {}
        counter = 1
        print("Online people: \n")
        for person in online_people:
            print(str(counter) + ". Name: " +
                  str(person[0]) + " IP: " + str(person[1]))
            temp_dict[counter] = person
            counter += 1

        print()
        person_num = input(
            "Select a person by number. \nTo cancel, type 'c' \n")
        while not person_num.isdigit() or int(person_num) > (counter - 1) or int(person_num) < 1:
            if person_num == "c":
                break
            person_num = input("Invalid person number. Please enter again: \n")
        if person_num == "c":
            continue
        person_cho = temp_dict[int(person_num)]
        person_name = person_cho[0]
        person_ip = person_cho[1]

        send_call(person_ip)
        print("Calling", person_name + ".", "Waiting for response...")
        endCall = input("To cancel call, type 'c'.")
        while endCall != "c" and not call_started:
            print("Invalid answer, try again.")
            endCall = input("To cancel call, type 'c'.")

        if not call_started:
            send_cancel_call(person_ip)
            flash_messages.append("Call canceled.")
    elif choice == "5":  # Calls
        clear()
        print("------------------Pending calls------------------ \n\n")
        if len(calls) == 0:
            flash_messages.append("No pending calls!\n")
            continue
        for i in range(len(calls)):
            print(str(i+1)+".", "Name:", calls[i][0], "Ip:", calls[i][1])
        person_num = input("Select a person to answer. To cancel, type 'c'.\n")

        while not person_num.isdigit() or int(person_num) > len(calls) or int(person_num) < 1:
            if person_num == "c":
                break
            person_num = input("Invalid person number. Please enter again: \n")
        if person_num == "c":
            continue
        will_be_called_person = calls[int(person_num)-1]
        try:
            calls.remove(will_be_called_person)
        except ValueError:
            pass
        start_call = False
        accepted_call_ip = will_be_called_person[1]
        send_accept_call(will_be_called_person[1])  # ip
        time.sleep(3)
        if start_call:
            print("Video call starting... ")
            executor.submit(start_video_chat, will_be_called_person[1])
        else:
            flash_messages.append("No respond from other side in 3 seconds.")
    elif choice == "6": # Manage Groups
        groups_string = ", ".join(groups)
        flash_messages.append("You are in these groups: " + groups_string + "\n")
        
        print_group_manage_options()
        gchoice = input("Choose an action: \n")

        # def print_group_manage_options():
        #     print("1. List of all groups")
        #     print("2. List of groups I attended")
        #     print("3. Enter a group")
        #     print("4. Leave a group")
        #     print("c. Cancel")

        while gchoice != "c":
            gchoice = input("Choose an action: \n")
            print_group_manage_options()
            if gchoice == "1": # todo List of all groups
                print("Syncing groups please wait 5 seconds..")
                send_allgroups_request()
                time.sleep(5)
                all_groups_string = ", ".join(all_groups)
                print("All groups: ", all_groups_string)
            elif gchoice == "2": # List of groups I attended
                sync_groups()
                groups_string = ", ".join(groups)
                print("You are in these groups: ", groups_string)
            elif gchoice == "3": # todo Enter a group
                groupname = input("Enter group name to enter. Remember that only alphanumeric groups are accepted. To cancel type 'c'")
                if groupname == "c":
                    continue
                enter_group(groupname)
            elif gchoice == "4": # todo Leave a group
                sync_groups()
                groups_string = ", ".join(groups)
                print("You are in these groups: ", groups_string)
                groupname = input("Enter group name to leave. Remember that only alphanumeric groups are accepted. To cancel type 'c'")
                if groupname == "c":
                    continue
                leave_group(groupname)
    elif choice == "7": # todo Send message to a group
        pass
    elif choice == "8": # todo Attend video chat in a group
        pass
    elif choice == "9": # todo See group video chats going on. 
        pass
    elif choice == "t":  # ! testing purposes
        clear()
        print("------------------Testing------------------ \n\n")
        if len(online_people) == 0:
            flash_messages.append("No one is online!\n")
            continue
        temp_dict = {}
        counter = 1

        print("Online people: \n")
        for person in online_people:
            print(str(counter) + ". Name: " +
                  str(person[0]) + " IP: " + str(person[1]))
            temp_dict[counter] = person
            counter += 1

        print()
        person_num = input(
            "Select a person by number. \nTo cancel, type 'c' \n")
        while not person_num.isdigit() or int(person_num) > (counter - 1) or int(person_num) < 1:
            if person_num == "c":
                break
            person_num = input("Invalid person number. Please enter again: \n")
        if person_num == "c":
            continue
        person_cho = temp_dict[int(person_num)]
        person_name = person_cho[0]
        person_ip = person_cho[1]
        # todo: Add testing code
        # executor.submit(send_response,person_ip)
        # responser = threading.Thread(target=send_response, args=[
        #                              person_ip], daemon=True)
        # responser.start()


    # elif choice == "5":  # Online people
    #     flash_messages.append(threading.active_count())
clear()
print("Goodbye!")
