import copy, os, getopt, subprocess, sys, time

__version__ = '0.3.0'

# Configuration settings
CONFIG = {
	'color': True,
	'color_invalid': 4,
	'color_success': 2,
	'color_fail': 1,

	'cli': False,
	'abbrev': True,
	'suppress': (),
	'options': '',
	'long_options': [],
	}


# Output string formats / messages
LOCALE = {
	'abort': 'abort {}: {}',
	'abort_bad_file': "required file '{}' does not exist",
	'abort_bad_task': 'required task {} failed',
	'enter': 'enter {}',
	'enter_gen': 'enter {} -> {!r}',
	'enter_genreq': 'enter {} -> {!r} <- {}',
	'enter_req': 'enter {} <- {}',
	'help_aliases': '\taliases: {}',
	'help_args': '\targuments:',
	'help_arg': '\t\t--{} = {}',
	'help_command': '{}{}: {}',
	'help_generates': '\tgenerates: {!r}',
	'help_requires': '\trequires: {}',
	'help_unknown': 'unknown task: {}',
	'leave': 'leave {}',
	'shell': '$ {}',
	}


# State variables
TASKS = {}
GENERATES = {}
DEFAULT = None
SETUP = None
TEARDOWN = None
OPTIONS = None


# Private helpers
def _get_task(name):
	global TASKS

	if name in TASKS:
		return TASKS[name]
	elif CONFIG['abbrev']:
		matches = [task for key, task in TASKS.items() if task.match(name)]
		if matches:
			return matches[0]

def _opts_to_dict(*opts):
	ret = {}
	for key, val in opts:
		if key[:2] == '--': key = key[2:]
		elif key[:1] == '-': key = key[1:]
		if val == '': val = True
		ret[key] = val
	return ret

def _highlight(string, color):
	if CONFIG['color']:
		if color < 8:
			return '\033[{color}m{string}\033[0m'.format(string = string, color = color+30)
		else:
			return '\033[{color}m{string}\033[0m'.format(string = string, color = color+82)


# Private classes
class _AbortException(Exception):
	def __init__(self, message):
		Exception.__init__(self, message)

class _Task:
	aliases = ()
	suppress = ()
	args = []
	defaults = {}
	requirements = ()
	file_requirements = ()
	task_requirements = ()
	generates = None
	valid = None
	method = False

	def __init__(self, func):
		self.func = func
		self.name = func.__name__
		self.help = func.__doc__

	def __call__(self, *args, **kwargs):
		if self.requirements and self.generates:
			self.__print('enter_genreq', self, self.generates, self.reqstr())
		elif self.requirements:
			self.__print('enter_req', self, self.reqstr())
		elif self.generates:
			self.__print('enter_gen', self, self.generates)
		else:
			self.__print('enter', self)

		try:
			require(*self.requirements)
			if self.method:
				self.func(self, *args, **kwargs)
			else:
				self.func(*args, **kwargs)
		except _AbortException, ex:
			self.valid = False
			self.__print('abort', self, ex.message)
		else:
			self.valid = True
			self.__print('leave', self)

		return self.valid

	def __repr__(self):
		color = CONFIG['color_invalid']

		if self.valid:
			color = CONFIG['color_success']
		elif self.valid == False:
			color = CONFIG['color_fail']

		return _highlight('[' + self.name + ']', color)

	def __print(self, id, *args):
		if 'all' in self.suppress or id in self.suppress: return
		if 'all' in CONFIG['suppress'] or id in CONFIG['suppress']: return

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

class _Generic:
	def __init__(self, func):
		self.task = task(copy.deepcopy(func))
		method(self.task)
		private(self.task)

	def default(self):
		default(self.task)
		return self
	def setup(self):
		setup(self.task)
		return self
	def teardown(self):
		teardown(self.task)
		return self
	def options(self):
		options(self.task)
		return self
	def suppress(self, *messages):
		suppress(*messages)(self.task)
		return self
	def requires(self, *requirements):
		requires(*requirements)(self.task)
		return self
	def args(self, **opts):
		args(**opts)(self.task)
		return self
	def generates(self, target):
		generates(target)(self.task)
		return self


# Decorators | attributes
def task(func):
	global TASKS
	if not isinstance(func, _Task):
		func = _Task(func)
		TASKS[func.name] = func
	return func

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

def options(func):
	global OPTIONS
	func = task(func)
	OPTIONS = func
	return func

def private(func):
	global TASKS
	func = task(func)
	if func.name in TASKS:
		del TASKS[func.name]
	return func

def method(func):
	func = task(func)
	func.method = True
	return func

def generic(func):
	func = task(func)
	method(func)
	private(func)
	return func

def attributes(*attrs):
	def wrapper(func):
		if 'default' in attrs: default(func)
		if 'setup' in attrs: setup(func)
		if 'teardown' in attrs: teardown(func)
		if 'options' in attrs: options(func)
		if 'private' in attrs: private(func)
		if 'method' in attrs: method(func)
		if 'generic' in attrs: generic(func)
		return func
	return wrapper


# Decorators | configuration
def generates(target):
	def wrapper(func):
		global GENERATES
		func = task(func)
		func.generates = target
		GENERATES[target] = func
		return func
	return wrapper

def requires(*requirements):
	def wrapper(func):
		func = task(func)
		func.requirements = requirements
		func.file_requirements = [req for req in requirements if type(req) is str]
		func.task_requirements = [req for req in requirements if type(req) is not str]
		return func
	return wrapper

def args(**opts):
	def wrapper(func):
		func = task(func)
		func.args = [key + ('=' if opts[key] is not None else '') for key in opts]
		func.defaults = opts
		return func
	return wrapper

def alias(*aliases):
	def wrapper(func):
		global TASKS
		func = task(func)
		func.aliases = aliases
		for alias in aliases:
			TASKS[alias] = func
		return func
	return wrapper

def suppress(*messages):
	def wrapper(func):
		func = task(func)
		func.suppress = messages
		return func
	return wrapper


# Helper functions
def require(*requirements):
	for req in requirements:
		if type(req) is str:
			# does not exist and unknown generator
			if not os.path.exists(req) and req not in GENERATES:
				abort(LOCALE['abort_bad_file'].format(req))

			# exists but unknown generator
			if req not in GENERATES:
				return

			# exists and known generator
			if req in GENERATES:
				req = GENERATES[req]

		if req.valid is None:
			req()

		if req.valid is False:
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
	if not paths:
		return 0

	for path in paths:
		if not os.path.exists(path):
			return time.time()

	return min([(time.time() - os.path.getmtime(path)) for path in paths])

def clean():
	global GENERATES
	shell('rm -f ' + ' '.join([key for key in GENERATES]))

def abort(message):
	raise _AbortException(message)

def clone(func):
	return _Generic(func)

def config(**kwargs):
	for key in kwargs:
		CONFIG[key] = kwargs[key]


# Default 'help' function
@default
@suppress('enter', 'leave')
def help():
	'''Print all available tasks and descriptions.'''
	for key, task in TASKS.items():
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
		if task.generates:
			print LOCALE['help_generates'].format(task.generates)
		if task.defaults:
			print LOCALE['help_args']
			for arg in task.defaults:
				print LOCALE['help_arg'].format(arg, task.defaults[arg])


# Do everything awesome
def main(args):
	if OPTIONS and (CONFIG['options'] or CONFIG['long_options']):
		opts, args = getopt.getopt(args, CONFIG['options'], CONFIG['long_options'])
		opts = _opts_to_dict(*opts)
		OPTIONS(**opts)

	if SETUP:
		SETUP()

	if not args and DEFAULT:
		DEFAULT()
	else:
		if CONFIG['cli']:
			temp = None
			if len(args) > 0:
				temp = _get_task(args[0])
				if temp:
					args = args[1:]

			if not temp and DEFAULT:
				temp = DEFAULT

			kwargs = temp.defaults
			if temp.args:
				temp_kwargs, args = getopt.getopt(args, '', temp.args)
				temp_kwargs = _opts_to_dict(*temp_kwargs)
				for key in temp_kwargs:
					kwargs[key] = temp_kwargs[key]

			try:
				temp(*args, **kwargs)
			except Exception, ex:
				temp.valid = False
				print LOCALE['abort'].format(temp, ex.message)

		else:
			for arg in args:
				temp = _get_task(arg)
				if temp is not None:
					temp()
				else:
					print LOCALE['help_unknown'].format(arg)

	if TEARDOWN:
		TEARDOWN()
