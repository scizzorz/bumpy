# Bumpy

**Simplify repetitive project tasks with Python.**

Bumpy aims to provide a simple and effective way to collect and automate build, test, and deploy tasks. In order to leverage Python's powerful syntax while still maintaining a minimal and readable build file, Bumpy includes several helper functions to reduce the amount of code and clutter your build files need to include without sacrificing functionality.

Bumpy is derived from [pynt](https://github.com/rags/pynt), and by extension, [microbuild](https://github.com/CalumJEadie/microbuild).

## Usage

Bumpy is simple to use. Just open a `bum.py` file, define your tasks, and run `bump` in the same directory.

```python
from bumpy import task

@task
def compile():
	'''Compiles ALL THE CODE.'''
	print 'Compiling...'
```

```bash
$ bump compile
execute [compile]
Compiling...
finish [compile]
```

### API

Bumpy uses Python decorators to record and manipulate your tasks.

*(all of the given examples can be found in the included `bum.py`)*

#### Decorators

##### `@task`

Registers a function as a Bumpy task. The function name is used to invoke tasks through `bump`.

All other decorators will automatically register a function as a task, so you only need to use `@task` when you have no other decorators.

```python
@task
def example():
	'''This is an example task.'''
	print 'Running the example!'
```

---

##### `@requires(*reqs)`

Indicates that a task depends on other tasks to be executed beforehand. Bumpy will resolve any dependencies automatically and will try to minimize repeating a task unless explicitly requested. You can also require that a file exists by providing its path as a string.

```python
@requires(example)
def dependency():
	'''This is an example task with a dependency.'''
	print 'I bet example() was executed before me.'

@requires('name.txt', dependency)
def hello():
	'''This is an example task with a file dependency.'''
	print 'Hello! My name is ' + open('name.txt').read().strip()
	print 'Darn. How do those two always get executed before me?!'
```

---

##### `@generates(target)`

Indicates that a task will produce a specific file. Bumpy will use this to resolve file dependencies; if task A requires file B, Bumpy will look up which task will generate file B and then invoke it. Bumpy will also record all files that are generated and can automatically clean them up.

```python
@generates('name.txt')
def whoami():
	'''This is an example task that generates a file.'''
	open('name.txt', 'w').write('Bumpy Bill\n')
```

---

##### `@alias(*alts)`

Registers a task with multiple names that can be used interchangeably with `bump`.

```python
@alias('list', 'show')
def view():
	'''This is an example task with some aliases.'''
	print 'I think I can be invoked with view, list, OR show!'
```

---

##### `@default`

Registers a task as the *default* task, meaning it will be executed if `bump` is invoked with no arguments. If this decorator is not used, a builtin `help` task will be executed instead.

```python
@default
def usage():
	'''This is an example default task.'''
	print 'Please specify a task to execute.'
```

---

##### `@setup`

Registers a task as the *setup* task, meaning it will be executed immediately, *before* all other Bumpy processing occurs.

```python
@setup
def begin():
	'''This is an example setup task.'''
	print 'Beginning execution.'
```

---

##### `@teardown`

Registers a task as the *teardown* task, meaning it will be executed *after* all other Bumpy processing has occurred.

```python
@teardown
def end():
	'''This is an example teardown task.'''
	print 'Ending execution.'
```

---

##### `@private`

Registers a task as a *private* task, meaning it will be omitted from the builtin `help` output and can only be invoked by other tasks, rather than through `bump`.

```python
@private
def secret():
	'''This is an example private task.'''
	print 'Try invoking this with bump!'
```

---

##### `@method`

Registers a task as a *method*, meaning it will have a reference to itself passed in as the first parameter, much like traditional class-based methods.

```python
@method
def what(self):
	'''This is an example method.'''
	print 'Hello! My name is ' + self.name
```

---

#### Helpers

##### `abort(message)`

Raises an exception and immediately aborts Bumpy execution, printing the error message as output.

```python
@task
def fail():
	'''This is an example task that is destined to fail.'''
	abort('This task is bad.')
```

---

##### `shell(command)`

Pass `command` to the shell and return the output.

```python
@task
def echo():
	'''This is an example task that uses a shell command.'''
	print shell('echo hi')
```

---

##### `require(*reqs)`

The internal implementation of the `@requires(*reqs)` decorator, with the advantage that it can be called during task runtime rather than during task loading.

```python
@task
def explode():
	'''This is a very bizarre example.'''
	require(fail)
```

---

##### `age(*paths)`

Return the *youngest* age of any given `path`. If any given does not exist, the current time since the Unix epoch is returned. Subsequently, a missing path will always be interpreted as older than an existing path.

```python
@task
def newer():
	'''This is an example task that uses the age helper.'''
	if age('bum.py') < age('name.txt'):
		print 'Your bumpfile is so young!'
	else:
		print 'Your name.txt is so young!'
```

---

##### `valid(*reqs)`

Returns whether all tasks have already been executed and all files exist.

---

##### `clean()`

Automatically removes any files that have been registered through a `@generates(target)` decorator.

```python
@task
def cleanup():
	'''This is an example task that cleans all generated files.'''
	clean()
```

#### Not documented yet:

Feel free to investigate the source for these. I'll write them up shortly:

* `@args(*args)`
* `@suppress(*types)`
* `@options`
* `config(*settings)`
* `clone(task)`

### CLI

Included in the package is a tool called `bump`. By default, `bump` will search the current working directory for a file named `bum.py` or `build.py`, load it, and then pass the CLI arguments on to Bumpy. Normal mode Bumpy allows you to specify multiple tasks at a time and will execute them each in sequence:

```bash
$ bump clean compile run
```

Additionally, Bumpy allows you to abbreviate task names as long as they remain uniquely identifiable:

```bash
$ bump cl co r
```

`bump --version` will print the currently running version of Bumpy.

`bump -f <file>` will tell `bump` to load a different file instead of `bum.py` or `build.py`.
