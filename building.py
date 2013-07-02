import sys, subprocess, os, time

CONFIG = {
	'color': True,
	'color_invalid': 4,
	'color_success': 2,
	'color_fail': 1,
}

LOCALE = {
	'execute_single': 'execute\t{}',
	'execute_multi': 'execute\t{} - {}',
	'finish': 'finish \t{}',
	'abort': 'abort  \t{} - {}',
	'abort_bad_task': 'required task {} failed',
	'abort_bad_file': "required file '{}' does not exist",
	'help_command': '{} - {}',
	'help_requires': '\trequires {}',
	'help_unknown': 'unknown command: {}',
}

LIST = []
DICT = {}

def _highlight(string, color):
	if CONFIG['color']:
		if color < 8:
			return '\033[{color}m{string}\033[0m'.format(string = string, color = color+30)
		else:
			return '\033[{color}m{string}\033[0m'.format(string = string, color = color+82)

class AbortException(Exception):
	def __init__(self, message):
		Exception.__init__(self, message)

class Task:
	def __init__(self, func):
		self.func = func
		self.name = func.__name__
		self.help = func.__doc__

		self.requirements = ()
		self.valid = None

	def __call__(self, *args, **kwargs):
		if self.requirements:
			print LOCALE['execute_multi'].format(self, self.reqstr())
		else:
			print LOCALE['execute_single'].format(self)

		try:
			require(*self.requirements)
			self.func(*args, **kwargs)
		except AbortException, ex:
			self.valid = False
			print LOCALE['abort'].format(self, ex.message)
		else:
			self.valid = True
			print LOCALE['finish'].format(self)

		return self.valid

	def __repr__(self):
		color = CONFIG['color_invalid']

		if self.valid:
			color = CONFIG['color_success']
		elif self.valid == False:
			color = CONFIG['color_fail']

		return _highlight('[' + self.name + ']', color)

	def reqstr(self):
		return ', '.join(x.__repr__() for x in self.requirements)


def task(func):
	if not isinstance(func, Task):
		func = Task(func)
		LIST.append(func)
		DICT[func.name] = func
	return func

def abort(message):
	raise AbortException(message)

def shell(*command):
	try:
		return subprocess.check_output(list(command))
	except subprocess.CalledProcessError, ex:
		return ex

def requires(*requirements):
	def wrapper(func):
		func = task(func)
		func.requirements = requirements
		return func

	return wrapper

def require(*requirements):
	for req in requirements:
		if type(req) is str:
			if not os.path.exists(req):
				abort(LOCALE['abort_bad_file'].format(req))
		else:
			if req.valid is None:
				req()

			if req.valid == False:
				abort(LOCALE['abort_bad_task'].format(req))


def age(path):
	if not os.path.exists(path):
		return time.time()

	return time.time() - os.path.getmtime(path)

def main(args):
	if len(args) == 0:
		for task in LIST:
			print LOCALE['help_command'].format(task, task.help)

			if task.requirements:
				print LOCALE['help_requires'].format(task.reqstr())

	else:
		for arg in args:
			if arg in DICT:
				DICT[arg]()
			else:
				print LOCALE['help_unknown'].format(arg)
