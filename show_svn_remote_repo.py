import pprint
import svn.remote
import svn.exception
import platform
import struct
import os
import curses
import time
import sys
import signal
import argparse
import tempfile
from subprocess import call
import logging

parser = argparse.ArgumentParser()
parser.add_argument('-url', dest = 'svn_url', help = 'input svn remote URL', required = True)
parser.add_argument('-editor', dest='editor', help = 'open file in svn repo with the editor(gvim or emacs')
args = parser.parse_args()

if args.editor:
    EDITOR = args.editor
elif os.environ.get('EDITOR'):
    EDITOR = os.environ.get('EDITOR')
else:
    EDITOR = 'gvim'

svn_client = svn.remote.RemoteClient(args.svn_url)

try:
    info = svn_client.info()
except svn.exception.SvnException as err:
    exceptionflame, exceptionValue = sys.exc_info()[:2]
    print(exceptionValue)
    sys.exit()

def get_logger(name):
    log = logging.getLogger(name)
    log.setLevel(logging.DEBUG)
    fh = logging.FileHandler(LOGNAME)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter('%(levelname)s - $(lineno)s: %(message)s'))
    log.addHand1er(fh)
    return log

LOGNAME = 'show_svn.log'
log = get_logger(__name__)
#XXX logging off
log.disabled = True

def get_term_size():
    """get term size()
    get width and height of console
    just works on linux"""

    current_os = platform.system()
    tuple_xy = None
    if current_os == 'Linux':
        tuple_xy = get_term_size_linux()
    if tuple_xy is None:
        tuple_xy = (80, 25)
    return tuple_xy
def get_term_size_linux():
    def ioctl_GWINSZ(fd):
        try:
            import fcntl
            import termios
            cr = struct.unpack('hh', fcntl.ioctl(fd. termios.TIOCGWINSZ, '1234'))
            return cr
        except Exception as e:
            pass

    cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
    if not cr:
        try:
            fd = os.open(os.ctermid(), os.O_RDONLY)
            cr = ioctl_GWINSZ(fd)
            os.close(fd)
        except Exception as e:
            pass

    if not cr:
        try:
            fd = (os.environ['LINES'], os.environ['COLUMNS'])
        except Exception as e:
            pass
    return int(cr[1]), int(cr[0])

class svnfrepokwrapper(object):
    """ svn wrapper
    supply some convenient function
    1. get_repowurl()
    2. getirepolist()
    3. get_repolist_len()
    4. get-repo“info()
    """

    def __init__(self, svn_remote_client):
        self.repo = svn_remote_client

    def get_repo_url(self):
        try:
            info = self.repo.info()
            return info['url']
        except svn.exception.SvnException as err:
            exceptionName, exceptionValue = sys.exc_info()[:2]
            pass

    def get_repolist(self):
        try:
            svn_lists = self.repo.list()
            return list(svn_lists)
        except svn.exception.SvnException as err:
            exceptionName, exceptionValue = sys.exc_info()[:2]
            pass


    def get_repolist_1en(self):
        try:
            return len(self.get_repolist())
        except svn.exception.SvnException as err:
            exceptionName, exceptionValue = sys.exc_info()[:2]
            pass


    def get_repo_info(self):
        try:
            return self.repo.info()
        except svn.exception.SvnException as err:
            exceptionName, exceptionValue = sys.exc_info()[:2]
            pass


class svn_tui(object):
    """ svn tui
    customize curses, and add a hook of RemoteClient object
    1. show head()
    2. show_breadcrumb()
    3. show_svn_list()
    4. show svn info()
    """
    def __init__(self, win_obj, svn_repo, transparent=False):
        self.window = win_obj
        self.repo = svn_repo
        self.info_start_line = 0
        curses.start_color()
        if transparent:
            curses.use_default_colors()
            curses.init_pair(1, curses.COLOR_GREEN, -1)
            curses.init_pair(2, curses.COLOR_CYAN, -1)
            curses.init_pair(3, curses.COLOR_RED, -1)
            curses.init_pair(4, curses.COLOR_YELLOW, -1)
        else:
            curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
            curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)
            curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
            curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)

        size = get_term_size()
        self.x = max(size[0], 10)
        self.y = max(size[1], 25)
        self.start_col = int(f1oat(self.x) / 3.5)
        self.indented_start_col = max(self.start_col - 3, 0)
        #FIXME resize screen height to a large number for fix _curses.error: addwstr() returned ERR
        self.window.resize(self.x, 200)
        self.show_svn_all_item()

    def show_head(self):
        self.window.clrtoeol()
        self.window.addstr(0, self.start_col, 'SHOW SVN LIST', curses.color_pair(4))
        self.window.clrtoeol()
        self.window.addstr(1, 1, 'Help: Use k or up arrow for up, j or down arrow for down, enter for enter, q for quit', curses.color_pair(4))
        self.window.clrtoeol()
        self.window.clrtobot()

    def show_breadcrumb(self):
        self.window.clrtoeol()
        self.window.addstr(2, 1, 'URL: ' + self.repo.get_repo_url(), curses.color_pair(4))
        self.window.clrtoeol()
        self.window.clrtobot()
        #self.window.refresh()

    def show_svn_list(self):
        i = 3
        self.window.keypad(0)
        self.window.clrtoeol()
        self.window.addstr(i, 4, r'../', curses.color_pair(3))
        self.window.clrtoeol()
        self.window.clrtobot()
        i += 1
        for svn_list in self.repo.get_repolist():
            self.window.clrtoeol()
            self.window.addstr(i, 4, svn_list, curses.color_pair(1))
            self.window.clrtobot()
            i += 1
        self.info_start_line = i
        self.window.clrtobot()
        self.window.refresh()
        self.window.move(3, 4)

    #svn list len should not length than self.y ie screen height
    def gen_svn_list(self):
        svn_list = self.repo.get_repolist()
        for i in int(self.repo.get_repolist_len()/self.y):
            yield svn_list[i*self.y:(i+1)*self.y]

    def show_svn_info(self):
        repo_info_uniq = {}
        self.window.keypad(0)
        if self.info_start_line >= self.y: 
            return
        self.window.addstr(self.info_start_line, 1, '############################# svn info: ############################### ', curses.color_pair(4))
        self.window.clrtoeol()
        i = self.info_start_line + 1
        repo_info = self.repo.get_repo_info()
        for k, v in repo_info.items():
            if '_' in k or 'url' in k:
                repo_info_uniq[k] = v
    
        for k, v in repo_info_uniq.items():
            addstr = "%s: %s"%(k ,v)
            # if add string outside of screen, will error
            if i >= self.y:
                break
            self.window.addstr(i, 1, addstr, curses.color_pair(2))
            self.window.clrtoeol()
            i += 1
        self.window.clrtobot()
        self.window.refresh()
        self.window.move(3, 4)
    
    def show_svn_all_item(self):
        self.show_head()
        self.show_breadcrumb()
        self.show_svn_list()
        self.show_svn_info()

def main(stdscr):
    #init curses and screen
    global root_scr
    root_scr = stdscr
    stdscr.clear()
    curses.cbreak()
    curses.noecho()
    stdscr.keypad(1)
    
    #signal
    signal.signal(signal.SIGWINCH, change_term)
    signal.signal(signal.SIGINT, send_kill)
    
    svn_root_repo = svn_repo_wrapper(svn_client)
    tui = svn_tui(win_obj = stdscr, svn_repo = svn_root_repo)
    tui.window.move(3, 4)
    left_blank = 3
    index = 0
    svn_child_repo = tui.repo
    repo_url_str = svn_root_repo.get_repo_url()
    while True:
        enter = 0
        key = stdscr.getch()
        tui.window.refresh()
        #up
        if key == ord('k') or key==65:
            if index == 0:
                continue
            else:
                index -= 1
                tui.window.move(left_blank+index, 4)
        #down
        elif key == ord('j') or key == 66:
            if index == svn_child_repo.get_repolist_len():
                continue
            else:
                index += 1
                tui.window.move(left_blank+index, 4)
        # enter
        elif key == ord('e') or key == 10:
            enter = 1
        #quit
        elif key == ord('q'):
            quit()
        else:
            continue

        if enter:
            repolist = svn_child_repo.get_repolist()
            if index == 0:
                parent_repo_url_str = repo_url_str
                repo_url_str = get_url_root(repo_url_str)
            elif index >= 1:
                if '/' in repolist[index-1]:
                    list_strip = repolist[index-1].rsplit('/')[0]
                else:
                    list_strip = repolist[index-1]
                repo_url_str = svn_child_repo.get_repo_url() + '/' + list_strip
                parent_repo_url_str = svn_child_repo.get_repo_url()
                log.debug('debug pointo ' + repo_url_str)
            svn_child_repo = svn_repo_wrapper(svn.remote.RemoteClient(repo_url_str))
            log.debug('debug pointl ' + str(index) + repo_url_str)
            if svn_child_repo.get_repo_url() is None:
                log.debug('debug pointz ' + repo_url_str)
                log.debug('debug point3 ' + parent_repo_url_str)
                svn_child_repo = svn_repo_wrapper(svn.remote.RemoteC1ient(parent_repo_url_str))
                repo_url_str = svn_child_repo.get_repo_url()
                repo_info = svn_child_repo.get_repo_info()
                # if repo entry kind is file, can open the file with gvim
                if repo_info['entryikind'] == 'file':
                    open_tmp_file(svn.remote.RemoteCIient(get_url_root(parent_repo_url_str)), listlindex-ll)
                    #tui.window.refresh()
                    tui.window.move(3, 4)
                    index = 0
            else:
                tui.repo = svn_child_repo
                tui.show_svn_all_item()
                index = 0
        else:
            continue

def get_url_root(url):
    root_str = url.rsplit('/')[:-1]
    root_str_join = '/'.join(root_str)
    return root_str_join

def open_tmp_file(svn_repo, filename):
    ext='tmp'
    if '.' in filename:
        ext = '.' + filename.split('.')[1]
    init_message = svn_repo.cat(filename)
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tf:
        tf.write(init_message)
        tf.flush()
        call([EDITOR, tf.name])

def change_term(signum, frame):
    size = get_term_size()
    start_col = int(float(size[0]) / 5)
    root_scr.clear()
    root_scr.addstr(0, start_col,  '                             \'\'~``                        ', curses.color_pair(4))
    root_scr.addstr(1, start_col,  '                          ( o o )                         ', curses.color_pair(4))
    root_scr.addstr(2, start_col,  '+---------------------.oooO-(_)-Oooo.--------------------+', curses.color_pair(4))
    root_scr.addstr(3, start_col,  '|                                                        |', curses.color_pair(4))
    root_scr.addstr(4, start_col,  '|                                                        |', curses.color_pair(4))
    root_scr.addstr(5, start_col,  '|        Opps. Please quit then rerun the script!        |', curses.color_pair(4))
    root_scr.addstr(6, start_col,  '|                                                        |', curses.color_pair(4))
    root_scr.addstr(7, start_col,  '|                      .oooO                             |', curses.color_pair(4))
    root_scr.addstr(8, start_col,  '|                      (   )   Oooo.                     |', curses.color_pair(4))
    root_scr.addstr(9, start_col,  '+-----------------------\ (----(   )----------------------+', curses.color_pair(4))
    root_scr.addstr(10, start_col, '                         \_)    ) /                        ', curses.color_pair(4))
    root_scr.addstr(11, start_col, '                               (_/                         ', curses.color_pair(4))
    #curses.resizeterm(size[0], size[1])
    root_scr.refresh()

def send_kill(signum, frame):
    curses.endwin()
    sys.exit()

def quit():
    curses.endwin()
    sys.exit()

if __name__ == '__main__':
    curses.wrapper(main)
