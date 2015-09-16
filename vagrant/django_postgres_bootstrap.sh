#!/bin/bash
export HOME=/home/vagrant
export WORKON_HOME=$HOME/.virtualenvs
source /usr/local/bin/virtualenvwrapper.sh
mkvirtualenv -a /home/vagrant/icommons_tools -r /home/vagrant/icommons_tools/icommons_tools/requirements/local.txt icommons_tools
workon icommons_tools
python manage.py init_db --force
python manage.py migrate
