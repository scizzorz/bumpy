import sys, subprocess, os, time

CONFIG = {
	'color': True,
	'color_invalid': 4,
	'color_success': 2,
	'color_fail': 1,

	'cli': False,
	'abbrev': True,
	'suppress': (),
	}

LOCALE = {
	'execute_single': 'execute\t{}',
	'execute_multi': 'execute\t{} - {}',
	'finish': 'finish \t{}',
	'abort': 'abort  \t{} - {}',
	'abort_bad_task': 'required task {} failed',
	'abort_bad_file': "required file '{}' does not exist",
	'help_command': '{}{} - {}',
	'help_aliases': '\taliases: {}',
	'help_requires': '\trequires: {}',
	'help_unknown': 'unknown task: {}',
	'shell': '$ {}',
	}

LIST = []
DICT = {}
GENERATES = []
DEFAULT = None
SETUP = None
TEARDOWN = None

def _highlight(string, color):
	if CONFIG['color']:
		if color < 8:
			return '\033[{color}m{string}\033[0m'.format(string = string, color = color+30)
		else:
			return '\033[{color}m{string}\033[0m'.format(string = string, color = color+82)

class _AbortException(Exception):
	def __init__(self, message):
		Exception.__init__(self, message)

class _Task:
	def __init__(self, func):
		self.func = func
		self.name = func.__name__
		self.help = func.__doc__

		self.aliases = ()
		self.suppress = ()
		self.requirements = ()
		self.valid = None

	def __call__(self, *args, **kwargs):
		if self.requirements:
			self.__print('execute_multi', self, self.reqstr())
		else:
			self.__print('execute_single', self)

		try:
			require(*self.requirements)
			self.func(*args, **kwargs)
		except _AbortException, ex:
			self.valid = False
			self.__print('abort', self, ex.message)
		else:
			self.valid = True
			self.__print('finish', self)

		return self.valid

	def __repr__(self):
		color = CONFIG['color_invalid']

		if self.valid:
			color = CONFIG['color_success']
		elif self.valid == False:
			color = CONFIG['color_fail']

		return _highlight('[' + self.name + ']', color)

	def __print(self, id, *args):
		if ('all' not in self.suppress) and (id not in self.suppress) and ('all' not in CONFIG['suppress']) and (id not in CONFIG['suppress']):
			print LOCALE[id].format(*args)

	def match(self, name):
		if self.name.startswith(name):
			return True

		for alias in self.aliases:
			if alias.startswith(name):
				return True

	def reqstr(self):
		return ', '.join(x.__repr__() for x in self.requirements)

	def aliasstr(self):
		return ', '.join(x.__repr__() for x in self.aliases)


# bumpy decorators
def task(func):
	global LIST, DICT

	if not isinstance(func, _Task):
		func = _Task(func)
		LIST.append(func)
		DICT[func.name] = func
	return func
command = task
cmd = task

def default(func):
	global DEFAULT

	func = task(func)
	DEFAULT = func

	return func

def setup(func):
	global SETUP

	func = task(func)
	SETUP = func

	return func

def teardown(func):
	global TEARDOWN

	func = task(func)
	TEARDOWN = func

	return func

def private(func):
	global LIST, DICT

	func = task(func)

	if func in LIST:
		LIST.remove(func)

	if func.name in DICT:
		del DICT[func.name]

	return func

def suppress(*messages):
	def wrapper(func):
		func = task(func)
		func.suppress = messages
		return func

	return wrapper

def requires(*requirements):
	def wrapper(func):
		func = task(func)
		func.requirements = requirements
		return func

	return wrapper

def alias(*aliases):
	def wrapper(func):
		global DICT

		func = task(func)
		func.aliases = aliases

		for alias in aliases:
			DICT[alias] = func

		return func

	return wrapper

def generates(*files):
	def wrapper(func):
		global GENERATES
		func = task(func)
		GENERATES += list(files)
		return func

	return wrapper


# bumpy helpers
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

def valid(*things):
	for thing in things:
		if type(thing) is str:
			return os.path.exists(thing)
		else:
			return req.valid

def shell(command):
	global CONFIG
	if 'shell' not in CONFIG['suppress']:
		print LOCALE['shell'].format(command)

	try:
		return subprocess.check_output(command, shell=True)
	except subprocess.CalledProcessError, ex:
		return ex

def age(*paths):
	for path in paths:
		if not os.path.exists(path):
			return time.time()

	return min([(time.time() - os.path.getmtime(path)) for path in paths])

def clean():
	global GENERATES
	shell('rm ' + ' '.join(GENERATES))

def abort(message):
	raise _AbortException(message)


# bumpy help
@default
@suppress('execute_single', 'execute_multi', 'finish')
def help():
	'''Print all available tasks and descriptions.'''
	for task in LIST:
		tags = ''
		if task is DEFAULT:
			tags += '*'
		if task is SETUP:
			tags += '+'
		if task is TEARDOWN:
			tags += '-'

		print LOCALE['help_command'].format(task, tags, task.help)

		if task.aliases:
			print LOCALE['help_aliases'].format(task.aliasstr())
		if task.requirements:
			print LOCALE['help_requires'].format(task.reqstr())


# bumpy
def config(**kwargs):
	for key in kwargs:
		CONFIG[key] = kwargs[key]

def get_task(name):
	global LIST, DICT

	if name in DICT:
		return DICT[name]
	elif CONFIG['abbrev']:
		matches = [task for task in LIST if task.match(name)]
		if matches:
			return matches[0]

def main(args):
	if SETUP:
		SETUP()

	if not args and DEFAULT:
		DEFAULT()
	else:
		if CONFIG['cli']:
			temp = get_task(args[0])
			i = 1
			nargs = []
			kwargs = {}

			if temp is None:
				i = 0

			while i < len(args):
				if args[i].startswith('--'):
					kwargs[args[i][2:]] = args[i+1]
					i += 2
				else:
					nargs.append(args[i])
					i += 1

			if not temp and DEFAULT:
				temp = DEFAULT

			try:
				temp(*nargs, **kwargs)
			except Exception, ex:
				temp.valid = False
				print LOCALE['abort'].format(temp, ex.message)

		else:
			for arg in args:
				temp = get_task(arg)
				if temp is not None:
					temp()
				else:
					print LOCALE['help_unknown'].format(arg)

	if TEARDOWN:
		TEARDOWN()
