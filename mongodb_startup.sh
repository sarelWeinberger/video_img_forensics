#!/bin/bash
# MongoDB startup script
# This script starts MongoDB server if it's not already running

# Check if MongoDB is running
if pgrep -x "mongod" > /dev/null
then
    echo "MongoDB is already running."
else
    echo "Starting MongoDB server..."
    mkdir -p /data/db
    mongod --dbpath /data/db --fork --logpath /var/log/mongodb.log
    echo "MongoDB server started."
fi