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

```bash
$ withlist -l -r test_handler listname MyHandler /path/to/some_test_2_pj.eml  > /tmp/out.handler && less -40 /tmp/out.handler
```
