import cgi
import os
import os.path
import sys
import pgdb
import cStringIO


class http_response(object):
	def __init__(self, environ, start_response):
		import cStringIO
		self.buffer = cStringIO.StringIO()
		self.environ = environ
		self.start_response = start_response
		self.status = '200 OK'
		self.headers = [('Content-type', 'text/html; charset=utf-8'), ('P3P', '''policyref="/w3c/p3p.xml", CP="NOI NOR CURa OUR"''')]

	def write(self, data):
		self.buffer.write(data)

	def finalise(self):
		"""
		Closes the output buffer, writes the correct header/s and returns
		something suitable for returning from the top-level application() call
		"""
		self.html_footers()
		self.value = self.buffer.getvalue()
		self.buffer.close()
		self.headers.append(('Content-Length', str(len(self.value))))
		self.start_response(self.status, self.headers)
		return [self.value]

	def boom(self, msg):
		self.status = '500 Server side error'
		print >>self.buffer, "Critical error, HTTP status 500<br />"
		print >>self.buffer, str(msg)
		return self.finalise()

	def oops(self, msg):
		print >>self.buffer, """<div style="border:1px black dotted;">"""
		print >>self.buffer, "Oops! " + str(msg) + "<br />"
		print >>self.buffer, """<a href="index.py">Go home</a><br />\n"""
		print >>self.buffer, """</div>"""
		return self.finalise()


	def html_headers(self, *head_items):
		print >>self.buffer, """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"\n    "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">"""
		print >>self.buffer, """<html>\n<head>
		<title>QQC!</title>
		<meta http-equiv="Content-Type" content="text/html;charset=utf-8" />
		<link rel="stylesheet" href="qqc.css" type="text/css" title="QQC" />
		<link rel="P3Pv1" href="/w3c/p3p.xml" />"""
		for item in head_items:
			print >>self.buffer, "\t%s" % item
		print >>self.buffer, """</head>\n<body onLoad="toggle_howto();">"""

	def html_footers(self):
		print >>self.buffer, """\n<hr />\n<div>"""
		print >>self.buffer, """<a href="http://validator.w3.org/check?uri=referer"><img src="valid-xhtml11.png" alt="Valid XHTML 1.1" height="31" width="88" /></a>"""
		print >>self.buffer, """</div>\n</body>\n</html>"""




def application(environ, start_response):
	# cwd gets set to /, which is annoying :(
	cwd = os.path.split(environ['SCRIPT_FILENAME'])[0]
	sys.path.insert(0, cwd)
	import qqc_include as inc

	# Setup our output
	output = http_response(environ, start_response)
	sys.stdout = output
	wsgi_errors = environ['wsgi.errors']


	# Get all our form input
	form = cgi.FieldStorage(fp=environ['wsgi.input'], environ=environ)
	TABLENAME = str(form.getfirst("script_name", ''))
	PROOFREADER = str(form.getfirst("proofreader", ''))
	ORDER = str(form.getfirst("newest", ''))
	ERROR_ID = form.getfirst("error_id", '')
	LINENUM = str(form.getfirst("linenum", ''))
	GET_ALL = form.getfirst("all", None)
	REMOTE_USER = environ.get("REMOTE_USER", 'USERNAME_ERROR')
	try:
		REMOTE_USER = [x for x in REMOTE_USER.split('/') if x.startswith('CN=')][0][3:]
	except:
		pass



	# Connect to DB
	try:
		connection = pgdb.connect(host=inc.db_host, database=inc.db_name, user=inc.db_user, password=inc.db_pass)
		cursor = connection.cursor()
	except:
		return output.boom("Could not connect to database")


	# Get useful things from the DB
	try:
		cursor.execute('''SELECT "name","privileged" FROM "proofreaders"''')
		name_tuples = cursor.fetchall()
		names = [x[0] for x in name_tuples]
		cursor.execute('''SELECT DISTINCT "script_name" FROM "lines"''')
		scripts = [x[0] for x in cursor.fetchall()]
	except:
		return output.boom("Could not get stuff from database")

	try:
		PRIVILEGED = [x for x in name_tuples if x[0] == REMOTE_USER][0][1]
	except:
		PRIVILEGED = False


	# Handle deletion if one was requested
	try:
		if ERROR_ID and PRIVILEGED:
			# Only perform the deletion if the user has the privileged flag set
			cursor.execute('''SELECT clear_error(''' + ERROR_ID + ''')''')
			connection.commit()
	except Exception, data:
		return output.oops("Error during deletion - " + str(data))


	# Start output
	output.html_headers()


	# Header bar
	print """
	<div class="header">
	<h5 style="position: absolute;">
	<a href="qqc_report.py">Report an error</a><br />
	<a href="qqc_view.py">View reported errors</a>
	</h5>
	<h1 style="font-family:fantasy; padding:0px;">QQC!</h1>
	<small>Written by Barney Desmond</small>
	</div>
	"""


	# Sort out critera and inform the user
	link = environ['SCRIPT_NAME'] + '?'
	if PROOFREADER:
		link += '''&amp;proofreader='''+PROOFREADER
	if TABLENAME:
		link += '''&amp;script_name='''+TABLENAME

	if ORDER:
		order = 'Sort by script name, Z-A'
		swap = '''<small>(<a href="%s">sort A-Z</a>)</small>''' % link
	else:
		order = 'Sort by script name, A-Z'
		swap = '''<small>(<a href="%s&amp;newest=true">sort Z-A</a>)</small>''' % link

	print """
	<fieldset>
	<legend>Criteria</legend>
	<ul>
	\t<li>%s %s</li>""" % (order, swap)

	if TABLENAME:
		print """\t<li>Show reports for <strong>%s</strong></li>""" % TABLENAME
	if PROOFREADER:
		print """\t<li>Show reports from <strong>%s</strong></li>""" % PROOFREADER

	print """\t</ul>
	<a href="%s">Show all error reports</a>
	</fieldset>
	""" % environ['SCRIPT_NAME']


	# Retrieve all errors
	resultset = []
	query = """SELECT "error_id","script_name","linenum"::integer,"proofreader","description","img_filename","ttext","fixed_flag" FROM "errors" NATURAL JOIN "lines" WHERE TRUE """
	if TABLENAME:
		query += """ AND "script_name"=%(script)s"""
	if PROOFREADER:
		query += """ AND "proofreader"=%(reader)s"""
	if LINENUM:
		query += """ AND "linenum"=%(linenum)s"""

	if ORDER:
		query += """ ORDER BY "fixed_flag", "script_name" DESC, "linenum" ASC"""
	else:
		query += """ ORDER BY "fixed_flag", "script_name" ASC, "linenum" ASC"""

	query_dict = { "script": TABLENAME, "reader": PROOFREADER, "linenum": LINENUM }
	try:
		cursor.execute(query, query_dict)
		resultset = cursor.fetchall()
	except Exception, data:
		return output.oops("Error trying to retrieve reports - " + str(data))


	# Start showing the errors
	print """
	<fieldset>
	<legend>%s Reports (plus %s dismissed reports)</legend>

	<table class="results">

	<tr>
	<th>Script file</th>
	<th>Line number</th>
	<th>Proofreader</th>
	<th>Problem</th>
	<th>Screenshot</th>
	<th>Translated line</th>
	<th></th>
	</tr>
	""" % ( len([x for x in resultset if not x[7]]) , len([x for x in resultset if x[7]]) )

	extra_params = ''
	if TABLENAME:
		extra_params += """<input type="hidden" value="%s" name="script_name" />""" % TABLENAME
	if PROOFREADER:
		extra_params += """<input type="hidden" value="%s" name="proofreader" />""" % PROOFREADER
	if ORDER:
		extra_params += """<input type="hidden" value="%s" name="newest" />""" % ORDER



	for row in resultset:
		if row[7] and not GET_ALL:
			continue
		error_params = {}
		row[2] = str(row[2])

		link = environ['SCRIPT_NAME'] + '?'
		if row[1] != TABLENAME:
			link += """&amp;script_name="""+row[1]
			if PROOFREADER:
				link += """&amp;proofreader="""+PROOFREADER
			if ORDER:
				link += """&amp;newest="""+ORDER
			error_params['script_file'] = """<a href="%s">%s</a>""" % (link, cgi.escape(row[1]))
		else:
			error_params['script_file'] = cgi.escape(row[1])

		error_params['line_num'] = cgi.escape(row[2])

		link = environ['SCRIPT_NAME'] + '?'
		if row[3] != PROOFREADER:
			link += """&amp;proofreader="""+row[3]
			if TABLENAME:
				link += """&amp;script_name="""+TABLENAME
			if ORDER:
				link += """&amp;newest="""+ORDER
			error_params['proofreader'] = """<a href="%s">%s</a>""" % (link, cgi.escape(row[3]))
		else:
			error_params['proofreader'] = cgi.escape(row[3])

		error_params['problem'] = cgi.escape(row[4])
		if row[5]:
			error_params['screenshot'] = """<a href="uploads/%s">File</a>""" % row[5]
		else:
			error_params['screenshot'] = 'None'
		error_params['error_id'] = int(row[0])
		error_params['ttext'] = cgi.escape(row[6])
		error_params['fixed_flag'] = row[7]
		error_params['extra'] = extra_params

		if row[7]:
			error_params['style'] = ''' class="fixed"'''
			error_params['disabled'] = '''disabled="disabled"'''
		else:
			error_params['style'] = ''' class="unfixed"'''
			error_params['disabled'] = ''

		print """<form method="get" action="%s">""" % environ['SCRIPT_NAME']
		if PRIVILEGED:
			print """<tr%(style)s>
	<td>%(script_file)s</td>
	<td>%(line_num)s</td>
	<td>%(proofreader)s</td>
	<td>%(problem)s</td>
	<td>%(screenshot)s</td>
	<td>%(ttext)s</td>
	<td><input type="hidden" name="error_id" value="%(error_id)s" />%(extra)s<input type="submit" value="Dismiss" %(disabled)s /></td>
	</tr>
	</form>
	""" % error_params
		else:
			print """<tr%(style)s>
	<td>%(script_file)s</td>
	<td>%(line_num)s</td>
	<td>%(proofreader)s</td>
	<td>%(problem)s</td>
	<td>%(screenshot)s</td>
	<td>%(ttext)s</td>
	<td><input type="hidden" name="error_id" value="%(error_id)s" />%(extra)s</td>
	</tr>
	</form>
	""" % error_params



	print """
	</table>

	</fieldset>
	"""


	# All regular output should be done by now
	connection.close()
	return output.finalise()

from paste.exceptions.errormiddleware import ErrorMiddleware
application = ErrorMiddleware(application, debug=True)






