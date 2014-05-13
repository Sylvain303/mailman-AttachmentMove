#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: et sw=4 ts=4:
#
# This script is opensource and can be found here:
# https://github.com/Sylvain303/mailman-AttachmentMove
#
# Copyright (C) 2001-2011 by the Free Software Foundation, Inc.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301,
# USA.

""" Mail attachment detach filter

The detached parts are stored as attachment on the list archive. But the 
attachment used is a fresh copy uploaded to a remote location given by the
extra parameters:

mlist.ftp_remote_host = 'ftp.example.com'
mlist.ftp_remote_login = 'username'
mlist.ftp_remote_pass = 'secr3te'
# put the ending slash /
mlist.remote_http_base = 'http://example.com/root/for/username/'

can be added from command line with list_config


to be set in lists/yourlistname/extend.py

import copy
from Mailman import mm_cfg
def extend(mlist):
    mlist.pipeline = copy.copy(mm_cfg.GLOBAL_PIPELINE)
    # The next line inserts MyHandler ahead of Moderate.
    mlist.pipeline.insert(mlist.pipeline.index('Moderate'), 'MyHandler')
    # Alternatively, the next line replaces Moderate with MyHandler
    #mlist.pipeline[mlist.pipeline.index('Moderate')] = 'MyHandler'
    # Pick one of the two above example alternatives

    mlist.ftp_remote_host = 'ftp.example.com'
    mlist.ftp_remote_login = 'username'
    mlist.ftp_remote_pass = 'secr3te'
    # put the ending slash /
    mlist.remote_http_base = 'http://example.com/root/for/username/'

"""


from __future__ import nested_scopes

import os
import re
import time
import errno
import binascii
import tempfile
from cStringIO import StringIO
from types import IntType, StringType

from email.Utils import parsedate
from email.Parser import HeaderParser
from email.Generator import Generator
from email.Charset import Charset, QP, BASE64
from email.MIMEMultipart import MIMEMultipart
from email.mime.image import MIMEImage
from email import encoders


from Mailman import mm_cfg
from Mailman import Utils
from Mailman import LockFile
from Mailman import Message
from Mailman.Errors import DiscardMessage
from Mailman.i18n import _
from Mailman.Logging.Syslog import syslog
from Mailman.Utils import sha_new

from ftplib import FTP_TLS

# Path characters for common platforms
pre = re.compile(r'[/\\:]')
# All other characters to strip out of Content-Disposition: filenames
# (essentially anything that isn't an alphanum, dot, dash, or underscore).
sre = re.compile(r'[^-\w.]')
# Regexp to strip out leading dots
dre = re.compile(r'^\.*')

# match mutipart content-type
mutipartre = re.compile(r'^multipart/')

BR = '<br>\n'
SPACE = ' '

HTML_ATTACHMENT_HOLDER = """
   <br>
   <div style="padding: 15px; background-color: rgb(217, 237, 255);">
      <div style="margin-bottom: 15px;">Pi&egrave;ce jointe disponible ici
      :</div>
          <div style="background-color: rgb(255, 255, 255); padding: 15px;">
          %(HTML_HERE)s
          </div>
   </div>
"""

HTML_ATTACHMENT_CLIP_TPL = """
<div style="border: 1px solid rgb(205, 205, 205); border-radius:
  5px 5px 5px 5px; margin-top: 10px; margin-bottom: 10px;
  padding: 15px;" class="cloudAttachmentItem"><img
    src="cid:%(CID_clip)s"
    style="margin-right: 5px; float: left; width: 24px; height:
    24px;"><a style="color: rgb(15, 126, 219) ! important;" 
    href="%(URL_replace)s">%(FNAME_replace)s</a><span
    style="margin-left: 5px; font-size: small; color: grey;">
    (%(SIZE_replace)s)</span>
</div>
"""

TXT_ATTACHT_REPLACE = """
--------------------
Mailman attachment :
--------------------
Pièce jointe disponible ici :
"""

# Content-Type: image/png; name="attachment-24.png"
# Content-Transfer-Encoding: base64
# Content-ID: <part1.%(CID_clip)s>
# Content-Disposition: inline; filename="attachment-24.png"

# embeded clip picture base64

ATTACH_CLIP = """
iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAABHNCSVQICAgIfAhkiAAAAAlw
SFlzAAAN1wAADdcBQiibeAAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoA
AAH+SURBVEiJ7ZVNaxNRFIaf09T6AXXpUgQpfmGnSmYSsCB0qe50pdJFuxEVKhUEQVBcCipI
S+yiG21dxLoTEQQFV83MBJJpF0LxRyiK0EzmddEkGMlnxV0PDMzc97znuefeuTMmif8Zg+2E
dDq9KyY1LZjFGGkSxYbBk0Gqi2EYVrYFiElNy8i1FI0RQS4mJWChE2CgnSCY3brRTBT6qXJQ
sHJQsCj0U5jdquXMdCreEVBflqgYzElKGmApOXLo4Fzt8RiA43orjpdZ7g/wR8FRN/PWcbNv
6mP5fL7612wuIi638rfdgyY7nIftvW1dO/jX2AHsABohgKPj48MAjnPmQG08aevoE/AZYGgz
vgTAUHwdAONdN2OPB81eCJ016bbjZr9T/05VedrN26mDbwCnPG8s/rU3j9gAToBWgGGMV+Vi
4WN92foHyJYBEtmd9fVPPyzFBUEAIOlhFPhXAXZvVp7XDGutyli7P9rpbPZ4taoisMfgWiko
LACcTKcPr4XhV4AxNzsltAj8lKrpKAy/9AwAGPW8KyZbAipmmir5/lJDc7PnDL0G9hk2WQpW
X/bVQT0cN/MAuL+VbY+TJM4ZA5Nmdg8YMDRfCvyb7fxdAbXZ3jD0jOY9SwR3o6DwqJO3p3MQ
BavzMk0A74HE0AeZJroVB0BSX1cmk9nfT/5vekgJrtOb2V0AAAAASUVORK5CYII=
"""

try:
    True, False
except NameError:
    True = 1
    False = 0


try:
    from mimetypes import guess_all_extensions
except ImportError:
    import mimetypes
    def guess_all_extensions(ctype, strict=True):
        # BAW: sigh, guess_all_extensions() is new in Python 2.3
        all = []
        def check(map):
            for e, t in map.items():
                if t == ctype:
                    all.append(e)
        check(mimetypes.types_map)
        # Python 2.1 doesn't have common_types.  Sigh, sigh.
        if not strict and hasattr(mimetypes, 'common_types'):
            check(mimetypes.common_types)
        return all

def process(mlist, msg, msgdata=None):
    # main entry code for the Handler

    if msgdata is None:
        msgdata = {}
    
    modified = False
    
    dir = calculate_attachments_dir(mlist, msg, msgdata)
    syslog('debug', 'dir: %s', dir)
    # Now walk over all subparts of this message and scrub out various types
    seen_attachment = []
    boundary = None
    
    for part in msg.walk():
        ctype = part.get_content_type()
        partlen = len(part.get_payload())
        syslog('debug', 'met part : %s %d', ctype, partlen)

        # If the part is text/plain, we leave it alone
        if ctype == 'text/plain':
            continue
        elif ctype == 'text/html':
            continue
        elif ctype == 'message/rfc822':
            continue
        elif partlen > 0 and not part.is_multipart():
            # we met an attachment
            syslog('debug', '> part is attachment %s', ctype)
            if part.has_key('Content-ID'):
                syslog('debug', '> part as Content-ID %s', part['Content-ID'])
                # keep it
                continue
            else:
                syslog('debug', '> detaching...')

            # we are going to detach it and store it localy and remotly
            # a dic storing attachment related data
            attachment = {}
            fname = get_attachment_fname(mlist, part)
            attachment['name'] = fname
            attachment['orig'] = fname
            attachment['size'] = sizeof_fmt(partlen)
            syslog('debug', '> att: %s', fname)
            # save attachment to the disk, at this stage duplicate name
            # are resolved
            path, url = save_attachment(mlist, part, dir)
            syslog('debug', '> detached: %s %s', path, url)
            # remote storing, no trouble very simple code here using
            # secured FTP and the remote user config
            remote_fname = ftp_upload_attchment(mlist, path)
            # build the new url of the document, will be used when 
            # modifying parts see bellow.
            url = mlist.remote_http_base + remote_fname
            attachment['url'] = url
            # replace the attachment by a small plain/text 
            new_payload = TXT_ATTACHT_REPLACE + make_link(attachment)
            reset_payload(part, new_payload, fname, url)
            seen_attachment.append(attachment)
            modified = True
            continue
        elif mutipartre.search(ctype):
            # match multipart/*
            boundary = part.get_boundary()
            syslog('debug', '>>> is multipart part %s, boundary: %s',
                ctype, boundary)
            continue
        else:
            if boundary != None and part.get_boundary() == boundary:
                syslog('debug', 'same boundary skiped : %s', ctype)
                continue
            else:
                boundary = None
            syslog('debug', 'attachement : %s', ctype)
        syslog('debug', 'end of loop?? : %s', ctype)

    if not modified:
        return msg

    # rewrite content
    footer_attach = ''
    html_footer_attach = ''
    replace = {}
    clip_cid = "clip.12345789"
    clip = MIMEImage(ATTACH_CLIP, 'png', _encoder=encoders.encode_noop)
    clip['Content-Transfer-Encoding'] = 'base64'
    clip.add_header('Content-ID', '<part1.%s>' % clip_cid)

    # compose attachment url
    for att in seen_attachment:
        footer_attach += make_link(att) + "\n"

        replace['CID_clip'] = 'part1.' + clip_cid
        replace['FNAME_replace'] = att['orig']
        replace['URL_replace'] = att['url']
        replace['SIZE_replace'] = att['size']
        html_footer_attach += HTML_ATTACHMENT_CLIP_TPL % replace
   
    fix_msg(msg, footer_attach, html_footer_attach, clip)

    return msg

def reset_payload(msg, txt, fname, url):
    # Reset payload of msg to contents of subpart, and fix up content headers
    msg.set_payload(txt)
    del msg['content-type']
    del msg['content-transfer-encoding']
    del msg['content-disposition']
    del msg['content-description']
    
    msg.add_header('X-Mailman-Part', 'Attachment-moved', url=url)
    msg.add_header('Content-Type', 'text/plain', charset='UTF-8', name=fname)
    msg.add_header('Content-Transfer-Encoding', '8bit')
    msg.add_header('Content-Disposition', 'attachment', filename=fname)
    msg.add_header('Content-Description', "Attachment-moved by Mailman")


def fix_msg(msg, txt_attach, html_attach, clip_payload):
    """
    Scan the message recursively to replace the text/html by a 
    multipart/related containing the original text/html and the new 
    clip_payload png attachment
    """

    if msg.is_multipart():
        parts = msg.get_payload()
        # remove the next level parts, then process and reattach them
        msg.set_payload(None)
        for p in parts:
            msg.attach(fix_msg(p, txt_attach, html_attach, clip_payload))
        return msg
    else:
        # process the 'leaf' parts
        ctype = msg.get_content_type()
        if ctype == 'text/plain' and not msg['X-Mailman-Part']:
            # add footer to plain text
            new_footer = TXT_ATTACHT_REPLACE + txt_attach
            msg.set_payload(msg.get_payload() + new_footer)
            syslog('debug', 'add txt footer')
            return msg
        elif ctype == 'text/html':
            # build multipart/related for HTML
            related = MIMEMultipart('related')

            html_footer = HTML_ATTACHMENT_HOLDER % {'HTML_HERE': html_attach}
            html_footer += '</body>'
            old_content = msg.get_payload(decode=True)
            new_content = re.sub(r'</body>', html_footer, old_content)
            if old_content != new_content:
                syslog('debug', 'add html footer')
            else:
                syslog('debug', 'no html footer added')
            charset = msg.get_content_charset()
            syslog('debug', 'get_content_charset: %s, Content-Transfer-Encoding: %s', charset, msg['Content-Transfer-Encoding'])

            del msg['content-transfer-encoding']
            charset = Charset("utf-8")
            charset.header_encoding = BASE64
            charset.body_encoding = BASE64
            msg.set_charset(charset)
            msg.set_payload(new_content)

            related.attach(msg)
            related.attach(clip_payload)
            return related
        # unmodified
        return msg

def make_link(att):
    return att['orig'] + ' <' + att['url'] + '> (' + att['size'] + ')' 

def sizeof_fmt(num):
    #for x in ['bytes','KB','MB','GB','TB']:
    for x in ['octets','Ko','Mo','Go','To']:
        if num < 1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0

def guess_extension(ctype, ext):
    # mimetypes maps multiple extensions to the same type, e.g. .doc, .dot,
    # and .wiz are all mapped to application/msword.  This sucks for finding
    # the best reverse mapping.  If the extension is one of the giving
    # mappings, we'll trust that, otherwise we'll just guess. :/
    all = guess_all_extensions(ctype, strict=False)
    if ext in all:
        return ext
    return all and all[0]


def safe_strftime(fmt, t):
    try:
        return time.strftime(fmt, t)
    except (TypeError, ValueError, OverflowError):
        return None


def calculate_attachments_dir(mlist, msg, msgdata):
    # Calculate the directory that attachments for this message will go
    # under.  To avoid inode limitations, the scheme will be:
    # archives/private/<listname>/attachments/YYYYMMDD/<msgid-hash>/<files>
    # Start by calculating the date-based and msgid-hash components.
    fmt = '%Y%m%d'
    datestr = msg.get('Date')
    if datestr:
        now = parsedate(datestr)
    else:
        now = time.gmtime(msgdata.get('received_time', time.time()))
    datedir = safe_strftime(fmt, now)
    if not datedir:
        datestr = msgdata.get('X-List-Received-Date')
        if datestr:
            datedir = safe_strftime(fmt, datestr)
    if not datedir:
        # What next?  Unixfrom, I guess.
        parts = msg.get_unixfrom().split()
        try:
            month = {'Jan':1, 'Feb':2, 'Mar':3, 'Apr':4, 'May':5, 'Jun':6,
                     'Jul':7, 'Aug':8, 'Sep':9, 'Oct':10, 'Nov':11, 'Dec':12,
                     }.get(parts[3], 0)
            day = int(parts[4])
            year = int(parts[6])
        except (IndexError, ValueError):
            # Best we can do I think
            month = day = year = 0
        datedir = '%04d%02d%02d' % (year, month, day)
    assert datedir
    # As for the msgid hash, we'll base this part on the Message-ID: so that
    # all attachments for the same message end up in the same directory (we'll
    # uniquify the filenames in that directory as needed).  We use the first 2
    # and last 2 bytes of the SHA1 hash of the message id as the basis of the
    # directory name.  Clashes here don't really matter too much, and that
    # still gives us a 32-bit space to work with.
    msgid = msg['message-id']
    if msgid is None:
        msgid = msg['Message-ID'] = Utils.unique_message_id(mlist)
    # We assume that the message id actually /is/ unique!
    digest = sha_new(msgid).hexdigest()
    return os.path.join('attachments', datedir, digest[:4] + digest[-4:])


def makedirs(dir):
    # Create all the directories to store this attachment in
    try:
        os.makedirs(dir, 02775)
        # Unfortunately, FreeBSD seems to be broken in that it doesn't honor
        # the mode arg of mkdir().
        def twiddle(arg, dirname, names):
            os.chmod(dirname, 02775)
        os.path.walk(dir, twiddle, None)
    except OSError, e:
        if e.errno <> errno.EEXIST: raise

def get_attachment_fname(mlist, msg):
    # i18n file name is encoded
    lcset = Utils.GetCharSet(mlist.preferred_language)
    filename = Utils.oneline(msg.get_filename(''), lcset)
    return filename


def save_attachment(mlist, msg, dir):
    # attachment is extracted from the message part pointed by msg and stored
    # to standard mailman attachement dir. See Mailman/Handlers/Scrubber.py 
    # where this code come from. Scrubber specific behavior have been removed
    # the return value is a composed pair, physical filename and it's mailman's
    # list url. Not used by this handler, see ftp_upload_attchment().
    fsdir = os.path.join(mlist.archive_dir(), dir)
    makedirs(fsdir)
    # Figure out the attachment type and get the decoded data
    decodedpayload = msg.get_payload(decode=True)
    # BAW: mimetypes ought to handle non-standard, but commonly found types,
    # e.g. image/jpg (should be image/jpeg).  For now we just store such
    # things as application/octet-streams since that seems the safest.
    ctype = msg.get_content_type()
    filename = get_attachment_fname(mlist, msg)
    filename, fnext = os.path.splitext(filename)
    # HTML message doesn't have filename :-(
    ext = fnext or guess_extension(ctype, fnext)
    if not ext:
        # We don't know what it is, so assume it's just a shapeless
        # application/octet-stream, unless the Content-Type: is
        # message/rfc822, in which case we know we'll coerce the type to
        # text/plain below.
        if ctype == 'message/rfc822':
            ext = '.txt'
        else:
            ext = '.bin'
    # Allow only alphanumerics, dash, underscore, and dot
    ext = sre.sub('', ext)
    path = None
    # We need a lock to calculate the next attachment number
    lockfile = os.path.join(fsdir, 'attachments.lock')
    lock = LockFile.LockFile(lockfile)
    lock.lock()
    try:
        # Now base the filename on what's in the attachment, uniquifying it if
        # necessary.
        if not filename:
            filebase = 'attachment'
        else:
            # Sanitize the filename given in the message headers
            parts = pre.split(filename)
            filename = parts[-1]
            # Strip off leading dots
            filename = dre.sub('', filename)
            # Allow only alphanumerics, dash, underscore, and dot
            filename = sre.sub('', filename)
            # If the filename's extension doesn't match the type we guessed,
            # which one should we go with?  For now, let's go with the one we
            # guessed so attachments can't lie about their type.  Also, if the
            # filename /has/ no extension, then tack on the one we guessed.
            # The extension was removed from the name above.
            filebase = filename
        # Now we're looking for a unique name for this file on the file
        # system.  If msgdir/filebase.ext isn't unique, we'll add a counter
        # after filebase, e.g. msgdir/filebase-cnt.ext
        counter = 0
        extra = ''
        while True:
            path = os.path.join(fsdir, filebase + extra + ext)
            # Generally it is not a good idea to test for file existance
            # before just trying to create it, but the alternatives aren't
            # wonderful (i.e. os.open(..., O_CREAT | O_EXCL) isn't
            # NFS-safe).  Besides, we have an exclusive lock now, so we're
            # guaranteed that no other process will be racing with us.
            if os.path.exists(path):
                counter += 1
                extra = '-%04d' % counter
            else:
                break
    finally:
        lock.unlock()
    # `path' now contains the unique filename for the attachment. 
    fp = open(path, 'w')
    fp.write(decodedpayload)
    fp.close()
    # Now calculate the url
    baseurl = mlist.GetBaseArchiveURL()
    # Private archives will likely have a trailing slash.  Normalize.
    if baseurl[-1] <> '/':
        baseurl += '/'
    # A trailing space in url string may save users who are using
    # RFC-1738 compliant MUA (Not Mozilla).
    # Trailing space will definitely be a problem with format=flowed.
    # Bracket the URL instead.
    url = baseurl + '%s/%s%s%s' % (dir, filebase, extra, ext)
    return path, url

def ftp_upload_attchment(mlist, full_fname):
    fname = os.path.basename(full_fname)
    ftps = FTP_TLS(mlist.ftp_remote_host)
    ftps.login(mlist.ftp_remote_login, mlist.ftp_remote_pass)
    ftps.prot_p()
    ftps.storbinary('STOR ' + fname, open(full_fname, 'rb'))
    ftps.quit()

    return fname

