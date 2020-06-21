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
* [Troubleshooting Tips](#troubleshooting-tips)


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

 5. Install the necessary tools in the virtual environment.

        python3 -m venv ~/.venv/tophn.org/
        . ~/.venv/tophn.org/bin/activate
        pip install jinja2 urllib3
        deactivate

 6. Generate the website.

        cd ~/git/tophn
        sudo ln -sf ~/git/tophn/etc/systemd/tophn.service /etc/systemd/system/
        sudo systemctl start tophn

 7. Visit http://tophn/ with a web browser to see a local copy of the
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


Troubleshooting Tips
--------------------
### Error When Rendering Unicode Characters

The following error occurred in Debian 8.8 in DigitalOcean droplet.

    2017-10-12 00:29:17 - tophn - INFO - Working ...
    2017-10-12 00:29:17 - tophn - INFO - Current Time: 1507768157: 2017-10-12 00:29:17 GMT
    2017-10-12 00:29:17 - tophn - INFO - Top ID on HN: 15453974
    2017-10-12 00:29:17 - tophn - INFO - Most frequent top ID in the past 24 hours: 15447706
    2017-10-12 00:29:17 - tophn - INFO - Creating /home/sunaina/tophn.org/_stage/ directory ...
    2017-10-12 00:29:17 - tophn - INFO - Copying static directory to /home/sunaina/tophn.org/_stage/ ...
    2017-10-12 00:29:17 - tophn - INFO - Rendering home page ...
    2017-10-12 00:29:17 - tophn - ERROR - Unexpected error occurred
    Traceback (most recent call last):
      File "./tophn.py", line 406, in _main
        _stage_top_hn(config, archive_list)
      File "./tophn.py", line 326, in _stage_top_hn
        _render(config, templates_home, archive_list[-1], home_page)
      File "./tophn.py", line 185, in _render
        f.write(template.render(template_values))
    UnicodeEncodeError: 'ascii' codec can't encode character '\u2019' in position 382: ordinal not in range(128)
    2017-10-12 00:29:17 - tophn - INFO - Sleeping for 60 seconds ...
    2017-10-12 00:30:18 - tophn - INFO - Working ...

Perform the following steps to fix this issue.

 1. Reconfigure locale on Debain 8.8.

        locale-gen en_US.UTF-8
        sudo dpkg-reconfigure locales

    Select en_US.UTF-8 UTF-8 in Configuring Locales - Locales to be
    generated and Default locale for the system environment.

 2. Add the following lines in /etc/enviroment

        LANGUAGE=en_US.UTF-8
        LC_ALL=en_US.UTF-8

 3. Logout and login again and check the locale.

        locale
