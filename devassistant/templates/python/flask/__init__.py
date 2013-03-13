from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return 'Find me in {0}'.format(__file__)

if __name__ == '__main__':
    app.run()
