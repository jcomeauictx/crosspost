SERVER := 
USERNAME := 
SERVER_DIR := src/repost
DRYRUN ?= --dry-run
MACHINE := graph.facebook.com
PAGE_ID := $(shell awk '$$2 ~ /^$(MACHINE)$$/ {print $$4}' $(HOME)/.netrc)
APP_ID := $(shell awk '$$2 ~ /^$(MACHINE)$$/ {print $$6}' $(HOME)/.netrc)
APP_SECRET := $(shell awk '$$2 ~ /^$(MACHINE)$$/ {print $$8}' $(HOME)/.netrc)
SCOPE := manage_pages,publish_actions,publish_pages
FB := https://www.facebook.com
GRAPH := https://$(MACHINE)
CODE ?=
TOKEN ?=
TWOMONTHTOKEN ?=
BROWSER ?= w3m -dump
REDIRECT := http://jc.unternet.net/test.cgi
CLIENT_SIDE := $(FB)/dialog/oauth?client_id=$(APP_ID)&redirect_uri=$(REDIRECT)
CLIENT_SIDE := $(CLIENT_SIDE)&scope=$(SCOPE)&response_type=code
SERVER_SIDE := $(GRAPH)/oauth/access_token?client_id=$(APP_ID)
SERVER_SIDE := $(SERVER_SIDE)&redirect_uri=$(REDIRECT)
SERVER_SIDE := $(SERVER_SIDE)&client_secret=$(APP_SECRET)&code=$(CODE)
LONG_LIVED := $(GRAPH)/oauth/access_token?client_id=$(APP_ID)
LONG_LIVED := $(LONG_LIVED)&client_secret=$(APP_SECRET)
LONG_LIVED := $(LONG_LIVED)&grant_type=fb_exchange_token
LONG_LIVED := $(LONG_LIVED)&fb_exchange_token=$(TOKEN)
ACCOUNTS := $(GRAPH)/me/accounts?access_token=$(TWOMONTHTOKEN)
export
env:
	env
	@echo Usage: make code
	@echo '        ' make CODE=codefrompreviousstep token
	@echo '        ' make TOKEN=tokenfrompreviousstep longterm
	@echo '        ' make TWOMONTHTOKEN=tokenfrompreviousstep accounts
	@echo Then edit '$$HOME/.netrc' replacing password with page token
code:
	$(BROWSER) "$(CLIENT_SIDE)"
token:
	$(BROWSER) "$(SERVER_SIDE)"
longterm:
	$(BROWSER) "$(LONG_LIVED)"
accounts:
	$(BROWSER) $(ACCOUNTS)
upload:
	rsync -avuz $(DRYRUN) \
		--exclude '.bzr*' \
		--exclude '*.pyc' \
		--exclude '*.pyo' \
		. $(USERNAME)@$(SERVER):$(SERVER_DIR)/
download:
	rsync -avuz $(DRYRUN) \
		--exclude '*.pyc' \
		--exclude '*.pyo' \
		$(USERNAME)@$(SERVER):$(SERVER_DIR)/ .
	rsync -avuz $(DRYRUN) \
	       	$(USERNAME)@$(SERVER):tmp/repost_state.txt ~/tmp/
ssh:
	ssh $(USERNAME)@$(SERVER)
rootssh:
	ssh root@$(SERVER)
test:
	DO_NOT_POST=1 python repost.py
