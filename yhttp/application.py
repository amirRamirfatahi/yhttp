import inspect
import re
import types

import pymlconf

from . import statuses, static
from .request import Request
from .response import Response
from .lazyattribute import lazyattribute
from .cli import Main


class Application:
    """Web Application representation, instance of this class can be used as
    WSGI application.

    """
    builtinsettings = '''
    debug: true
    '''

    #: Instance of :class:`pymlconf.Root` as the global configuration instance.
    settings = None

    #: A list of :class:`easycli.Argument` or :class:`easycli.SubCommand`.
    cliarguments = None

    def __init__(self):
        self.cliarguments = []
        self.routes = {}
        self.events = {}
        self.settings = pymlconf.Root(self.builtinsettings)

    def _findhandler(self, request):
        patterns = self.routes.get(request.verb)
        if not patterns:
            raise statuses.methodnotallowed()

        for pattern, func, info in patterns:
            match = pattern.match(request.path)
            if not match:
                continue

            arguments = [a for a in match.groups() if a is not None]
            querystrings = {
                k: v for k, v in request.query.items()
                if k in info['kwonly']
            }

            return func, arguments, querystrings

        raise statuses.notfound()

    def __call__(self, environ, startresponse):
        """The actual WSGI Application.

        So, will be called on every request.

        .. code-block::

           from yhttp import Application


           app = Application()
           result = app(environ, start_response)

        Checkout the `PEP 333 <https://www.python.org/dev/peps/pep-0333/>`_
        for more info.

        """
        response = Response(self, startresponse)
        request = Request(self, environ, response)

        try:
            handler, arguments, querystrings = self._findhandler(request)
            body = handler(request, *arguments, **querystrings)
            if isinstance(body, types.GeneratorType):
                response._firstchunk = next(body)

            response.body = body

        except statuses.HTTPStatus as ex:
            ex.setupresponse(response, stacktrace=self.settings.debug)

        # Setting cookies in response headers, if any
        cookie = request.cookies.output()
        if cookie:
            for line in cookie.split('\r\n'):
                response.headers.add(line)

        return response.start()

    def route(self, pattern='/', verb=None):
        """Decorator factory to register a handler for given regex pattern.
        if ``verb`` is ``None`` then the function name will used instead.

        .. code-block::

           @app.route(r'/.*')
           def get(req):
               ...

        You can bypass this behavior by passing ``verb`` keyword argument:

        .. code-block::

           @app.route('/', verb='get')
           def somethingelse(req):
               ...

        Regular expression groups will be capture and dispatched as the
        positional arguments of the handler after ``req``:

        .. code-block::

           @app.route(r'/(\d+)/(\w*)')
           def get(req, id, name):
               ...

        This method returns a decorator for handler fucntions. So, you can use
        it like:

        .. code-block::

           books = app.route(r'/books/(.*)')

           @books
           def get(req, id):
               ...

           @books
           def post(req, id):
               ...

        .. seealso::

           :ref:`cookbook-routing`

        :param pattern: Regular expression to match the requests.
        """

        def decorator(f):
            routes = self.routes.setdefault(verb or f.__name__, [])
            info = dict(
                kwonly={
                    k for k, v in inspect.signature(f).parameters.items()
                    if v.kind == inspect.Parameter.KEYWORD_ONLY
                }
            )
            routes.append((re.compile(f'^{pattern}$'), f, info))

        return decorator

    def when(self, func):
        """A Decorator to registers the ``func`` into
        :attr:`.Application.events` by its name.

        Currently these hooks are suuported:

        * ready
        * shutdown
        * endresponse

        The hook name will be choosed by the func.__name__, so if you need to
        aware when ``app.ready`` is called write something like this:

        .. code-block::

           @app.when
           def ready(app):
               ...

           @app.when
           def shutdown(app):
               ...

           @app.when
           def endresponse(response):
               ...

        """

        callbacks = self.events.setdefault(func.__name__, [])
        if func not in callbacks:
            callbacks.append(func)

    def hook(self, name, *a, **kw):
        """The only way to fire registered hooks with :meth:`.Application.when`
        by the name

        .. code-block::

           app.hook('endresponse')

        Extra parameters: ``*a, **kw`` will be passed to event handlers.

        Normally, users no need to call this method.
        """

        callbacks = self.events.get(name)
        if not callbacks:
            return

        for c in callbacks:
            c(*a, **kw)

    def staticfile(self, pattern, filename):
        """Register a filename with a regular expression pattern to be served.

        .. code-block::

            app.staticfile('/a.txt', 'physical/path/to/a.txt')

        .. seealso::

           :ref:`cookbook-static`

        """
        return self.route(pattern)(static.file(filename))

    def staticdirectory(self, pattern, directory):
        """Register a directory with a regular expression pattern, So the
        files inside the directory are accessible by their names:

        .. code-block::

            app.staticdirectory('/foo/', 'physical/path/to/foo')

        You you can do:

        .. code-block:: bash

           curl localhost:8080/foo/a.txt

        .. seealso::

           :ref:`cookbook-static`

        """

        return self.route(f'{pattern}(.*)')(static.directory(directory))

    def climain(self, argv=None):
        """Provide a callable to call as the CLI entry point

        .. code-block::

           import sys


           if __name__ == '__main__':
               sys.exit(app.climain(sys.argv))

        You can use this method as the setuptools entry point for
        `Automatic Script Creation <https://setuptools.readthedocs.io/en/latest/setuptools.html#automatic-script-creation>`_

        ``setup.py``

        .. code-block::

           from setuptools import setup


           setup(
               name='foo',
               ...
               entry_points={
                   'console_scripts': [
                       'foo = foo:app.climain'
                   ]
               }
           )

        .. seealso::

           :ref:`quickstart-commandlineinterface`

        """
        return Main(self).main(argv)

    def ready(self):
        """Calls the ``ready`` :meth:`hook`

        You need to call this method before using the instance as the WSGI
        application.

        Typical usage:

        .. code-block::

           from yhttp import Application, text


           app = Application()

           @app.route()
           @text
           def get(req):
               return 'Hello World!'

           if __name__ != '__main__':
               app.ready()
        """

        self.hook('ready', self)

    def shutdown(self):
        """Calls the ``shutdown`` :meth:`hook`
        """
        self.hook('shutdown', self)

