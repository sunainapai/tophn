NAME = tophn
FQDN = $(NAME).org
MAIL = sunainapai.in@gmail.com

help:
	@echo 'Usage: make [target]'
	@echo
	@echo 'High-level targets:'
	@echo '  setup   Install Debian packages.'
	@echo '  https   Reinstall live website and serve with Nginx via HTTPS.'
	@echo '  http    Reinstall live website and serve with Nginx via HTTP.'
	@echo '  update  Pull latest Git commits and update live website.'
	@echo '  rm      Uninstall live website.'
	@echo
	@echo 'Low-level targets:'
	@echo '  pull    Pull latest Git commits but do not update live website.'
	@echo
	@echo 'Default target:'
	@echo '  help    Show this help message.'

setup:
	apt-get update
	apt-get -y install nginx certbot python3-venv
	python3 -m venv /opt/venv/tophn
	/opt/venv/tophn/bin/pip3 install jinja2

tophn:
	mkdir -p /opt/tophn.org
	chown www-data /opt/tophn.org
	systemctl enable "$$PWD/etc/tophn.service"
	systemctl daemon-reload
	systemctl start tophn

https: http
	@echo Setting up HTTPS website ...
	certbot certonly -n --agree-tos -m '$(MAIL)' --webroot \
	                 -w '/var/www/$(FQDN)' -d '$(FQDN),www.$(FQDN)'
	(crontab -l | sed '/::::/d'; cat etc/crontab) | crontab
	ln -snf "$$PWD/etc/nginx/https.$(FQDN)" '/etc/nginx/sites-enabled/$(FQDN)'
	systemctl reload nginx
	@echo Done; echo

http: rm tophn
	@echo Setting up HTTP website ...
	ln -snf "$$PWD/_live" '/var/www/$(FQDN)'
	ln -snf "$$PWD/etc/nginx/http.$(FQDN)" '/etc/nginx/sites-enabled/$(FQDN)'
	systemctl reload nginx
	echo 127.0.0.1 '$(NAME)' >> /etc/hosts
	@echo Done; echo

update: pull

rm: checkroot
	@echo Removing website ...
	rm -f '/etc/nginx/sites-enabled/$(FQDN)'
	rm -f '/var/www/$(FQDN)'
	systemctl reload nginx
	sed -i '/$(NAME)/d' /etc/hosts
	#
	# Following crontab entries left intact:
	crontab -l | grep -v "^#" || :
	@echo Done; echo

local:
	@echo Serving website locally ...
	if python3 -c "import http.server" 2> /dev/null; then \
		echo Running Python3 http.server ...; \
		cd _site && python3 -m http.server; \
	elif python -c "import http.server" 2> /dev/null; then \
		echo Running Python http.server ...; \
		cd _site && python -m http.server; \
	elif python -c "import SimpleHTTPServer" 2> /dev/null; then \
		echo Running Python SimpleHTTPServer ...; \
		cd _site && python -m SimpleHTTPServer; \
	else \
		echo Cannot find http.server or SimpleHTTPServer.;  \
	fi
	@echo Done; echo

pull:
	@echo Pulling new changes ...
	git fetch
	if [ "$$(git rev-parse HEAD)" = "$$(git rev-parse "@{u}")" ]; then \
		echo; echo No new changes; echo; false; \
	fi
	git merge
	@echo Done; echo

checkroot:
	@echo Checking if current user is root ...
	[ $$(id -u) = 0 ]
	@echo Done; echo

clean:
	find . -name "__pycache__" -exec rm -r {} +
	find . -name "*.pyc" -exec rm {} +
