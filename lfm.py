#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib, urllib2
import sys, os
import json
import linecache
import dateutil.parser, calendar, datetime
import collections
import codecs

class LFMPy:

   def __init__(self, username="docmatrix", filename="output.txt"):
      self.LFM_URL = "http://ws.audioscrobbler.com/2.0/?"
      self.API_KEY = "4b9024f7f463c51f13960fe5cedebab9"
      self.username = username
      self.filename  = filename


   """
   Craft the last api request using command line arguments and details from file
   """
   def send_request(self, args, **kwargs):
      #load supplied arguments
      kwargs.update(args)

      #add default args
      kwargs.update({"api_key" : self.API_KEY,
                     "format" : "json"})

      try:
         params = self.LFM_URL + urllib.urlencode(kwargs)
         data = urllib2.urlopen(params)
         response_data = json.load(data)
         data.close()
         return response_data
      except urllib2.HTTPError, e:
         print "HTTP error: %d" % e.code
      except urllib2.URLError, e:
         print "Network error: %s" % e.reason.args[1]

   def get_recent_tracks(self, last_access="0", first_track="0"):
      args = { "method" : "user.getrecenttracks",
               "user" : username,
               "from" : last_access,
               "to" : first_track}

      response_data = self.send_request(args)
      """
      Open file append response to start of the file
      """

      #output_file = codecs.open(filename, 'w', "utf-8")
      output_list = []
      for tracks in response_data["recenttracks"]["track"]:
         if tracks.has_key("@attr"):
            continue
         output_list.append({"timestamp" :
                        str(dateutil.parser.parse(tracks["date"]["#text"])),
                            "track_name" : tracks["name"],
                            "artist_name" : tracks["artist"]["#text"],
                            "album_name" : tracks["album"]["#text"],
                            "image" : tracks["image"][0]["#text"]}
                            )

      #output_file.write(json.dumps(output_list, indent=4)).close()

      #Return the datetime of first/last track received
      #To be used on subsequent runs of get_recent_tracks
      #return (output_list[0]["timestamp"],output_list[-1]["timestamp"])
      return output_list


if __name__ == "__main__":
   username = "docmatrix"
   filename = "output.txt"

   """
   Take in the command line parameters
   """
   if (len(sys.argv) != 3):
      print """Program requires 2 command line arguments
                           arg1 Lastfm username eg. docmatrix
                           arg2 Filename to store results"""
   else:
      username = sys.argv[1]
      filename = sys.argv[2]


   """
   If the file passed to the script exists, open it, parse json structure,
   check time of last track, convert time to UNIX time stamp format
   """
   if (os.path.exists(filename) and
      linecache.getline(filename, 1) is "[" and
      linecache.getline(filename, -1) is "]"):
      file_in = open(filename, 'r')
      file_in_json = json.loads(file_in.read())

      last_access_date = dateutil.parser.parse(file_in_json[0]["timestamp"])
      last_access = str(calendar.timegm(last_access_date.utctimetuple()))

      first_access_date = dateutil.parser.parse(file_in_json[-1]["timestamp"])
      first_access = str(calendar.timegm(first_access_date.utctimetuple()))

      first_run = False
   #If file does not exist, create it and set first/last values accordingly 
   else:
      open(filename,'w').close()
      first_run = True
      last_access = "0"
      first_access = "0"

   lastfm_request = LFMPy(username,filename)
   #datetime_tuple = lastfm_request.get_recent_tracks()

   #last_access = from first_track = to
   output_list = []
   #If it is the programs first run retrieve results 5 times and store in list
   if first_run:
      to_date = "0"
      for x in range(5):
         output_list.extend(lastfm_request.get_recent_tracks("0",to_date))
         to_str = dateutil.parser.parse(output_list[-1]["timestamp"])
         to_date = str(calendar.timegm(to_str.utctimetuple()))
         
         output_file = codecs.open(filename, 'w', "utf-8")
         output_file.write(json.dumps(output_list, indent=4))
         output_file.close()

         
   #If we already have results stored retrieve newer tracks then older
   else:
      #Grab newer tracks
      output_list.extend(lastfm_request.get_recent_tracks(last_access,"0"))

      output_file = codecs.open(filename, 'a', "utf-8")
      output_file.seek(0)
      output_file.write(json.dumps(output_list, indent=4))
      output_file.close()
      output_list = []

      #Grab older tracks
      for x in range(4):
         output_list.extend(last_fm_request.get_recent_tracks("0",first_access))
         from_str = dateutil.parser.parse(output_list[-1]["timestamp"])
         first_access = str(calendar.timegm(from_str.utctimetuple()))

         output_file = codecs.open(filename, 'a', "utf-8")
         output_file.seek(0)
         output_file.write(json.dumps(output_list, indent=4))
         output_file.close()
      
      





      
