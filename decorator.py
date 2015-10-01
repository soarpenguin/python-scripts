#!/usr/bin/env python
# -*- coding: utf-8 -*-

# decorator.py -- Decorator usage of python.


# ----------------------------------------------------
# decorator without parameter.
def b(fn):
    return lambda s: '<b>%s</b>' % fn(s)
 
def em(fn):
    return lambda s: '<em>%s</em>' % fn(s)
 
@b
@em
def greet(name):
    return 'Hello, %s!' % name

print(greet('world'))


# ----------------------------------------------------
# decorator with parameter.
def tag_wrap(tag):
    def decorator(fn):
        def inner(s):
            return '<%s>%s</%s>' % (tag, fn(s), tag)
        return inner
    return decorator
 
@tag_wrap('b')
@tag_wrap('em')
def greet(name):
    return 'Hello, %s!' % name
 
print(greet('world'))
