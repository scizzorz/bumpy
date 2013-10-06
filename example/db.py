import bumpy as b

@b.task
def init():
	print 'Initializing database'

@b.task
def migrate(start=0.1, end=0.2):
	start, end = float(start), float(end)
	if end <= start:
		b.abort('Unable to migrate to a previous version')

	print 'Migrating database from {} to {}'.format(start, end)

@b.task
def destroy():
	print 'Destroying database'
