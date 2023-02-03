## sirch.Makefile: commands for generating a low-memory search enabled Hugo site for markdown files

.DEFAULT_GOAL := help
TARGET_MAX_CHAR_NUM=20
# COLORS
ifneq (,$(findstring xterm,${TERM}))
	BLACK        := $(shell tput -Txterm setaf 0 || exit 0)
	RED          := $(shell tput -Txterm setaf 1 || exit 0)
	GREEN        := $(shell tput -Txterm setaf 2 || exit 0)
	YELLOW       := $(shell tput -Txterm setaf 3 || exit 0)
	LIGHTPURPLE  := $(shell tput -Txterm setaf 4 || exit 0)
	PURPLE       := $(shell tput -Txterm setaf 5 || exit 0)
	BLUE         := $(shell tput -Txterm setaf 6 || exit 0)
	WHITE        := $(shell tput -Txterm setaf 7 || exit 0)
	RESET := $(shell tput -Txterm sgr0)
else
	BLACK        := ""
	RED          := ""
	GREEN        := ""
	YELLOW       := ""
	LIGHTPURPLE  := ""
	PURPLE       := ""
	BLUE         := ""
	WHITE        := ""
	RESET        := ""
endif

## show usage / common commands available
.PHONY: help
help:
	@printf "\n${PURPLE}common${RESET}: collection of commands to simplify running common Docker containers\n\n"
	@printf "${RED}cmds:\n\n";

	@awk '{ \
			if ($$0 ~ /^.PHONY: [a-zA-Z\-\_0-9]+$$/) { \
				helpCommand = substr($$0, index($$0, ":") + 2); \
				if (helpMessage) { \
					printf "  ${LIGHTPURPLE}%-$(TARGET_MAX_CHAR_NUM)s${RESET} ${GREEN}%s${RESET}\n\n", helpCommand, helpMessage; \
					helpMessage = ""; \
				} \
			} else if ($$0 ~ /^[a-zA-Z\-\_0-9.]+:/) { \
				helpCommand = substr($$0, 0, index($$0, ":")); \
				if (helpMessage) { \
					printf "  ${BLUE}%-$(TARGET_MAX_CHAR_NUM)s${RESET} ${GREEN}%s${RESET}\n", helpCommand, helpMessage; \
					helpMessage = ""; \
				} \
			} else if ($$0 ~ /^##/) { \
				if (helpMessage) { \
					helpMessage = helpMessage"\n                     "substr($$0, 3); \
				} else { \
					helpMessage = substr($$0, 3); \
				} \
			} else { \
				if (helpMessage) { \
					print "\n${YELLOW}             "helpMessage"\n" \
				} \
				helpMessage = ""; \
			} \
		}' \
		$(MAKEFILE_LIST)


## -- shell commands --

# general config
ifeq ($(parser_in),)
parser_in := /Users/abenezer/Code/packages/sirch/content
endif
ifeq ($(parser_out),)
parser_out := /Users/abenezer/Code/packages/sirch/site/content/post
endif
ifeq ($(input_path),)
input_path := /Users/abenezer/Code/packages/sirch/content
endif
ifeq ($(output_path),)
output_path := /Users/abenezer/Code/packages/sirch/site/content/post
endif
ifeq ($(root_path),)
root_path := /Users/abenezer/Code/packages/sirch/content
endif

## create site
create:
	@hugo new site site
	@cd site
	@git init
	@git submodule add https://github.com/zwbetz-gh/papercss-hugo-theme.git themes/papercss-hugo-theme
	@hugo server -D

 
## install deps
deps:
	@brew install hugo
	@python3 -m pip install -U pip setuptools wheel
	@python3 -m pip install -r requirements.txt
	@python3 -m spacy download en_core_web_sm

## format parser
format:
	@python3 -m black parser

## lint parser
lint:
	@python3 -m pylint parser

## generate annotated markdown files
annotate:
	@cd parser
	@python3 cli.py ${input_path} ${root_path} ${output_path}

## sync annotated files
sync:
	@cp -r ${parser_in}/*.md ${parser_out}

## run searchable site
run:
	@cd site && hugo server -D