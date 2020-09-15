TopHN
=====

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
