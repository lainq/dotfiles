import sys
import os

import inquirer

from rich.console import Console
from rich.markdown import Markdown
from rich.syntax import Syntax


def get_directory(args):
    if len(args) > 0:
        filename = args[0]
        if not os.path.isdir(filename):
            print(f"Cannot find {filename}")
            sys.exit()
        return filename
    return os.getcwd()


def files(directory):
    console = Console()
    content = os.listdir(directory)
    questions = [
        inquirer.List("open", message="Open", choices=content),
    ]
    open_file = inquirer.prompt(questions).get("open")
    path = os.path.join(directory, open_file)
    if os.path.isfile(path):
        with open(path, "r") as reader:
            content = reader.read()
        if path.endswith(".md"):
            console.print(Markdown(content))
        else:
            console.print(Syntax(content, open_file.split(".")[-1]))
        files(directory)
    elif os.path.isdir(path):
        os.system("clear")
        files(path)


def main():
    args = sys.argv[1:]
    directory = get_directory(args)
    files(directory)


if __name__ == "__main__":
    main()
