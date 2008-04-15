#!/usr/bin/python
#
# Copyright (C) 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# This file demonstrates how to use the Google Data API's Python client library
# to interface with the Blogger service.  There are examples for the following
# operations:
#
# * Retrieving the list of all the user's blogs
# * Retrieving all posts on a single blog
# * Performing a date-range query for posts on a blog
# * Creating draft posts and publishing posts
# * Updating posts
# * Retrieving comments
# * Creating comments
# * Deleting comments
# * Deleting posts


__author__ = 'lkeppler@google.com (Luke Keppler)'

import sys
sys.path.append('/usr/share/python-support/python-elementtree/')

try:
  from xml.etree import ElementTree # for Python 2.5 users
except:
  from elementtree import ElementTree


import time
import gdata
import gdata_service
import atom
import getopt
import sys
import re

import encodings

class BloggerSync:

  def __init__(self, email, password):
    """Creates a GDataService and provides ClientLogin auth details to it.
    The email and password are required arguments for ClientLogin.  The
    'source' defined below is an arbitrary string, but should be used to
    reference your name or the name of your organization, the app name and
    version, with '-' between each of the three values."""

    # Authenticate using ClientLogin.
    self.service = gdata_service.GDataService(email, password)
    self.service.source = 'Blogger_Python_Sample-1.0'
    self.service.service = 'blogger'
    self.service.server = 'www.blogger.com'
    self.service.ProgrammaticLogin()

    self.commentservice= gdata_service.GDataService()
    self.commentservice.source= 'Bloggsynk'
    self.commentservice.service = 'blogger'
    self.commentservice.server = 'www.blogger.com'

    # Get the blog ID for the first blog.
    feed = self.service.Get('/feeds/default/blogs')


    #e = gdata.GDataEntry(feed.entry[0])
    #self_link = e.GetSelfLink()

    #print e
    
    #if self_link:
    #  self.blog_id = self_link.href.split('/')[-1]
    self.blog_id = '1938689576098732827'


  def PrintUserBlogTitles(self):
    """Prints a list of all the user's blogs."""

    # Request the feed.
    query = gdata_service.Query()
    query.feed = '/feeds/default/blogs'
    feed = self.service.Get(query.ToUri())

    # Print the results.
    print feed.title.text
    for entry in feed.entry:
      print "\t" + entry.title.text
    print

  def CreatePost(self, title, content, author_name, date,tag):
    """This method creates a new post on a blog.  The new post can be stored as
    a draft or published based on the value of the is_draft parameter.  The
    method creates an GDataEntry for the new post using the title, content,
    author_name and is_draft parameters.  With is_draft, True saves the post as
    a draft, while False publishes the post.  Then it uses the given
    GDataService to insert the new post.  If the insertion is successful, the
    added post (GDataEntry) will be returned.
    """

    # Create the entry to insert.
    entry = gdata.GDataEntry()
    entry.author.append(atom.Author(atom.Name(text=author_name)))
    entry.title = atom.Title('xhtml', title)
    entry.content = atom.Content('html', '', content)

    entry.published = atom.Published(date)
    entry.category = [atom.Category(tag)]
    
    # Ask the service to insert the new entry.

    return self.service.Post(entry, 
                               '/feeds/' + self.blog_id + '/posts/default')
    

  def PrintAllPosts(self):
    """This method displays the titles of all the posts in a blog.  First it
    requests the posts feed for the blogs and then it prints the results.
    """

    # Request the feed.
    feed = self.service.GetFeed('/feeds/' + self.blog_id + '/posts/default')

    # Print the results.
    print feed.title.text
    for entry in feed.entry:
      if not entry.title.text:
        print "\tNo Title"
      else:
        print "\t" + entry.title.text
    print


  def DeleteAllPosts(self):
    feed = self.service.GetFeed('/feeds/' + self.blog_id + '/posts/default')

    print feed.title.text
    for entry in feed.entry:
      #print entry.title
      
      for p in entry.link:
        if p.rel == 'edit':
          print "Removing post "+p.href
          self.DeletePost(p.href)
    print
    

  def PrintPostsInDateRange(self, start_time, end_time):
    """This method displays the title and modification time for any posts that
    have been created or updated in the period between the start_time and
    end_time parameters.  The method creates the query, submits it to the
    GDataService, and then displays the results.
  
    Note that while the start_time is inclusive, the end_time is exclusive, so
    specifying an end_time of '2007-07-01' will include those posts up until
    2007-6-30 11:59:59PM.

    The start_time specifies the beginning of the search period (inclusive),
    while end_time specifies the end of the search period (exclusive).
    """

    # Create query and submit a request.
    query = gdata_service.Query()
    query.feed = '/feeds/' + self.blog_id + '/posts/default'
    query.updated_min = start_time
    query.updated_max = end_time
    feed = self.service.Get(query.ToUri())

    # Print the results.
    print feed.title.text + " posts between " + start_time + " and " + end_time
    print feed.title.text
    for entry in feed.entry:
      if not entry.title.text:
        print "\tNo Title"
      else:
        print "\t" + entry.title.text
    print

  def UpdatePostTitle(self, entry_to_update, new_title):
    """This method updates the title of the given post.  The GDataEntry object
    is updated with the new title, then a request is sent to the GDataService.
    If the insertion is successful, the updated post will be returned.

    Note that other characteristics of the post can also be modified by
    updating the values of the entry object before submitting the request.

    The entry_to_update is a GDatEntry containing the post to update.
    The new_title is the text to use for the post's new title.  Returns: a
    GDataEntry containing the newly-updated post.
    """
    
    # Set the new title in the Entry object
    entry_to_update.title = atom.Title('xhtml', new_title)
    
    # Grab the edit URI
    edit_uri = entry_to_update.GetEditLink().href  

    return self.service.Put(entry_to_update, edit_uri)

  def CreateComment(self, post_id, comment_text, author_name, date):
    """This method adds a comment to the specified post.  First the comment
    feed's URI is built using the given post ID.  Then a GDataEntry is created
    for the comment and submitted to the GDataService.  The post_id is the ID
    of the post on which to post comments.  The comment_text is the text of the
    comment to store.  Returns: an entry containing the newly-created comment

    NOTE: This functionality is not officially supported yet.
    """

    # Build the comment feed URI
    feed_uri = '/feeds/' + self.blog_id + '/' + post_id + '/comments/default'

    print feed_uri
    
    # Create a new entry for the comment and submit it to the GDataService
    entry = gdata.GDataEntry()
    entry.content = atom.Content('xhtml', '', comment_text)
    #entry.body = atom.Content('xhtml', '', comment_text)

    entry.author.append(atom.Author(atom.Name(text=author_name)))
    entry.published = atom.Published(date)

    return self.commentservice.Post(entry, feed_uri)

  def PrintAllComments(self, post_id):
    """This method displays all the comments for the given post.  First the
    comment feed's URI is built using the given post ID.  Then the method
    requests the comments feed and displays the results.  Takes the post_id
    of the post on which to view comments. 
    """

    # Build comment feed URI and request comments on the specified post
    feed_url = '/feeds/' + self.blog_id + '/comments/default'
    feed = self.service.Get(feed_url)

    # Display the results
    print feed.title.text
    for entry in feed.entry:
      print "\t" + entry.title.text
      print "\t" + entry.updated.text
    print

  def DeleteComment(self, post_id, comment_id):
    """This method removes the comment specified by the given edit_link_href, the
    URI for editing the comment.
    """
    
    feed_uri = '/feeds/' + self.blog_id + '/' + post_id + '/comments/default/' + comment_id
    self.service.Delete(feed_uri)

  def DeletePost(self, edit_link_href):
    """This method removes the post specified by the given edit_link_href, the
    URI for editing the post.
    """

    self.service.Delete(edit_link_href)
  
  def run(self,p):
    """Runs each of the example methods defined above, demonstrating how to
    interface with the Blogger service.
    """


    #self.DeleteAllPosts()

    entries = []

    for x in range(10):
      feed = self.service.GetFeed('/feeds/' +
                                  self.blog_id +
                                  '/posts/default?max-results=100&start-index=%d' % (x*100+1) )
      for q in feed.entry:
        if not q in entries:
          entries.append(q)

    ind = 0
    o=open('/tmp/hmmap.txt','w')
    
    for post in p:
      ind = ind+1
      
#      if ind in (171,):
#        ind=ind+1

      newdate  = convertdate(post['date'])
      print newdate
      ex = 0
      print len(feed.entry)

      thisentry=None
      
      for entry in entries:
        #print entry.title
        #print atom.Title('text',post['title'])
        #print str(entry.published)[:66]
        #print str(atom.Published(newdate))[:66]
        
        if str(entry.title) == str(atom.Title('text',post['title'])) and str(entry.published)[:66] == str(atom.Published(newdate))[:66]:
          print "Post %s already exists, skipping " % entry.title
          ex = 1
          self_id = entry.id.text 
          tokens = self_id.split("-")
          post_id = tokens[-1]
          url = entry.link

      if not ex:
        print "Creating post titled %s" % repr(post['title'])
        new_post = self.CreatePost(post['title'],post['content'],'Pontus',newdate,post['primary category'])

	#        time.sleep(5)
        self_id = new_post.id.text 
        tokens = self_id.split("-")
        post_id = tokens[-1]
        url = new_post.link

        if new_post.title.text:
          print "Successfully created post: \"" + new_post.title.text + "\". %s \n" % post_id


      o.write('%d %s\n' % (ind,url[0].href))


      if post.has_key('comments'):
        for c in post['comments']:
          try:
	    new_comment = self.CreateComment(post_id, c['text'], c['author'], convertdate(c['date']))
            print "Created comment "+repr(new_comment)
	    time.sleep(160)
            pass
          except Exception,e:
            print "Comment creation failed for %s" % post_id
            print e
	    pass
          
        
    # Demonstrate deleting posts.
    #print "Now deleting the post titled: \"" + public_post.title.text + "\"."
    #self.DeletePost(edit_uri)
    #print "Successfully deleted post." 
    #self.PrintAllPosts()



def readline(f):
  k=f.readline()
  #print k
  return encodings.utf_8.decode(k.strip())[0]


def convertdate(s):
  t=time.strptime(s,"%m/%d/%Y %H:%M:%S")
  m = time.mktime(t)
  return time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime(m))

  m=s[0:2]
  y=s[6:10]
  d=s[3:5]

  h=s[11:13]
  ms=s[14:]

  if int(h)<8:
    h=str(int(h)+12)

  tz="+0100"
  if int(m) > 4 and int(m)<11:
    tz="+0200"

  return "%s-%s-%sT%s:%s%s" % (y,m,d,h,ms,tz)

def readPost(f):
  s = ''

  post={}
  
  while s!= '-----':
    s = readline(f)

    if s and s!='-----':

      l = s[:s.index(':')].lower()
      r = s[s.index(':')+2:]

      post[l] = r


  s = readline(f)

  if s != 'BODY:':
    print 'Error'

  content=''
  s=''
  
  while s!= '-----':
    content = content+s
    s = readline(f)

  post['content'] = content

  
  while s!= '--------':
    s=readline(f)

    if s == 'COMMENT:':

      comment = {}
      
      s=readline(f)
      comment['author'] = s[s.index(':')+2:]
      s=readline(f)
      s=readline(f)
      s=readline(f)
      s=readline(f)
      comment['date'] = s[s.index(':')+2:]
            
      c=''
      s =''
      
      while s!= '-----':
        c = c+s
        s = readline(f)
      
      comment['text'] = c

      if post.has_key('comments'):
        post['comments'].append(c)
      else:
        post['comments'] = [comment]
      
  
  return post
  



def main():
  """The main function runs the BloggerSync application with the provided
  username and password values.  Authentication credentials are required.
  NOTE:  It is recommended that you run this sample using a test account."""

  # parse command line options
  try:
    opts, args = getopt.getopt(sys.argv[1:], "", ["email=", "password="])
  except getopt.error, msg:
    print ('python BloggerSync.py --email [email] --password [password] ')
    sys.exit(2)

  email = ''
  password = ''

  # Process options
  for o, a in opts:
    if o == "--email":
      email = a
    elif o == "--password":
      password = a
    
  if email == '' or password == '':
    print ('python BloggerSync.py --email [email] --password [password]')
    sys.exit(2)

  sample = BloggerSync(email, password)


  f = open('/home/pontus/Desktop/c.txt')
  p = readPost(f)

  posts = []

  f.seek(0,2)
  end = f.tell()
  f.seek(0,0)
  
  while p and f.tell() != end :
    p = readPost(f)
    posts.append(p)


            
  sample.run(posts)


if __name__ == '__main__':
  main()
