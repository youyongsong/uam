# -*- coding: utf-8 -*-
import itertools


def dict_add(*args):
    return dict(itertools.chain(*[arg.items() for arg in args]))
