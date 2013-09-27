from bumpy import *

@task
def example():
	'''This is an example task.'''
	print 'Running the example!'

@requires(example)
def dependency():
	'''This is an example task with a dependency.'''
	print 'I bet example() was executed before me.'

@requires('name.txt', dependency)
def hello():
	'''This is an example task with a file dependency.'''
	print 'Hello! My name is ' + open('name.txt').read().strip()
	print 'Darn. How do those two always get executed before me?!'

@generates('name.txt')
def whoami():
	'''This is an example task that generates a file.'''
	open('name.txt', 'w').write('Bumpy Bill\n')

@alias('list', 'show')
def view():
	'''This is an example task with some aliases.'''
	print 'I think I can be invoked with view, list, OR show!'

@default
def usage():
	'''This is an example default task.'''
	print 'Please specify a task to execute.'

@setup
def begin():
	'''This is an example setup task.'''
	print 'Beginning execution.'

@teardown
def end():
	'''This is an example teardown task.'''
	print 'Ending execution.'

@private
def secret():
	'''This is an example private task.'''
	print 'Try invoking this with bump!'

@method
def what(self):
	'''This is an example method.'''
	print 'Hello! My name is ' + self.name

@task
def fail():
	'''This is an example task that is destined to fail.'''
	abort('This task is bad.')

@task
def echo():
	'''This is an example task that uses a shell command.'''
	print shell('echo hi')

@task
def explode():
	'''This is a very bizarre example.'''
	require(fail)

@task
def newer():
	'''This is an example task that uses the age helper.'''
	if age('bum.py') < age('name.txt'):
		print 'Your bumpfile is so young!'
	else:
		print 'Your name.txt is so young!'
@task
def cleanup():
	'''This is an example task that cleans all generated files.'''
	clean()
