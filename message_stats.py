'''
Created on Oct 5, 2020

@author: michaelfink
'''

import sqlite3
import datetime
import os
import sys
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from wordcloud import WordCloud, STOPWORDS

DB_PATH = '/Users/michaelfink/Library/Messages/chat.db'
# DB_PATH = 'D:/python_projects/imessage_stats/chat.db'

PIC_PATH = '/Users/michaelfink/pythonProjects/iMessageScripts/wordcloud.png'

def send_message(phone_number, message):
    '''
    Sends a message from mac computers via applescript using imessage app.
    
    phone_number - the number to send a message to.
    message - the message to be sent.
    '''
    
    os.system('osascript send.scpt {} "{}"'.format(phone_number, message))
    

def send_picture(phone_number):
    '''
    Sends a picture from mac computers via applescript using imessage app.
    
    phone_number - the number to send a message to.
    '''
    
    os.system('osascript sendpic.scpt {}'.format(phone_number))
    
    
def db_connect(db_path):
    '''
    Attempts to form a connection between this script and the database.
    
    db_path - the path to the database of messages (should be /Users/yourusername/Library/Messages/chat.db)
    '''
    
    conn = None
    try:
        conn = sqlite3.connect(db_path)
    except Exception as e:
        print(e)
        
    return conn
    
def poll(db_path):
    '''
    Polls the message database for the most recent row.

    db_path - the path to the database of messages (should be /Users/yourusername/Library/Messages/chat.db)
    '''
    
    conn = db_connect(db_path)
    c = conn.cursor()
    c.execute("SELECT MAX(ROWID),text,handle_id,is_from_me FROM `message`")
    return(c.fetchone())

def convert_timestamp(mac_abs_timestamp):
    '''
    Converts Mac absolute timestamp into datetime object representing the same time
    
    mac_abs_timestamp - timestamp desired to be converted
    '''
    
    unix = datetime(1970, 1, 1)
    cocoa = datetime(2001, 1, 1)
    delta = cocoa - unix
    
    #fromtimestamp returns local datetime corresponding to POSIX (time since Jan. 1, 1970 in seconds)
    #add difference between that and the given mac absolute timestamp and we have our current time
    return(datetime.fromtimestamp(mac_abs_timestamp) + delta)
    
def check_for_command(message):
    if(message == '!command1'):
        print('')
    elif(message == '!command2'):
        print('')
        
def get_records(db_path, id, time_frame = sys.maxsize):
    '''
    Gets all records within a desired time frame for a certain conversation.
    
    db_path - path to the database to get records from.
    id - id of the conversation from which to get records.
    time_frame - Number of seconds back through which the average should be calculated. Default value of maxsize to get all records by default.
    '''
    
    # Database connection
    conn = db_connect(db_path)
    c = conn.cursor()
    
    #Grab most recent message from desired chat and save the time
    #Left join with c_m_j because it holds chat_id rather than handle_id. This gets me a certain chat rather than a certain person across chats
    # This fixes group chats messing with data for a conversation
    c.execute("SELECT MAX(date) FROM message \
              LEFT JOIN chat_message_join on message.ROWID = chat_message_join.message_id\
              WHERE chat_id = {}".format(id))
    most_recent = c.fetchone()[0]
    
    # Get all data within the desired time_frame by subtracting it from the most recently sent message in a conversation
    c.execute("SELECT date, is_from_me, text, chat_id FROM message \
              LEFT JOIN chat_message_join on message.ROWID = chat_message_join.message_id\
              WHERE chat_id = {} and date > {}".format(id, most_recent - time_frame))

    # All records filtered from the database.
    return(c.fetchall())
    
def average_response_time(id, time_frame = sys.maxsize):
    '''
    Calculates average response time per user in a conversation and sends results to that chat.
     
    id - Conversation to be analyzed.
    time_frame - Number of seconds back through which the average should be calculated. Default value of maxsize to get all records by default.
    '''
    
    records = get_records(DB_PATH, id, time_frame)
    # Start off by having the 'waiting' record as the first record in the time frame
    waiting = records[0]
     
    my_response_times = []
    recipients_response_times = []
     
    # Loop through all records and calculate the average response time.
    for record in records:
        # If the next message is_from_me value is different from the waiting value then the most recent sender has swapped
        if record[1] != waiting[1]:
            # If I was waiting add response time to recipients list and update waiting value
            if waiting[1] == 1:
                recipients_response_times.append(record[0] - waiting[0])
                waiting = record
            # If recipient was waiting add response time to my list and update waiting value
            elif waiting [1] == 0:
                my_response_times.append(record[0] - waiting[0])
                waiting = record
    
    try:
        my_avg_response_time = sum(my_response_times) / len(my_response_times)
        recipients_avg_response_time = sum(recipients_response_times) / len(recipients_response_times)
    except ZeroDivisionError:
        my_avg_response_time = "Error! No responses found."
        recipients_avg_response_time = "Error! No responses found."
     
#     print("Michael's average response time (s): " + str(my_avg_response_time))
#     print("Your average response time (s): " + str(recipients_avg_response_time))
    return my_avg_response_time, recipients_avg_response_time
    
def longest_response_time(id, time_frame = sys.maxsize):
    records = get_records(DB_PATH, id, time_frame)
    # Start off by having the 'waiting' record as the first record in the time frame
    waiting = records[0]
     
    my_response_times = []
    recipients_response_times = []
     
    # Loop through all records and calculate the average response time.
    for record in records:
        # If the next message is_from_me value is different from the waiting value then the most recent sender has swapped
        if record[1] != waiting[1]:
            # If I was waiting add response time to recipients list and update waiting value
            if waiting[1] == 1:
                recipients_response_times.append(record[0] - waiting[0])
                waiting = record
            # If recipient was waiting add response time to my list and update waiting value
            elif waiting [1] == 0:
                my_response_times.append(record[0] - waiting[0])
                waiting = record
                
    my_longest_response_time = max(my_response_times)
    recipients_longest_response_time = max(recipients_response_times)
    
    return my_longest_response_time, recipients_longest_response_time
       

def average_message_length(id, time_frame = sys.maxsize):
    '''
    Calculates average message length in words per user in a conversation and sends results to that chat.
    
    id - Conversation to be analyzed
    time_frame - Number of seconds back through which the average should be calculated. Default value of maxsize to get all records by default.
    '''
    
    records = get_records(DB_PATH, id, time_frame)
    
    my_response_lengths = []
    recipients_response_lengths = []
    
    #Go through all records record the number of words in the message
    for record in records:
        #Ensure no "None" types as empty strings will cause issues
        if record[2] is not None: 
            msg_length = len(record[2].split())           
            if record[1] == 1:
                my_response_lengths.append(msg_length)
            else:
                recipients_response_lengths.append(msg_length)
            
    try:
        my_avg_response_length = sum(my_response_lengths) / len(my_response_lengths)
        recipients_avg_response_length = sum(recipients_response_lengths) / len(recipients_response_lengths)
    except ZeroDivisionError:
        my_avg_response_length = "Error! No responses found."
        recipients_avg_response_length = "Error! No responses found."

    return my_avg_response_length, recipients_avg_response_length


    
def longest_message_length(id, time_frame = sys.maxsize):
    '''
    Calculates longest message length in words per user in a conversation and sends results to that chat.
    
    id - Conversation to be analyzed
    time_frame - Number of seconds back through which the average should be calculated. Default value of maxsize to get all records by default.
    '''
    
    records = get_records(DB_PATH, id, time_frame)
    
    my_response_lengths = []
    recipients_response_lengths = []
    
    #Go through all records record the number of words in the message
    for record in records:
        #Ensure no "None" types as empty strings will cause issues
        if record[2] is not None: 
            msg_length = len(record[2].split())           
            if record[1] == 1:
                my_response_lengths.append(msg_length)
            else:
                recipients_response_lengths.append(msg_length)
            
    my_longest_message = max(my_response_lengths)
    recipients_longest_message = max(recipients_response_lengths)
    
    return my_longest_message, recipients_longest_message


def message_sent_totals(id, time_frame = sys.maxsize):
    conn = db_connect(DB_PATH)
    c = conn.cursor()
    
    #Grab most recent message from desired chat and save the time
    #Left join with c_m_j because it holds chat_id rather than handle_id. This gets me a certain chat rather than a certain person across chats
    # This fixes group chats messing with data for a conversation
    c.execute("SELECT MAX(date) FROM message \
              LEFT JOIN chat_message_join on message.ROWID = chat_message_join.message_id\
              WHERE chat_id = {}".format(id))
    most_recent = c.fetchone()[0]
    
    # Get all data within the desired time_frame by subtracting it from the most recently sent message in a conversation
    c.execute("SELECT date FROM message \
              LEFT JOIN chat_message_join on message.ROWID = chat_message_join.message_id\
              WHERE chat_id = {} and date > {} and is_from_me = 1".format(id, most_recent - time_frame))
    num_messages_from_me = len(c.fetchall())

    c.execute("SELECT date FROM message \
              LEFT JOIN chat_message_join on message.ROWID = chat_message_join.message_id\
              WHERE chat_id = {} and date > {} and is_from_me = 0".format(id, most_recent - time_frame))
    num_messages_from_recipient = len(c.fetchall())
    
    return num_messages_from_me, num_messages_from_recipient

def generate_wordcloud(id, time_frame = 3600 * 4200):
    # default time frame of half year because it takes a while
    records = get_records(DB_PATH, id, time_frame)
    
    words = ''
    
    #Go through all records record the number of words in the message
    for record in records:
        #Ensure no "None" types as empty strings will cause issues
        if record[2] is not None: 
            msg = record[2].split()
            #Create one long string of all texts in the time frame
            for word in msg:
                words = words + ' ' + word
    
    #Create a wordcloud of all words sent
    wordcloud = WordCloud(width = 800, height = 800, 
                background_color ='white', 
                stopwords = STOPWORDS,
                min_font_size = 10).generate(words)
    
    wordcloud.to_file(PIC_PATH)
    
    #Send the wordcloud
   

'''

total messages sent
text frequency by hour
specific word frequency
top 5 most used words (possibly excluding the, of, a things of that nature


do all that with chosen time frame ^^
do all via text commands??

'''

if __name__ == '__main__':
        
    # print(average_response_time(8))
    # print()
    # print(average_message_length(8, 3600 * 8))
    # generate_wordcloud(8, 3600 * 1)
    message_sent_totals(8)
    
    
    
    
    
    