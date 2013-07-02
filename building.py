import sys

CONFIG = {
	'color': True,
	'color_invalid': 4,
	'color_success': 2,
	'color_fail': 1,
}

LOCALE = {
	'execute_single': 'execute\t{}',
	'execute_multi': 'execute\t{} - {}',
	'abort': 'abort  \t{} - {}',
	'abort_bad_require': 'abort  \t{} - {} require failed',
	'help_command': '{} - {}',
	'help_requires': '\t- requires {}',
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
	def __init__(self, func, requires):
		self.func = func
		self.name = func.__name__
		self.help = func.__doc__
		self.requires = requires

		self.valid = None

	def __call__(self, *args, **kwargs):
		if self.requires:
			print LOCALE['execute_multi'].format(self, self.requires)
		else:
			print LOCALE['execute_single'].format(self)
		for req in self.requires:
			if req.valid is None:
				req()

			if req.valid == False:
				self.valid = False
				print LOCALE['abort_bad_require'].format(self, req)
				return False

		try:
			self.func(*args, **kwargs)
		except AbortException, ex:
			self.valid = False
			print LOCALE['abort'].format(self, ex.message)
		else:
			self.valid = True

		return self.valid

	def __repr__(self):
		color = CONFIG['color_invalid']

		if self.valid:
			color = CONFIG['color_success']
		elif self.valid == False:
			color = CONFIG['color_fail']

		return _highlight('[' + self.name + ']', color)


def task(*requires):
	def wrapper(f):
		new_task = Task(f, requires)
		LIST.append(new_task)
		DICT[new_task.name] = new_task
		return new_task

	return wrapper

def shell(command):
	try:
		return subprocess.check_output(command)
	except subprocess.CalledProcessError, ex:
		return ex

def main(args):
	if len(args) == 0:
		for t in LIST:
			print LOCALE['help_command'].format(t, t.help)

			if t.requires:
				print LOCALE['help_requires'].format(t.requires)

	else:
		for arg in args:
			if arg in DICT:
				DICT[arg]()
			else:
				print LOCALE['help_unknown'].format(arg)
