#!/bin/bash
export HOME=/home/vagrant
export WORKON_HOME=$HOME/.virtualenvs
source /usr/local/bin/virtualenvwrapper.sh
mkvirtualenv -a /home/vagrant/canvas_account_admin_tools -r /home/vagrant/canvas_account_admin_tools/canvas_account_admin_tools/requirements/local.txt canvas_account_admin_tools
