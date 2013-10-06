# Bumpy

**Simplify repetitive project tasks with Python.**

Bumpy aims to provide a simple and effective way to collect and automate build, test, and deploy tasks. In order to leverage Python's powerful syntax while still maintaining a minimal and readable build file, Bumpy includes several helper functions to reduce the amount of code and clutter your build files need to include without sacrificing functionality. In addition, Bumpy requires only built-in Python libraries - that means no external dependencies!

Bumpy is derived from [pynt](https://github.com/rags/pynt), and by extension, [microbuild](https://github.com/CalumJEadie/microbuild).

## Usage

Bumpy is simple to use. Just open a `bum.py` file, define your tasks, and run `bump` in the same directory.

```python
import bumpy as b

@b.task
def build():
	'''Builds ALL THE CODE.'''
	print 'Building'
```

```bash
$ bump build
Building
```

### API

Bumpy provides a simple function decorator to register and track your tasks, as well as several helper functions to make your life easier when interfacing with shell commands and files.

#### Tasks

In order to convert your lovely functions into a Bumpy task, it's as simple as applying the `@task` decorator:

```python
import bumpy as b

@b.task
def build():
	'''Builds ALL THE CODE.'''
	print 'Building'
```

The function name will be used as the task name. The docstring will be saved and used for the built-in help. Any arguments or keyword arguments will be parsed and registered as CLI flags.

---

Prerequisite tasks / files can be specified with an optional `reqs` keyword argument to `@task`:

```python
@b.task(reqs=build)
def run():
	print 'Running'
```

`reqs` can be a single requirement or a tuple of requirements. A dependency will only be executed the first time it's required, although it may be explicitly executed multiple times via the command line:

```bash
$ bump run
Building
Running
$ bump build run
Building
Running
$ bump build build run
Building
Building
Running
```

`str` requirements will be interpreted as files / paths.

---

Generated files can be specified with an optional `gens` keyword argument:

```python
@b.task(gens='docs')
def docs():
	print 'Documenting'
```

Generated files will be saved and can be automatically deleted with Bumpy's `clean()` helper function. Generated files will also be used to look up file-based dependency chains.

---

Task aliases can be specified with an optional `alias` keyword argument:

```python
@b.task(alias='pkg', reqs=(build, docs))
def package():
	print 'Packaging'
```

`alias` can be a single alias or a tuple of aliases.

---

A task can be set as the 'default' task, ie the task that Bumpy will invoke if no arguments are provided, by providing `'default'` as an optional argument:

```python
@b.task('default'):
def build():
	print 'Building'
```

---

A task can be set as the 'setup' task, ie the task that Bumpy will invoke prior to any other tasks, by providing `'setup'` as an optional argument:

```python
@b.task('setup')
def setup():
	print 'Setting stuff up'
```

Setup tasks can also accept arguments. More on this later!

---

Similar to 'setup' tasks, 'teardown' tasks are invoked after every other task, just before exiting:

```python
@b.task('teardown')
def teardown():
	print 'Tearing stuff down'
```

---

A task can be removed from the lookup table by adding a `'private'` optional argument or by prefixing its name with an underscore:

```python
@b.task('setup', 'private'):
def setup():
	print 'Setting stuff up'

@b.ask('teardown')
def _teardown():
	print 'Tearing stuff down'
```

Private tasks can still be required and executed, but cannot be invoked from the command line and will not be included in the built-in help.

---

A task can grab a reference to itself by adding a `'method'` optional argument:

```python
@b.task('method', gens='output.txt')
def output(self):
	print 'Generating {}'.format(self.gens)
```

---

Function arguments / keyword arguments will be converted into command-line flags and options.

```python
@b.task
def docs(modules, format='markdown'):
	print 'Documenting {!r} as {}'.format(modules, format)
```

Which can then be invoked like this:

```bash
$ bump docs all
Documenting 'all' as markdown
$ bump docs --format rst bumpy
Documenting 'bumpy' as rst
$ bump docs
abort [bumpy.main]: Too few arguments: [docs] expects 1
$ bump docs --format rst
abort [bumpy.main]: Too few arguments: [docs] expects 1
```

Keyword arguments *must* come before standard arguments, contrary to Python's standards.

#### Helpers

To abort task execution and display an error message, use `abort(message, *formatargs)`:

```python
@b.task
def abort():
	b.abort('This task is bad.')
```

If `*formatargs` are provided, `message` will be used as a string format for `str.format`.

---

To invoke shell commands, use `shell(command, *formatargs)`:

```python
@b.task
def echo():
	'''This is an example task that uses a shell command.'''
	print b.shell('echo hi')
```

If `*formatargs` are provided, `command` will be used as a string format for `str.format`.

---

To require tasks during execution rather than pre-execution, use `require(*reqs)`:

```python
@b.task
def test(fail=False):
	if fail:
		require(abort)

	print 'Flexibly surviving'
```

To check whether requirements are valid without actually executing them, use `valid(*reqs)`.

---

To get the youngest age of a collection of files, use: `age(*paths)`:

```python
@b.task(reqs='input.txt', gens='output.txt')
def output():
	if b.age('input.txt') < b.age('output.txt'):
		b.shell('cp input.txt output.txt')
```

---

If you're meticulous about recording your generated files with `gens`, Bumpy will be able to automatically remove all generated files with `clean()`:

```python
@b.task
def clean():
	b.clean()
```

### Namespaces

Tasks can be grouped into namespaces by using an optional `namespace` keyword argument:

```python
@b.task(namespace='db')
def init():
	print 'Initialize database'
```

```bash
$ bump db.init
Initialize database
```

When bumpy fires up, it searches for modules in a `bump/` directory and imports them, assigning each an appropriate namespace. If you want tasks to be in the global namespace, add them to `bump/__bumpy_main__.py`, `bum.py`, or `build.py`, only the first of which will be imported. If tasks in one namespace depend on tasks in another, you can use Python's `import` to import their containing module.

### CLI

`bump --version` will print the currently running version of Bumpy.

`bump -h` or `bump --help` will print a built-in help message.

`bump -f <file>` will tell `bump` to load a different file instead of `bum.py` or `build.py`.

`bump -v TASK` will enable verbose mode, printing an enter/exit message each time a task begins and ends execution.

`bump TASK1 TASK2 TASK3` will execute tasks in sequence
