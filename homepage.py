'''
To run:

$ python homepage.py
'''

from flask import Flask, render_template, request, jsonify
app = Flask(__name__)

######## Example data, in sets of 3 ############
data = list(range(1, 300, 3))
print (data)


@app.route("/")
def home_page():
    # return "Hello, world!"
    example_embed = "This string is from python"
    return render_template("index.html", embed=example_embed)

######## Example fetch ############
@app.route('/test', methods=['GET', 'POST'])
def testfn():
    # POST request
    if request.method == 'POST':
        print(request.get_json())  # parse as JSON
        return 'OK', 200
    # GET request
    else:
        message = {'greeting': 'Hello from Flask!'}
        return jsonify(message)  # serialize and use JSON headers

######## Data fetch ############
@app.route('/getdata/<transaction_id>/<second_arg>', methods=['GET','POST'])
def datafind(transaction_id, second_arg):
    # POST request
    if request.method == 'POST':
        print('Incoming..')
        print(request.get_text())  # parse as text
        return 'OK', 200
    # GET request
    else:
        message = 't_in = %s ; result: %s ; opt_arg: %s'%(transaction_id, data[int(transaction_id)], second_arg)
        return message #jsonify(message)  # serialize and use JSON headers

@app.route("/get_data/<year>/month/day/h/m")
def fun():
    # TODO: retrieve
    return data

app.run(debug=True)


'''
references

https://flask.palletsprojects.com/en/1.1.x/quickstart/#a-minimal-application

https://towardsdatascience.com/talking-to-python-from-javascript-flask-and-the-fetch-api-e0ef3573c451

https://becominghuman.ai/full-stack-web-development-python-flask-javascript-jquery-bootstrap-802dd7d43053

https://www.jitsejan.com/python-and-javascript-in-flask.html
'''
