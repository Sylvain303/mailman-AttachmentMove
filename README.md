mailman-AttachmentMove
======================

A custom mailman Handler

Detach incomming email attachment and upload it online, modifying the original txt and html message.

Goal is to develop a custom handler which performs:

* detach all attachments, but not related html pictures (big pdf for example)
* post detached content somewhere available on http
* modify the content of the original email, keeping original html, adding an html link to the moved document
* adding a small clip image as an attachment symbol as an embed object

Why?

To totaly remove the upload process of the user posting to a mailing list. I've took inspiration from [Thunderbird filelink](https://support.mozilla.org/en-US/kb/filelink-large-attachments) extension.

When the custom handler is installed with mailman, the poster simply post as a normal mail to one destination (the mailing list), AttachmentMove will perform the task of hosting the attachment on some remote public location, as filelink do.

Install the custom handler:

The detached parts are stored as attachment on the list archive. But the 
attachment used is a fresh copy, uploaded to a remote location given by the
extra required parameters:

```python
mlist.ftp_remote_host = 'ftp.example.com'
mlist.ftp_remote_login = 'username'
mlist.ftp_remote_pass = 'secr3te'
# put the ending slash /
mlist.remote_http_base = 'http://example.com/root/for/username/'
# optional, a prefix on the remote storage:
mlist.ftp_upload_prefix = 'listname_or_dev_'
```

store those parameters in a file tempfile.py

from command line with: 
```bash
config_list -i tempfile.py listname
```

or it can be set in lists/listname/extend.py
(working but not the recommanded way)

```python
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
```

The extend.py is somewhat complex internal behavior not reloaded after config_list -i,  or loaded before…
So use it when you know what you are doing.

restart mailman:
```bash
/etc/init.d/mailman restart
```

If nothing seems to happend… 
- do you have restarted mailman?
- have a look at mailman logs: /var/log/mailman



More documentation about writing your custom Handler for mailman can be found 
here: 

Mailman processes incoming messages through a pipeline of handlers which each do parts of the message processing 
<http://wiki.list.org/pages/viewpage.action?pageId=7602227>

4.67. How do I implement a custom handler in Mailman
<http://wiki.list.org/pages/viewpage.action?pageId=4030615>

Python documentation on the message object used to process parts
https://docs.python.org/2/library/email.message.html

An example of mailman's handler. I used Scrubber.py as a start.
http://wiki.list.org/download/attachments/4030615/MyHandler.py?version=1&modificationDate=1283485784289

To test your handler form command line:
```bash
$ withlist -l -r test_handler listname MyHandler /path/to/some_test_2_pj.eml  > /tmp/out.handler && less -40 /tmp/out.handler
```

test_handler is available here: http://www.msapiro.net/scripts/test_handler.py
The documentation is inside the code. The FAQ at <http://wiki.list.org/x/l4A9>


