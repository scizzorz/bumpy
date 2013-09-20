#!/usr/bin/env python
import bumpy
import sys

# $ bumpy
@bumpy.default
def default():
	pass

# $ bumpy task
@bumpy.task
def task():
	pass

# $ bumpy args arg1 arg2 arg3
@bumpy.task
def args(*args):
	print "Local bumpy args:"
	print args

# $ bumpy opts --one Hello --two arg1 arg2 arg3
@bumpy.args(one = 'Yes', two = None)
def opts(*args, **kwargs):
	print "Local bumpy args:"
	print args
	print "Local bumpy options:"
	print kwargs


# invoked before any other bumpy tasks
@bumpy.setup
def setup():
	pass

# invoked after all other bumpy tasks
@bumpy.teardown
def teardown():
	pass

# invoked before all other bumpy tasks
# used to process global opts
@bumpy.options
def options(**kwargs):
	print "Global bumpy options:"
	print kwargs

# mark this as a "cli" file, rather than a "build" file
bumpy.config(cli = True)

# global options
# $ bumpy --one --two -a -b task
bumpy.config(long_options = ['one', 'two', 'three'])
bumpy.config(options = 'abc')
