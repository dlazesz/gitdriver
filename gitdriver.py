#!/usr/bin/python
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

NAME_OF_FILE = 'content.{extension}'
SLEEP_TIME = 5

import os
import sys
import argparse
import subprocess
import yaml

import time
import re
from bs4 import BeautifulSoup as bs

# For unauthed download
import urllib2
import codecs

from drive import GoogleDrive, DRIVE_RW_SCOPE

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--config', '-f', default='gd.conf',
            help='OAuth 2.0 credentials')
    p.add_argument('--text', '-T', action='store_const', const='text/plain',
            dest='mime_type_text', help='Download TXT version')
    p.add_argument('--html', '-H', action='store_const', const='text/html',
            dest='mime_type_html', help='Download HTML version')
    p.add_argument('--mime-type', dest='mime_type_other',
            help='Download other formats (extension goes here for --noauth!)')
    p.add_argument('--raw', '-R', action='store_true',
            help='Download original document if possible.')
    p.add_argument('--noauth', '-N', action='store_true',
            help='No OAuth 2.0 authentication (very limited usage)')
    p.add_argument('--preview', '-P', action='store_true',
            help='Compile latex file to PDF and preview')
    p.add_argument('--url', '-U', action='store_true',
            help='Use URL instead of docid')
    p.add_argument('docid')

    return p.parse_args()

# Latex Preview
def latex_preview(filename):
    subprocess.call(['latexmk', '-f', '-pv', '-silent', '-gg', '-pdf',
                      filename])

# Git get last commit date
def get_last_commit_date():
    p = subprocess.Popen(['git', 'log', '-1', '--pretty=%B'],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    out, _ = p.communicate() # 'revision from 2014-03-10T12:53:00.799Z'
    if out:
        return time.strptime(out.strip(), 'revision from %Y-%m-%dT%H:%M:%S.%fZ')
    else:
        return time.ctime(0)

def reformat_file(filename):
    # Strip BOM for latex
    if filename.endswith('txt'):
        with open(filename) as fd:
            text = fd.read()
            if text.startswith(codecs.BOM_UTF8):
                text = text[len(codecs.BOM_UTF8):]
        with open(filename, 'w') as fd:
            fd.write(text)
    # Add newlines to HTML source (Git friendly)
    elif filename.endswith('html'):
        with open(filename) as fd:
            html = bs(fd.read()).prettify()
        with codecs.open(filename, 'w', 'UTF-8') as fd:
            fd.write(html)

def git_main(gd, docid, mime_types_to_download, raw, preview):
    # Establish our credentials.
    gd.authenticate()

    # Get information about the specified file.  This will throw
    # an exception if the file does not exist.
    md = gd.get_file_metadata(docid)

    # Initialize the git repository.
    print(u'Create repository "{title}"'.format(title=unicode(md['title'])))
    subprocess.call(['git', 'init', unicode(md['title'])])

    orig_dir = os.getcwd()
    os.chdir(unicode(md['title']))
    last_commit_date = get_last_commit_date()

    # Iterate over the revisions (from oldest to newest).
    for rev in gd.revisions(docid):
        if time.strptime(rev['modifiedDate'],
                         '%Y-%m-%dT%H:%M:%S.%fZ') > last_commit_date:
            for ext, mime_type in mime_types_to_download.items():
                filename = NAME_OF_FILE.format(extension=ext)
                with open(filename, 'w') as fd:
                    if 'exportLinks' in rev and not raw:
                        # If the file provides an 'exportLinks' dictionary,
                        # download the requested MIME type.
                        r = gd.session.get(rev['exportLinks'][mime_type])
                    elif 'downloadUrl' in rev:
                        # Otherwise, if there is a downloadUrl, use that.
                        r = gd.session.get(rev['downloadUrl'])
                    else:
                        raise KeyError('unable to download revision')

                    # Write file content into local file.
                    for chunk in r.iter_content():
                        fd.write(chunk)
                # Reformat after writing
                reformat_file(filename)

                subprocess.call(['git', 'add', filename])
            # Commit changes to repository.
            subprocess.call(['git', 'commit', '-m',
                'revision from {date}'.format(date=rev['modifiedDate'])])
    if preview and last_commit_date < get_last_commit_date():
        filename = NAME_OF_FILE.format(extension='txt')
        subprocess.call(['git', 'checkout', filename])
        latex_preview(filename)
    print('Done.')
    os.chdir(orig_dir)

# Source from a simmilar project: https://github.com/uid/gdoc-downloader
def unauth_main(docid, mime_types_to_download, preview):
    export_url = 'https://docs.google.com/document/d/{DocID}/export?format={{extension}}'.format(DocID=docid)
    for ext, mime_type in mime_types_to_download.items():
        if ext != 'other':
            export_url_w_ext = export_url.format(extension=ext)
            filename = NAME_OF_FILE.format(extension=ext)
        else:
            export_url_w_ext = export_url.format(extension=mime_type)
            filename = NAME_OF_FILE.format(extension=mime_type)

        # open a connection to it
        conn = urllib2.urlopen(export_url_w_ext)
        # we were redirected to a login -- doc isn't publicly viewable
        if 'ServiceLogin' in conn.geturl():
            raise Exception("""
The google doc
  https://docs.google.com/document/d/{docID}
is not publicly readable. It needs to be publicly
readable in order for this script to work.
To fix this, visit the doc in your web browser,
and use Share >> Change... >> Anyone with Link >> can view.
""".format(docID=docid))

        # download the file
        raw = conn.read()
        encoding = conn.headers['content-type'].split('charset=')[-1]
        data = unicode(raw, encoding)
        conn.close()
        with codecs.open(filename, 'w', 'UTF-8') as fd:
            fd.write(data)

        # Reformat after writing
        reformat_file(filename)

    if preview:
        latex_preview(NAME_OF_FILE.format(extension='txt'))

if __name__ == '__main__':
    opts = parse_args()
    if not opts.noauth:
        cfg = yaml.load(open(opts.config))
        gd = GoogleDrive(
                client_id=cfg['googledrive']['client id'],
                client_secret=cfg['googledrive']['client secret'],
                scopes=[DRIVE_RW_SCOPE],
                )

    mime_types_to_download = dict()
    if opts.mime_type_text:
        mime_types_to_download['txt'] = opts.mime_type_text
    if opts.mime_type_html:
        mime_types_to_download['html'] = opts.mime_type_html
    if opts.mime_type_other:
        mime_types_to_download['other'] = opts.mime_type_other
    if not mime_types_to_download:
        print('No mime-types are given!')
        exit(1)

    if opts.preview and not opts.mime_type_text:
        print('Warning: No preview without txt format! Addig txt format!')
        mime_types_to_download['txt'] = 'text/plain'

    # URL or DocID
    # Source from a simmilar project: https://github.com/uid/gdoc-downloader
    if opts.url:
        try:
            docid = re.search('/document/d/([^/]+)/', opts.docid).group(1)
        except:
            raise Exception('can not find a google document ID in {DocID}'.format(DocID=opts.docid))
    else:
        docid = opts.docid

    while True:
        if opts.noauth:
            unauth_main(docid, mime_types_to_download, opts.preview)
        else:
            git_main(gd, docid, mime_types_to_download, opts.raw, opts.preview)
        time.sleep(SLEEP_TIME)
