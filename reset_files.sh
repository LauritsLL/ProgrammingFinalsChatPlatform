#!/usr/bin/bash
read -p "Are you sure? [Y/n] " prompt
if [[ $prompt == "n" || $prompt == "N" || $prompt == "no" || $prompt == "No" ]]
then
  echo "Done. Exiting..."
  echo "No changes were made."
else
  echo "Resetting files for creation of new database."
  rm DB_MANAGER_LOG.log && touch DB_MANAGER_LOG.log
  rm -r device*/
  
  # DROP DATABASE WHEN CALLED (DANGER!)
  if [ -e "DROPPING" ] # If a file called 'DROPPING' exists, drop database on call.
  then
    echo "Dropping database 'chatplatform'"
    echo "DROP DATABASE IF EXISTS chatplatform;" | mysql -h 127.0.0.1 -P 3306 -u root chatplatform
  else
    echo "Didn't find file 'DROPPING' in CWD. Database intact."
  fi
fi
