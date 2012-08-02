#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib, urllib2
import sys, os
import json
import linecache
import dateutil.parser, calendar, datetime, time
import collections
import codecs

class LFMPy:

   def __init__(self, username="docmatrix", filename="output.txt"):
      """Initialisation function for LFMPy

      Arguments:
      username -- the username whose profile is to be quried
         defaults to docmatrix for testing purposees
      filename -- the output file where returned data is to be stored
         defaults to output.txt for testing purposes

      Constants:
      LFM_URL -- url of the lastfm api
      API_KEY -- the api_key used for the programs queries

      """
      self.LFM_URL = "http://ws.audioscrobbler.com/2.0/?"
      self.API_KEY = "4b9024f7f463c51f13960fe5cedebab9"
      self.username = username
      self.filename  = filename


   def send_request(self, args, **kwargs):
      """Function to craft and send api request to lastfm.

         Keyword arguments:
         args -- list of arguments to be used in request
         **kwargs -- unpacked dictionary

         Returns:
         reponse_data -- json formatted response from the lastfm API
      """

      #load supplied arguments
      kwargs.update(args)

      #add default arguments
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
         sys.exit(1)
      except urllib2.URLError, e:
         print "Network error: %s" % e.reason.args[1]
         sys.exit(1)
   
   def get_recent_tracks(self, last_track="0", first_track="0"):
      """Function to request the recently played tracks from lastfm API
         within the given time period constraint of to/from used by the
         lastfm api.

         When we are requesting newer tracks it will be:
            from:last_track   ->    to: time now
         When we are requesting older tracks it will be:
            from: "0"         ->    to: last_track

         Keyword arguments:
         last_track -- the newest track currently in file
         first_track -- the oldest track currently in file

         Returns:
         Tuple containing:
            output_list: A list of dictionaries

               each dictionary encapsulates 1 track and it's relevant data
                     -- timestamp
                     -- track_name
                     -- artist_name
                     -- album_name
                     -- image
            total_pages: the number of pages from that time period
            This is used in the case of new tracks to be added, so that
            all new tracks are added to data. To prevent fragmentation
            within data file.
                  
      """
      
      args = { "method" : "user.getrecenttracks",
               "user" : username,
               "from" : last_track,
               "to" : first_track}

      #Send a lastfm api request with given arguments
      response_data = self.send_request(args)

      return_list = []

      total_pages = int(response_data["recenttracks"]["@attr"]["totalPages"])

      if int(response_data["recenttracks"]["@attr"]["total"]) == 1:
         tmp_dict = { "timestamp" :
            str(dateutil.parser.parse(response_data["recenttracks"]["track"]["date"]["#text"])),
                      "track_name": response_data["recenttracks"]["track"]["name"],
                     "artist_name" : response_data["recenttracks"]["track"]["artist"]["#text"],
                     "album_name" : response_data["recenttracks"]["track"]["album"]["#text"],
                      "image" : response_data["recenttracks"]["track"]["image"][0]["#text"]
            }
         return ([tmp_dict],total_pages)

      """Enumerate over the json structure extracting the relevant data
      and storing it in in output_list structure which when finished will
      contain a list of dictionaries"""
      for tracks in response_data["recenttracks"]["track"]:
         #Skip nowplaying track
         if '@attr' in tracks and 'nowplaying' in tracks['@attr']:
            print "Skipping now playing"
            continue

         if 'date' in tracks and '#text' in tracks['date']:
            date_str = str(dateutil.parser.parse(tracks["date"]["#text"]))
         else:
            print "Problem reading date from server response"
            print tracks
            date_str = "ERROR"

         return_list.append({"timestamp" : date_str,
                            "track_name" : tracks["name"],
                            "artist_name" : tracks["artist"]["#text"],
                            "album_name" : tracks["album"]["#text"],
                            "image" : tracks["image"][0]["#text"]}
                            )

      #Return the list/json structure and total pages remaining in query
      return return_list,total_pages


if __name__ == "__main__":
   username = "docmatrix"
   filename = "output.txt"
   json_list = []

   """
   Take in the command line parameters
      arg1 -- last.fm username
      arg2 -- filename for data to be outputted to

   If none specified use defaults for testing purposes
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
   check time of last/first track, convert time to UNIX time stamp format
   """
   if (os.path.exists(filename)):
      print "Output file already exists appending tracks to given file."
      file_in = open(filename, 'r')
      file_in_str = file_in.read()

      try:
         json_list = json.loads(file_in_str)

      except ValueError, e:
         print "File specified exists but does not contain valid JSON. \n" \
            "Continuing execution of program as if it was a first run."
         first_run = True
      else:
         last_access_date = dateutil.parser.parse(json_list[0]["timestamp"])
         last_access = str(calendar.timegm(last_access_date.utctimetuple()))

         first_access_date = dateutil.parser.parse(json_list[-1]["timestamp"])
         first_access = str(calendar.timegm(first_access_date.utctimetuple()))         
         
         first_run = False
      
   #If file does not exist, create it and set first/last values accordingly 
   else:
      print "New output file specified creating file"
      open(filename,'w').close()
      first_run = True
      last_access = "0"
      first_access = "0"


   lastfm_request = LFMPy(username,filename)

   output_list = []

   #If it is the programs first run retrieve results 5 times and store in list
   if first_run:
      to_date = "0"
      print "Querying LastFm API and writing results to file"
      for x in range(5):
         (tmp_list, _)= lastfm_request.get_recent_tracks("0", to_date) 
         output_list.extend(tmp_list)
         to_str = dateutil.parser.parse(output_list[-1]["timestamp"])
         to_date = str(calendar.timegm(to_str.utctimetuple()))
         
      #Write results to file
      print "Writing %d track details to file" % len(output_list)
      output_file = codecs.open(filename, 'w', "utf-8")
      output_file.write(json.dumps(output_list, indent=4))
      output_file.close()

         
   #If we already have results stored retrieve newer tracks then older
   else:
      print "Querying LastFm API and writing results to file"

      #Grab newer tracks
      current_time = str(int(time.time()))

      #Query once to retrieve first group of results and number of remaining result pages
      (tmp_list,page_count) = lastfm_request.get_recent_tracks(last_access, current_time)
      tmp_time = dateutil.parser.parse(tmp_list[-1]["timestamp"])
      current_time = str(calendar.timegm(tmp_time.utctimetuple()))
      output_list.extend(tmp_list)
      tmp_list = []

      
      for x in range(page_count-1):
         (tmp_list,_) = lastfm_request.get_recent_tracks(last_access, current_time)
         current_time = str(dateutil.parser.parse(tmp_list[-1]["timestamp"]))
         output_list.extend(tmp_list)
         tmp_list = []
         

      print "Adding new %d track details to beginning of file" % len(output_list)

      #Prepend output_list to json_list then reset output_list
      json_list = output_list + json_list
      output_list = []


      #Grab older tracks range is reduced if more pages of new tracks were retrieved
      #To stay within limit of 5 queries per script execution
      for x in range(4-page_count):
         (tmp_list, _) = lastfm_request.get_recent_tracks("0",first_access)
         output_list.extend(tmp_list)
         
         from_str = dateutil.parser.parse(output_list[-1]["timestamp"])
         first_access = str(calendar.timegm(from_str.utctimetuple()))

      #Append output_list to json_list
      print "Adding %d older track details to end of file" % len(output_list)
      json_list = json_list + output_list

      
      #Write json_list to file
      output_file = codecs.open(filename, 'w', "utf-8")
      output_file.write(json.dumps(json_list, indent=4))
      output_file.close()



      
