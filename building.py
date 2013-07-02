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
		return _highlight('[' + self.name + ']', CONFIG['color_tasks'])


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
