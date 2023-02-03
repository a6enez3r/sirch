# `sirch`

Is a tool that allows you to annotate static markdown content with Hugo metadata to generate a searchable static documentation site. 

It leverages `Hugo`, an open-source static site generator, and `Pagefind`, a static search library. In addition, it uses various open source NLP libraries such as `spaCy` and `transformers` to auto-generate tags based on the content of files.

## quickstart

- Create a virtual environment & install all dependencies
```
python3 -m venv venv
source venv/bin/activate
make deps
```
- Generate annotated Markdown files
```
# default locations
make annotate

# override locations
make annotate input_path=<path/to/md/handbook> root_path=<path/to/md/repo/root> output_path=<path/to/output/dir>
```
- Sync annotated files
```
# default locations
make sync
```
- Start searchable website
```
make run
```
