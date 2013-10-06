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
