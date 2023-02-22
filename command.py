import Table
import json

import database_manager as dm



class Command():
    def __init__(self):
        self.user = None
        self.opened_conversation=None
        self.commands={
            "help":self.help,"startconversation":self.start_conversation,  "openconversation":self.open_conversation,
            "adduser":self.add_user, "logout":self.logout, "sendmessage":self.send_message, "readmessages":self.read_messages,"printuser":self.print_user, 
            "sendfriendrequest":self.send_friend_request, "friendrequests":self.friend_requests,"makeshortcut":self.make_shortcut,
            "shortcuts":self.shortcuts,"members":self.members,
        }
        try:
            with open("shortcuts.txt", "r") as f:
                self.shortcuts=json.loads(f.read())
        except FileNotFoundError:
            self.shortcuts={}
        

    
    def command_format(self, command): return command.replace(" ", "").replace("_", "").lower()

    def help(self):
        """prints all the commands"""
        print("_ and spaces are ignored")
        for i,command in enumerate(self.commands):
            (len(str(len(self.commands)-1))-len(str(i)))*"0" + str(i)
            print(str(i)+":",command)

    def open_conversation(self):
        """opens a conversation by setting the opened_conversation to a giving conversation"""
        #gets the name of the conversation to open
        conversationToOpen=input("Which conversation do you want to open: ")
        if conversationToOpen=="ls":
            #if the user wrote ls print all the names of the conversations
            #gets all userconversation realtion for the login user
            conversation=Table.get("UserConversationRelation",{'user':self.user.get("id")},filtered=True)
            for userconversation in conversation:
                #foreach user check if the nickname is equal to ""
                if userconversation.get("nickname") == "":
                    #if it is get the name of the of conversation and print it
                    print("Name:",Table.get("Conversation",{'id': userconversation.get("id")}).get("name"))
                else:
                    #else print the nickname
                    print("Name:",userconversation.get("nickname"))
            #call open_conversation again
            self.open_conversation() # GRIMT ÆNDR!
            return

        if conversationToOpen == "back":
            return
        
        ucrel = Table.get("UserConversationRelation",{'nickname': conversationToOpen,"user":self.user.get("id")},filtered=True)
        conversations = Table.get("Conversation",{"name":conversationToOpen},filtered=True)
        for conversation in conversations:
            ucrel.append(Table.get("UserConversationRelation",{"conversation":conversation.get("id"),"user":self.user.get("id")}))
        
        if len(ucrel) > 1:
            print("More than one conversation with that name")
        elif len(ucrel) != 0:
            ucrel=ucrel[0] # Will only be 1 element, always
            conversation=Table.get("Conversation",{'id': ucrel.get("conversation")})
            print("UC:",ucrel,"|","CONV:",conversation)
            self.opened_conversation=Table.Table("Conversation",{"id":conversation.get("id"),"nickname":ucrel.get("nickname"),"name":conversation.get("name")},commit=False)
            if conversation.get("class") is None:
                userconversationrelations = Table.get("UserConversationRelation",{'conversation':conversation.get("id")},filtered=True)
                users=[]
                for userconversationrelation in userconversationrelations:
                    _user=Table.get("User",{"id":userconversationrelation.get("user")})
                    users.append(_user)
                self.opened_conversation.set("users", users, commit=False)
                print("OPENED CONVERS:",self.opened_conversation)
            else:
                #this is a class do something
                pass


        else:
            print("conversation not found")
            self.open_conversation()
            return

    def send_message(self):
        """if there are a open conversation get a message from the user can add the message to the conversation"""
        print(self.opened_conversation)
        #returns if there is no open conversation
        if self.opened_conversation == None:
            print("no conversation opened")
            return
        
        print(f"Send message in {self.opened_conversation.get('nickname')}")
        #get a message from the user
        message=input("> ")
        #creates a message obj with the user as the sender the opened_conversation as the conversation and a message
        dm.manager.create_message(self.user, self.opened_conversation, message)

    def print_user(self):
        print(self.user)

    def read_messages(self):
        """gets all messages in a conversation and prints it"""
        #return of there are no opened conversation
        if self.opened_conversation == None:
            print("no conversation opened")
            return
        #gets all the messages for the opened_conversation
        messages=dm.manager.get_messages(self.opened_conversation)
        #returns if there are no messages and prints no message in this conversation
        if messages == None: 
            print("no messages in this conversation")
            return
        
        for msg in messages:
            #foreach
            #if the messages sender is the login in user write Me:{message} else write {sender}:{message}
            # Sender is converted to a username instead for an id (In DB Manager -> get_messages())
            if msg.get("sender") == self.user.get("username"):
                print(f"You: {msg.get('text')}")
            else:
                print(f"{msg.get('sender')}: {msg.get('text')}")

    def send_friend_request(self):
        """Creates a friend request obj with the loggedin user as the sender and a giving user"""
        username=input("username: ")
        #calls the dm.manager.friend_request from the database manager with the giving username and the user_id
        result = dm.manager.friend_request(username, self.user["id"])
        print(result)

    def friend_requests(self):
        """Gets all the friend request sendt to you then you can either accept or decline them"""
        #gets all the friend requests
        requests = dm.manager.get_friend_requests(self.user["id"])
        print("You have a friend request from: ")
        #prints all the friend requests
        for request in requests:
            print(request["sender"][1])

        print("Do you want to accept or decline any or do you want to return")
        while True:
            t=input("").lower()
            if t == "return":
                return
            elif t == "accept":
                print("Which one do you want to accept")
                _user=input("")
                for request in requests:
                    if _user == request["sender"][1]:
                        dm.manager.accept_friend_request(request)
                        break
                else:
                    print("You do no have a friend request from that user")
            elif t == "decline":
                print("Which one do you want to decline")
                _user=input("")

    def start_conversation(self):
        username=input("username: ")
        dm.manager.create_conversation(self.user,username)

    def add_user(self):
        if self.opened_conversation == None:
            print("no opened conversation")
            return
        
        username=input("Who do you want to add: ")
        print(self.opened_conversation)
        for _user in self.opened_conversation.get("users"):
            print(_user)
            if _user.get("username") == username:
                print(f"{username} is already in this conversation")
                break
        else:
            dm.manager.add_user_to_conversation(self.opened_conversation, username)

    def members(self):
        if self.opened_conversation:
            users = self.opened_conversation.get("users")
            usernames = [u.get("username") for u in users]
            print("Users in conversation:",(n + " | " for n in usernames))

    def logout(self):
        self.user=None
        self.opened_conversation=None

    def shortcuts(self):
        s="\n"
        for k,v in self.shortcuts.items():
           s+=f"{k}: {v}\n"
        print(s)      

    def make_shortcut(self):
        command = input("Which command do you want to make a shortcut for: ")
        command = self.command_format(command)
        if self.commands.get(command,None) is not None:
            shortcut=input("What do you want the shortcut to be: ")
            self.shortcuts[shortcut]=command
            #Save shortcuts in shortcuts fil
            # Save shortcuts.
            # Sejr vil gerne have at shortcuts skal gemmes og lave file calls hver gang. SHAME ON HIM!
            f = open('shortcuts.txt', 'w')
            json.dump(self.shortcuts,f)
            f.close()

commands = Command()