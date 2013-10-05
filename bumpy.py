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
	'''Look up a task by name.'''
	global TASKS

	if name in TASKS:
		return TASKS[name]
	elif CONFIG['abbrev']:
		matches = [task for key, task in TASKS.items() if task.match(name)]
		if matches:
			return matches[0]

def _opts_to_dict(*opts):
	'''Convert a tuple of options returned from getopt into a dictionary.'''
	ret = {}
	for key, val in opts:
		if key[:2] == '--': key = key[2:]
		elif key[:1] == '-': key = key[1:]
		if val == '': val = True
		ret[key] = val
	return ret

def _highlight(string, color):
	'''Return a string highlighted for a terminal.'''
	if CONFIG['color']:
		if color < 8:
			return '\033[{color}m{string}\033[0m'.format(string = string, color = color+30)
		else:
			return '\033[{color}m{string}\033[0m'.format(string = string, color = color+82)
	else:
		return string


# Private classes
class _AbortException(Exception):
	'''Thrown when a task needs to abort.'''
	def __init__(self, message):
		Exception.__init__(self, message)

class _Task:
	'''A wrapper around a function that contains bumpy-specific information.'''
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
		'''Initialize the Task with a name and help string.'''
		self.func = func
		self.name = func.__name__
		self.help = func.__doc__

	def __call__(self, *args, **kwargs):
		'''Invoke the wrapped function after meeting all requirements.'''
		try:
			require(*self.requirements)

			if self.requirements and self.generates:
				self.__print('enter_genreq', self, self.generates, self.reqstr())
			elif self.requirements:
				self.__print('enter_req', self, self.reqstr())
			elif self.generates:
				self.__print('enter_gen', self, self.generates)
			else:
				self.__print('enter', self)

			if self.method:
				self.func(self, *args, **kwargs)
			else:
				self.func(*args, **kwargs)
		except Exception, ex:
			self.valid = False
			self.__print('abort', self, ex.message)
		else:
			self.valid = True
			self.__print('leave', self)

		return self.valid

	def __repr__(self):
		'''Highlight the wrapped function name based on its state.'''
		color = CONFIG['color_invalid']

		if self.valid:
			color = CONFIG['color_success']
		elif self.valid == False:
			color = CONFIG['color_fail']

		return _highlight('[' + self.name + ']', color)

	def __print(self, id, *args):
		'''Print a message if it's not suppressed.'''
		if 'all' in self.suppress or id in self.suppress: return
		if 'all' in CONFIG['suppress'] or id in CONFIG['suppress']: return

		print LOCALE[id].format(*args)

	def match(self, name):
		'''Compare an argument string to the task name.'''
		if self.name.startswith(name):
			return True

		for alias in self.aliases:
			if alias.startswith(name):
				return True

	def reqstr(self):
		'''Concatenate the requirements tuple into a string.'''
		return ', '.join(x.__repr__() for x in self.requirements)

	def aliasstr(self):
		'''Concatenate the aliases tuple into a string.'''
		return ', '.join(x.__repr__() for x in self.aliases)

class _Generic:
	'''An anonymous wrapper around another task.
	All methods return a reference to this object so that they can be linked.'''
	def __init__(self, func):
		'''Initialize the task with a deep copy and mark @private and @method.'''
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


def _taskify(func):
	global TASKS
	if not isinstance(func, _Task):
		func = _Task(func)
		TASKS[func.name] = func
	return func

def _tuplify(args):
	if not isinstance(args, tuple):
		args = (args,)
	return args

# Decorators | attributes
def task(*args, **kwargs):
	'''Convert a function into a task.'''

	# support @task
	if args and hasattr(args[0], '__call__'):
		return _taskify(args[0])

	# as well as @task(), @task('default'), etc.
	else:
		def wrapper(func):
			func = attributes(*args)(func)
			if 'requires' in kwargs:
				requires(*_tuplify(kwargs['requires']))(func)
			if 'generates' in kwargs:
				generates(kwargs['generates'])(func)
			if 'alias' in kwargs:
				alias(*_tuplify(kwargs['alias']))(func)
			if 'suppress' in kwargs:
				suppress(*_tuplify(kwargs['suppress']))(func)

			return func

		return wrapper


def default(func):
	'''Execute this task when bumpy is invoked with no arguments.'''
	global DEFAULT
	func = _taskify(func)
	DEFAULT = func
	return func

def setup(func):
	'''Execute this task before all other tasks.'''
	global SETUP
	func = _taskify(func)
	SETUP = func
	return func

def teardown(func):
	'''Execute this task after all other tasks.'''
	global TEARDOWN
	func = _taskify(func)
	TEARDOWN = func
	return func

def options(func):
	'''Execute this task after processing option flags.
	Must accept **kwargs as a parameter.'''
	global OPTIONS
	func = _taskify(func)
	OPTIONS = func
	return func

def private(func):
	'''Remove this task from the task index.
	This will prevent it from being iterated over, and subsequently will hide it
	from the help task.'''
	global TASKS
	func = _taskify(func)
	if func.name in TASKS:
		del TASKS[func.name]
	return func

def method(func):
	'''Explicitly pass the task into itself as a parameter.'''
	func = _taskify(func)
	func.method = True
	return func

def generic(func):
	'''Alias combination for @method and @private.'''
	func = _taskify(func)
	method(func)
	private(func)
	return func

def attributes(*attrs):
	'''Apply multiple attributes to this task.
	Attributes include default, setup, teardown, options, private, method,
	and generic.'''
	def wrapper(func):
		func = _taskify(func)
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
	'''Indicates that this task will produce an output file.
	This is used for file-based dependency chains as well as recording which
	files can be erased by clean().'''
	def wrapper(func):
		global GENERATES
		func = _taskify(func)
		func.generates = target
		GENERATES[target] = func
		return func
	return wrapper

def requires(*requirements):
	'''Indicates that this task depends on something.
	Requirements can either be an external filename or another task. Task
	requirements will be executed before execution of this task. File
	requirements will be generated if they can be looked up in the
	generator table; otherwise, missing files will cause the task to fail.'''
	def wrapper(func):
		func = _taskify(func)
		func.requirements = requirements
		func.file_requirements = [req for req in requirements if type(req) is str]
		func.task_requirements = [req for req in requirements if type(req) is not str]
		return func
	return wrapper

def args(**opts):
	'''Indicates that this task should accept command line options.'''
	def wrapper(func):
		func = _taskify(func)
		func.args = [key + ('=' if opts[key] is not None else '') for key in opts]
		func.defaults = opts
		return func
	return wrapper

def alias(*aliases):
	'''Allow this task to be looked up under other names.'''
	def wrapper(func):
		global TASKS
		func = _taskify(func)
		func.aliases = aliases
		for alias in aliases:
			TASKS[alias] = func
		return func
	return wrapper

def suppress(*messages):
	'''Indicate what types of messages this task should not print.'''
	def wrapper(func):
		func = _taskify(func)
		func.suppress = messages
		return func
	return wrapper


# Helper functions
def require(*requirements):
	'''Require tasks or files at runtime.
	Similar to @requires(...), but it can be invoked at runtime rather than at
	function creation.'''
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
	'''Return True if all tasks or files are valid.
	Valid tasks have been completed already. Valid files exist on the disk.'''
	for thing in things:
		if type(thing) is str and not os.path.exists(thing):
			return False
		if req.valid is None:
			return False
	return True

def shell(command):
	'''Pass a command into the shell.'''
	global CONFIG
	if 'shell' not in CONFIG['suppress']:
		print LOCALE['shell'].format(command)

	try:
		return subprocess.check_output(command, shell=True)
	except subprocess.CalledProcessError, ex:
		return ex

def age(*paths):
	'''Return the minimum age of a set of files.
	Returns 0 if no paths are given.
	Returns time.time() if a path does not exist.'''
	if not paths:
		return 0

	for path in paths:
		if not os.path.exists(path):
			return time.time()

	return min([(time.time() - os.path.getmtime(path)) for path in paths])

def clean():
	'''Removes all files added to the generator table via @generates.'''
	global GENERATES
	shell('rm -f ' + ' '.join([key for key in GENERATES]))

def abort(message):
	'''Raise an AbortException, halting task execution and exiting.'''
	raise _AbortException(message)

def clone(task):
	'''Return a Generic linked to a task.'''
	return _Generic(task)

def config(**kwargs):
	'''Set bumpy configuration values.'''
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
@private
@method
def main(self, args):
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

			temp = temp if temp else DEFAULT
			if temp is None:
				abort('Unable to find task "{}"'.format(arg))

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
				self.__print('abort', temp, ex.message)

		else:
			for arg in args:
				temp = _get_task(arg)
				if temp is None:
					abort('Unable to find task "{}"'.format(arg))

				temp()

	if TEARDOWN:
		TEARDOWN()
