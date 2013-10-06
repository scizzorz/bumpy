import copy, getopt, inspect, os, subprocess, sys, time

__version__ = '0.4.0'

# Configuration settings
CONFIG = {
	'color': True,
	'color_invalid': 4,
	'color_success': 2,
	'color_fail': 1,
	'abbrev': True,
	'suppress': (),
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
	'help_arg': '\t\t<{}>',
	'help_key': '\t\t--{} = {}',
	'help_command': '{}{}: {}',
	'help_gens': '\tgenerates: {!r}',
	'help_reqs': '\trequires: {}',
	'help_unknown': 'unknown task: {}',
	'leave': 'leave {}',
	'shell': '$ {}',
	'error_no_task': 'Unable to find task "{}"',
	'error_wrong_args': 'Incorrect amount of arguments: {} expects {}',
	}


# State variables
TASKS = {}
GENERATES = {}
DEFAULT = None
SETUP = None
TEARDOWN = None


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

def _taskify(func):
	global TASKS
	if not isinstance(func, _Task):
		func = _Task(func)

		spec = inspect.getargspec(func.func)
		if spec.args and spec.defaults:
			num_args = len(spec.args)
			num_kwargs = len(spec.defaults)
			isflag = lambda x, y: '' if x.defaults[y] is False else '='

			func.args = spec.args[:(num_args - num_kwargs)]
			func.defaults = {spec.args[i - num_kwargs]: spec.defaults[i] for i in range(num_kwargs)}
			func.kwargs = [key + isflag(func, key) for key in func.defaults]

		if not func.name.startswith('_'):
			TASKS[func.fullname] = func

	return func

def _tuplify(args):
	if not isinstance(args, tuple):
		args = (args,)
	return args

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
	kwargs = []
	defaults = {}

	reqs = ()
	file_reqs = ()
	task_reqs = ()
	gens = None

	valid = None
	method = False

	def __init__(self, func):
		'''Initialize the Task with a name and help string.'''
		self.func = func
		self.name = func.__name__
		self.help = func.__doc__
		self.mod = inspect.getmodule(func).__name__
		if self.mod == '__bumpy_main__':
			self.fullname = self.name
		else:
			self.fullname = self.mod + '.' + self.name

	def __call__(self, *args, **kwargs):
		'''Invoke the wrapped function after meeting all requirements.'''
		try:
			require(*self.reqs)

			if self.reqs and self.gens:
				self.__print('enter_genreq', self, self.gens, self.reqstr())
			elif self.reqs:
				self.__print('enter_req', self, self.reqstr())
			elif self.gens:
				self.__print('enter_gen', self, self.gens)
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

		return _highlight('[' + self.fullname + ']', color)

	def __print(self, id, *args):
		'''Print a message if it's not suppressed.'''
		if 'all' in self.suppress or id in self.suppress: return
		if 'all' in CONFIG['suppress'] or id in CONFIG['suppress']: return

		print LOCALE[id].format(*args)

	def match(self, name):
		'''Compare an argument string to the task name.'''
		if self.fullname.startswith(name):
			return True

		for alias in self.aliases:
			if alias.startswith(name):
				return True

	def reqstr(self):
		'''Concatenate the requirements tuple into a string.'''
		return ', '.join(x.__repr__() for x in self.reqs)

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
	def suppress(self, *messages):
		suppress(*messages)(self.task)
		return self
	def requires(self, *reqs):
		requires(*reqs)(self.task)
		return self
	def args(self, **opts):
		args(**opts)(self.task)
		return self
	def generates(self, target):
		generates(target)(self.task)
		return self


# The decorator
def task(*args, **kwargs):
	'''Convert a function into a task.'''

	# support @task
	if args and hasattr(args[0], '__call__'):
		return _taskify(args[0])

	# as well as @task(), @task('default'), etc.
	else:
		def wrapper(func):
			global TASKS, GENERATES, DEFAULT, SETUP, TEARDOWN
			func = _taskify(func)

			if 'default' in args:
				DEFAULT = func

			if 'setup' in args:
				SETUP = func

			if 'teardown' in args:
				TEARDOWN = func

			if ('private' in args or 'generic' in args) and func.fullname in TASKS:
				del TASKS[func.fullname]

			if ('method' in args or 'generic' in args):
				func.method = True

			if 'requires' in kwargs:
				func.reqs = _tuplify(kwargs['requires'])
				func.file_reqs = [req for req in func.reqs if type(req) is str]
				func.task_reqs = [req for req in func.reqs if type(req) is not str]

			if 'gens' in kwargs:
				func.gens = kwargs['gens']

			if 'alias' in kwargs:
				func.aliases = _tuplify(kwargs['alias'])
				TASKS.update({alias: func for alias in func.aliases})

			if 'suppress' in kwargs:
				func.suppress = _tuplify(kwargs['suppress'])

			return func

		return wrapper


# Helper functions
def require(*reqs):
	'''Require tasks or files at runtime.
	Similar to @requires(...), but it can be invoked at runtime rather than at
	function creation.'''
	for req in reqs:
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

def shell(command, *args):
	'''Pass a command into the shell.'''
	if args:
		command = command.format(args)

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

def abort(message, *args):
	'''Raise an AbortException, halting task execution and exiting.'''
	if args:
		raise _AbortException(message.format(*args))

	raise _AbortException(message)

def clone(task):
	'''Return a Generic linked to a task.'''
	return _Generic(task)

def config(**kwargs):
	'''Set bumpy configuration values.'''
	for key in kwargs:
		CONFIG[key] = kwargs[key]


# Default 'help' function
@task('default', suppress=('enter', 'leave'))
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
		if task.reqs:
			print LOCALE['help_reqs'].format(task.reqstr())
		if task.gens:
			print LOCALE['help_gens'].format(task.gens)
		if task.defaults:
			print LOCALE['help_args']
			for arg in task.args:
				print LOCALE['help_arg'].format(arg)
			for arg in task.defaults:
				print LOCALE['help_key'].format(arg, task.defaults[arg])


# Do everything awesome
def _invoke(task, args):
	kwargs = task.defaults.copy()
	if task.kwargs:
		temp_kwargs, args = getopt.getopt(args, '', task.kwargs)
		temp_kwargs = _opts_to_dict(*temp_kwargs)
		kwargs.update(temp_kwargs)

	if task.args:
		for e in task.args:
			if not len(args):
				abort(LOCALE['error_wrong_args'], task, len(task.args))
			kwargs.update({e: args[0]})
			args = args[1:]

	task(**kwargs)
	return args

@task('private')
def main(args):
	if SETUP:
		args = _invoke(SETUP, args)

	if not args and DEFAULT:
		DEFAULT()
	else:
		while args:
			task = _get_task(args[0])
			if task is None:
				abort(LOCALE['error_no_task'], args[0])

			args = _invoke(task, args[1:])

	if TEARDOWN:
		TEARDOWN()
