import mysql.connector
from mysql.connector import Error
import Table
import random as r

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import load_pem_public_key


class DbManager():
    def __init__(self):
        self.host_name="localhost"
        self.username="root"
        self.user_password=""
        self.db_name="chatplatform"
        self.connection = None

    def list_format(self, l):
        s = ""
        for i in range(len(l)):
            s += l[i] + (" | " if not i+1 == len(l) else "")
        print(s)

    def setup(self):
        self.create_connection(self.host_name, self.username, self.user_password)
        # Create database if it doesn't already exists.
        cmd = f"""
        CREATE DATABASE IF NOT EXISTS `{self.db_name}`;
        """
        self.execute_query(cmd)
        self.connection.close()
        self.connection = None
        
        self.create_connection(self.host_name, self.username, self.user_password, self.db_name)
        
        tables={}

        tables["Teachertable"]= """
        CREATE TABLE IF NOT EXISTS Teacher ( 
            id INT NOT NULL,
            PRIMARY KEY (id)
        ) ENGINE = InnoDB
        """

        tables["ILUsertable"]= """
        CREATE TABLE IF NOT EXISTS ILUser ( 
            id INT NOT NULL,
            itslearning_id VARCHAR(32) NOT NULL,
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
            password VARCHAR(128) NOT NULL,
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

        tables["TeacherConversationtable"]= """
        CREATE TABLE IF NOT EXISTS TeacherConversation (
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
            text VARCHAR(1000) NOT NULL,
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

        tables["EncryptedMessagetable"]= """
        CREATE TABLE IF NOT EXISTS EncryptedMessage (
            id INT NOT NULL,
            message INT NOT NULL,
            device INT NOT NULL,
            text VARCHAR(1000) NOT NULL,
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
        ) ENGINE = InnoDB
        """
            
        tables["ClassILAttributes"] = """
        CREATE TABLE IF NOT EXISTS ClassILAttributes (
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
    
    def create_connection(self, host_name, username, user_password, db_name=""):
        try:
            self.connection = mysql.connector.connect(
                            host=host_name,
                            user=username,
                            passwd=user_password,
                            database=db_name,
                        )

        except Error as e:
            print(f"The error '{e}' occurred")

    def execute_query(self, query):
        cursor = self.connection.cursor()
        try:
            cursor.execute(query)
            self.connection.commit()
            print("Query executed successfully")
        except Error as e:
            print(f"The error '{e}' occurred")

    def execute_read_query(self, query):
        cursor = self.connection.cursor()
        result = None
        try:
            cursor.execute(query)
            result = cursor.fetchall()
            return result
        except Error as e:
            print(f"The error '{e}' occurred")

    def authenticate_user(self, username, hashed):
        user = Table.get('User', {'username': username})
        print(user)

        if user is None: return None
        else:
            if user.get("password") == hashed:
                return user
            else:
                return None

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
            return Table.Table("User",
                {"username":username,"salt":salt, "password":hashed,"firstname":firstname,"lastname":lastname})
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
        else: 
            # Check that username is befriended.
            other_user = Table.get("User", {"username": username})
            if other_user is None: print("No friends found with that username."); return
            if not self.is_friends_with(user, other_user):
                print("You are not friends with this user yet or the user does not exist.")
            else:
                name = f"{user.get('username')} and {username}"
                con_id=r.randint(0,99999)
                while Table.get("Conversation",{"con_id":con_id}) is not None:
                    con_id=r.randint(0,99999)
                conversation = Table.Table("Conversation", {"name":name,"con_id":con_id})
                
                # Generating relation between users both ways.
                Table.Table("UserConversationRelation",{"user":other_user.get("id"), "nickname":user.get("username"),"conversation":conversation.get("id")})
                Table.Table("UserConversationRelation",{"user":user.get("id"), "nickname":other_user.get("username"),"conversation":conversation.get("id")})

    def get_conversations(self, user, get_ids=False):
        try:
            ucrs = Table.get("UserConversationRelation",{"user":user.get("id")},filtered=True)
            conversations=[]
            for ucr in ucrs:
                conversations.append(Table.get("Conversation",{"id":ucr.get("conversation")}))

            for conversation in conversations:
                nickname = Table.get("UserConversationRelation",{"conversation":conversation.get("id"),"user":user.get("id")}).get("nickname")  
                if get_ids or nickname != "":
                    conversation.set(commit=False, nickname=nickname)

            return conversations
        except Error as e:
            print(e)

    def open_conversation(self,conversationToOpen,user):
        if conversationToOpen[0] == "#":
            try:
                con_id=int(conversationToOpen)
                conversation = Table.get("Conversation",{"con_id":con_id}) 
                if conversation is not None:
                    status="Conversation found"
                else:
                    status="Conversation not found"
                return conversation, status
            
            except ValueError:
                return None, "using '#' means its a id and it should be followed by an integer"
            
        ucrel = Table.get("UserConversationRelation",{'nickname': conversationToOpen,"user":user.get("id")},filtered=True)
        conversations = Table.get("Conversation",{"name":conversationToOpen},filtered=True)
        for conversation in conversations:
            ucrel.append(Table.get("UserConversationRelation",{"conversation":conversation.get("id"),"user":self.user.get("id")}))
        
        if len(ucrel) > 1:
            print("More than one conversation with that name")
        elif len(ucrel) != 0:
            ucrel = ucrel[0] # Will always be one element.
            conversation=Table.get("Conversation",{'id': ucrel.get("conversation")})
            opened_conversation=Table.Table("Conversation",{"id":conversation.get("id"),"nickname":ucrel.get("nickname"),"name":conversation.get("name")},commit=False)
            if conversation.get("class") is None:
                userconversationrelations = Table.get("UserConversationRelation",{'conversation':conversation.get("id")},filtered=True)
                users=[]
                for userconversationrelation in userconversationrelations:
                    with_user=Table.get("User",{"id":userconversationrelation.get("user")})
                    users.append(with_user)
                opened_conversation.set(commit=False, users=users)
            else:
                #this is a class do something
                pass
            return opened_conversation, "success"
        else:
            return None,"Conversation not found"

    def add_user_to_conversation(self, _user, conversation, username):
        user=Table.get("User",{"username":username})
        if not self.is_friends_with(user,_user):
            return f"you are not friends with {username}"
        # Enumerating through already added users to modify conversation name.
        name=""
        users = conversation.get("users")
        for i,user2 in enumerate(users): # Curated list of users from relation.
            if i+1 == len(users):
                name+=user2.get("username") + " and "
            else:
                name+=user2.get("username") + ", " 
        
        name += username

        Table.Table("UserConversationRelation",{"user":user.get("id"),"nickname":"","conversation":conversation.get("id")})
        conversation.set(name=name)
        conversation.data["users"].append(user)
        if len(users)==2:
            # Set the general name for conversation.
            self.execute_query(f"UPDATE conversation SET name = '{name}' WHERE id = {conversation.get('id')}")
            # Set nickname for all users in the conversation to ""
            users=conversation.get("users")

            for user3 in users:
                nickname=""
                unum=0
                for user4 in users:
                    if user4 != user3:
                        if unum == 1:
                            nickname+=f" and {user4.get('username')}"
                        else:
                            nickname+=f"{user4.get('username')}"
                        unum+=1
                userconversationrelation = Table.get("UserConversationRelation", {"user":user3.get("id"),"conversation":conversation.get("id")})
                userconversationrelation.set(nickname=nickname)
        
        return f"{username} is added to the conversation"
                
    def create_message(self, user, conversation):
        return Table.Table("Message", {"sender":user.get("id"), "conversation":conversation.get("id")})

    def get_devices(self, user):
        return Table.get("DeviceUserRelation",{"user":user.get("id")},filtered=True)

    def create_encrypted_message(self,encrypted,message_obj,device_id):
        Table.Table("EncryptedDeviceMessageRelation", {"device":device_id,"message":message_obj.get("id"),"text":encrypted})

    def get_messages(self, conversation, device):
        messages = Table.get("Message", {'conversation': conversation.get('id')}, filtered=True)
        if messages is None: return
        for i, msg in enumerate(messages):
            username = Table.get("User", {'id': msg.get("sender")}).get("username")
            print(msg,device)
            obj=Table.get("EncryptedDeviceMessageRelation",{"message":msg.get("id"),"device":device.get("id")})
            print(obj)
            text=obj.get("text")
            # Creates unconventional table with username being string and not an id reference (An deletes unused fields) for convenience with main.
            messages[i]=Table.Table("Message",{"id":msg.get("id"),"sender":username,"text":text},commit=False)

        return messages

    def friend_request(self, username, user):
        if username == user.get("username"):
            return "ARE U SO SAD YOU WANT TO FRIEND REQUEST YOURSELF? ARE YOU SHITTING YOUR PANTS AT YOUR MOM'S HOME??! GET A F'IN LIFE!"
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
        Table.Table("DeviceUserRelation",{"public_key":publickey_str,"device":device.get("id"),"user":user.get("id")})
        return "Successful creation of Device-User relation. Eller noget"
    
    def get_public_key(self, user):
        """Get public key from selected user."""
        uid = user.get("id")

        public_key = Table.get("DeviceUserRelation", {"user": uid}).get("public_key")
        public_key = load_pem_public_key(public_key, default_backend())
        print(public_key)
        

manager = DbManager()
