# puppet manifest

Exec {
    path => [
    '/usr/local/sbin',
    '/usr/local/bin',
    '/usr/sbin',
    '/usr/bin',
    '/sbin',
    '/bin',
    ],
    logoutput => true,
}

exec {'apt-get-update-1':
    command => 'apt-get update',
}

package {'software-properties-common':
    ensure => latest,
    require => Exec['apt-get-update-1'],
}

package {'python-software-properties':
    ensure => latest,
    require => Package['software-properties-common'],
}

exec {'add-nodejs-repo':
    command => 'add-apt-repository ppa:chris-lea/node.js',
    require => Package['python-software-properties']
}

exec {'apt-get-update':
    command => 'apt-get update',
    require => Exec['add-nodejs-repo'],
}


# make sure apache is installed and running
package {'libxslt1-dev':
    ensure => latest,
    require => Exec['apt-get-update'],
}

package {'apache':
    name => 'apache2',
    ensure => latest,
    require => Exec['apt-get-update'],
}

package {'build-essential':
    ensure => latest,
    require => Exec['apt-get-update'],
}

service {'apache':
    name => 'apache2',
    ensure => running,
    enable => true,
}

package {'redis-server':
    ensure => latest,
    require => Exec['apt-get-update'],
}

package {'python-dev':
    ensure => installed,
    require => Exec['apt-get-update']
}

package {'python-pip':
    ensure => installed,
    require => Package['python-dev']
}

package {'libaio1':
    ensure => installed,
    require => Exec['apt-get-update']
}

package {'libaio-dev':
    ensure => installed,
    require => Exec['apt-get-update']
}

# For python cryptography requirements
package {'libffi-dev':
    ensure => installed,
    require => Exec['apt-get-update']
}

#package {'python-django':
#    ensure => installed,
#    require => Exec['apt-get-update'],
#}


package {'nodejs':
    ensure => latest,
    require => Exec['apt-get-update'],
}

package {'git':
    ensure => latest,
    require => Exec['apt-get-update'],
}

package {'unzip':
    ensure => latest,
    require => Exec['apt-get-update'],
}

package {'curl':
    ensure => latest,
    require => Exec['apt-get-update'],
}

package {'wget':
    ensure => latest,
    require => Exec['apt-get-update'],
}

package {'libcurl4-openssl-dev':
    ensure => latest,
    require => Exec['apt-get-update'],
}

package {'openssl':
    ensure => latest,
    require => Exec['apt-get-update'],
}

package {'zlib1g-dev':
    ensure => latest,
    require => Exec['apt-get-update'],
}

package {'libsqlite3-dev':
    ensure => latest,
    require => Exec['apt-get-update'],
}

package {'sqlite3':
    ensure => latest,
    require => Exec['apt-get-update'],
}

# Install Postgresql
package {'postgresql':
    ensure => latest,
    require => Exec['apt-get-update'],
}

package {'postgresql-contrib':
    ensure => latest,
    require => Exec['apt-get-update'],
}

package {'libpq-dev':
    ensure => latest,
    require => Exec['apt-get-update'],
}

# Create vagrant user for postgresql
exec {'create-postgresql-user':
    require => Package['postgresql'],
    command => 'sudo -u postgres psql -c "CREATE ROLE vagrant SUPERUSER CREATEDB CREATEROLE INHERIT LOGIN PASSWORD \'vagrant\'"',
    unless => 'sudo -u postgres psql -qt -c "select 1 from pg_roles where rolname=\'vagrant\'" | grep -q 1',
}

# Create vagrant db for postgresql
exec {'create-postgresql-db':
    require => Exec['create-postgresql-user'],
    command => 'sudo -u postgres createdb vagrant',
    unless => 'sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -wq vagrant',
}

# make a workspace directory and link it into the homedir

#file {'/vagrant/workspace':
#    ensure => directory,
#    owner => 'vagrant',
#    group => 'vagrant',
#}

#file {'/home/vagrant/workspace':
#    ensure => link,
#    target => '/vagrant/workspace',
#}


# install the Oracle instant client

define download ($uri, $timeout = 300) {
  exec {
      "download $uri":
          command => "wget -q '$uri' -O $name",
          creates => $name,
          timeout => $timeout,
          require => Package[ "wget" ],
  }
}

download {
  "/tmp/instantclient-basiclite-linux.x64-11.2.0.3.0.zip":
      uri => "http://test.isites.harvard.edu/oracle/instantclient-basiclite-linux.x64-11.2.0.3.0.zip",
      timeout => 900;
}

download {
  "/tmp/instantclient-sqlplus-linux.x64-11.2.0.3.0.zip":
      uri => "http://test.isites.harvard.edu/oracle/instantclient-sqlplus-linux.x64-11.2.0.3.0.zip",
      timeout => 900;
}

download {
  "/tmp/instantclient-sdk-linux.x64-11.2.0.3.0.zip":
      uri => "http://test.isites.harvard.edu/oracle/instantclient-sdk-linux.x64-11.2.0.3.0.zip",
      timeout => 900;
}

#download {
#  "/tmp/cx_Oracle-5.1.2.tar.gz":
#      uri => "http://test.isites.harvard.edu/oracle/cx_Oracle-5.1.2.tar.gz",
#      timeout => 900;
#}


file {'/opt/oracle':
    ensure => directory,
}

exec {'instantclient-basiclite':
    require => [ Download['/tmp/instantclient-basiclite-linux.x64-11.2.0.3.0.zip'], File['/opt/oracle'], Package['unzip'] ],
    cwd => '/opt/oracle',
    command => 'unzip /tmp/instantclient-basiclite-linux.x64-11.2.0.3.0.zip',
    creates => '/opt/oracle/instantclient_11_2/BASIC_LITE_README',
}

exec {'instantclient-sqlplus':
    require => [ Download['/tmp/instantclient-sqlplus-linux.x64-11.2.0.3.0.zip'], File['/opt/oracle'], Package['unzip'] ],
    cwd => '/opt/oracle',
    command => 'unzip /tmp/instantclient-sqlplus-linux.x64-11.2.0.3.0.zip',
    creates => '/opt/oracle/instantclient_11_2/sqlplus',
}

exec {'instantclient-sdk':
    require => [ Download['/tmp/instantclient-sdk-linux.x64-11.2.0.3.0.zip'], File['/opt/oracle'], Package['unzip'] ],
    cwd => '/opt/oracle',
    command => 'unzip /tmp/instantclient-sdk-linux.x64-11.2.0.3.0.zip',
    creates => '/opt/oracle/instantclient_11_2/sdk',
}

file {'/opt/oracle/instantclient_11_2/libclntsh.so':
    ensure => link,
    target => 'libclntsh.so.11.1',
    require => Exec['instantclient-basiclite'],
}

file {'/opt/oracle/instantclient_11_2/libocci.so':
    ensure => link,
    target => 'libocci.so.11.1',
    require => Exec['instantclient-basiclite'],
}

file {'/etc/profile.d/oracle.sh':
    ensure => file,
    content => 'export ORACLE_HOME=/opt/oracle/instantclient_11_2; export PATH=$ORACLE_HOME:$PATH; export LD_LIBRARY_PATH=$ORACLE_HOME',
    mode => '755',
    require => Exec['instantclient-basiclite'],
}

# Ensure github.com ssh public key is in the .ssh/known_hosts file so
# pip won't try to prompt on the terminal to accept it
file {'/home/vagrant/.ssh':
    ensure => directory,
    mode => 0700,
}

exec {'known_hosts':
    provider => 'shell',
    user => 'vagrant',
    group => 'vagrant',
    command => 'ssh-keyscan github.com >> /home/vagrant/.ssh/known_hosts',
    unless => 'grep -sq github.com /home/vagrant/.ssh/known_hosts',
    require => [ File['/home/vagrant/.ssh'], ],
}

file {'/home/vagrant/.ssh/known_hosts':
    ensure => file,
    mode => 0744,
    require => [ Exec['known_hosts'], ],
}

# install virtualenv and virtualenvwrapper - depends on pip

package {'virtualenv':
    ensure => latest,
    provider => 'pip',
    require => [ Package['python-pip'], ],
}

package {'virtualenvwrapper':
    ensure => latest,
    provider => 'pip',
    require => [ Package['python-pip'], ],
}

file {'/etc/profile.d/venvwrapper.sh':
    ensure => file,
    content => 'source `which virtualenvwrapper.sh`',
    mode => '755',
    require => Package['virtualenvwrapper'],
}

# Create a symlink from ~/<project_name> to /vagrant as a convenience for the developer
file {'/home/vagrant/icommons_tools':
    ensure => link,
    target => '/vagrant',
}

# Create a virtualenv for <project_name>
exec {'create-virtualenv':
    provider => 'shell',
    user => 'vagrant',
    group => 'vagrant',
    require => [ Package['virtualenvwrapper'], File['/home/vagrant/icommons_tools'], File['/etc/profile.d/oracle.sh'],
		 Exec['known_hosts'], ],
    environment => ["ORACLE_HOME=/opt/oracle/instantclient_11_2","LD_LIBRARY_PATH=/opt/oracle/instantclient_11_2",
		    "HOME=/home/vagrant", "WORKON_HOME=/home/vagrant/.virtualenvs"],
    command => '/vagrant/vagrant/venv_bootstrap.sh',
    creates => '/home/vagrant/.virtualenvs/icommons_tools',
}

# set the DJANGO_SETTINGS_MODULE environment variable
file_line {'add DJANGO_SETTINGS_MODULE env to postactivate':
    ensure => present,
    line => 'export DJANGO_SETTINGS_MODULE=icommons_tools.settings.local',
    path => '/home/vagrant/.virtualenvs/icommons_tools/bin/postactivate',
    require => Exec['create-virtualenv'],
}

file_line {'add DJANGO_SETTINGS_MODULE env to postdeactivate':
    ensure => present,
    line => 'unset DJANGO_SETTINGS_MODULE',
    path => '/home/vagrant/.virtualenvs/icommons_tools/bin/postdeactivate',
    require => Exec['create-virtualenv'],
}

# init the development db, and run initial migrations
exec {'init-db-and-migrate':
    provider => 'shell',
    user => 'vagrant',
    group => 'vagrant',
    require => [ File_line['add DJANGO_SETTINGS_MODULE env to postactivate'], ],
    environment => ["ORACLE_HOME=/opt/oracle/instantclient_11_2","LD_LIBRARY_PATH=/opt/oracle/instantclient_11_2","HOME=/home/vagrant","WORKON_HOME=/home/vagrant/.virtualenvs"],
    command => '/vagrant/vagrant/django_postgres_bootstrap.sh',
    unless => 'psql -lqt | cut -d \| -f 1 | grep -wq icommons_tools',
    logoutput => true,
}

# Active this virtualenv upon login
file {'/home/vagrant/.bash_profile':
    owner => 'vagrant',
    content => '
# Show git repo branch at bash prompt
parse_git_branch() {
    git branch 2> /dev/null | sed -e \'/^[^*]/d\' -e \'s/* \(.*\)/(\1)/\'
}
PS1="${debian_chroot:+($debian_chroot)}\u@\h:\w\$(parse_git_branch) $ "

echo "Activating python virtual environment \"icommons_tools\""
workon icommons_tools
    ',
    require => Exec['create-virtualenv'],
}
