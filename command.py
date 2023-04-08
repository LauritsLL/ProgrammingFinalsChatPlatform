import json
import hashlib
import random as r
from rich import print
import rich
import os
import sys

import database_manager as dm
import Table

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
import base64

# STANDARD WHITESPACE ADJUSTMENT FOR PRINT FORMATTING.
DEFAULT_WS_ADJ = 15


class Encryption():
    """Encryption class for handling END-TO-END Encryption between client and database server."""
    def __init__(self) -> None:
        self.private_key = None
        self.public_key = None
        self.device = None
        self.device_folder = "device1"
        if not os.path.exists(self.device_folder):
            os.makedirs(self.device_folder)
    
    def setup_encryption(self, user):
        self.private_key = self.get_privatekey(user)
        if not self.private_key:
            # Generate private key for user-device.
            self.private_key = self.create_privatekey(user)
            self.public_key = self.private_key.public_key()
            # Send pubk to db.
            success = self.send_public_key_to_database(user)
            # No authentication is given per default to new devices.
            return success
        
        else:
            self.public_key = self.private_key.public_key()
            self.get_device() # Set up member variable device.
            if dm.manager.is_device_authenticated(user, self.device):
                return True
            else:
                return False 

    def create_privatekey(self, user):

        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )

        pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        p = os.path.join(os.path.abspath(self.device_folder), str(user.get("id")) + "_private_key.pem")
        with open(p, 'wb') as f:
            f.write(pem)
        
        return private_key

    def get_privatekey(self, user):
        if not self.private_key:
            try:
                p = os.path.join(os.path.abspath(self.device_folder), str(user.get("id")) + "_private_key.pem")
                with open(p, "rb") as key_file:
                    private_key = serialization.load_pem_private_key(
                        key_file.read(),
                        password=None,
                        backend=default_backend()
                    )
                self.private_key=private_key
            except FileNotFoundError:
                return None
                
            
        return self.private_key

    def get_device(self):
        """Get a device object."""
        if not self.device:
            try:
                p = os.path.join(os.path.abspath(self.device_folder), "device_id.txt")
                with open(p, "r") as device_id:
                    device_id=device_id.read()
                    self.device = Table.get("Device", {"device_id": int(device_id)})
                    if not self.device:
                        self.device = dm.manager.generate_device(int(device_id))
            except FileNotFoundError:
                # Generate new device.
                self.device = dm.manager.generate_device()
                # Save new device id to file.
                p = os.path.join(os.path.abspath(self.device_folder), "device_id.txt")
                with open(p, "w") as dfile:
                    dfile.write(str(self.device.get("device_id")))
        
        return self.device

    def send_public_key_to_database(self, user):
        # Send the public key from current user.
        pem = self.public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        #public key decode for the database
        status = dm.manager.create_device_user_relation(pem.decode(), user, self.get_device()) 
        return status

    def read_public_key(self, pem: str):
        public_key = serialization.load_pem_public_key(pem.encode(), default_backend())

        return public_key

    def encrypt_message(self, message, conversation, sender, other_device_user_rel=None):
        message_obj = dm.manager.create_message(sender, conversation)
        if other_device_user_rel:
            deviceuserrel = other_device_user_rel
            for deviceuserrel in deviceuserrel:
                public_key = self.read_public_key(deviceuserrel.get("public_key"))
                
                encrypted = public_key.encrypt(
                    message.encode(),
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )
                
                dm.manager.create_encrypted_message(base64.b64encode(encrypted),message_obj,deviceuserrel.get("id"))
        else:  
            for user in conversation.get("users"):
                deviceuserrel = dm.manager.get_device_user_rel(user)
                for deviceuserrel in deviceuserrel:
                    public_key = self.read_public_key(deviceuserrel.get("public_key"))
                    
                    encrypted = public_key.encrypt(
                        message.encode(),
                        padding.OAEP(
                            mgf=padding.MGF1(algorithm=hashes.SHA256()),
                            algorithm=hashes.SHA256(),
                            label=None
                        )
                    )
                    
                    dm.manager.create_encrypted_message(base64.b64encode(encrypted),message_obj,deviceuserrel.get("id"))
    
    def encrypt_existing_messages_for_other_user(self, encrypted_messages, other_user):
        """Encrypt an existing message with other user's public key."""
        other_user_device_rel = Table.get("DeviceUserRelation", {"user": other_user.get("id"), "device": self.device.get("id")})
        public_key = self.read_public_key(other_user_device_rel.get("public_key"))
        # Re-encrypt messages for new user.
        for emsg in encrypted_messages:
            decrypted = self.decrypt_message(emsg.get("text")) 
            message_obj = Table.get("Message", {"id": emsg.get("message")})

            encrypted = public_key.encrypt(
                decrypted.encode(),
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )

            # Create new entry for other user.
            dm.manager.create_encrypted_message(base64.b64encode(encrypted), message_obj, other_user_device_rel.get("id"))
               
    def decrypt_message(self,encrypted_message):
        if not self.private_key: return

        original_message = self.private_key.decrypt(
            base64.b64decode(encrypted_message),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        return original_message.decode()

class Command():
    def __init__(self):
        self.user = None
        self.opened_conversation=None # UNCONVENTIONAL TABLE WITH ADDITIONAL FIELDS: nickname, user
        self.encryption = Encryption()
        # A Dictionary with the command(s) the user can write as the key and the function it calls as the value.
        self.commands={
            "help":self.help,"startconversation":self.start_conversation,  "openconversation":self.open_conversation,
            "adduser":self.add_user, "logout":self.logout, "sendmessage":self.send_message, "readmessages":self.read_messages,
            "printuser":self.print_user, "sendfriendrequest":self.send_friend_request, "friendrequests":self.friend_requests,
            "friends": self.friends, "makeshortcut":self.make_shortcut,"shortcuts":self.shortcuts,"members":self.members,
            "setnickname":self.set_nickname, "changename":self.change_name,
            "leaveconversation": self.leave_conversation, "shutdown": self.shutdown, "connectilid":self.connect_IL_id,
        }
        try:
            with open("shortcuts.txt", "r") as f:
                self.user_shortcuts=json.loads(f.read())
        except FileNotFoundError:
            self.user_shortcuts={}
    
    def command_format(self, command): return command.replace(" ", "").replace("_", "").lower()
    def shutdown(self): sys.exit(0)

    def list_format(self, l):
        s = ""
        for i in range(len(l)):
            s += l[i] + (" | " if not i+1 == len(l) else "")
        print(s)
    
    def help(self):
        """prints all the commands"""
        print("_ and spaces are ignored. Please proceed.")
        for i,command in enumerate(self.commands.keys()):
            i = (len(str(len(self.commands)-1))-len(str(i)))*"0" + str(i)
            print(str(i)+":",command)
    
    def login(self):
        """Logs in a user."""
        # Get details.
        username=input("Username: ")
        password=input("Password: ")
        salt=dm.manager.getsalt(username)
        if not salt:
            print("Username or password is incorrect")
            return False
        #calls the authenticate function in the database manager
        hashed=hashlib.sha256((password + salt).encode()).hexdigest()
        self.user=dm.manager.authenticate_user(username,hashed)
        if not self.user:
            print("Username or password was incorrect")
            return False 

        return True
    
    def register(self):
        """Registers a new user."""
        # Get details.
        username=input("Username: ")
        firstname=input("First name: ")
        lastname=input("Last name: ")
        password=input("Password: ")
        # Confirm the password
        confirmpassword=input("Password (Confirm): ")
        #check if it's the same
        if confirmpassword==password:
            #create a salt (a 10 digit number )
            salt=str(r.randint(0,10**10))
            #add zeros at the beginning 
            salt="0"*(10-len(salt)) + salt
            hashed=hashlib.sha256((password + salt).encode()).hexdigest()
            #useses the create user function from the database manager 
            self.user=dm.manager.registeruser(username,salt,hashed,firstname,lastname)
            if not self.user:
                print("Username already taken")
                return False 
        else:
            print("Passwords do not match")
            return False

        return True

    def open_conversation(self):
        """opens a conversation by setting the opened_conversation to a giving conversation"""
        #gets the name of the conversation to open
        conversationToOpen=input("Which conversation do you want to open: ")
        if conversationToOpen == "ls":
            conversations = list(dm.manager.get_conversations(self.user))
            for conversation in conversations:
                ucrel = Table.get("UserConversationRelation", {"user": self.user.get("id"), "conversation": conversation.get("id")})
                nickname = ucrel.get("nickname")
                if nickname:
                    print(nickname)
                else:
                    print(conversation.get("name"))
            #call open_conversation again
            self.open_conversation() # TODO: GRIMT ÆNDR!
            return
        elif self.command_format(conversationToOpen) == "info":
            conversations = dm.manager.get_conversations(self.user,get_ids=True)
            #finds the number of spaces need between the name, the nickname and the id
            id_offset=len("nickname")
            nick_offset=len("name")
            for conversation in conversations:
                name_len = len(conversation.get("name"))
                nick_len = len(conversation.get("nickname"))
                if name_len > nick_offset:
                    nick_offset=name_len
                if nick_len > id_offset:
                    id_offset=nick_len

            print("{0: <{nioff}}| {1: <{idoff}}| {2: <{wow}} |".format('name','nickname','id', nioff=nick_offset+1, idoff=id_offset+1, wow=6))
            for conversation in conversations:
                con_id=conversation.get('con_id')
                print("{0: <{nioff}}| {1: <{idoff}}| {2} |".format(conversation.get("name"), conversation.get("nickname"), '#' + '0'*(5-len(str(con_id)))+str(con_id), nioff=nick_offset+1,idoff=id_offset+1))
            #call open_conversation again
            self.open_conversation() # GRIMT ÆNDR!
            return

        if conversationToOpen == "back":
            return
        
        con, status = dm.manager.open_conversation(conversationToOpen,self.user)
        print(status)
        if con != None:
            self.opened_conversation = con

    def send_message(self):
        """if there are a open conversation get a message from the user can add the message to the conversation"""
        #returns if there is no open conversation
        if self.opened_conversation == None:
            print("no conversation opened")
            return
        
        if self.opened_conversation.get("nickname"):
            print(f"Send message in {self.opened_conversation.get('nickname')}")
        else:
            print(f"Send message in {self.opened_conversation.get('name')}")
        #get a message from the user
        message=input("> ")
        #creates a message obj with the user as the sender the opened_conversation as the conversation and a message
        self.encryption.encrypt_message(message, self.opened_conversation, self.user)

    def print_user(self): # DEBUG/TESTING
        print(self.user)

    def read_messages(self):
        """Gets all messages in a conversation and prints it"""
        #return of there are no opened conversation
        if self.opened_conversation == None:
            print("No conversation opened")
            return
        #gets all the messages for the opened_conversation
        messages=dm.manager.get_messages(self.opened_conversation, self.user, self.encryption.get_device())
        #returns if there are no messages and prints no message in this conversation
        if not messages: 
            print("No messages in this conversation")
            return
        
        for msg in messages:
            #foreach
            #if the messages sender is the logged in user - write You:{message} else write {sender}:{message}
            # Sender is converted to a username instead for an id (In DB Manager -> get_messages())
            if msg.get("sender") == "":
                print(f"{self.encryption.decrypt_message(msg.get('text'))}")
            elif msg.get("sender") == self.user.get("username"):
                print(f"You: {self.encryption.decrypt_message(msg.get('text'))}")
            else:
                print(f"{msg.get('sender')}: {self.encryption.decrypt_message(msg.get('text'))}")

    def send_friend_request(self):
        """Creates a friend request obj with the logged in user as the sender and a giving user"""
        username=input("Send to username: ")
        #calls the dm.manager.friend_request from the database manager with the giving username and the user_id
        status = dm.manager.friend_request(username, self.user)
        print(status)

    def friend_requests(self):
        """Gets all the friend request sendt to you then you can either accept or decline them"""
        # Gets all the friend requests
        frequests = dm.manager.get_friend_requests(self.user)
        print("Friend requests found." if frequests else "No friend requests were found. Sad you :( hehe")
        if frequests:
            print("You have a friend request from: ")
            # Prints all the friend requests
            for request in frequests:
                print("From username:", Table.get("User", {"id": request.get("user1")}).get("username"))
            
            fcommands = ["back", "accept", "decline", "help", "declineall", "acceptall"]
            done = False
            while not done:
                pending_fr = dm.manager.get_friend_requests(self.user)
                if not pending_fr:
                    # Done.
                    done = True
                    continue
                t=self.command_format(input("Do you want to accept or decline any (See 'help' for more info)? "))
                if t == "back":
                    done = True
                elif t == "accept":
                    print("Which one do you want to accept? ")
                    user_to_accept=input()
                    for request in frequests:
                        sending_username = Table.get("User", {"id": request.get("user1")}).get("username")
                        if user_to_accept == sending_username:
                            status = dm.manager.accept_friend_request(request)
                            print(status)
                            break
                    else: # Use of else-block in for-loop to detect if it ran without breaking.
                        print("You do not have a friend request from that user.")
                elif t == "decline":
                    print("Which one do you want to decline? ")
                    user_to_decline=input()
                    for request in frequests:
                        sending_username = Table.get("User", {"id": request.get("user1")}).get("username")
                        if user_to_decline == sending_username:
                            status = dm.manager.decline_friend_request(request)
                            print(status)
                            break
                    else: # Use of else-block in for-loop to detect if it ran without breaking.
                        print("You do not have a friend request from that user")
                elif t == "declineall":
                    # Decline all pending friend requests.
                    for request in frequests:
                        status = dm.manager.decline_friend_request(request)
                        print(status)
                    print("No pending friend requests.")
                    done = True
                elif t == "acceptall":
                    # Accept all pending friend requests.
                    for request in frequests:
                        status = dm.manager.accept_friend_request(request)
                        print(status)
                    print("No pending friend requests.")
                    done = True
                elif t == "help":
                    print("Commands here:")
                    for c in fcommands:
                        print(c)

    def start_conversation(self):
        username=input("With username: ")
        status = dm.manager.create_conversation(self.user,username)
        print(status)
    
    def leave_conversation(self):
        if self.opened_conversation:
            validate = input("Are you sure you want to leave this conversation (CANNOT BE UNDONE!)? (y/N) ")
            validate = validate.strip().lower()
            if validate == "y" or validate == "yes":
                # Leaving conversation...
                status = dm.manager.leave_conversation(self.opened_conversation, self.user)
                print(status)
                self.opened_conversation = None
            else:
                # Everything else, "N", "no" or any other invalid input is defaulted to no.
                return
        else:
            print("No conversation has been opened.")

    def add_user(self):
        if self.opened_conversation is None:
            print("No opened conversation")
            return
        
        username=input("Who do you want to add: ")
        for user in self.opened_conversation.get("users"):
            if user.get("username") == username:
                print(f"'{username}' is already in this conversation.")
                break
        else:
            user_added, status = dm.manager.add_user_to_conversation(self.user, self.opened_conversation, username)
            if user_added:
                dur_specific_device = dm.manager.get_device_user_rel(self.user, device_id=self.encryption.device.get("id"))[0] # Returned as list of one object only.
                encrypted_msgs = dm.manager.get_encrypted_messages_current_conversation(dur_specific_device, self.opened_conversation)
                # Re-encrypt messages for new user.
                self.encryption.encrypt_existing_messages_for_other_user(encrypted_msgs,user_added)
            
            print(status)

    def members(self):
        if self.opened_conversation:
            users = self.opened_conversation.get("users")
            usernames = [u.get("username") for u in users]
            # Hide all deleted users from member list.
            for i, u in enumerate(usernames):
                if u == dm.manager.deleted_username:
                    usernames.pop(i)
            print("Users in conversation:")
            self.list_format(usernames)
    
    def set_nickname(self):
        """Set nickname of currently opened convo."""
        if self.opened_conversation:
            # Get new nickname
            new_nickname = input("Enter the new nickname: ")
            status = dm.manager.set_nickname(self.user, self.opened_conversation, new_nickname)
            print(status)
        else:
            print("No conversation have been opened.")

    def change_name(self):
        if self.opened_conversation:
            print(f"What would you like to change the name of '{self.opened_conversation.get('name')}'")
            name=input("> ")
            dm.manager.change_name(name,self.opened_conversation)
        else:
            print("Open a conversation first.")

    def friends(self):
        """List current friends of current user."""
        friends = dm.manager.get_friends(self.user)
        if not friends:
            print("You currently have no friends HA! Sad you :)")
            return
        
        # Acquiring the "other user" in the friend request.
        print(f"Current friends of user '{self.user.get('username')}':")
        names=[]
        for f in friends:
            un=Table.get("User", {"id": f.get("user2")}).get("username")
            if un != self.user.get("username"):
                names.append(un)
            un=Table.get("User", {"id": f.get("user1")}).get("username")    
            if un != self.user.get("username"):
                names.append(un)
        
        self.list_format(names)

    def logout(self):
        self.user=None
        self.opened_conversation=None
        self.encryption = Encryption() # New encryption for new user.
        l = ["logout"]
        for i in self.get_user_obj(): # Check if new user wants to sign in.
            l.append(i)
        return l

    def shortcuts(self):
        s="\n"
        for k,v in self.user_shortcuts.items():
           s+=f"{k}: {v}\n"
        print(s)      

    def make_shortcut(self):
        command = input("Which command do you want to make a shortcut for: ")
        command = self.command_format(command)
        if self.commands.get(command,None) is not None:
            shortcut=input("What do you want the shortcut to be: ")
            self.user_shortcuts[shortcut]=command
            #Save shortcuts in shortcuts fil
            # Save shortcuts.
            # Sejr vil gerne have at shortcuts skal gemmes og lave file calls hver gang. SHAME ON HIM!
            with open('shortcuts.txt', 'w') as f:
                json.dump(self.user_shortcuts,f)

    def authenticated_devices(self, device_user_rels):
        durs = {}
        for i, dur in enumerate(device_user_rels):
            durs[i+1] = dur
            print(i+1, ": AUTHORIZED?", "No" if not dur.get("authenticated") else "Yes")
        
        print("Unauthorized login(s) have been found.")
        print("Please enter one of the labeled numbers into the input below and thereby choose which new devices to authenticate to your user.")
        print("OPTIONS:")
        print("shutdown -> Quit application")
        print("done -> Complete setup on unauthorized devices and grant access")

        to_authenticate=[]
        while True:
            inp=input("> ")
            if inp == "done":
                break
            elif inp == "shutdown":
                sys.exit(0)
            
            if inp and inp.isdigit() and inp != '0':
                for i, dur in durs.items():
                    if i == int(inp):
                        # Check if it has already been added.
                        if not dur in to_authenticate:
                            to_authenticate.append(dur)
                        else:
                            print("Device has already been added")
            else:
                print("Invalid input entered.")

        return to_authenticate
    
    def get_user_obj(self):
        """Get user object."""
        success = True
        while not self.user:
            #while there are no user logged in ask if the want to login or register
            inp=input("Login/Register/Shutdown: ")
            inp = self.command_format(inp)
            
            if inp == "register" or inp == "r":
                success = self.register()
            elif inp == "login" or inp == "l":
                success = self.login()
            elif inp == "shutdown":
                # If they want to shutdown the program.
                sys.exit(0)
            else:
                print("Try again")
        
        encryption_success = self.encryption.setup_encryption(self.user)
        if success and encryption_success:
            dm.manager.get_not_authenticated_users(self.user,self.authenticated_devices)
        
        return success,encryption_success

    def connect_IL_id(self):
        ILid = self.user.get("ILuserid")
        if ILid:
            print("You already have a ILid connected to your account")
            while True:
                answer = input("Do you want to change your ILid [Y/N]>")
                check = self.command_format(answer)
                if check == "n":
                    return
                elif check == "y":
                    break
                else:
                    print("Invalid input.")

        print("Write the IL id from your profile page on itslearning :)")
        answer = int(input("> "))
        print(dm.manager.connect_IL_id(self.user,answer))

    def add_ILobj(self):
        print("admin password")
        password = input("> ")
        if password == "crazylongpassword":
            ilid, isTeacher = None, None
            while not ilid or not isTeacher:
                ilid = input("ILid: ")
                if not ilid.isdigit():
                    print("Invalid input.")
                    ilid = None
                    continue
                isTeacher = input("Are you a teacher? (y/n): ")
                if self.command_format(isTeacher) not in ["y", "n"]:
                    print("Invalid input")
                    isTeacher = None
                    continue
                else:
                    isTeacher = self.command_format(isTeacher)

            dm.manager.create_ILobj(int(ilid), isTeacher=="y")

    def create_class(self):
        print("admin password")
        password = input("> ")
        if password == "crazylongpassword":
            class_name = input("class_name: ")
            dm.manager.create_class(class_name)
            
    def add_to_class(self):
        print("admin password")
        password = input("> ")
        if password == "crazylongpassword":
            while True:
                class_name = input("class_name: ")
                ILid = input("ILid: ")
                print(dm.manager.add_to_class(ILid, class_name))
                if input("do you want to return (y,n) ") == "y":
                    break



commands = Command()
