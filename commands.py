# TODO: Consider making this functionality a decorator instead
# of the __metaclass__ nightmare that it is.

# TODO: Add support for type conversion. Every argument is a string
# in the current code.

import os
import vim
import shlex
import inspect
from .util import AutoInstance

file_path = os.path.dirname(__file__)


def template(filename):
    """ Returns the data from the provided template filename. """

    handle = open(os.sep.join([
        file_path,
        'templates',
        filename + '.vim'
    ]), 'r')

    return handle.read()


vim_call_command = template('call_command')
vim_register_command = template('register_command')
vim_unregister_command = template('unregister_command')

def call_command(name, args):
    kwargs = dict()

    def kwargs_filter(value):
        try:
            position = value.index('=')
        except ValueError:
            return True

        key = value[:position]
        value = value[position+1:]

        kwargs[key] = value

        return False

    if name in global_command_map:
        args = filter(kwargs_filter, shlex.split(args))

        # TODO: Allow other command maps
        command = global_command_map[name]

        try:
            command(*args, **kwargs)
        except TypeError, e:
            vim.command('echoerr {0}'.format(e.message))


class CommandMap(dict):
    def register(self, name, command):
        """ Register (apply to Vim) a command. """

        inspection = inspect.getargspec(command.run)

        arg_count = len(inspection.args) - 1

        # Provide support for argument expansion
        if inspection.varargs is not None:
            if arg_count > 0:
                arg_count = '+'
            else:
                arg_count = '*'

        # TODO: Support custom completions via Python functions.
        if getattr(command, 'completion', False) is not False:
            completion = '-complete={0}'.format(command.completion)
        else:
            completion = ''

        if getattr(command, 'bang', False):
            bang = '-bang'
        else:
            bang = ''

        context = {
            'name': name,
            'arg_count': arg_count,
            'completion': completion,
            'bang': bang
        }

        command = vim_register_command.format(**context)

        # Register our command!
        vim.command(command)

    def deregister(self, name):
        """ Deregister any command managed by this map. """

        if name in self:
            vim.command(vim_unregister_command.format(name=name))

            return True

        return False

    def __setitem__(self, key, value):
        if key in self:
            del self[key]

        self.register(key, value)
        super(CommandMap, self).__setitem__(key, value)

    def __delitem__(self, key):
        self.deregister(key)
        super(CommandMap, self).__delitem__(key)

# A default global command map
global_command_map = CommandMap()


class Command(object):
    """ A command which can be used inside Vim. """

    command_map = global_command_map
    __metaclass__ = AutoInstance

    completion = False
    bang = False

    def __init__(self, command_map=None, register=True):
        name = getattr(self, 'name', False)

        if name is False:
            self.name = self.__class__.__name__

        if register is True:
            self.register()

    def register(self):
        """ Registers the current command name with the Vim command map. """

        self.command_map[self.name] = self

    def __call__(self, *args, **kwargs):
        self.run(*args, **kwargs)

    def run(self):
        raise NotImplementedError('Can not call base VimpyCommand.')

# Wraps our commands in Python calls.
vim.command(vim_call_command)