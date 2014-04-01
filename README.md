## Features and Changes

- Python 2.x version. For Python 3.x version see the other branch
- Fixed mime-type issuse for txt output
- Fixed Git update glitches (only newer revisions are commited)
- Added possibility to use full URL insead of DocID
- Added possibility to work without OAuth 2.0 credentials (Only the newest revision available. Using source from a simmilar project: https://github.com/uid/gdoc-downloader )
- Added possibility to latexmk preview
- Added possibility to download more format at once 
- Added Git and LaTeX friendly output formatting
- Added continous updates and previews (can be set as parameter. default: 5 sec)
- Fixed double writing in the previous version of program
- Some performance improvements

## Synopsis

    gitdriver.py [-h] [--config CONFIG] [--text] [--html] docid

## Options

- `--config CONFIG`, `-f CONFIG` -- path to configuration file
- `--text`, `-T` -- fetch plain text content
- `--html`, `-H` -- fetch HTML content
- `--mime-type` -- specify arbitrary mime type
- `--noauth` -- No OAuth 2.0 authentication (very limited usage)
- `--preview` -- Compile latex file to PDF and preview
- `--url` -- Use URL instead of docid


## Example usage:

    $ python gitdriver.py 1j6Ygv0_this_is_a_fake_document_id_a8Q66mvt4
    Create repository "Untitled"
    Initialized empty Git repository in /home/lars/projects/gitdriver/Untitled/.git/
    [master (root-commit) 27baec9] revision from 2013-01-08T21:57:38.837Z
     1 file changed, 1 insertion(+)
     create mode 100644 content
    [master 132175a] revision from 2013-01-08T21:57:45.800Z
     1 file changed, 1 insertion(+), 1 deletion(-)
    [master eb2302c] revision from 2013-01-09T01:47:29.593Z
     1 file changed, 5 insertions(+), 1 deletion(-)
    $ ls Untiled
    content
    $ cd Untitled
    $ git log --oneline
    d41ad6e revision from 2013-01-09T01:47:29.593Z
    8d3e3ec revision from 2013-01-08T21:57:45.800Z
    ccc0bdd revision from 2013-01-08T21:57:38.837Z

## Google setup

You will need to create an OAuth client id and secret for use with
this application, the Drive API [Python quickstart][] has links to the
necessary steps.

[python quickstart]: https://developers.google.com/drive/quickstart-python#step_1_enable_the_drive_api

## Configuration

In order to make this go you will need to create file named `gd.conf`
where the code can find it (typically the directory in which you're
running the code, but you can also use the `-f` command line option to
specify an alternate location).

The file is a simple YAML document that should look like this:

    googledrive:
      client id: YOUR_CLIENT_ID
      client secret: YOUR_CLIENT_SECRET

Where `YOUR_CLIENT_ID` and `YOUR_CLIENT_SECRET` are replaced with the
appropriate values from Google that you established in the previous
step.
