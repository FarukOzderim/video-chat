import socket
import threading
from concurrent.futures import ThreadPoolExecutor
from os import system, name, path, walk, mkdir, remove, kill
import signal
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


def enter_group(groupname, flash_messages):  # Enter a group
    sync_groups()
    if not isAlphaNumeric(groupname):
        flash_messages.append(
            "EnterGroup: The groupname you entered is not alphanumeric.")
    if groupname not in groups:
        f = open("groups/" + groupname, "w+")
        f.close()
        flash_messages.append("EnterGroup: Entered group " + groupname)
    else:
        flash_messages.append("EnterGroup: You are already in this group")


def leave_group(groupname, flash_messages):  # Leave a group
    sync_groups()
    if not isAlphaNumeric(groupname):
        flash_messages.append(
            "LeaveGroup: The groupname you entered is not alphanumeric.")
        return
    if groupname not in groups:
        flash_messages.append("LeaveGroup: You are not in that group.")
    else:
        flash_messages.append("LeaveGroup: You left group " + groupname)
        remove("groups/" + groupname)


def print_groups(flash_messages):
    if flash_messages != None:
        if len(groups) != 0:
            groups_string = ", ".join(groups)
            flash_messages.append(
                "Groups: You are in these groups: " + groups_string + "\n")
        else:
            flash_messages.append("Groups: You are not in any group")
    else:
        if len(groups) != 0:
            groups_string = ", ".join(groups)
            print("Groups: You are in these groups: " + groups_string + "\n")
        else:
            print("Groups: You are not in any group")


def isAlphaNumeric(word):
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
            print("Creation of the directory 'groups' failed")
            time.sleep(2)
        else:
            print("Successfully created the directory 'groups'")
            time.sleep(2)
    elif groups_isdir:
        for (root, dirs, files) in walk("groups"):
            for filename in files:
                if filename == "c":  # Do not allow a group called 'c' as it is used as cancel character.
                    files.remove(filename)
            groups = list(filter(isAlphaNumeric, files))

    else:
        try:
            mkdir("groups")
        except OSError:
            print("Creation of the directory 'groups' failed")
            time.sleep(2)
        else:
            print("Successfully created the directory 'groups'")
            time.sleep(2)


def add_new_people(name, ip):
    
    found = False
    for people in online_people:
        if people[1] == ip:
            found = True
            # print("Found ", people, "to have ip ",ip)
            if people[0] != name:
                online_people.remove(people)
                online_people.add((name, ip))
                subprocess.run(
                ["notify-send", "User with ip " + ip  +  " changed his name new name is " + name])

    if not found and (name, ip) != (username, userip):
        subprocess.run(
            ["notify-send", "New person online: " + name + ", Ip: " + ip])
        online_people.add((name, ip))


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


def send_announce_packet_once(announce_socket):
    try:
        announce_socket.sendto(("[" + str(username) + ", " + str(userip) + ", announce]").encode(
            "utf-8", errors="replace"), ('<broadcast>', 12345))
    except Exception as e:
        print("An error occured when broadcasting", e)
        time.sleep(1)


def send_response(ip):
    # print("Send response to",ip)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as response_s:
        try:
            response_s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            response_s.connect((ip, 12345))
            response_s.sendall(("[" + str(username) + ", " + str(userip) +
                                ", response]").encode("utf-8", errors="replace"))
            response_s.shutdown(socket.SHUT_RDWR)
        except Exception as e:
            print("An error occured when responding to an announce message", e)
            time.sleep(1)


def send_message(ip, payload):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as message_s:
        try:
            message_s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            message_s.connect((ip, 12345))
            message_s.sendall(
                ("[" + str(username) + ", " + str(userip) + ", message, " + str(payload) + "]").encode("utf-8", errors="replace"))
            message_s.shutdown(socket.SHUT_RDWR)
        except Exception as e:
            print("An error occured when message is sending", e)
            time.sleep(1)


def send_call(ip):  # Call request
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as call_s:
        try:
            call_s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            call_s.connect((ip, 12345))
            call_s.sendall(
                ("[" + str(username) + ", " + str(userip) + ", call]").encode("utf-8", errors="replace"))
            call_s.shutdown(socket.SHUT_RDWR)
        except Exception as e:
            print("An error occured when sending call message", e)
            time.sleep(1)


def send_accept_call(ip):  # Ok to call request, sent after getting a call
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as accept_call_s:
        try:
            accept_call_s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            accept_call_s.connect((ip, 12345))
            accept_call_s.sendall(
                ("[" + str(username) + ", " + str(userip) + ", acceptcall]").encode("utf-8", errors="replace"))
            accept_call_s.shutdown(socket.SHUT_RDWR)
        except Exception as e:
            print("An error occured when sending accept call message", e)
            time.sleep(1)


def send_start_call(ip):  # Starting response, sent after call is accepted by other party
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as start_call_s:
        try:
            start_call_s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            start_call_s.connect((ip, 12345))
            start_call_s.sendall(
                ("[" + str(username) + ", " + str(userip) + ", startcall]").encode("utf-8", errors="replace"))
            start_call_s.shutdown(socket.SHUT_RDWR)
        except Exception as e:
            print("An error occured when sending start call message", e)
            time.sleep(1)


def send_cancel_call(ip):  # Starting response, sent after call is accepted by other party
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as cancel_call_s:
        try:
            cancel_call_s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            cancel_call_s.connect((ip, 12345))
            cancel_call_s.sendall(
                ("[" + str(username) + ", " + str(userip) + ", cancelcall]").encode("utf-8", errors="replace"))
            cancel_call_s.shutdown(socket.SHUT_RDWR)
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


def send_allgroups_req_packet_once(allgroups_socket):
    try:
        allgroups_socket.sendto(("[" + str(username) + ", " + str(userip) + ", allgroups]").encode(
            "utf-8", errors="replace"), ('<broadcast>', 12345))
    except Exception as e:
        print("An error occured when broadcasting all groups request", e)
        time.sleep(1)


def send_my_groups_to(ip, groups):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as mygroups_s:
        try:
            mygroups_s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            mygroups_s.connect((ip, 12345))
            if len(groups) == 0:
                mygroups_s.sendall(
                    ("[" + str(username) + ", " + str(userip) + ", mygroups]").encode("utf-8", errors="replace"))
            else:
                mygroups_string = ", ".join(groups)
                mygroups_s.sendall(
                    ("[" + str(username) + ", " + str(userip) + ", mygroups, " + mygroups_string + "]").encode("utf-8", errors="replace"))
            mygroups_s.shutdown(socket.SHUT_RDWR)
        except Exception as e:
            print("An error occured when sending my groups", e)
            time.sleep(1)


def process_messages(data):
    decoded = data.decode("utf-8", errors="replace")
    # print(decoded)
    if decoded[0] == "[" and decoded[-1] == "]":
        decoded_striped = str(decoded[1:-1])  # Strip out square parantheses.
        decoded_splitted = decoded_striped.split(",")
        if len(decoded_splitted) < 3:
            print("Got an invalid message " + str(decode))
            return
        message_type = decoded_splitted[2].strip(' ')
        if message_type == 'announce':
            name = decoded_splitted[0].strip(' ')
            ip = decoded_splitted[1].strip(' ')
            add_new_people(name, ip)
            if ip != userip:
                executor.submit(send_response, ip)
        elif message_type == 'response':
            name = decoded_splitted[0].strip(' ')
            ip = decoded_splitted[1].strip(' ')
            add_new_people(name, ip)
        elif message_type == 'call':
            name = decoded_splitted[0].strip(' ')
            ip = decoded_splitted[1].strip(' ')
            subprocess.run(["notify-send", "New call from" +
                            name + ".\n" + "To accept, go to calls."])
            if (name, ip) not in calls:
                calls.append((name, ip))
        elif message_type == 'acceptcall':
            name = decoded_splitted[0].strip(' ')
            ip = decoded_splitted[1].strip(' ')
            print("Call accepted by", name, "starting video chat...")
            send_start_call(ip)
            start_video_chat(ip)
        elif message_type == 'startcall':
            global start_call_in_three_seconds
            name = decoded_splitted[0].strip(' ')
            ip = decoded_splitted[1].strip(' ')
            if ip == accepted_call_ip:
                start_call_in_three_seconds = True
        elif message_type == "cancelcall":
            name = decoded_splitted[0].strip(' ')
            ip = decoded_splitted[1].strip(' ')
            subprocess.run(
                ["notify-send", name + " canceled a call."], shellss)
            try:
                calls.remove((name, ip))
            except ValueError:
                pass
        elif message_type == "allgroups":
            ip = decoded_splitted[1].strip(' ')
            if ip != userip:
                sync_groups()
                send_my_groups_to(ip, groups)
        elif message_type == "mygroups":
            name = decoded_splitted[0].strip(' ')
            ip = decoded_splitted[1].strip(' ')
            for i in range(3, len(decoded_splitted)):
                group = decoded_splitted[i].strip(' ')
                all_groups.add(group)
        elif message_type == "announce_videochat_enter":
            name = decoded_splitted[0].strip(' ')
            ip = decoded_splitted[1].strip(' ')
            groupname = decoded_splitted[3].strip(' ')
            if active_video_chat_group == groupname and (name,ip) not in active_video_chat_attendees and ip != userip:
                active_video_chat_attendees.append((name, ip))
                render_video_chat(name, ip)
                send_attendence_response_to_videochat_request(ip, groupname)
        elif message_type == "announce_videochat_leave":
            name = decoded_splitted[0].strip(' ')
            ip = decoded_splitted[1].strip(' ')
            groupname = decoded_splitted[3].strip(' ')
            if active_video_chat_group == groupname and (name, ip) in active_video_chat_attendees:
                active_video_chat_attendees.remove((name, ip))
                subprocess.run(["notify-send", name + " leaved the video chat."])
                if (name, ip) in active_video_chat_attendee_processes:
                    processes = active_video_chat_attendee_processes[(
                        name, ip)]
                    for process in processes:
                        os.kill(process, signal.SIGKILL)
                    del active_video_chat_attendee_processes[(name, ip)]
        elif message_type == "response_videochat_enter":
            name = decoded_splitted[0].strip(' ')
            ip = decoded_splitted[1].strip(' ')
            groupname = decoded_splitted[3].strip(' ')
            if active_video_chat_group != "" and call_started and groupname == active_video_chat_group and (name, ip) not in active_video_chat_attendees:
                active_video_chat_attendees.append((name, ip))
                render_video_chat(name, ip)
        elif message_type == 'message':
            if len(decoded_splitted) < 4:
                print("Got an invalid message " + str(decode))
                return
            name = decoded_splitted[0].strip(' ')
            ip = decoded_splitted[1].strip(' ')
            message = decoded_splitted[3].strip(' ')

            subprocess.run(
                ["notify-send", "New message from " + name + ", Message: " + message])
            # print(str(name) + ": " + str(message))
            if (name, ip) in messages:
                messages[(name, ip)].append(message)
            else:
                messages[(name, ip)] = [message]
            add_new_people((name, ip))
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
        ["bash", "streamVideo.sh", own_ip, "40000"], stdout=subprocess.PIPE)
    outs, errs = streamVideoProcess.communicate()
    streamVideoProcessPid = int(outs.decode())

    streamAudioProcess = subprocess.Popen(
        ["bash", "streamAudio.sh", own_ip, "50000"], stdout=subprocess.PIPE)
    outs, errs = streamAudioProcess.communicate()
    streamAudioProcessPid = int(outs.decode())

    renderOwnVideoProcess = subprocess.Popen(
        ["bash", "renderVideo.sh", own_ip, "40000"], stdout=subprocess.PIPE)
    outs, errs = renderOwnVideoProcess.communicate()
    renderOwnVideoProcessPid = int(outs.decode())

    renderVideoProcess = subprocess.Popen(
        ["bash", "renderVideo.sh", friend_ip, "40000"], stdout=subprocess.PIPE)
    outs, errs = renderVideoProcess.communicate()
    renderVideoProcessPid = int(outs.decode())

    renderAudioProcess = subprocess.Popen(
        ["bash", "renderAudio.sh", friend_ip, "50000"], stdout=subprocess.PIPE)
    outs, errs = renderAudioProcess.communicate()
    renderAudioProcessPid = int(outs.decode())

    print("Video chat started...")

    inp = input("Press c to close video chat")
    while inp != "c":
        inp = input("Press c to close video chat")

    print("Closing")
    call_started = False
    try:
        print(streamVideoProcessPid,streamAudioProcessPid,renderOwnVideoProcessPid,renderVideoProcessPid,renderAudioProcessPid)
        os.kill(streamVideoProcessPid, signal.SIGTERM)
        os.kill(streamAudioProcessPid, signal.SIGTERM)
        os.kill(renderOwnVideoProcessPid, signal.SIGTERM)
        os.kill(renderVideoProcessPid, signal.SIGTERM)
        os.kill(renderAudioProcessPid, signal.SIGTERM)
    except Exception as e:
        print(e)
    # Kill gstreamer processes
    
    print("Done closing")
    # streamVideoProcess.kill()
    # streamAudioProcess.kill()
    # renderOwnVideoProcess.kill()
    # renderVideoProcess.kill()
    # renderAudioProcess.kill()
    # subprocess.run(["killall", "-9", "gst-launch-1.0"],
    #                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def render_video_chat(name, ip): # Render other group members' video audio and add to attendees object 
    global active_video_chat_attendee_processes
    person_ip_splitted = ip.split(".")
    friend_ip = "234." + str(person_ip_splitted[1]) + "." + str(
        person_ip_splitted[2]) + "." + str(person_ip_splitted[3])

    renderVideoProcess = subprocess.Popen(
        ["bash", "renderVideo.sh", friend_ip, "40000"], stdout=subprocess.PIPE)
    outs, errs = renderVideoProcess.communicate()
    renderVideoProcessPid = int(outs.decode())

    renderAudioProcess = subprocess.Popen(
        ["bash", "renderAudio.sh", friend_ip, "50000"], stdout=subprocess.PIPE)
    outs, errs = renderAudioProcess.communicate()
    renderAudioProcessPid = int(outs.decode())

    if (name, ip) not in active_video_chat_attendee_processes:
        active_video_chat_attendee_processes[(name, ip)] = [
            renderVideoProcessPid, renderAudioProcessPid]


def send_group_videochat_start(groupname):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as groupchatstart_s:
        groupchatstart_s.settimeout(0.2)
        groupchatstart_s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        groupchatstart_s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        send_group_videostart_packet_once(groupchatstart_s, groupname)
        time.sleep(1)
        send_group_videostart_packet_once(groupchatstart_s, groupname)
        time.sleep(1)
        send_group_videostart_packet_once(groupchatstart_s, groupname)


def send_group_videostart_packet_once(groupchatstart_s, groupname):
    try:
        groupchatstart_s.sendto(("[" + str(username) + ", " + str(userip) + ", announce_videochat_enter, " + str(groupname) + "]").encode(
            "utf-8", errors="replace"), ('<broadcast>', 12345))
    except Exception as e:
        print("An error occured when broadcasting video start message", e)
        time.sleep(1)


def send_group_video_chat_leave(groupname):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as groupchatleave_s:
        groupchatleave_s.settimeout(0.2)
        groupchatleave_s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        groupchatleave_s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        send_group_videostart_packet_once(groupchatleave_s, groupname)
        time.sleep(1)
        send_group_videostart_packet_once(groupchatleave_s, groupname)
        time.sleep(1)
        send_group_videostart_packet_once(groupchatleave_s, groupname)


def send_group_video_chat_leave_packet_once(groupchatleave_s, groupname):
    try:
        groupchatleave_s.sendto(("[" + str(username) + ", " + str(userip) + ", announce_videochat_leave, " + str(groupname) + "]").encode(
            "utf-8", errors="replace"), ('<broadcast>', 12345))
    except Exception as e:
        print("An error occured when broadcasting video start message", e)
        time.sleep(1)


def start_group_video_chat(groupname, flash_messages):
    global active_video_chat_attendees, active_video_chat_group, call_started
    if groupname not in groups:
        print("GroupChat: You are not in group", groupname)
        sync_groups()
        print_groups(None)
        return False
    call_started = True
    active_video_chat_attendees = []
    active_video_chat_group = groupname
    executor.submit(render_my_own_video_and_audio, flash_messages)
    send_group_videochat_start(groupname)
    return True


def render_my_own_video_and_audio(flash_messages):
    global active_video_chat_attendees, active_video_chat_attendee_processes, active_video_chat_group, call_started
    call_started = True
    
    user_ip_splitted = userip.split(".")

    own_ip = "234." + str(user_ip_splitted[1]) + "." + str(
        user_ip_splitted[2]) + "." + str(user_ip_splitted[3])

    streamVideoProcess = subprocess.Popen(
        ["bash", "streamVideo.sh", own_ip, "40000"], stdout=subprocess.PIPE)
    outs, errs = streamVideoProcess.communicate()
    streamVideoProcessPid = int(outs.decode())

    streamAudioProcess = subprocess.Popen(
        ["bash", "streamAudio.sh", own_ip, "50000"], stdout=subprocess.PIPE)
    outs, errs = streamAudioProcess.communicate()
    streamAudioProcessPid = int(outs.decode())
    
    renderOwnVideoProcess = subprocess.Popen(
        ["bash", "renderVideo.sh", own_ip, "40000"], stdout=subprocess.PIPE)
    outs, errs = renderOwnVideoProcess.communicate()
    renderOwnVideoProcessPid = int(outs.decode())


    flash_messages.append("Group video chat started...")

    inp = input("Press c to close video chat\n")
    # print("Input is ",inp)
    while inp != "c":
        inp = input("Press c to close video chat\n")
    print("Closing group chat")
    try:
        send_group_video_chat_leave(active_video_chat_group)
        call_started = False
        kill(streamVideoProcessPid, signal.SIGKILL)
        kill(streamAudioProcessPid, signal.SIGKILL)
        kill(renderOwnVideoProcessPid, signal.SIGKILL)
        for user_entry in active_video_chat_attendee_processes:
            processes = active_video_chat_attendee_processes[user_entry]
            for pid in processes:
                print("Killing",pid)
                kill(pid, signal.SIGKILL)
        active_video_chat_attendees = []
        active_video_chat_group = ""
        active_video_chat_attendee_processes = {}
    except Exception as e:
        print(e)
    print("Done closing")


def send_attendence_response_to_videochat_request(ip, groupname):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as send_attendence_groupchat_s:
        try:
            send_attendence_groupchat_s.setsockopt(
                socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            send_attendence_groupchat_s.connect((ip, 12345))
            send_attendence_groupchat_s.sendall(
                ("[" + str(username) + ", " + str(userip) + ", response_videochat_enter, " + str(groupname) + "]").encode("utf-8", errors="replace"))
            send_attendence_groupchat_s.shutdown(socket.SHUT_RDWR)
        except Exception as e:
            print(
                "An error occured when sending videochat attendence info to someoone", e)
            time.sleep(1)


def cleanup():
    subprocess.run(["killall", "-9", "gst-launch-1.0"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

#!Main
messages = {}
sent_messages = {}


calls = []
start_call_in_three_seconds = False
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

all_groups = set()
groups = []
active_video_chat_group = ""
active_video_chat_attendees = []
active_video_chat_attendee_processes = {}

sync_groups()

atexit.register(cleanup)

clear()
choice = None
flash_messages = ["Welcome to the transporter app. Have fun! \n"]
while choice != "q":
    clear()
    print(transporterLogo)
    if call_started:
        if active_video_chat_group != "":
            print("You are in video chat in group", active_video_chat_group)
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
        if call_started:
            flash_messages.append("First, end your ongoing video chat.")
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
        if call_started:
            flash_messages.append("First, end your ongoing video chat.")
            continue
        will_be_called_person = calls[int(person_num)-1]
        try:
            calls.remove(will_be_called_person)
        except ValueError:
            pass
        start_call_in_three_seconds = False
        accepted_call_ip = will_be_called_person[1]
        send_accept_call(will_be_called_person[1])  # ip
        time.sleep(3)
        if start_call_in_three_seconds:
            print("Video call starting... ")
            executor.submit(start_video_chat, will_be_called_person[1])
        else:
            flash_messages.append("No respond from other side in 3 seconds.")
    elif choice == "6":  # Manage Groups
        clear()
        print("------------------Manage Groups------------------ \n\n")
        sync_groups()
        print_groups(flash_messages)
        flash_messages = []
        while True:
            clear()
            for message in flash_messages:
                print(message)
            flash_messages.clear()
            print_group_manage_options()
            gchoice = input("Choose an action: \n")
            if gchoice == "c":
                break
            if gchoice == "1":  # List of all groups
                print("Syncing groups please wait 5 seconds..")
                all_groups.clear()
                send_allgroups_request()
                time.sleep(5)
                sync_groups()
                for group in groups:
                    all_groups.add(group)
                if len(all_groups) == 0:
                    flash_messages.append("No groups found")
                else:
                    all_groups_string = ", ".join(all_groups)
                    flash_messages.append("All groups: " + all_groups_string)
            elif gchoice == "2":  # List of groups I attended
                sync_groups()
                print_groups(flash_messages)
            elif gchoice == "3":  # Enter a group
                sync_groups()
                print_groups(flash_messages)
                groupname = input(
                    "Enter group name to enter. Remember that only alphanumeric groups are accepted. To cancel type 'c'\n")
                if groupname == "c":
                    continue
                enter_group(groupname, flash_messages)
            elif gchoice == "4":  # Leave a group
                sync_groups()
                print_groups(flash_messages)
                groupname = input(
                    "Enter group name to leave. Remember that only alphanumeric groups are accepted. To cancel type 'c'\n")
                if groupname == "c":
                    continue
                leave_group(groupname, flash_messages)
    elif choice == "7":  # todo Send message to a group
        pass
    elif choice == "8":  # Attend video chat in a group
        clear()
        print("------------------Attend Group Video Chat------------------ \n\n")
        if call_started:
            flash_messages.append("First, end your ongoing video chat.")
            continue
        sync_groups()
        print_groups(None)
        group = input("Enter a group name. To cancel type 'c'.\n")
        if group == "c":
            continue
        while not start_group_video_chat(group, flash_messages):
            group = input("Enter a group name. To cancel type 'c'.\n")
            if group == "c":
                break
    elif choice == "9":  # todo See group video chats going on.
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