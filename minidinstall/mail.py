# mail -*- mode: python; coding: utf-8 -*-

"""Simple mail support for mini-dinstall."""

# Copyright © 2008 Stephan Sürken <absurd@debian.org>

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

import smtplib
import email.mime.text

import logging

def send(smtp_server, smtp_from, smtp_to, body, subject="mini-dinstall mail notice"):
    """Send email; on error, log and continue."""

    logger = logging.getLogger("mini-dinstall")

    try:
        # Create a mime body
        mime_body = email.mime.text.MIMEText(body, 'plain', 'utf-8')
        mime_body['Subject'] = subject
        mime_body['From'] = smtp_from
        mime_body['To'] = smtp_to
        mime_body.add_header('X-Mini-Dinstall', 'YES')

        # Send via SMTP server
        smtp = smtplib.SMTP(smtp_server)
        smtp.sendmail(smtp_from, [smtp_to], mime_body.as_string())
        logger.info("Mail sent to %s (%s)" % (smtp_to, subject))
    except Exception, e:
        logger.exception("Error sending mail to %s ('%s') via %s: %s: %s", smtp_to, subject, smtp_server, type(e), e.args)
