import mysql.connector
from mysql.connector import Error
import hashlib
import Table
import random as r

class DbManager():
    def __init__(self):
        self.host_name="localhost"
        self.user_name="root"
        self.user_password=""
        self.db_name="chatplatform"
        self.connection = None
           
    def setup(self):
        self.create_connection(self.host_name, self.user_name, self.user_password)
        # Create database if it doesn't already exists.
        cmd = f"""
        CREATE DATABASE IF NOT EXISTS `{self.db_name}`;
        """
        self.execute_query(cmd)
        self.connection.close()
        self.connection = None
        
        self.create_connection(self.host_name, self.user_name, self.user_password, self.db_name)
        
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
            username VARCHAR(32) NOT NULL,
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
            text VARCHAR(256) NOT NULL,
            PRIMARY KEY (id),
            FOREIGN KEY (sender) REFERENCES User(id),
            FOREIGN KEY (conversation) REFERENCES Conversation(id)
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
    
    def create_connection(self, host_name, user_name, user_password, db_name=""):
        try:
            self.connection = mysql.connector.connect(
                            host=host_name,
                            user=user_name,
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

    def authenticate(self, username, hashed):
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
        # print(user)
        if user is None:
            # User is by default authenticated when registering first time.
            return Table.Table("User",
                {"username":username,"salt":salt, "password":hashed,"firstname":firstname,"lastname":lastname})
        else:
            return None

    def create_conversation(self, user, username):
        if username=="" or username == user.get("username"):
            if Table.get("UserConversationRelation",{"nickname":username,"user":user.get("id")}):
                print("Already have a conversation with the nickname of that username")
                return
            
            conversations = Table.get("Conversation",{"name":username},filtered=True)
            for conversation in conversations:
                ucrel = Table.get("UserConversationRelation",{"conversation":conversation.get("id"),"user":user.get("id")})
                if ucrel:
                    # Can have same "names"/"nicknames" if they're empty.
                    if ucrel.get("nickname") == "":
                        print("Already have a conversation with the name of that username and that conversation has no nickname")
                        return 
            conversation=Table.Table("Conversation",{"name":""})
            Table.Table("UserConversationRelation",{"user":user.get("id"), "nickname":user.get("username"),"conversation":conversation.get("id")})
        else: 
            _user = Table.get("User",{"username":username})
            print("_user:",_user)
            if _user == None:
                return

            conversation = Table.Table("Conversation", {"name":f"{user.get('username')} and {username}"})

            # Generating relation between users both ways.
            Table.Table("UserConversationRelation",{"user":_user.get("id"), "nickname":user.get("username"),"conversation":conversation.get("id")})
            Table.Table("UserConversationRelation",{"user":user.get("id"), "nickname":_user.get("username"),"conversation":conversation.get("id")})

    def add_user_to_conversation(self, conversation, username):
        user=Table.get("User",{"username":username})
        
        # Enumerating through already added users to modify conversation name.
        name=""
        users = conversation.get("users")
        for i,user2 in enumerate(users): # Curated list of users from relation.
            if i+1 == len(users):
                name+=user2.get("username") + " and "
            else:
                name+=user2.get("username") + ", " 

        name += user.get("username")
        Table.Table("UserConversationRelation",{"user":user.get("id"),"nickname":"","conversation":conversation.get("id")})
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
                userconversationrelation.set("nickname",nickname)
                

    def create_message(self, user, conversation, message):
        Table.Table("Message", {"sender":user.get("id"), "conversation":conversation.get("id"), "text":str(message)})
        
    def get_messages(self, conversation):
        messages = Table.get("Message", {'conversation': conversation.get('id')}, filtered=True)
        if messages is None: return
        for i, msg in enumerate(messages):
            username = Table.get("User", {'id': msg.get("sender")}).get("username")
            # Creates unconventional table with username being string and not an id reference (An deletes unused fields) for convenience with main.
            messages[i]=Table.Table("Message",{"id":msg.get("id"),"sender":username,"text":msg.get("text")},commit=False)

        return messages

    def friend_request(self, username, user):
        result = self.execute_read_query(f"SELECT * FROM user WHERE username = '{username}'")
        if len(result)==0:
            return "user not found"
        self.execute_query(self.create_friend_request_query({"user1":user, "user2":result[0][0]}))
        return f"friend request send to {username}"

    def get_friend_requests(self, user):
        result=self.execute_read_query(f"SELECT * FROM friends WHERE user2={user} AND in_process=1")
        requests=[]
        for request in result:
            requests.append({"id":request[0],"sender":self.execute_read_query(f"SELECT * FROM user WHERE id = {request[1]}")[0],"reciver":user})
        return requests

    def accept_friend_request(self, request):
        self.execute_query(f"UPDATE friends SET in_process = 0 WHERE id={request['id']}")

    def decline_friend_request(self, request):
        self.execute_query(f"DELETE friends WHERE id={request['id']}")

manager = DbManager()
