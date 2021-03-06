from bddrest import status, response, when


def test_querystringform(app, Given):

    @app.route('/empty')
    def get(req):
        assert req.form == {}

    @app.route()
    def get(req):
        assert req.form['foo'] == 'bar'

    with Given(query=dict(foo='bar')):
        assert status == 200

        when('/empty', query={})
        assert status == 200


def test_urlencodedform(app, Given):

    @app.route()
    def post(req):
        assert req.contenttype == 'application/x-www-form-urlencoded'
        assert req.form['foo'] == 'bar'

    @app.route()
    def patch(req):
        assert req.contenttype == 'application/x-www-form-urlencoded'

    with Given(verb='post', form=dict(foo='bar')):
        assert status == 200

        when(
            form={},
            verb='patch',
            content_type='application/x-www-form-urlencoded'
        )
        assert status == 200
        assert response == ''


def test_urlencodedform_duplicatedfield(app, Given):

    @app.route()
    def post(req):
        assert req.form['foo'] == ['bar', 'baz']

    with Given(
            verb='post',
            body='foo=bar&foo=baz',
            content_type='application/x-www-form-urlencoded'
        ):
        assert status == 200


def test_jsonform(app, Given):
    app.settings.debug = False

    @app.route()
    def post(req):
        assert req.contenttype == 'application/json'
        assert req.form['foo'] == 'bar'

    with Given(verb='post', json=dict(foo='bar')):
        assert status == 200

        # No content length
        when(body='', content_type='application/json')
        assert status == 400
        assert response.text == '400 Content-Length required'

        # Malformed
        when(body='malformed', content_type='application/json')
        assert status == 400
        assert response.text == '400 Cannot parse the request'


def test_multipartform(app, Given):
    app.settings.debug = False

    @app.route()
    def post(req):
        assert req.contenttype.startswith('multipart/form')
        assert req.form['foo'] == 'bar'

    with Given(verb='post', multipart=dict(foo='bar')):
        assert status == 200

        when(body='', content_type='multipart/form-data; boundary=')
        assert status == 400
        assert response == '400 Cannot parse the request'


