# uam
[![CircleCI](https://circleci.com/gh/youyongsong/uam.svg?style=svg)](https://circleci.com/gh/youyongsong/uam)    
---
uam is abbreviation of universal application manager.

## Local Development
uam project use [invoke](http://docs.pyinvoke.org/en/latest/getting_started.html) as task execution tool. All development related tasks can be found using `inv -l`. 

### Prerequirements
* `python3`, `pip3`
* run `pip3 install -r requirements-dev.txt` to setup development environment.

### Common Tasks
* `inv lint`: you should run this command to check your code quality before every time you want to make a commit.
* `inv install`: this command will install ake cli from source code in editable mode(the changes of source code will apply to ake cli real time).
* `inv build`: this command will package ake into a single executable file. The format of the executable file depends on environment the command run, this task is commonly used in ci environment.
