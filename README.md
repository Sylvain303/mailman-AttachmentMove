mailman-AttachmentMove
======================

mailman Handler: detach an attachment and upload it online modifying the original txt and html message

Goal is to develop a custom handler which performs:

* detach all attachments, but not related html pictures (big pdf for example)
* post detached content somewhere available on http
* modify the content of the original email, keeping original html, adding an html link to the moved document
* adding a small clip image as an attachment symbol as an embed object


* Content-Type: multipart/related
 * Content-Type: text/html;
 * Content-Type: image/png; name="clip-24.png"

The text/html is the old one.


What if the posted message has already this format. Some embeded images for example.

More documentation about writing your custom Handler for mailman can be found 
here: 

Mailman processes incoming messages through a pipeline of handlers which each do parts of the message processing <http://wiki.list.org/pages/viewpage.action?pageId=7602227>

4.67. How do I implement a custom handler in Mailman, <http://wiki.list.org/pages/viewpage.action?pageId=4030615>

Python documentation on the message object used to process parts
https://docs.python.org/2/library/email.message.html

An example of mailman's handler. I used Scrubber.py as a start.
http://wiki.list.org/download/attachments/4030615/MyHandler.py?version=1&modificationDate=1283485784289

```bash
$ withlist -l -r test_handler listname MyHandler /path/to/some_test_2_pj.eml  > /tmp/out.handler && less -40 /tmp/out.handler
```

