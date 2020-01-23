========
Cookbook
========


Query String
------------

``yhttp`` will dispatch query string to the python's ``keywordonly`` argument
if defined in handler, see ``foo`` argument in the example below.

of-course, all query string will available as a dictionary via
:attr:`req.query <yhttp.Request.query>`.

.. testsetup:: cookbook/qs

   from yhttp import Application, text
   app = Application()

.. testcode:: cookbook/qs


   @app.route()
   @text
   def get(req, *, foo=None):
       return f'{foo} {req.query.get("bar")}'
    
   app.ready()

.. `*  due the vim editor bug


A painless way to test our code is `bddrest
<https://github.com/pylover/bddrest>`_.

.. testcode:: cookbook/qs

   from bddrest import Given, response, when, given

   with Given(app, '/?foo=foo&bar=bar'):
       assert response.text == 'foo bar'

       when(query=given - 'foo')
       assert response.text == 'None bar'


HTTP Form
---------

Use :attr:`req.form <yhttp.Request.form>` as a dictionary for access the submitted fields.


.. testsetup:: cookbook/form

   from yhttp import Application, text
   app = Application()

.. testcode:: cookbook/form

   @app.route()
   @text
   def post(req):
       return f'{req.form.get("foo")}'
    
   app.ready()
   

.. testcode:: cookbook/form

   from bddrest import Given, response, when, given

   with Given(app, verb='POST', form={'foo': 'bar'}):
       assert response.text == 'bar'

       when(form=given - 'foo')
       assert response.text == 'None'

the ``form=`` parameter of the ``Given`` and ``when`` functions will send the
given dictionary as a ``urlencoded`` HTTP form, but you can try ``json`` and 
``multipart`` content types to ensure all API users will happy!

.. testcode:: cookbook/form

   with Given(app, verb='POST', json={'foo': 'bar'}):
       assert response.text == 'bar'

   with Given(app, verb='POST', multipart={'foo': 'bar'}):
       assert response.text == 'bar'

HTTP Status
-----------

There are two ways for to set HTTP status code for response: raise an instance
of :class:`.HTTPStatus` class or set 
:attr:`req.response.status <yhttp.Response.status>` directly.

There are some builtins HTTP status factory functions: 

:func:`.statuses.badrequest`

:func:`.statuses.unauthorized`

:func:`.statuses.forbidden`

:func:`.statuses.notfound`

:func:`.statuses.methodnotallowed`

:func:`.statuses.conflict`

:func:`.statuses.gone`

:func:`.statuses.preconditionfailed`

:func:`.statuses.notmodified`

:func:`.statuses.internalservererror`

:func:`.statuses.badgateway`

:func:`.statuses.movedpermanently`

:func:`.statuses.found`

See the example below for usage:


.. testsetup:: cookbook/status

   from yhttp import Application, text
   app = Application()

.. testcode:: cookbook/status

   from yhttp import statuses

   @app.route()
   def get(req):
       raise statuses.notfound()
    
   app.ready()
   

.. testcode:: cookbook/status

   from bddrest import Given, when, given, status

   with Given(app):
       assert status == 404
       assert status == '404 Not Found'

HTTP Redirect
^^^^^^^^^^^^^

To redirect the request to another location raise a 
:func:`.statuses.movedpermanently` or :func:`.statuses.found`

.. code-block:: python

   raise statuses.found('http://example.com')


Custom HTTP Status
^^^^^^^^^^^^^^^^^^

Use :func:`.statuses.status` to raise your very own status code and text.

.. code-block:: python

   raise statuses.status(700, 'Custom Status Text')

Or set :attr:`req.response.status <yhttp.Response.status>` directly.

.. code-block:: python

   @app.route()
   def get(req):
       req.response.status = '201 Created'
       return ... 


Routing
-------

the only way to register handler for http requests is
:meth:`.Application.route` decorator factory.

Hanler function's name will be used as HTTP verb. so, the ``get`` in these 
example stands for the HTTP ``GET`` method.


.. code-block::

   @app.route()                 # Default route
   def get(req): 
       ...

   @app.route('/foo')           # Not match with: /foo/bar
   def get(req): 
       ...

   @app.route('/books/(\d+)')   # Match with: /books/1
   def get(req, id): 
       ...


Static Contents 
---------------

:class:`.Application` class has two methods: :meth:`.Application.staticfile`
and :meth:`.Application.staticdirectory` to complete this mission!


.. code-block::

   app.staticfile(r'/a\.txt', 'path/to/a.txt')
   app.staticdirectory(r'/foo/', 'path/to/foo/directory')

.. note::

   Do not use any regular expression group inside 
   :meth:`.Application.staticdirectory`'s ``pattern`` parameter.




HTTP Cookie
-----------

There is how to use :attr:`req.cookies <yhttp.Request.cookies>`:

.. testsetup:: cookbook/cookie

   from yhttp import Application, text
   app = Application()

.. testcode:: cookbook/cookie

   @app.route()
   def get(req):
       counter = req.cookies['counter']
       req.cookies['counter'] = str(int(counter.value) + 1)
       req.cookies['counter']['max-age'] = 1
       req.cookies['counter']['path'] = '/a'
       req.cookies['counter']['domain'] = 'example.com'
    
   app.ready()
   

Test:

.. testcode:: cookbook/cookie

   from http import cookies

   from bddrest import Given, response, when, given

   headers = {'Cookie': 'counter=1;'}
   with Given(app, headers=headers):
       assert 'Set-cookie' in response.headers
        
       cookie = cookies.SimpleCookie(response.headers['Set-cookie'])
       counter = cookie['counter']
       assert counter.value == '2'
       assert counter['path'] == '/a'
       assert counter['domain'] == 'example.com'
       assert counter['max-age'] == '1'

..
   static
   validation
