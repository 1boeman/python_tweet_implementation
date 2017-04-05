#!/usr/bin/env python
# -*- coding: utf-8 -*-

import twitter
import os, sys, getopt, time, re
import re
from lxml import etree
import hashlib
import settings 

def main ():
  argv = sys.argv[1:]
  inputdir = ''
  logfile = ''
  help_message = 'Usage: tweet.py -i <inputdir> -l <logfile>'
  
  if len(argv) < 2:
    print help_message
    sys.exit(2)
   
  try:
    opts, args = getopt.getopt(argv,"i:l:")
  except getopt.GetoptError:
    print help_message
    sys.exit(2)
  for opt, arg in opts:
    if opt in ("-i"):
       inputdir = arg
    elif opt in ("-l"):
       logfile = arg
 
  if not len(inputdir) or not len(logfile):
    print help_message
    sys.exit(2)

  print 'Input dir is "', inputdir
  print 'Log file is "', logfile

  get_user_events(inputdir,logfile)


def get_user_events(directory,logfile):
  just_tweeted = []
  log = open(logfile,'a+')
  for fn in os.listdir(directory):
    file_path = os.path.join(directory,fn)
    if os.path.isfile(file_path):
      tree = etree.parse(file_path)
      dates = tree.xpath("//date")[0].text
      dates = re.split(',',dates)
      current_timestamp = time.time()
      for d in dates:
        timestamp = time.mktime(time.strptime(d, "%Y-%m-%d"))
        # check if the event is in the future
        if timestamp > current_timestamp:
          node_id = tree.xpath('//node_id')
          if not len(node_id):
            continue
          node_id = node_id[0].text
          
          if node_id in just_tweeted:
            continue

          print (file_path) 
          checksum = hashlib.md5(open(file_path,'rb').read()).hexdigest()

          title = tree.xpath("//title")[0].text

          check_title = re.sub('[\W_]+', '_', title)

          check_string = '-'+checksum+"-"+check_title+"\n"
          # check if we've already tweeted this
          if not string_in_file(check_string, logfile):
            # let's tweet. 
            city_no = tree.xpath('//cityno') 
            city_freetext = tree.xpath('//city')
            venue_id = tree.xpath('//venue_id')
            venue_freetext = tree.xpath('//venue_freetext')
            venue_string = ''
            city_string = ''
            with settings.db as db:
              # make city string
              if len(city_freetext) and city_freetext[0].text and len(city_freetext[0].text):
                city_string += city_freetext[0].text
              elif len(city_no) and city_no[0].text and len(city_no[0].text):
                cur = db.cursor()
                cur.execute("SELECT * FROM City where Id = :Id",{"Id":city_no[0].text})
                row = cur.fetchone()
                city_string += ' #'+camelCase(row[1])
                print row
 
              # make venue string
              if len(venue_id) and venue_id[0].text and len(venue_id[0].text) > 1:
                cur = db.cursor()
                cur.execute("SELECT * FROM Venue where Id = :Id",{"Id":venue_id[0].text})
                row = cur.fetchone()
                print row[2] 
                venue_string += ' #' + camelCase(row[2])
              elif len(venue_freetext) and venue_freetext[0].text:
                venue_string += venue_freetext[0].text
 
              tweet_string_list = [title + ": " ]
              tweet_string_list.append ("https://muziekladder.nl/node/" + node_id + " \n")
              tweet_string_list.append(venue_string)
              tweet_string_list.append(city_string)
              
              tweet_string = u' '.join(tweet_string_list).encode('utf-8').strip() 
            print tweet_string 
            log.write (check_string)
            tweet(tweet_string)
            just_tweeted.append(node_id)


def camelCase(st):
    print st
    return re.sub(r'\W+', '', st)

          
def string_in_file(string, file_path):
  found = False
  with open(file_path) as f:
    for line in f:  
      if line == string:
        found = True
  return found

def tweet (tweet_string):
  api = settings.api
  
  print(api.VerifyCredentials())

  status = api.PostUpdate(tweet_string)
  print status.text
  time.sleep(60)

main()
