import json
import hashlib
import random as r

import database_manager as dm
import Table
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

class Encryption():
    """General-purpose class for encryption"""
    def __init__(self) -> None:
        self.private_key = None
        self.public_key = None
        self.device = None

    def setup_encryption(self, user):
        self.private_key = self.get_privatekey(user)
        if not self.private_key:
            # Generate private key for user-device.
            self.private_key = self.create_privatekey(user)
            self.public_key = self.private_key.public_key()
            # Send pubk to db.
            self.send_public_key_to_database(user)
            # No authentication is given per default to new devices.
        else:
            self.public_key = self.private_key.public_key()
            self.get_device() # Set up member variable device.

    def create_privatekey(self, user):
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives.asymmetric import rsa
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )

        from cryptography.hazmat.primitives import serialization

        pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

        with open(f'{user.get("id")}_private_key.pem', 'wb') as f:
            f.write(pem)
        
        return private_key

    def get_privatekey(self, user):
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import serialization
        try:
            with open(f'{user.get("id")}_private_key.pem', "rb") as key_file:
                private_key = serialization.load_pem_private_key(
                    key_file.read(),
                    password=None,
                    backend=default_backend()
                )
            return private_key
        except FileNotFoundError:
            return None

    def get_device(self):
        """Get a device object."""
        if not self.device:
            try:
                with open("device_id.txt", "r") as device_id:
                    self.device = Table.get("Device", {"device_id": int(device_id.read())})
                    if not self.device:
                        self.device = dm.manager.generate_device(int(device_id.read()))
            except FileNotFoundError:
                # Generate new device.
                self.device = dm.manager.generate_device()
                # Save new device id to file.
                with open("device_id.txt", "w") as dfile:
                    dfile.write(str(self.device.get("device_id")))
        print(self.device)
        return self.device

    def send_public_key_to_database(self, user):
        # Send the public key from current user.
        pem = self.public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        status = dm.manager.create_device_user_relation(pem.decode(), user, self.get_device()) 
        print(status)

    def read_public_key(self, public_key):
        print(public_key)
        public_key = serialization.load_pem_public_key(
            public_key,
            backend=default_backend()
        )
        return public_key

    def encrypt_message(self, message, conversation):
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding
        for user in conversation.get("users"):
            message_obj = dm.manager.create_message(user, conversation)
            for dur in dm.manager.get_devices(user):
                print(dur)
                public_key = self.read_public_key(dur.get("public_key"))
                encrypted = public_key.encrypt(
                    message,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )
                dm.manager.create_encrypted_message(encrypted,message_obj,dur.get("device"))    
               
    def decryptmessage(self,encrypted_message,user):
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding

        
        private_key = self.get_privatekey(user)

        original_message = private_key.decrypt(
            encrypted_message,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return original_message


class Command():
    def __init__(self):
        self.user = None
        self.opened_conversation=None
        self.encryption = Encryption()
        # A Dictionary with the command(s) the user can write as the key and the function it calls as the value.
        self.commands={
            "help":self.help,"startconversation":self.start_conversation,  "openconversation":self.open_conversation,
            "adduser":self.add_user, "logout":self.logout, "sendmessage":self.send_message, "readmessages":self.read_messages,
            "printuser":self.print_user, "sendfriendrequest":self.send_friend_request, "friendrequests":self.friend_requests,
            "friends": self.friends, "makeshortcut":self.make_shortcut,"shortcuts":self.shortcuts,"members":self.members,
            "setnickname":self.set_nickname, "changename":self.change_name,
        }
        try:
            with open("shortcuts.txt", "r") as f:
                self.user_shortcuts=json.loads(f.read())
        except FileNotFoundError:
            self.user_shortcuts={}
    
    def command_format(self, command): return command.replace(" ", "").replace("_", "").lower()

    def list_format(self, l):
        s = ""
        for i in range(len(l)):
            s += l[i] + (" | " if not i+1 == len(l) else "")
        print(s)
    
    def help(self):
        """prints all the commands"""
        print("_ and spaces are ignored. Please proceed.")
        for i,command in enumerate(self.commands):
            (len(str(len(self.commands)-1))-len(str(i)))*"0" + str(i)
            print(str(i)+":",command)
    
    def login(self):
        """Logs in a user."""
        # Get details.
        username=input("Username: ")
        password=input("Password: ")
        salt=dm.manager.getsalt(username)
        if not salt:
            print("Username or password is incorrect")
            return
        #calls the authenticate function in the database manager
        hashed=hashlib.sha256((password + salt).encode()).hexdigest()
        self.user=dm.manager.authenticate_user(username,hashed)
        if not self.user:
            print("Username or password was incorrect")
            return
    
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
                return
        else:
            print("Password do not match")
            return

    def open_conversation(self):
        """opens a conversation by setting the opened_conversation to a giving conversation"""
        # print("If multiple conversation with same name are found, the first one in the list will be picked.")
        # print("You can afterwards use 'setnickname' command to change name.") # NOT IMPLEMENTED YET
        #gets the name of the conversation to open
        conversationToOpen=input("Which conversation do you want to open: ")
        if conversationToOpen[0:2] == "ls":
            if conversationToOpen == "ls":
                conversations = list(dm.manager.get_conversations(self.user))
                for conversation in conversations:
                    nickname = conversation.get("nickname")
                    if nickname is not None:
                        print(nickname)
                    else:
                        print(conversation.get("name"))
                #call open_conversation again
                self.open_conversation() # GRIMT ÆNDR!
                return
            elif conversationToOpen.replace(" ","").replace("_","") == "lsids":
                conversations = dm.manager.get_conversations(self.user,get_ids=True)
                print("name   nickname   id")
                for conversation in conversations:
                    con_id=conversation.get('con_id')
                    print(f"{conversation.get('name')}   {conversation.get('nickname')}   #{'0'*(5-len(str(con_id)))}{con_id}")
                #call open_conversation again
                self.open_conversation() # GRIMT ÆNDR!
                return

        if conversationToOpen == "back":
            return
        
        # # Try getting conversation through nickname. (WILL WORK IF CREATING CONVERSATION IS RESTRICTED TO ONE CONVERSATION ONLY WITH ONE USER -
        # # SUCH THAT IT IS ILLEGAL TO FOR EXAMPLE HAVE TWO CONVERSATIONS BETWEEN: l and burak )
        # ucrel = Table.get("UserConversationRelation",{'nickname': conversationToOpen,"user":self.user.get("id")})
        # # Add conversations with the name also to ensure that one conversation with that name OR nickname was found (Else no conversation exist).
        # temp = Table.get("Conversation",{"name":conversationToOpen})
        # ucrel = temp if temp and not ucrel else ucrel

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
        self.encryption.encrypt_message(message, self.opened_conversation)

    def print_user(self): # DEBUG/TESTING
        print(self.user)

    def read_messages(self):
        """Gets all messages in a conversation and prints it"""
        #return of there are no opened conversation
        if self.opened_conversation == None:
            print("No conversation opened")
            return
        #gets all the messages for the opened_conversation
        messages=dm.manager.get_messages(self.opened_conversation, self.encryption.get_device())
        #returns if there are no messages and prints no message in this conversation
        if messages == None: 
            print("No messages in this conversation")
            return
        
        for msg in messages:
            #foreach
            #if the messages sender is the login in user write Me:{message} else write {sender}:{message}
            # Sender is converted to a username instead for an id (In DB Manager -> get_messages())

            if msg.get("sender") == self.user.get("username"):
                print(f"You: {self.encryption.decryptmessage(msg.get('text'),self.user)}")
            else:
                print(f"{msg.get('sender')}: {msg.get('text')}")

    def send_friend_request(self):
        """Creates a friend request obj with the loggedin user as the sender and a giving user"""
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
        dm.manager.create_conversation(self.user,username)

    def add_user(self):
        if self.opened_conversation == None:
            print("No opened conversation")
            return
        

        username=input("Who do you want to add: ")
        for _user in self.opened_conversation.get("users"):
            if _user.get("username") == username:
                print(f"{username} is already in this conversation")
                break
        else:
            status = dm.manager.add_user_to_conversation(self.user, self.opened_conversation, username)
            print(status)

    def members(self):
        if self.opened_conversation:
            users = self.opened_conversation.get("users")
            usernames = [u.get("username") for u in users]
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
            print(f"what would you like to change the name of '{self.opened_conversation.get('name')}'")
            name=input(">")
            dm.manager.change_name(name,self.opened_conversation)
        else:
            print("Open a conversation first")

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
        self.get_user_obj() # Check if new user wants to sign in.

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
            f = open('shortcuts.txt', 'w')
            json.dump(self.user_shortcuts,f)
            f.close()
    
    def get_user_obj(self):
        """Get user object."""
        while not self.user:
            #while there are no user loggedin ask if the want to login or register
            inp=input("Login/Register/Shutdown: ")
            inp = self.command_format(inp)
        
            if inp == "register" or inp == "r":
                self.register()
            elif inp == "login" or inp == "l":
                self.login()
            elif inp == "shutdown":
                #if they want to shutdown the program.
                return False
            else:
                print("Try again")
        
        self.encryption.setup_encryption(self.user)
        return True

commands = Command()
