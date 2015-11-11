#!/usr/bin/python -OO
'''
repost someone's Instagram photos to my Facebook page
'''
import sys, os, netrc, urllib, urllib2, fcntl
import logging, httplib, requests, json, pwd
from collections import namedtuple
AUTH = namedtuple('AUTH', ['user', 'app_id', 'key'])
logging.basicConfig(level = logging.DEBUG)
FACEBOOK = 'graph.facebook.com'
INSTAGRAM = 'api.instagram.com'
NETRC = netrc.netrc()
FB = AUTH(*NETRC.authenticators(FACEBOOK))
IG = AUTH(*NETRC.authenticators(INSTAGRAM))
GRAPH = 'https://%s' % FACEBOOK
IGAPI = 'https://%s' % INSTAGRAM
IG_URL = '%s/v1/users/%s/media/recent/' % (IGAPI, IG.user)
MAX_POSTS_PER_RUN = 3  # limit to how many posts each cron run

def repost():
    '''
    grab Instagram photo and upload to Facebook page
    '''
    homedir = pwd.getpwuid(os.geteuid()).pw_dir
    os.chdir(homedir)
    if not os.path.exists('tmp'):
        os.mkdir('tmp')
    # ensure only one process is running
    pidfile = os.path.join('tmp', 'repost.pid')
    lockfile = open(pidfile, 'w')
    try:
        fcntl.lockf(lockfile, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        raise IOError('Another instance is running, exiting')
    statefile = os.path.join('tmp', 'repost_state.txt')
    try:
        last_posted = read(statefile).rstrip()
    except IOError:
        raise IOError('Must initialize $HOME/%s by `echo 0 > %s`' % (
            statefile, statefile))
    data = get_latest_photos(last_posted)
    post_count = 0
    for entry in data:
        if post_count >= MAX_POSTS_PER_RUN:
            break
        logging.debug('entry: %s' % repr(entry))
        try:
            post_type = entry['type']
            caption = entry['caption']['text']
            image_url = entry['images']['standard_resolution']['url']
            image_id = entry['id']
            # skip videos, and duplicate of last post from previous run
            if (post_type != 'image') or (image_id == last_posted):
                logging.debug('skipping %s %s' % (post_type, image_id))
                continue
        except:
            continue  # ignore malformed entries
        logging.debug('locals: ' + repr(locals()))
        if os.getenv('DO_NOT_POST', False):
            logging.debug('posting %s %s' % (post_type, image_id))
        else:
            update_facebook_page(image_url, caption)
            write(statefile, image_id)
            post_count += 1

def init_https():
    '''
    enable debugging of HTTPS connection if run from command-line
    '''
    debug = __debug__ and sys.stdin.isatty()
    handler = urllib2.HTTPSHandler(debuglevel = debug)
    opener = urllib2.build_opener(handler)
    urllib2.install_opener(opener)
    # and for `requests` module:
    httplib.HTTPConnection.debuglevel = debug

def update_facebook_page(photo = None, text = ''):
    '''
    make a POST to my Facebook page
    '''
    arguments = {}
    init_https()
    args = {
        'data': {'caption': text, 'access_token': FB.key}
    }
    if photo.startswith(('https://', 'http://')):
        args['data']['url'] = photo
    elif photo:
        args['files'] = {'source': open(photo)}
    else:
        raise ValueError('Photo must be provided')
    response = requests.post('%s/%s/photos' % (GRAPH, FB.user), **args)
    page = response.text
    logging.debug(page)

def get_latest_photos(last_fetched = None):
    '''
    download latest Instagram content
    '''
    init_https()
    args = {'client_id': IG.app_id}
    if last_fetched and last_fetched != '0':
        args.update({'min_id': last_fetched})
    else:
        args.update({'min_timestamp': 0})
    url = IG_URL + '?' + urllib.urlencode(args)
    response = urllib2.urlopen(url)
    page = response.read()
    logging.debug(page)
    data = json.loads(page)
    logging.debug('data: %s' % repr(data)[:256])
    return data.get('data', [])[::-1]  # reorder oldest first

def get_facebook_token():
    '''
    get permanent token for graph API calls

    only needs to be called once, with the APP secret in the `password`
    field of ~/.netrc; then replace password with the returned token
    '''
    init_https()
    url = '%s/oauth/access_token?client_id=%s' % (GRAPH, FB.app_id) + \
        '&client_secret=%s' % FB.key + \
        '&grant_type=client_credentials'
    response = urllib2.urlopen(url)
    page = response.read()
    logging.debug(page)

def read(filename):
    '''
    read line of text from file, closing it properly
    '''
    infile = open(filename)
    data = infile.read()
    infile.close()
    return data

def write(filename, data):
    '''
    print line of text to file, closing it properly
    '''
    outfile = open(filename, 'w')
    print >>outfile, data
    outfile.close()

if __name__ == '__main__':
    repost()

