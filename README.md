# tui_of_svn_remote_repo
  A python text-based user interface for svn remote repository
# Libs for this tools  
  * curses lib for text based user interface.<br/>
  * svn lib  for wrapping the svn commandline client.<br/>
  * argparse lib for argument parser.<br/>
  * tempfile lib for open file with gvim or emacs.
# Usage
  > python3.5 show_svn_remote_repo.py -url svn://judesvnrepo/12306_captcha <br/>
  > python3.5 show_svn_remote_repo.py -url svn://judesvnrepo/12306_captcha -editor emacs <br/>
  > python3.5 show_svn_remote_repo.py -h
# Display
  ![demo](https://github.com/zhajio1988/tui_of_svn_remote_repo/blob/master/demo.png)
# References
  Some tui ideas from [NetEase-MusicBox](https://pypi.python.org/pypi/NetEase-MusicBox/)
# License
   Apache 2.0 license.
