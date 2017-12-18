import re


def complete_shorten_address(address):
    shorten_pattern = re.compile(r"^[\w\-_\.]+/[\w\-_\.]+$")
    if shorten_pattern.match(address):
        return f'git@github.com:{address}.git'
    return address