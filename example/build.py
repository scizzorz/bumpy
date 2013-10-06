import bumpy as b
import db

@b.task
def clean():
	print 'Cleaning'

@b.task
def lint():
	print 'Linting'

@b.task('default')
def build():
	print 'Building'

@b.task(reqs=(build, db.init))
def run():
	print 'Running'

@b.task(reqs=lint)
def docs(modules, format='markdown'):
	print 'Documenting {!r} as {}'.format(modules, format)

@b.task(alias='pkg', reqs=(build, docs))
def package():
	print 'Packaging'

@b.task('setup', 'private')
def setup():
	print 'Setting stuff up'

@b.task('teardown')
def _teardown():
	print 'Tearing stuff down'

@b.task(reqs='input.txt', gens='output.txt')
def output():
	if b.age('input.txt') < b.age('output.txt'):
		b.shell('cp input.txt output.txt')

@b.task
def args(arg1, arg2):
	print 'arg1 = {!r}, arg2 = {!r}'.format(arg1, arg2)

@b.task
def kwargs(msg='Hello, world!', double=False):
	print msg
	if double:
		print msg
