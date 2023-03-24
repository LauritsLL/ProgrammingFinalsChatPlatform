import mysql.connector
from mysql.connector import Error
import sys

import database_manager as dm
from DbLog import DbLog

typeswithquotes=[type("")]


def get_column_names(tablename):
    """Return column names of specified table."""
    cmd = f"""
    SELECT COLUMN_NAME
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA='{dm.manager.db_name}' 
        AND TABLE_NAME='{tablename}';
    """
    columnnames = dm.manager.execute_read_query(cmd)
    columnnames = [col[0] for col in columnnames]
    return columnnames

# Table.get("Friends", {"user2": user.get("id"), "in_process": 1}, filtered=True)
def get(tablename, flags, column="all", filtered=False):
    query=f"SELECT * FROM {tablename} WHERE "
    for k,v in flags.items():
        if type(v) in typeswithquotes:
            query+=f"{k}='{v}' AND "
        else:
            query+=f"{k}={v} AND "
    
    query=query[:-5]

    result=dm.manager.execute_read_query(query)
    
    if filtered:
        if not result:
            return []
        rows=[]
        columnnames = get_column_names(tablename)
        for row in result:
            data={}
            for i,columnname in enumerate(columnnames):
                data[columnname]=row[i]
            tempdata={}
            if column != "all":
                columns=[c.strip() for c in column.split(",")]

                for c in columns:
                    tempdata[c]=flags[c]
            else:
                tempdata=data

            row=Table(tablename, tempdata, commit=False)
            rows.append(row)
            
        return rows
    if not result:
        return None
    if len(result) > 1:
        print(f"Got more than one {tablename}... The data needs to be more precise or use filtered=True!")
        return None
    
    result = result[0]
    columnnames = get_column_names(tablename)
    
    # Match up corresponding table columns with given data.
    flags={}
    for i,columnname in enumerate(columnnames):
        flags[columnname]=result[i]
    
    # If specified columns have been set, splitted by commas, match them up and forget rest of columns gotten.
    data={}
    if column != "all":
        columns=[c.strip() for c in column.split(",")]

        for c in columns:
            data[c]=flags[c]
    else:
        data=flags
    return Table(tablename, data, commit=False)


def get_id(tablename): 
    id = dm.manager.execute_read_query(f"SELECT {tablename}_next_id FROM Ids WHERE id = 1")[0][0]
    dm.manager.execute_query(f"UPDATE Ids SET {tablename}_next_id = {id+1} WHERE id = 1")
    return id

class Table():
    def __init__(self, tablename, data, commit=True):
        self.tablename=tablename
        self.data=data

        if commit:
            self.data["id"]=get_id(tablename)
            query=f"INSERT INTO {tablename} ("
            for k,v in self.data.items():
                query+=f"{k},"
            query=query[0:-1] + ")\nVALUES ("
            for k,v in self.data.items():
                if type(v) in typeswithquotes:
                    query+=f"'{v}',"
                else:
                    query+=f"{v},"
            query=query[0:-1] + ");"
            dm.manager.execute_query(query)
    
    def save(self, fields={}):
        query=f"UPDATE {self.tablename} SET"
        if not fields:
            for k,v in self.data.items():
                if k == "id":
                    continue
                if type(v) in typeswithquotes:
                    query+=f" {k} = '{v}',"
                else:
                    query+=f" {k} = {v},"
            # Remove last comma.
            query = query[:-1]
            query+=f" WHERE id = {self.data.get('id')}"
            dm.manager.execute_query(query)
        else:
            # Save specific fields.
            for k,v in fields.items():
                if k == "id" or not k in get_column_names(self.tablename):
                    continue
                if type(v) in typeswithquotes:
                    query+=f" {k} = '{v}',"
                else:
                    query+=f" {k} = {v},"
            # Remove last comma.
            query = query[:-1]
            query+=f" WHERE id = {self.data.get('id')}"
            dm.manager.execute_query(query)
                 
    def delete(self):
        dm.manager.execute_query(f"DELETE FROM {self.tablename} WHERE id={self.data['id']}")
    
    def get(self, field_name):
        """Get field name from table"""
        try:
            return self.data[field_name]
        except KeyError:
            print(f"{field_name} doesn't exist in {self.tablename}")
            return None
    
    def set(self, commit=True, **fields):
        for k,v in fields.items():
            self.data[k] = v
        if commit:
            self.save(fields=fields)
    
    def __str__(self):
        """String representation of table."""
        formatted = ""
        for k,v in self.data.items():
            formatted += f"{k.upper()}: "
            if type(v) is list:
                formatted += "["
                for item in v:
                    formatted += "\n\t* " + str(item)
                formatted += "]"
            else:
                if not len(str(v)) > 22:
                    formatted += str(v)
                else:
                    formatted += str(v)[0:19] + "..."
            formatted += " | "
        formatted = formatted[:-2]
        return formatted

    
