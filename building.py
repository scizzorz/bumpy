import sys

CONFIG = {
	'color': True,
	'color_tasks': 4,
}

LOCALE = {
	'execute': 'execute\t{}',
	'abort': 'abort  \t{} - {}',
	'abort_bad_require': 'abort  \t{} - {} require failed',
	'abort_no_buildfile': 'abort  \t- no build.py found',
	'require': 'require\t{}',
	'help_command': '{}\t- {}',
	'help_creates': '\t- creates {}',
	'help_requires': '\t- requires {}',
	'help_unknown': 'unknown command: {}',
}

LIST = []
DICT = {}

class AbortException(Exception):
	def __init__(self, message):
		Exception.__init__(self, message)

class Task:
	def __init__(self, func, requires=[], creates=[]):
		self.func = func
		self.name = func.__name__
		self.help = func.__doc__
		self.requires = requires
		self.creates = creates

		self.valid = False

	def __call__(self, *args, **kwargs):
		print LOCALE['execute'].format(self)
		for req in self.requires:
			if not req.valid:
				print LOCALE['require'].format(req)
				if req() == False:
					print LOCALE['abort_bad_require'].format(self, req)
					return False

		try:
			self.func(*args, **kwargs)
		except AbortException, ex:
			print LOCALE['abort'].format(self, ex.message)
			return False

		self.valid = True

	def __repr__(self):
		return highlight('[' + self.name + ']', CONFIG['color_tasks'])


def task(requires=[], creates=[]):
	def wrapper(f):
		new_task = Task(f, requires, creates)
		LIST.append(new_task)
		DICT[new_task.name] = new_task
		return new_task

	return wrapper

def highlight(string, color):
	if CONFIG['color']:
		if color < 8:
			return '\033[{color}m{string}\033[0m'.format(string = string, color = color+30)
		else:
			return '\033[{color}m{string}\033[0m'.format(string = string, color = color+82)

def main(args):
	if len(args) == 0:
		for t in LIST:
			print LOCALE['help_command'].format(t, t.help)

			if t.creates:
				print LOCALE['help_creates'].format(t.creates)

			if t.requires:
				print LOCALE['help_requires'].format(t.requires)

	else:
		for arg in args:
			if arg in DICT:
				DICT[arg]()
			else:
				print LOCALE['help_unknown'].format(arg)


@task()
def clean():
	'''Cleans the project.'''
	print 'clean()'

@task()
def compile():
	'''Compiles the project.'''
	print 'compile()'

@task(requires=[compile])
def run():
	'''Runs the project.'''
	print 'run()'

@task(requires=[run])
def stop():
	'''Stops the project.'''
	print 'stop()'

@task(requires=[compile])
def abort():
	'''Raises an AbortException to fail the build.'''
	print 'abort()'
	raise AbortException('Aborted.')

@task(requires=[abort])
def bad():
	'''A bad task.'''
	print 'bad()'

if __name__ == '__main__':
	main(sys.argv[1:])
