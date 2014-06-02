mailman-AttachmentMove
======================

A custom mailman's Handler

Detach incomming email attachment and upload it online, modifying the original txt and html message (multipart/alternative).

The goal is to develop a custom handler which performs:

* detach all attachments, big pdf for example, but not related html pictures (embedded in the html)
* post detached content somewhere available on http
* modify the content of the original email, keeping original html, adding an html link to the moved document
* adding a small clip image as an attachment symbol as an embed object

Why?

To totaly remove the upload process of the user who is posting to a mailing list. I've took inspiration from [Thunderbird filelink](https://support.mozilla.org/en-US/kb/filelink-large-attachments) extension.

When the custom handler is installed with mailman, the poster simply post as a normal mail to one destination (the mailing list), AttachmentMove will perform the task of hosting the attachment on some remote public location, as filelink do.

## Install the custom handler

copy the Handler code AttachmentMove.py to Mailman/Handlers.
You may want to synlink it, so you can git pull fix. Don't forget to restart mailman.

```bash
cd /to/some/cool/folder
git clone https://github.com/Sylvain303/mailman-AttachmentMove.git
# for debian, go to yours mailman code folder
cd /usr/lib/mailman/Mailman/Handlers/
ls -s /to/some/cool/folder/mailman-AttachmentMove/AttachmentMove.py .
```

The detached parts will be stored on the mailman server to generate unique filename. But the 
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
# optional, a folder on the remote storage. Not used in the linking.
mlist.ftp_remote_dir = 'remote_folder'

# optional, debug, will log debug() call in /var/log/mailman/debug (debian)
mlist.debug = 1

# required, install the handler in the pipeline

# inserting the code in the pipeline
# See bellow about how to find this list of Handlers
mlist.pipeline = [
    'SpamDetect',
    'Approve',
    'Replybot',
    'Moderate',
    'Hold',
    # inserting the Handler here.
    'AttachmentMove',
    'MimeDel',
    'Scrubber',
    'Emergency',
    'Tagger',
    'CalcRecips',
    'AvoidDuplicates',
    'Cleanse',
    'CleanseDKIM',
    'CookHeaders',
    'ToDigest',
    'ToArchive',
    'ToUsenet',
    'AfterDelivery',
    'Acknowledge',
    'ToOutgoing',
    ]

```

store those parameters in a file tempfile.py. You may want to keep this config file somewhere handy because config_list -o doesn't list custom parameters.

Load the config from command line with: 
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

The extend.py is a somewhat complex internal behavior, not reloaded after config_list -i, or loaded before…
So use it when you know what you are doing.


restart mailman:
```bash
/etc/init.d/mailman restart
```

## List configuration
- General > max_message_size: 0
- Content filtering 
 - filter_content : yes
 - pass_mime_types :  empty (disable)
 - collapse_alternatives : No
 - convert_html_to_plaintext : No
 - filter_action : Keep


### Mailman pipeline

The pipeline may change depending the version of mailman. It is defined in the code (/usr/lib/mailman in debian package)
We will copy it to suite our needs on a per list basis.

1. Open Mailman/Defaults.py
2. Copy the definition of GLOBAL_PIPELINE
3. paste it into a the config file changing the name from GLOBAL_PIPELINE to mlist.pipeline and add your handler so it becomes

```python
mlist.pipeline = [
    'SpamDetect',
    'Approve',
    'Replybot',
    'Moderate',
    'Hold',
    # inserting the Handler here.
    'AttachmentMove',
    'MimeDel',
    'Scrubber',
    'Emergency',
    'Tagger',
    'CalcRecips',
    'AvoidDuplicates',
    'Cleanse',
    'CleanseDKIM',
    'CookHeaders',
    'ToDigest',
    'ToArchive',
    'ToUsenet',
    'AfterDelivery',
    'Acknowledge',
    'ToOutgoing',
    ]
```

## Troubleshooting

If nothing seems to happend… 
- do you have restarted mailman?
- have a look at mailman logs: /var/log/mailman 
- enable debuging and see… /var/log/mailman/debug
```bash
config_list -i <(echo mlist.debug=1) listname
```
- test it from command line see bellow
- check folder list permissions:
```bash
ls -l /var/lib/mailman/archives/private/
total 24
drwxrwsr-x 6 www-data list     4096 mai    8 03:27 somelist
drwxrwsr-x 2 www-data list     4096 avril 11 16:10 somelist.mbox
drwxrwsr-x 3 root     www-data 4096 juin   1 09:24 attachment-move
drwxrwsr-x 2 root     www-data 4096 mai   31 10:29 attachment-move.mbox
drwxrwsr-x 2 root     www-data 4096 mars  13 10:34 mailman
drwxrwsr-x 2 root     www-data 4096 mars  13 10:34 mailman.mbox

cd /var/lib/mailman/archives/private/
chown -R www-data:list attachment-move*
```

## More documentation about writing custom Handler for mailman

Mailman processes incoming messages through a pipeline of handlers which each do parts of the message processing 
<http://wiki.list.org/pages/viewpage.action?pageId=7602227>

4.67. How do I implement a custom handler in Mailman
<http://wiki.list.org/pages/viewpage.action?pageId=4030615>

Python documentation on the message object used to process parts
https://docs.python.org/2/library/email.message.html

An example of mailman's handler. I used Mailman/Handlers/Scrubber.py as a start.
http://wiki.list.org/download/attachments/4030615/MyHandler.py?version=1&modificationDate=1283485784289

## To test your handler form command line
```bash
$ withlist -l -r test_handler listname AttachmentMove /path/to/some_test_2_pj.eml  > /tmp/out.handler && less -40 /tmp/out.handler
```

Same without performing the FTP upload (disable_upload=1):
```bash
$ withlist -l -r test_handler listname AttachmentMove /path/to/some_test_2_pj.eml disable_upload=1  > /tmp/out.handler
```

*test_handler* is available here: http://www.msapiro.net/scripts/test_handler.py
The documentation is inside the code. The FAQ at <http://wiki.list.org/x/l4A9>


