import sqlite3
from flask import Flask, request, jsonify
import xml.sax
import os

def initialize_database():
    connection = sqlite3.connect('data.db')
    cursor = connection.cursor()

    # Создание таблиц
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tag_name TEXT NOT NULL,
            file_id INTEGER,
            FOREIGN KEY (file_id) REFERENCES Files(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Attributes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            attr_name TEXT NOT NULL,
            attr_value TEXT,
            tag_id INTEGER,
            FOREIGN KEY (tag_id) REFERENCES Tags(id)
        )
    ''')

    connection.commit()
    connection.close()


def add_file(filename):
    connection = sqlite3.connect('data.db')
    cursor = connection.cursor()
    cursor.execute('INSERT INTO Files (filename) VALUES (?)', (filename,))
    connection.commit()
    file_id = cursor.lastrowid
    connection.close()
    return file_id


def add_tag(tag_name, file_id):
    connection = sqlite3.connect('data.db')
    cursor = connection.cursor()
    cursor.execute('INSERT INTO Tags (tag_name, file_id) VALUES (?, ?)', (tag_name, file_id))
    connection.commit()
    tag_id = cursor.lastrowid
    connection.close()
    return tag_id


def add_attribute(attr_name, attr_value, tag_id):
    connection = sqlite3.connect('data.db')
    cursor = connection.cursor()
    cursor.execute('INSERT INTO Attributes (attr_name, attr_value, tag_id) VALUES (?, ?, ?)',
                   (attr_name, attr_value, tag_id))
    connection.commit()
    connection.close()

app = Flask(__name__)


class SimpleXMLHandler(xml.sax.ContentHandler):
    def __init__(self, file_id):
        self.file_id = file_id
        self.current_tag = None
        self.tag_count = {}

    def startElement(self, name, attrs):
        self.current_tag = name
        if name in self.tag_count:
            self.tag_count[name] += 1
        else:
            self.tag_count[name] = 1

        tag_id = add_tag(name, self.file_id)

        for attr_name, attr_value in attrs.items():
            add_attribute(attr_name, attr_value, tag_id)

    def endElement(self, name):
        self.current_tag = None


@app.route('/api/file/read', methods=['POST'])
def read_xml_file():
    if 'file' not in request.files:
        return jsonify(False), 400

    uploaded_file = request.files['file']

    if not uploaded_file.filename.endswith('.xml'):
        return jsonify(False), 400

    filename = uploaded_file.filename
    uploaded_file.save(filename)

    try:
        file_id = add_file(filename)
        handler = SimpleXMLHandler(file_id)
        xml.sax.parse(filename, handler)
        return jsonify(True)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify(False)
    finally:
        if os.path.exists(filename):
            os.remove(filename)


@app.route('/api/tags/get-count', methods=['POST'])
def get_tag_count():
    data = request.get_json()
    file_path = data.get('file_path')
    tag_name = data.get('tag_name')

    if not os.path.exists(file_path):
        return jsonify({"error": "Файл не найден"}), 404

    class CountXMLHandler(xml.sax.ContentHandler):
        def __init__(self):
            self.count = 0

        def startElement(self, name, attrs):
            if name == tag_name:
                self.count += 1

    handler = CountXMLHandler()
    xml.sax.parse(file_path, handler)

    if handler.count == 0:
        return jsonify({"error": "В файле отсутствует тег с данным названием"}), 404

    return jsonify({"count": handler.count})

class AttributeXMLHandler(xml.sax.ContentHandler):
    def __init__(self, tag_name):
        self.tag_name = tag_name
        self.attributes = set()

    def startElement(self, name, attrs):
        if name == self.tag_name:
            for attr in attrs.keys():
                self.attributes.add(attr)

@app.route('/api/tags/attributes/get', methods=['POST'])
def get_tag_attributes():
    data = request.get_json()
    file_path = data.get('file_path')
    tag_name = data.get('tag_name')

    if not os.path.exists(file_path):
        return jsonify({"error": "Файл не найден"}), 404

    handler = AttributeXMLHandler(tag_name)
    xml.sax.parse(file_path, handler)

    return jsonify({"attributes": list(handler.attributes)})

if __name__ == '__main__':
    initialize_database()
    app.run(debug=True)

# curl -X POST -F "file=@file.path" http://127.0.0.1:5000/api/file/read

