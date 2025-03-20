import pytest
import os
from main import  app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

# def test_file_read(client):
#     response = client.post(
#         '/api/file/read',
#         json={
#             'file_path': 'file.xml',
#         }
#     )
#     assert response.status_code == 200
#     assert response.json is True

def test_successful_tag_count(client):
    response = client.post(
        '/api/tags/get-count',
        json={
            'file_path': 'file.xml',
            'tag_name': 'price'
        }
    )
    assert response.status_code == 200
    assert response.json == {'count': 2}

def test_tag_not_found(client):
    response = client.post(
        '/api/tags/get-count',
        json={
            'file_path': 'file.xml',
            'tag_name': 'main'
        }
    )

    assert response.status_code == 404
    assert 'В файле отсутствует тег с данным названием' == response.json['error']

def test_file_not_exists(client):
    response = client.post(
        '/api/tags/get-count',
        json={
            'file_path': 'non_existent.xml',
            'tag_name': 'title'
        }
    )

    assert response.status_code == 404
    assert 'Файл не найден' == response.json['error']

def test_get_tag_count_false(client):
    response = client.post(
        '/api/tags/attributes/get',
        json={
            'file_path': 'file.xml',
            'tag_name': 'product'
        }
    )
    assert response.json['attributes'] == []

def test_get_tag_count_success(client):
    response = client.post(
        '/api/tags/attributes/get',
        json={
            'file_path': 'file.xml',
            'tag_name': 'person'
        }
    )
    assert response.json['attributes'] == ['type', 'id']