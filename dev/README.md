TopHN
=====
This document describes how to set up the development and the live
environments of the website [TopHN][WEBSITE].

Note that the TopHN website is developed primarily on a Debian system,
so the steps below are written for Debian system. To develop this
website on any other system, some of the steps below may have to be
modified.

[WEBSITE]: https://tophn.org/


Contents
--------
* [Development Setup](#development-setup)
* [Live Setup](#live-setup)


Development Setup
-----------------
Perform the following steps to setup the development environment for
the website on local system.

 1. Install necessary tools.

        sudo apt-get update
        sudo apt-get -y install nginx git

 2. Clone this repository.

        mkdir -p ~/git
        cd ~/git
        git clone https://github.com/sunainapai/tophn.git

 3. Configure Nginx for development.

        sudo ln -sf ~/git/tophn/etc/nginx/dev.tophn.org /etc/nginx/sites-enabled/
        sudo ln -sf ~/tophn.org/live /var/www/tophn.org
        sudo systemctl reload nginx

 4. Associate the hostname `tophn` with the loopback interface.

        echo 127.0.2.1 tophn | sudo tee -a /etc/hosts

 5. Set up the log and database directories.

        mkdir -p ~/tophn.org/log ~/tophn.org/database

 6. Install the necessary tools in the virtual environment.

        python3 -m venv ~/.venv/tophn.org/
        . ~/.venv/tophn.org/bin/activate
        pip install jinja2 urllib3
        deactivate

 7. Generate the website.

        cd ~/git/tophn
        nohup ./tophn.sh >> ~/tophn.org/log/nohup.out &

 8. Visit http://tophn/ with a web browser to see a local copy of the
    website.


Live Setup
----------
Perform the following steps to setup the live environment on an internet
facing server.

 1. Log in as user sunaina and perform steps 1, 2, 3, 5, 6 and 7 from the
    previous section.

 2. Install certbot.

        echo 'deb http://ftp.debian.org/debian jessie-backports main' | sudo tee /etc/apt/sources.list.d/backports.list
        sudo apt-get update
        sudo apt-get install certbot -t jessie-backports

 3. Get TLS certificates.

        sudo certbot certonly --webroot -w /var/www/tophn.org -m sunainapai.in@gmail.com -d tophn.org,www.tophn.org

 4. Configure Nginx for the live website.

        sudo rm /etc/nginx/sites-enabled/dev.tophn.org
        sudo ln -sf ~/git/tophn/etc/nginx/tophn.org /etc/nginx/sites-enabled/tophn.org
        sudo systemctl reload nginx

 5. Visit https://tophn.org/ with a web browser to see the live website.
