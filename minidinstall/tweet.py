# mail -*- mode: python; coding: utf-8 -*-

"""Simple tweet support for mini-dinstall."""

# Copyright © 2010 Christopher R. Gabriel <cgabriel@truelite.it>

# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.


import logging
import urllib2
import base64

def send(tweet_body, tweet_server, tweet_user, tweet_password):
    """Send tweet; on error, log and continue."""
    logger = logging.getLogger("mini-dinstall")
    post_url = None
    auth_realm = None
    if tweet_server == 'identica':
        post_url = 'http://identi.ca/api/statuses/update.json'
        auth_realm = 'Identi.ca API'
    if tweet_server == 'twitter':
        post_url = 'http://api.twitter.com/1/statuses/update.json'
        auth_realm = 'Twitter API'

    if not post_url:
        logger.exception("Unknown tweet site")
    if not tweet_user or not tweet_password:
        logger.exception("Missing username or password for twitting")

    auth_handler = urllib2.HTTPBasicAuthHandler()
    auth_handler.add_password(realm=auth_realm,
                              uri=post_url,
                              user=tweet_user,
                              passwd=tweet_password)
    m_http_opener = urllib2.build_opener(auth_handler)

    req = urllib2.Request(post_url)
    req.add_data("status=%s" % tweet_body)
    handle = None
    try:
        handle = m_http_opener.open(req)
        a = handle.read()
        logger.info("Tweet sent to %s (%s)" % (tweet_server, tweet_user))
    except Exception, e:
        logger.exception("Error sending tweet to %s ('%s') via %s: %s: %s", tweet_server, tweet_body, tweet_user, type(e), e.args)
