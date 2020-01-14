from bddrest import response, status

from rehttp import contenttypes


def test_jsonencoding(app, session):

    json = contenttypes.json(app)

    @app.route()
    @json
    def get():
        return dict(foo='bar')

    with session(app):
        assert status == 200
        assert response.json == dict(foo='bar')
        assert response.content_type == 'application/json'
        assert response.headers['Content-Type'] == \
            'application/json; charset=utf-8'

