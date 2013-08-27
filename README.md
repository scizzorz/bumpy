# bumpy

A library for writing and executing BUildy / Makey tasks, written in PYthon. Get it? Brilliance.

Bumpy aims to provide a simple and effective way to collect and automate build, test, and deploy tasks. In order to leverage Python's powerful syntax while still maintaining a minimal and readable build file, bumpy includes several helper functions to reduce the amount of code and clutter your build files need to include without sacrificing functionality.

Bumpy is derived from [pynt](https://github.com/rags/pynt), and by extension, [microbuild](https://github.com/CalumJEadie/microbuild).

## Usage

Bumpy is simple to use. Just import it, define your tasks, and run `bumpy` in the same directory.

```python
import bumpy

@bumpy.task
def compile():
	'''Compiles all the code.'''
	print 'Running...'
```

And that's it. You can run the code like this:

```bash
$ bumpy compile
execute [compile]
Compiling...
finish [compile]
```

### Moar

Bumpy uses Python decorators to record and manipulate your tasks. Bumpy also includes several helper functions to minimize the code you need to write while still providing maximal functionality.

#### Decorators

* `@task` (also `@command` and `@cmd`) registers the decorated function as a task. The function name will be used at the command line to invoke this task, and the function's docstring will be displayed when the `help` command is called. All other decorators will invoke `@task` if necessary, so if you are using the advanced decorators you don't need to use this.
* `@default` marks the decorated function as the "default" task. The "default" task will be run when no other arguments are given to bumpy.
* `@setup` identifies a task as the "setup" task. The "setup" task will be run immediately, before any other bumpy processing has started.
* `@teardown` identifies a task as the "teardown" task. The "teardown" task will be run just prior to exiting, after all other bumpy processing has completed.
* `@private` hides the task from the `help` task. Can be used to hide the setup and teardown tasks or to create tasks that can act as requirements but can't be called manually.
* `@requires(...)` specifies that this task requires certain things before it can be run. The requirements can either be a filename (as a string) or another bumpy task: `@requires("file.txt")` or `@requires(compile)`. Any missing files will cause bumpy to abort this task. Any required tasks will be executed before executing this task, and failures will prevent this task from being executed. If a task is required multiple times it will only be executed once.
* `@alias(...)` allows the task to be called from names other than its declared function name
* `@generates(...)` tracks a list of files created by this task that can be automatically deleted by calling `clean()`
* `@suppress(...)` prevents bumpy from displaying its own output when executing this task. Acceptable messages to suppress:
  * `all` - everything will be suppressed
  * `execute_single` - displayed when a task with no requirements is executed
  * `execute_multi` - displayed when a task with requirements is executed; includes requirements list
  * `finish` - displayed when a task finishes
  * `abort` - displayed when a task aborts
  * `abort_bad_task` - displayed when a task aborts because a required task failed
  * `abort_bad_file` - displayed when a task aborts because a required file was missing

#### Helpers

* `abort(message)` will raise an exception and abort the current task, printing an error message as output and preventing any dependent tasks from executing
* `shell(command)` will pass the command into the user's shell, returning the command's output or any raised exceptions
* `require(*requirements)` is similar to the `@requires(...)` decorator, although it can be called in the middle of a task rather than at the beginning. It can be used to verify that a certain file was produced or to require a different task depending on a condition.
* `age(*paths)` returns the *minimum* age of any file in `*paths`. If none of the given files exist, the current Unix timestamp is returned. This means that missing files are always interpreted as older than existing files.
* `valid(*things)` checks whether all of the `things` are "valid", ie if they were required, they would pass
* `clean()` erases any files that have been added by a `@generates(...)` decorator

## To be continued
