"""
parser: extract SSG friendly markdown from plain markdown files

fields we need:
- title: use the file name
- subtitle: use bert summarizer (abstractive summary)
- date: use git log --follow --format=%ad --date default <file_path>  | tail -1
        NOTE: has to be run at the repo of the content repo
- updated: use git log --follow --format=%ad --date default <file_path>  | tail -1
- draft: whether it is published or not [Hugo specific config]
- categories: use spaCy NER + keyword extractor
- tags: use spaCy NER + keyword extractor
"""
import pathlib
import shutil
import subprocess
from io import StringIO

import spacy
from markdown import Markdown
from transformers import pipeline
from tqdm import tqdm

# load spacy model
nlp = spacy.load("en_core_web_sm")


class Metadata:
    """
    class to parse Markdown files & generate Hugo metadata
    """

    @staticmethod
    def title(path):
        """
        get title metadata for a path. path is a valid path to a markdown file

        :param path (str): path to markdown file we want to get title metdata for
        """
        filename = pathlib.Path(path).name.split(".")[0].replace("_", " ").title()
        if "readme" in filename.lower():
            return f"{pathlib.Path(path).parent.name} {filename.lower()}"
        return filename

    @staticmethod
    def text(path):
        """
        get text content of a markdown file

        :param path (str): path to markdown file we want to get text from
        """

        # read file
        data = open(path, "r").read()

        def unmark_element(element, stream=None):
            if stream is None:
                stream = StringIO()
            if element.text:
                stream.write(element.text)
            for sub in element:
                unmark_element(sub, stream)
            if element.tail:
                stream.write(element.tail)
            return stream.getvalue()

        # patching Markdown
        Markdown.output_formats["plain"] = unmark_element
        __md = Markdown(output_format="plain")
        __md.stripTopLevelTags = False
        return __md.convert(data)

    @staticmethod
    def tags(path):
        """
        get tags metadata for a path. path is a valid path to a markdown file.
        tags are extracted using spaCy

        :param path (str): path to markdown file we want to get tags metdata for
        """

        text = Metadata.text(path)
        doc = nlp(text)
        labels = set([w.label_ for w in doc.ents])
        labelled = {}
        for label in labels:
            entities = [
                e.text
                for e in doc.ents
                if label == e.label_
                and "/" not in e.text
                and "." not in e.text
                and "-" not in e.text
                and "\\" not in e.text
                and "_" not in e.text
            ]
            entities = list(set(list(entities)))[:5]
            labelled[label] = entities
        cleaned = labelled["ORG"] if "ORG" in labelled else []
        return [
            entity.replace("\n", " ").strip().replace("_", " ")
            for entity in cleaned
            if "#" not in entity and "_" not in entity
        ]

    @staticmethod
    def categories(path, root):
        """
        get categories metadata for a path. in this case a category is whatever directory
        the markdown file is in

        :param path (str): path to markdown file we want to get category metdata for
        :param root (str): path to the root of all md files from which we will extract a rel path
        """
        relpath = str(pathlib.Path(path).relative_to(root))
        if "/" in relpath:
            return [item for item in relpath.split("/") if "." not in item]
        if "." in relpath:
            return []
        return [relpath]

    @staticmethod
    def subtitle(path):
        """
        get subtitle metadata for a path. path is a valid path to a markdown file
        subtitle is an abstract summarization of the contents of the markdown file

        :param path (str): path to markdown file we want to get title metdata for
        """

        text = Metadata.text(path).replace("\n", "")
        summarizer = pipeline("summarization")
        # TODO: better processing
        summary_text = summarizer(text[:2500])[0]["summary_text"]
        return summary_text.replace('"', "")

    @staticmethod
    def created(path, repo):
        """
        get created date metadata a path. path is a valid path to a markdown file
        this method uses subprocess + git log to get this information (git log might
        be flaky sometimes)

        :param path (str): path to markdown file we want to get title metdata for
        :param repo (str): path to repo containing file
        """

        created = subprocess.check_output(
            f"git log --diff-filter=A --follow --format=%aI --date human -- {path} | tail -1",
            cwd=repo,
            shell=True,
        )
        return created.decode("utf-8").strip()

    @staticmethod
    def updated(path, repo):
        """
        get last modified date metadata a path. path is a valid path to a markdown file
        this method uses subprocess + git log to get this information (git log might
        be flaky sometimes)

        :param path (str): path to markdown file we want to get title metdata for
        :param repo (str): path to repo containing file
        """
        updated = subprocess.check_output(
            f'git log -1 --pretty="format:%ci" {path} | tail -1', cwd=repo, shell=True
        )
        return updated.decode("utf-8").strip()

    @staticmethod
    def generate(path: str, repo: str, author="sirch", output: str = "./content"):
        """
        generate metadata for a given path. path can be a single markdown file or a
        directory containing a bunch of markdown files. this function simply extracts
        Hugo friendly metadata for each markdown file & appends it at the top & saves
        the file in a new location

        :param path (str): path to markdown file we want to get title metdata for
        :param repo (str): path to repo containing files
        :param output (str): path to output directory
        """
        # path config
        paths = []
        if path is None:
            for item in pathlib.Path(repo).rglob("*.md"):
                paths.append(item)
        else:
            if pathlib.Path(path).is_file():
                paths = [path]
            else:
                for item in pathlib.Path(path).rglob("*.md"):
                    paths.append(item)
        # processing
        for item in tqdm(paths):
            print(f"processing: {item}")
            try:
                title = Metadata.title(item)
                subtitle = Metadata.subtitle(item)
                tags = Metadata.tags(item)
                categories = Metadata.categories(item, repo)
                created = Metadata.created(item, repo)
                updated = Metadata.created(item, repo)
                metadata = f"""---
author: "{author}"
title: "{title}"
subtitle: "{subtitle}"
created: {created}
date: {updated}
draft: false
weight: 10
tags: {tags}
categories: {categories}
---
"""
                print(metadata)
                # copy file first
                source = pathlib.Path(item)
                # TODO: maintain directory structure or retain some sort of history
                new = pathlib.Path(output) / source.name
                shutil.copy(source, new)
                # insert metadata to new file
                def line_prepender(filename, line):
                    with open(filename, "r+") as f:
                        content = f.read()
                        f.seek(0, 0)
                        f.write(line.rstrip("\r\n") + "\n" + content)

                line_prepender(str(new), metadata)
            except:
                print(f"skipping: {item}")
                pass
