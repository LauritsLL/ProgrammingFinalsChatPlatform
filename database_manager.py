import mysql.connector
from mysql.connector import Error
import Table
import random as r
import sys

from DbLog import DbLog

WRITE_LOG = True
DEBUG_PRINT = False

class DbManager(DbLog):
    def __init__(self):
        super(DbManager, self).__init__()
        self.host_name="localhost"
        self.username="root"
        self.user_password=""
        self.db_name="chatplatform"

        self.write_to_file = WRITE_LOG
        self.debug_print = DEBUG_PRINT
        self.deleted_user = None # Table containing the "Deleted user" table for use when conserving old messages from a user that leaves
        self.deleted_username = "<deleted_user>"
    
    def get_or_create_deleted_user_obj(self):
        """Get the throw-away object for deleted and leaving users."""
        if not Table.get("User", {"username": "<deleted_user>"}):
            # Set up "Deleted user" throw-away table.
            self.deleted_user = Table.Table("User", {"username": self.deleted_username, "firstname": "<Deleted>", "lastname": "<Deleted>", "salt": 0000000000, "password": "PrUaYZS1j1lJIWjJIQHIbFh9I3I8r9tLEKMnMDPqXwZKRsvQT2vrCLd9y27t7s5EmDO0BvUx4SizhPXLh8WFMODvqxQpaRObcXFcwEq2Adq28llrLhAtW64JTQTK8V294bL08yZTid2fE2kkGr5lHcZoPXX8bQFcNjKYbQ9dvNuMtNzLNnpUEqFjf8Ofu6O7hDQ9BAAaS9dZoAYE71mJ75p6v0stDjcE1PQMtRBWux0mvh1AnnYR8Jlb1FX4TJQJ"})
        else:
            # Get the existing throw-away object.
            self.deleted_user = Table.get("User", {"username": self.deleted_username})

    def list_format(self, l):
        s = ""
        for i in range(len(l)):
            s += l[i] + (" | " if not i+1 == len(l) else "")
        self.log(s)

    def setup(self):
        # Create database if it doesn't already exists.
        cmd = f"""
        CREATE DATABASE IF NOT EXISTS `{self.db_name}`;
        """
        self.execute_query(cmd)
        
        
        tables={}
        
        tables["IdsTable"] = """
        CREATE TABLE IF NOT EXISTS Ids (
            id INT NOT NULL AUTO_INCREMENT,
            Teacher_next_id INT NOT NULL DEFAULT 1,
            ILUser_next_id INT NOT NULL DEFAULT 1,
            User_next_id INT NOT NULL DEFAULT 1,
            Friends_next_id INT NOT NULL DEFAULT 1,
            Class_next_id INT NOT NULL DEFAULT 1,
            Conversation_next_id INT NOT NULL DEFAULT 1,
            TeacherConversationRelation_next_id INT NOT NULL DEFAULT 1,
            Message_next_id INT NOT NULL DEFAULT 1,
            Device_next_id INT NOT NULL DEFAULT 1,
            DeviceUserRelation_next_id INT NOT NULL DEFAULT 1,
            EncryptedDeviceMessageRelation_next_id INT NOT NULL DEFAULT 1,
            UserConversationRelation_next_id INT NOT NULL DEFAULT 1,
            ClassILAttributesRelation_next_id INT NOT NULL DEFAULT 1,
            PRIMARY KEY (id)
        ) ENGINE = InnoDB
        """

        tables["Teachertable"]= """
        CREATE TABLE IF NOT EXISTS Teacher ( 
            id INT NOT NULL,
            PRIMARY KEY (id)
        ) ENGINE = InnoDB
        """

        tables["ILUsertable"]= """
        CREATE TABLE IF NOT EXISTS ILUser ( 
            id INT NOT NULL,
            itslearningid VARCHAR(32) NOT NULL,
            isTeacher INT,
            PRIMARY KEY (id),
            FOREIGN KEY (isTeacher) REFERENCES Teacher(id)
        ) ENGINE = InnoDB
        """
        
        tables["Usertable"]= """
        CREATE TABLE IF NOT EXISTS User ( 
            id INT NOT NULL,
            username VARCHAR(32) NOT NULL UNIQUE,
            firstname VARCHAR(32) NOT NULL,
            lastname VARCHAR(64) NOT NULL,
            salt VARCHAR(10) NOT NULL,
            password VARCHAR(256) NOT NULL,
            admin BOOL NOT NULL,
            ILuserid INT,
            PRIMARY KEY (id),
            FOREIGN KEY (ILuserid) REFERENCES ILUser(id)
        ) ENGINE = InnoDB
        """

        tables["Friendstable"]= """
        CREATE TABLE IF NOT EXISTS Friends ( 
            id INT NOT NULL,
            user1 INT  NOT NULL,
            user2 INT  NOT NULL,
            in_process BOOL NOT NULL,
            PRIMARY KEY (id),
            FOREIGN KEY (user1) REFERENCES User(id),
            FOREIGN KEY (user1) REFERENCES User(id)
        ) ENGINE = InnoDB
        """

        tables["Classtable"] = """
        CREATE TABLE IF NOT EXISTS Class (
            id INT NOT NULL,
            name VARCHAR(256),
            PRIMARY KEY (id)
        ) ENGINE = InnoDB
        """

        tables["Conversationtable"]= """
        CREATE TABLE IF NOT EXISTS Conversation (
            id INT NOT NULL,
            name VARCHAR(32),
            class INT,
            con_id INT UNIQUE, 
            PRIMARY KEY (id),
            FOREIGN KEY (class) REFERENCES Class(id)
        ) ENGINE = InnoDB
        """

        tables["TeacherConversationRelationtable"]= """
        CREATE TABLE IF NOT EXISTS TeacherConversationRelation (
            id INT NOT NULL,
            conversation INT NOT NULL,
            teacher INT NOT NULL, 
            PRIMARY KEY (id),
            FOREIGN KEY (conversation) REFERENCES Conversation(id),
            FOREIGN KEY (teacher) REFERENCES Teacher(id)
        ) ENGINE = InnoDB
        """

        tables["Messagetable"]= """
        CREATE TABLE IF NOT EXISTS Message (
            id INT NOT NULL,
            sender INT NOT NULL,
            conversation INT NOT NULL,
            PRIMARY KEY (id),
            FOREIGN KEY (sender) REFERENCES User(id),
            FOREIGN KEY (conversation) REFERENCES Conversation(id)
        ) ENGINE = InnoDB
        """    

        tables["Devicetable"]= """
        CREATE TABLE IF NOT EXISTS Device (
            id INT NOT NULL,
            device_id BIGINT UNIQUE NOT NULL,
            PRIMARY KEY (id)
        ) ENGINE = InnoDB
        """

        tables["DeviceUserRelationtable"]= """
        CREATE TABLE IF NOT EXISTS DeviceUserRelation (
            id INT NOT NULL,
            user INT NOT NULL,
            device INT NOT NULL,
            public_key VARCHAR(10000) NOT NULL,
            authenticated BOOL NOT NULL,
            PRIMARY KEY (id),
            FOREIGN KEY (user) REFERENCES User(id),
            FOREIGN KEY (device) REFERENCES Device(id)
        ) ENGINE = InnoDB
        """
        
        tables["EncryptedDeviceMessageRelationtable"]= """
        CREATE TABLE IF NOT EXISTS EncryptedDeviceMessageRelation (
            id INT NOT NULL,
            message INT NOT NULL,
            deviceuserrelation INT NOT NULL,
            text VARBINARY(1000) NOT NULL,
            PRIMARY KEY (id),
            FOREIGN KEY (message) REFERENCES Message(id)
        ) ENGINE = InnoDB
        """

        tables["UserConversationRelationtable"]= """
        CREATE TABLE IF NOT EXISTS UserConversationRelation (
            id INT NOT NULL,
            nickname VARCHAR(32),
            user INT NOT NULL,
            conversation INT NOT NULL,
            PRIMARY KEY (id),
            FOREIGN KEY (user) REFERENCES User(id),
            FOREIGN KEY (conversation) REFERENCES Conversation(id)
        ) ENGINE = InnoDB """
            
        tables["ClassILAttributesRelationtable"] = """
        CREATE TABLE IF NOT EXISTS ClassILAttributesRelation (
            id INT NOT NULL,
            ILuserid INT NOT NULL,
            class INT NOT NULL,
            PRIMARY KEY (id),
            FOREIGN KEY (ILuserid) REFERENCES ILUser(id),
            FOREIGN KEY (class) REFERENCES Class(id)

        ) ENGINE = InnoDB
        """
        
        for v in tables.values():
            self.execute_query(v)
        
        # Set up id chain for all tables...
        if not Table.get("Ids", {"id":1}):
            self.execute_query("INSERT INTO Ids () VALUES ()")

        self.get_or_create_deleted_user_obj()
            
    def create_connection(self, host_name, username, user_password, db_name=""):
        try:
            return mysql.connector.connect(
                            host=host_name,
                            user=username,
                            passwd=user_password,
                            database=db_name,
                        )
        except Exception as e:
            try:
                # Will be run, if a new database is to be made.
                return mysql.connector.connect(
                    host=host_name,
                    user=username,
                    passwd=user_password,
                )
            except:
                status = "An error occurred while establishing a connnection to the database. Have you started it yet? (See log for more details)"
                self.log(f"The error '{e}' occurred", err=True, reason="Couldnt connect to database!")
                print(status)
                sys.exit(0)

    def execute_query(self, query):
        connection = self.create_connection(self.host_name, self.username, self.user_password, self.db_name)
        cursor = connection.cursor()
        try:
            cursor.execute(query)
            connection.commit()
            self.log("Query executed successfully", reason=f"DB Query \"{query.split()[0]}\"")
        except Error as e:
            self.log(f"The error '{e}' occurred", err=True, reason=f"DB Query \"{query.split()[0]}\"")
        connection.close()
        connection = None

    def execute_read_query(self, query):
        connection = self.create_connection(self.host_name, self.username, self.user_password, self.db_name)
        cursor = connection.cursor()
        result = None
        try:
            cursor.execute(query)
            result = cursor.fetchall()
            self.log("Query executed successfully", reason=f"DB Query \"{query.split()[0]}\"")
            return result
        except Error as e:
            self.log(f"The error '{e}' occurred", err=True, reason=f"DB Query \"{query.split()[0]}\"")
        connection.close()
        connection = None

    def authenticate_user(self, username, hashed):
        user = Table.get('User', {'username': username})
        self.log(user, reason="Authentication")

        if user is None: return None
        else:
            if user.get("password") == hashed:
                return user
            else:
                return None

    def get_not_authenticated_users(self, user, authenticated_devices_function):
        device_user_rels=Table.get("DeviceUserRelation",{"user": user.get("id"),"authenticated": False},filtered=True)
        if len(device_user_rels) == 0: return
        for dur in device_user_rels:
            # Creating unconventional table for getting device OBJECT when authenticating!
            dur.set(commit=False, device=Table.get("Device",{"id":dur.get("device")}))
        to_authenticate = authenticated_devices_function(device_user_rels) # Passed authentication function.
        for dur in to_authenticate:
            dur.set(authenticated=True)
            
    def getsalt(self,username):
        # Gets single field.
        u = Table.get("User",{"username":username})
        if u:
            return u.get("salt")
        else:
            return

    def registeruser(self, username, salt, hashed, firstname, lastname):
        user = Table.get("User", {'username': username})
        if user is None:
            # User is by default authenticated when registering first time.
            user =Table.Table("User",
                {"username":username,"salt":salt, "password":hashed,"firstname":firstname,"lastname":lastname, "admin":0})

            return user
        else:
            return None
    
    def set_nickname(self, user, opened_conversation, nickname):
        """Set new nickname for current opened conversation."""
        userconv = Table.get("UserConversationRelation", {"conversation": opened_conversation.get("id"), "user": user.get("id")})
        userconv.set(nickname=nickname)
        status = "Sat conversation nickname to: '" + nickname + "' successfully."
        return status
    
    def change_name(self, name, opened_conversation):
        opened_conversation.set(name=name)
    
    def is_friends_with(self, user, other):
        """Check if user is befriended with other user."""
        if Table.get("Friends", {"user1": other.get("id"), "user2": user.get("id")}) is not None: 
            return True
        
        if Table.get("Friends", {"user1": user.get("id"), "user2": other.get("id")}) is not None: 
            return True
            
        return False
    
    def create_conversation(self, user, username):
        if username=="" or username == user.get("username"):

            con_id=r.randint(0,99999)
            while Table.get("Conversation",{"con_id":con_id}) is not None:
                con_id=r.randint(0,99999)
                 
            conversation=Table.Table("Conversation",{"name":"","con_id":con_id})
            Table.Table("UserConversationRelation",{"user":user.get("id"), "nickname":user.get("username"),"conversation":conversation.get("id")})
            status = "Successfully created a single-user conversation."
            self.log(status, reason="Create singe-user conversation")
            return status
        else: 
            # Check that username is befriended.
            other_user = Table.get("User", {"username": username})
            if other_user is None:
                status = "No friends found with that username."
                self.log(status, reason=f"Create conversation with user '{username}'")
                return status
            if not self.is_friends_with(user, other_user):
                status = "You are not friends with this user yet or the user does not exist."
                self.log(status, reason=f"Create conversation with user '{username}'")
                return status
            else:
                name = f"{user.get('username')} and {username}"
                con_id=r.randint(0,99999)
                while Table.get("Conversation",{"con_id":con_id}) is not None:
                    con_id=r.randint(0,99999)
                conversation = Table.Table("Conversation", {"name":name,"con_id":con_id})
                
                # Generating relation between users both ways.
                Table.Table("UserConversationRelation",{"user":other_user.get("id"), "nickname":user.get("username"),"conversation":conversation.get("id")})
                Table.Table("UserConversationRelation",{"user":user.get("id"), "nickname":other_user.get("username"),"conversation":conversation.get("id")})
                status = "Success!"
                self.log(status, reason="Success create conversation.")
                return status
    
    def leave_conversation(self, conversation, user, encryption): # 'encryption' for server messages.
        """Leave the conversation for good with user received."""
        # Get UserConversationRelation from user that wants to leave and set the new user to be the default "Deleted user" which resides in the DB on setup()
        # Basically "deletes" conversation for the leaving user.
        ucrel = Table.get("UserConversationRelation", {"user": user.get("id"), "conversation": conversation.get("id")})
        ucrel.set(user=self.deleted_user.get("id"))
        if not Table.get("UserConversationRelation", {"user": user.get("id"), "conversation": conversation.get("id")}):
            status = "Successfully leaved the conversation."
            self.log(status, reason="Leave conversation")
            # Substitute all messages' sender.
            messages = Table.get("Message", {"sender": user.get("id")}, filtered=True)
            for msg in messages:
                msg.set(sender=self.deleted_user.get("id"))
            # Append a '{username} left the conversation' as a server message ('sender' == 0)
            #msg_obj = self.create_message(1, conversation)
            #encrypted = encryption.encrypt_message()
            # NOT DONE TODO 
            return status
        else:
            status = "Failed to leave the conversation."
            self.log(status, err=True, reason="Failed leaving the conversation")
            return status
        
    def get_conversations(self, user, get_ids=False):
        ucrels = Table.get("UserConversationRelation",{"user":user.get("id")},filtered=True)
        conversations=[]
        # Get conversation objects for user.
        for ucrel in ucrels:
            conversations.append(Table.get("Conversation",{"id":ucrel.get("conversation")}))
        
        for conversation in conversations:
            nickname = Table.get("UserConversationRelation",{"conversation":conversation.get("id"),"user":user.get("id")}).get("nickname")
            if get_ids or nickname != "":
                conversation.set(nickname=nickname, commit=False)

        return conversations

    def open_conversation(self,conversationToOpen,user):
        if conversationToOpen:
            if conversationToOpen[0] == "#":
                try:
                    con_id=int(conversationToOpen[1:]) # Cut # away
                    conversation = Table.get("Conversation",{"con_id":con_id})
                    if not conversation:
                        status = "Failed getting conversation by id."
                        self.log(status, reason="Open conversation by id")
                        return None,status
           
                    ucrel = Table.get("UserConversationRelation", {"user": user.get("id"), "conversation": conversation.get("id")})
                    conversation.set(nickname=ucrel.get("nickname"), commit=False) # Command().opened_conversation is a non-conventional Table. Set nickname
                    users = self.get_conversation_users(conversation)
                    conversation.set(users=users, commit=False)
                    if conversation is not None:
                        status="Conversation found"
                    else:
                        status="Conversation not found"
                    return conversation, status
                except ValueError:
                    return None, "Using '#' means its a id and it should be followed by an integer (Whole number)."
            
        ucrels = Table.get("UserConversationRelation",{'nickname': conversationToOpen,"user":user.get("id")},filtered=True)
        ucrel_nicknames = [ucrel.get("nickname") for ucrel in ucrels]
        conversations = Table.get("Conversation",{"name":conversationToOpen},filtered=True)
        for conversation in conversations:
            # Only if nicknames and names aren't the same. Else duplicates come.
            if not conversation.get("name") in ucrel_nicknames: 
                ucrels.append(Table.get("UserConversationRelation",{"conversation":conversation.get("id"),"user":user.get("id")}))
        
        if len(ucrels) > 1:
            return None,"More than one conversation with that name"
        elif len(ucrels) != 0:
            ucrel = ucrels[0] # Will always be one element.
            conversation=Table.get("Conversation",{'id': ucrel.get("conversation")})
            opened_conversation=Table.Table("Conversation",{"id":conversation.get("id"),"nickname":ucrel.get("nickname"),"name":conversation.get("name")},commit=False)
            if conversation.get("class") is None:
                users = self.get_conversation_users(conversation)
                opened_conversation.set(commit=False, users=users)
            else:
                #this is a class do something TODO
                pass
            return opened_conversation, "Success!"
        else:
            return None,"Conversation not found"
    
    def get_conversation_users(self, conversation):
        """Get all users from a given conversation."""
        ucrels = Table.get("UserConversationRelation", {"conversation": conversation.get("id")}, filtered=True)
        users = []
        for ucrel in ucrels:
            users.append(Table.get("User", {"id": ucrel.get("user")}))
        
        return users
    
    def update_conversation_name(self, conversation, username):
        """Enumerate through already added users to modify conversation name"""
        name=""
        users = conversation.get("users")
        for i,user in enumerate(users): # Curated list of users from relation.
            if i+1 == len(users):
                name+=user.get("username") + " and "
            else:
                name+=user.get("username") + ", " 
        name += username
        return name
    
    def add_user_to_conversation(self, current_user, conversation, username):
        user_to_add=Table.get("User",{"username":username})
        if user_to_add is None:
            return None,"You are not friends with this user or the user does not exist."
        if not self.is_friends_with(current_user, user_to_add):
            return None,f"You are not friends with '{username}'."

        name = self.update_conversation_name(conversation, username)
        Table.Table("UserConversationRelation",{"user":user_to_add.get("id"),"nickname":"","conversation":conversation.get("id")})
        conversation.set(name=name)
        conversation.data["users"].append(user_to_add)
        users = conversation.get("users")
        if len(users)==2:
            # Set the general name for conversation.
            conversation.set(name=name)

            # Set nickname for all users in the conversation.
            users=conversation.get("users")
            for user in users:
                nickname=""
                unum=0
                for user_enum in users:
                    if user_enum != user:
                        if unum == 1:
                            nickname+=f" and {user_enum.get('username')}"
                        else:
                            nickname+=f"{user_enum.get('username')}"
                        unum+=1
                userconversationrelation = Table.get("UserConversationRelation", {"user":user.get("id"),"conversation":conversation.get("id")})
                userconversationrelation.set(nickname=nickname)

        return user_to_add,f"'{username}' has been added to the conversation."
                
    def create_message(self, user, conversation):
        return Table.Table("Message", {"sender":user.get("id"), "conversation":conversation.get("id")})

    def get_device_user_rel(self, user, device_id=0):
        # Set device_id if relation for current device and user are wanted.
        if not device_id:
            return Table.get("DeviceUserRelation",{"user":user.get("id"), "authenticated": True},filtered=True)
        else:
            return Table.get("DeviceUserRelation", {"user":user.get("id"),"device":device_id, "authenticated": True}, filtered=True)

    def create_encrypted_message(self,encrypted,message_obj,deviceuserrel_id):
        query = """
        INSERT INTO EncryptedDeviceMessageRelation (id, deviceuserrelation, message, text)
        VALUES (%s, %s, %s, %s)
        """
        data = (Table.get_id("EncryptedDeviceMessageRelation"),deviceuserrel_id, message_obj.get("id"), encrypted)
        connection = self.create_connection(self.host_name, self.username, self.user_password, self.db_name)
        try:
            cursor = connection.cursor()
            cursor.execute(query, data)
            connection.commit()
            self.log("Query executed successfully", reason="Create encrypted message")
        except Error as e:
            self.log(f"The error '{e}' occurred", err=True, reason="Create encrypted message")
        connection.close()
        connection = None
    
    def get_encrypted_messages_current_conversation(self, dur_specific_device, opened_conversation):
        """Encrypt messages for a newly added user."""
        # Get messages from synced, currently logged in user.
        messages = Table.get("Message", {"conversation": opened_conversation.get("id")}, filtered=True)
        encrypted_msgs = []
        for msg in messages:
            encrypted = Table.get("EncryptedDeviceMessageRelation", 
                {"deviceuserrelation":dur_specific_device.get("id"), "message": msg.get("id")})
            encrypted_msgs.append(encrypted)
        
        return encrypted_msgs

    def get_messages(self, conversation, user, device):
        messages = Table.get("Message", {'conversation': conversation.get('id')}, filtered=True)
        if messages == []: return
        deviceuserrel = Table.get("DeviceUserRelation", {"user":user.get("id"),"device":device.get("id")})
        for i, msg in enumerate(messages):
            if msg.get("sender") != 0:
                username = Table.get("User", {'id': msg.get("sender")}).get("username")
            else:
                username = ""
            # Get specific encrypted message from user.
            obj=Table.get("EncryptedDeviceMessageRelation",{"message":msg.get("id"),"deviceuserrelation":deviceuserrel.get("id")})
            text=obj.get("text") # Get encrypted bytes.
            # Creates unconventional table with username being string and not an id reference (An deletes unused fields) for convenience with main.
            messages[i]=Table.Table("Message",{"id":msg.get("id"),"sender":username,"conversation":conversation.get("id"), "text":text},commit=False)

        return messages

    def friend_request(self, username, user):
        if username == user.get("username"):
            return "Why would you friend request yourself? Don't you have any friends? I will be your friend :))"
        user_to_request = Table.get("User", {'username': username})
        if not user_to_request:
            return "User not found"
        
        # User found - send request if no friend request have already been sent to that user.
        pending_fr = self.get_friend_requests(user, Table.get("User",{"username":username}))
        if pending_fr:
            # A friend request have already been found. No more can be made.
            return f"'{username}' already requested you to be friends." if pending_fr.get("in_process") else f"You are already friends with '{username}'."
        pending_fr=self.get_friend_requests(Table.get("User",{"username":username}), user)
        if pending_fr:
            # A friend request have already been found. No more can be made.
            return f"You have already requested '{username}' to be friends." if pending_fr.get("in_process") else f"You are already friends with '{username}'."
        
        
        
        # Send request.
        Table.Table("Friends", {"user1":user.get("id"), "user2":user_to_request.get("id"), "in_process": 1})
        return f"Friend request was send to user with username '{username}'"

    def get_friend_requests(self, user, user2=None):
        # As a default the CURRENT user is the RECEIVING user for the pending friend request.
        if user2 is None:
            pending_fr = Table.get("Friends", {"user2":user.get("id"), "in_process": 1}, filtered=True)
        else:
            pending_fr = Table.get("Friends", {"user1":user2.get("id"),"user2":user.get("id"), "in_process": 1})
        
        if pending_fr:
            return pending_fr
        # "Returns" None object if no friend requests were found.
    
    def get_friends(self, user):
        friends = Table.get("Friends", {"user1": user.get("id"), "in_process": 0}, filtered=True)
        f2 = Table.get("Friends", {"user2": user.get("id"), "in_process": 0}, filtered=True)
        friends.extend(f2)
        if not friends:
            return None
        
        return friends

    def accept_friend_request(self, request):
        request = Table.get("Friends", {"id": request.get("id")})
        request.set(in_process=0) # Accepted.
        return f"Friend request was accepted."

    def decline_friend_request(self, request):
        # Declining is just deleting friend request without letting sending user know.
        request = Table.get("Friends", {"id": request.get("id")})
        request.delete() # Declined.
        return f"Friend request was declined."
    
    def generate_device(self, device_id=-1):
        """Generate new device and save to DB."""
        #generate an id if non where given
        if device_id==-1:
            # Random number 16 ciphers.
            device_id = r.randint(0, 10**16)
            while Table.get("Device", {"device_id": device_id}):
                device_id = r.randint(0,10**16)
        
        # Unique id found.
        return Table.Table("Device", {"device_id": device_id}) 

    def create_device_user_relation(self, publickey_str, user, device):
        if Table.get("DeviceUserRelation", {"user": user.get("id")}, filtered=True):
            Table.Table("DeviceUserRelation",{"public_key":publickey_str,"device":device.get("id"),"user":user.get("id"), "authenticated": False})
            return False
        else:
            Table.Table("DeviceUserRelation",{"public_key":publickey_str,"device":device.get("id"),"user":user.get("id"), "authenticated": True})
            return True  

    def is_device_authenticated(self, user, device):
        """Check if a corresponding DeviceUserRelation has authenticated=True"""
        check = Table.get("DeviceUserRelation", {"user": user.get("id"), "device": device.get("id")})
        if check:
            return check.get("authenticated")
        else:
            return None
           
    def connect_IL_id(self,user,ILid):
        ILid_obj=Table.get("ILUser",{"itslearningid":ILid})
        if not ILid_obj:
            return "Id not found"

        user.set(ILuserid=ILid_obj.get("id"))

        return "success"

    def create_ILobj(self, ilid, isTeacher):
        ILobj = Table.Table("ILUser",{"itslearningid":ilid})
        if isTeacher:
            ILobj.set(Teacher=Table.Table("Teacher", {}))

    def create_class(self, class_name):
        Table.Table("Class",{"name":class_name})

    def add_to_class(self, ILid, class_name):
        class_id = Table.get("Class",{"name":class_name})
        ILUser_id = Table.get("ILUser",{"itslearningid":ILid})

        if ILUser_id and class_id:
            Table.Table("ClassILAttributesRelation",{"ILuserid":ILUser_id.get("id"),"class":class_id.get("id")})
        elif class_id:
            return "ILUser not found"
        elif ILUser_id:
            return "class_id not found"
        else:
            return "class_id and ILUser not found"

manager = DbManager()
