import cgi
import os
import os.path
import sys
import sha
import pgdb
import cStringIO


class http_response(object):
	def __init__(self, environ, start_response):
		self.buffer = cStringIO.StringIO()
		self.environ = environ
		self.start_response = start_response
		self.status = '200 OK'
		self.headers = [('Content-Type', 'text/html; charset=utf-8'), ('P3P', '''policyref="/w3c/p3p.xml", CP="NOI NOR CURa OUR"''')]

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

	def redirect(self, url):
		self.buffer.close()
		self.status = '302 Found'
		self.headers = [('Content-Type', 'text/html'), ('Location', url)]
		self.start_response(self.status, self.headers)
		return ['redirecting']

	def user_failure(self, msg):
		self.status = '400 User error'
		print >>self.buffer, "Problem with submission, HTTP status 400<br />"
		print >>self.buffer, str(msg)
		return self.finalise()

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
	cwd = os.path.dirname(__file__)
	sys.path.insert(0, cwd)
	import qqc_include as inc

	# Setup our output
	output = http_response(environ, start_response)
	sys.stdout = output
	wsgi_errors = environ['wsgi.errors']


	# Get all our form input
	form = cgi.FieldStorage(fp=environ['wsgi.input'], environ=environ)
	TABLENAME = str(form.getfirst("script_name", ''))
	SUBMISSION = str(form.getfirst("submitted", ''))
	LINES = [str(x) for x in form.getlist("line_number")]
	PROBLEM = str(form.getfirst("problem", ''))
	SEARCHALL = str(form.getfirst("search_all", ''))
	PROOFREADER = environ.get("REMOTE_USER", 'USERNAME_ERROR')
	try:
		PROOFREADER = [x for x in PROOFREADER.split('/') if x.startswith('CN=')][0][3:]
	except:
		pass

	word_array = form.getfirst("words", "").split()
	words = '%'.join(word_array)
	words = '%' + words + '%'


	# Connect to DB
	try:
		connection = pgdb.connect(host=inc.db_host, database=inc.db_name, user=inc.db_user, password=inc.db_pass)
		cursor = connection.cursor()
	except:
		return output.boom("Could not connect to database")


	# Get useful things from the DB
	try:
		cursor.execute('''SELECT "name" FROM "proofreaders"''')
		names = [x[0] for x in cursor.fetchall()]
		cursor.execute('''SELECT DISTINCT "script_name" FROM "lines"''')
		scripts = [x[0] for x in cursor.fetchall()]
	except:
		return output.boom("Could not get stuff from database")


	# Handle a report here; if we get one and it's successful, 302-redirect to
	# this page so you don't get a double report if the user refreshes
	if SUBMISSION:
		try:
			# A hack, now that the script_name is part of the line_number field
			LINES = [tuple(x.split('|', 1)) for x in LINES]
			for LINE in LINES:
				assert LINE[0] in scripts, "Bad script_name: " + LINE[0]
				assert len(LINE[1]), "Line tag was zero-length: " + LINE[0] + ", " + LINE[1]
			assert PROOFREADER in names, "Unknown name for proofreader"
			assert len(PROBLEM), "The problem was not specified"
		except Exception, data:
			return output.user_failure(str(data))

		try:
			new_filename = ''
			if form.has_key("screenshot"):
				if type(form["screenshot"]) is list:
					items = form["screenshot"]
				else:
					items = [form["screenshot"]]

				# Only handle one file due to reports only keeping one filename
				item = items[0]
				if item.file and item.filename:
					hash = sha.new(item.value)
					new_filename = hash.hexdigest()[0:8] + item.filename
					new_path = os.path.join('uploads', new_filename)
					fout = file(new_path, 'wb')
					while True:
						chunk = item.file.read(100000)
						if not chunk:
							break
						fout.write(chunk)
					fout.close()

			for LINE in LINES:
				report_params = { "script_name": LINE[0], "line_num": LINE[1], "reader": PROOFREADER, "problem": PROBLEM, "path": new_filename }
				if new_filename:
					cursor.execute('''SELECT report_error(%(script_name)s, %(line_num)s, %(reader)s, %(problem)s, %(path)s)''', report_params)
				else:
					cursor.execute('''SELECT report_error(%(script_name)s, %(line_num)s, %(reader)s, %(problem)s, null)''', report_params)
			connection.commit()
		except Exception, data:
			return output.boom("There was a problem while logging the report: " + str(data))

		if SEARCHALL:
			SA = '&search_all=on'
		else:
			SA = ''
		new_dest =  "%(self)s?proofreader=%(reader)s&thanks=true&script_name=%(script_name)s&line_number=%(line_num)s%(sa)s" % {
			"self": environ['SCRIPT_NAME'],
			"reader": PROOFREADER,
			"script_name": TABLENAME,
			"line_num": LINE,
			"sa": SA}
		return output.redirect(new_dest)

	js = """<script type='text/javascript'>
		function toggle_howto()
		{
			if(document.getElementById('howto').style.display == "block")
			{
				document.getElementById('howto').style.display = "none";
			}
			else
			{
				document.getElementById('howto').style.display = "block";
			}
		}
	</script>"""




	# Start output
	output.html_headers(js)


	# Header bar
	print """
	<div class="header">
	<h5 style="position: absolute;">
	<a href="qqc_report.py">Report an error</a><br />
	<a href="qqc_view.py">View reported errors</a><br />
	<a href="javascript:toggle_howto();">Show/Hide usage guide</a>
	</h5>
	<h1 style="font-family:fantasy; padding:0px;">QQC!</h1>
	<small>Written by Barney Desmond</small>
	</div>
	"""

	# Usage guide
	print """
<div class="howto" id="howto" style="display:block;">
<h3 style="font-style:italic;">A brief usage guide for QQC</h3>
<p>QQC! is designed for quick and efficient reporting of errors, and its usage is split into distinct, easy steps. QQC! is enhanced for keyboard usage meaning less time spent moving back and forth to the mouse. Text fields will auto-highlight when possible, ready for immediate typing.<br />
<ol>
	<li>Finding the line with the error
	<ul>
		<li>Type a few words from the recalcitrant line into the search field. You <em>don't</em> need the full sentence, just a few significant words, in order. Hit enter.</li>
	<li>Hopefully there's only one &quot;hit&quot; from your search. If so, it's automatically selected, and you can go to the next step. If there's multiple hits, use the mouse to select the appropriate ones, or refine your search keywords (the search box is already highlighted).</li>
	<li>There's a tickbox there to select the search mode. If you know what file the line comes from, you can use the drop-down box to select it, which makes the search space much smaller and more accurate. If you've no idea where you are, just tick the box and search every line in the project. It's generally more efficient to search with some specific, well chosen keywords than to try and guess which file your line is from. If you're getting a lot of hits, enter a longer string from the line to nail it down.</li>
	</ul>
	</li>

	<li>Start complaining
	<ul>
		<li>Make a terse suggestion about what needs fixing. Simple things like <strong>foo-&gt;bar</strong> are best.</li>
		<li>The editor/translator can see the line that you're complaining about, so you don't need to provide context. <em>Just say what the problem is</em>.</li>
		<li>There are times when more description is needed, such as dealing with consistency issues. Explain the situation, the editor/translator will go back and fix problems as needed. Eg. <em>Yuki said her mother died when she was young, and now she's talking about her aunt; what gives?</em> The translator may have confused oba-san/obaa-san (aunt/mother), so they'll go back and fix it themself.</li>
		<li>If it's a simple error, you can just hit tab-&gt;enter, and you're ready to report another error. If it's a more interesting error, there's more work to do.</li>
	</ul>

	<li>Technical errors and glitches
	<ul>
		<li>Sometimes you'll see funny things like rendering glitches, overflowing textboxes and other oddities.</li>
		<li>Take a screenshot using your preferred method. In Windows, you probably want to hit PrintScreen, paste it into mspaint, crop it down to the relevant area and then save it to a JPEG file somewhere. Try and crop it to a reasonable area. At the very least, make the image no larger than the game-window. Any larger is just sloppy and annoying, as it takes longer to look at and longer to upload.</li>
		<li>Browse for the file and select it. Really obvious.</li>
		<li>Hit the big button to submit the report.</li>
	</ul>
	</li>

	<li>Problems with QQC!
	<ul>
		<li>Got a problem with QQC!? Jump on IRC and tell the translator or project leader. They'll know what to do.</li>
	</ul>
	</li>
</ol>
</p>
</div>
"""

	# Report on submissions here
	if form.getfirst("thanks", ""):
		print """\n<fieldset>\n<legend><strong>Submission received</strong></legend>\nThank you, %s, your report has been recorded\n</fieldset>""" % str(PROOFREADER)


	# Query box
	print """
	<form method="get" action="%s">
	<fieldset>
	<legend>Line search</legend>
		<table class="metadata">

		<tr>
		<th><label for="qbox">Some words in the sentence</label></th>
		<td><input type="text" name="words" size="60" id="qbox" accesskey="q" value="%s" /></td>
		</tr>

		<tr>
		<th><label for="script">Script file</label></th>
		<td>
			<select name="script_name" id="script">""" % (environ['SCRIPT_NAME'], ' '.join(word_array))

	for s in scripts:
		if s == TABLENAME:
			print """\t\t\t<option value="%s" selected="selected">%s</option>""" % (s, s)
		else:
			print """\t\t\t<option value="%s">%s</option>""" % (s, s)

	if SEARCHALL:
		search_all_text = ''' checked="checked"'''
	else:
		search_all_text = ''
	print """
			</select>
			<input type="checkbox" name="search_all" id="searchall" %s /><label for="searchall">Ignore selection and search all scripts</label>
		</td>
		</tr>

		<tr>
		<th><input type="hidden" name="proofreader" value="%s" /></th><td><input type="submit" value="Find lines" /></td>
		</tr>

		</table>
	</fieldset>
	</form>""" % (search_all_text, PROOFREADER)


	# Show matching lines
	resultset = []
	if len(word_array):
		query = '''SELECT lines.linenum, lines.speaker, lines.ttext, lines.script_name, COUNT(errors.description) AS report_count FROM lines LEFT OUTER JOIN errors ON (lines.script_name=errors.script_name AND lines.linenum=errors.linenum) WHERE lines."script_name"=%(tn)s AND ttext ILIKE %(like)s GROUP BY lines.linenum, lines.speaker, lines.ttext, lines.script_name ORDER BY lines.script_name,lines.linenum'''
		if SEARCHALL:
			query = '''SELECT lines.linenum, lines.speaker, lines.ttext, lines.script_name, COUNT(errors.description) AS report_count FROM lines LEFT OUTER JOIN errors ON (lines.script_name=errors.script_name AND lines.linenum=errors.linenum) WHERE ttext ILIKE %(like)s GROUP BY lines.linenum, lines.speaker, lines.ttext, lines.script_name ORDER BY lines.script_name,lines.linenum'''
		cursor.execute(query, {"tn":TABLENAME, "like":words} )
		resultset = cursor.fetchall()

		print """
		<form method="post" action="%s" enctype="multipart/form-data">
		<fieldset>
		<legend>%s Lines</legend>
		""" % (environ['SCRIPT_NAME'], str(len(resultset)))

		print """
		<table class="results">
		<tr><th>Script Name</th><th>Line Tag</th><th>Speaker</th><th>Dialogue</th><th>Selector</th><th>Existing reports</th></tr>
		"""

		max_lines = 50
		cur_line = 0
		for row in resultset:
			if cur_line > max_lines and len(word_array)==0:
				break

			# If there's only one row, mark the checkbox immediately
			if len(resultset) == 1:
				selection = ''' checked="checked"'''
			else:
				selection = ''

			print """
			<tr class="fixed">
			<td><label for="r%(script_name)s|%(line)s">%(script_name)s</label></td>
			<td><label for="r%(script_name)s|%(line)s">%(line)s</label></td>
			<td><label for="r%(script_name)s|%(line)s">%(speaker)s</label></td>
			<td><label for="r%(script_name)s|%(line)s">%(dialogue)s</label></td>
			<td><input type="checkbox" class="checkbox" name="line_number" value="%(script_name)s|%(line)s" id="r%(script_name)s|%(line)s"%(extra)s /></td>
			<td><label for="r%(script_name)s|%(line)s"> <a href="qqc_view.py?&amp;script_name=%(script_name)s&amp;linenum=%(line)s&amp;all=true">%(report_count)s</a></label></td>
			</tr>
			""" % { "line": cgi.escape(str(row[0])),
				"speaker": cgi.escape(str(row[1])),
				"dialogue": cgi.escape(str(row[2])),
				"script_name": cgi.escape(str(row[3])),
				"extra": selection,
				"report_count": cgi.escape(str(row[4]))
				}
			cur_line = cur_line + 1


		print """
		</table>
		</fieldset>
		"""


		# File upload
		print """
		<fieldset>
		<legend>Supplementary data</legend>
		<label for="screenshot">Do you need to upload a screenshot to point out the problem?</label><br />
		<input type="file" name="screenshot" id="screenshot" />
		</fieldset>
		"""


		# Details of the complaint
		print """
		<fieldset>
		<legend>Details</legend>

		<table class="metadata">
		"""


		if SEARCHALL:
			SA = '''<input type="hidden" name="search_all" value="on" />'''
		else:
			SA = ''

		print """
		<tr>
		<th><label for="problem">What seems to be<br />the problem here?</label></th>
		<td><textarea rows="4" cols="60" name="problem" id="problem"></textarea></td>
		</tr>

		<tr>
		<th><input type="hidden" name="script_name" value="%s" />%s</th><td><input type="submit" name="submitted" value="Report the problem!" /></td>
		</tr>

		</table>
		</fieldset>
		""" % (TABLENAME, SA)


		# Finish up
		print """</form>"""



	if len(resultset) == 1:
		print """
	<script type="text/javascript">
		document.getElementById("problem").focus()
	</script>
	"""
	else:
		print """
	<script type="text/javascript">
		document.getElementById("qbox").focus()
	</script>
	"""



	# All regular output should be done by now
	connection.close()
	return output.finalise()

from paste.exceptions.errormiddleware import ErrorMiddleware
application = ErrorMiddleware(application, debug=True)

