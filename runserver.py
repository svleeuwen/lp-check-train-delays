__author__ = 'Sander van Leeuwen <replytosander@gmail.com>'

from lpapp import app
app.debug = app.config['DEBUG']
app.run(host='0.0.0.0')
#app.run()
