#!/usr/bin/env python
# coding: utf-8
# http://www.gesource.jp/programming/python/code/0008.html
# http://sheep.art.pl/2007-10-25_Wiki_parser_in_python
import sys; sys.path += [
		r'/home/periwnkl/python', 
	]
# sys.stderr = open('log.txt', 'w')
import cgitb; cgitb.enable()
#from acanthus import *
import os
import sys
import re
import cgi
from string import Template

class Wiki(object):
	def __init__(self):
		self.indexTmpl = Template(open(self.tempFile('index'), 'r').read())
		self.editTmpl = Template(open(self.tempFile('edit'), 'r').read())
		self.DataCheck()
		self.scriptName = os.environ.get('SCRIPT_NAME', '/')
		self.httpHost = os.environ.get('HTTP_HOST', '')
		self.ipAddress = os.environ.get('REMOTE_ADDR', '')
		form = cgi.FieldStorage()
		query = os.environ.get('PATH_INFO', '')[1:].split('/')#/page/nds_environment
		cmd = query[0]
		if cmd == 'page':
			self.ShowPage(query[1])
		elif cmd == 'edit':
			self.EditPage(query[1])
		elif cmd == 'new':
			self.EditPage()
		elif cmd == 'save':
			page = form.getvalue('page', '')
			text = form.getvalue('text', '')
			self.SavePage(page, text)
		else:
			self.ShowPage()
	#
	def DataCheck(self):
		if not os.path.isdir(self.dataDir()):
			os.mkdir(self.dataDir(), int('0700', 8))
	def Write(self, s):
		sys.stdout.write(str(s))
	def ipCheck(self):
		return True#self.ipAddress == 'localhost' or self.ipAddress == '127.0.0.1'
	#
	def dir(self):
		dir = os.path.dirname(self.scriptName)
		if dir[-1] != '/':
			dir += '/'
		return dir
	def tempDir(self):
		return os.path.join(os.path.dirname(sys.argv[0]), 'template/mollio')
	def tempFile(self, page):
		return os.path.join(self.tempDir(), page+'.html')
	def dataDir(self):
		return os.path.join(os.path.dirname(sys.argv[0]), 'data')
	def pageFile(self, page):
		return os.path.join(self.dataDir(), page+'.txt')
	#
	def ShowPage(self, page='Home'):
		pageFile = self.pageFile(page)
		if os.path.isfile(pageFile):
			self.Write('Content-Type: text/html; charset=utf-8\n\n')
			showHTML = WikiParser().ParseFile(pageFile)
			html = self.indexTmpl.substitute({'title': page, 'body': showHTML, 'dir': self.dir()})
			self.Write(html)
		else:
			self.EditPage(page)
	def EditPage(self, page=''):
		text = ''
		pageFile = self.pageFile(page)
		if os.path.isfile(pageFile):
			text = open(pageFile, 'r').read()
		editHTML = self.editTmpl.substitute(
			{
				'action': self.scriptName + '/save', 
				'page': cgi.escape(page), 
				'text': cgi.escape(text)
			}
		)
		html = self.indexTmpl.substitute({'title': page, 'body': editHTML, 'dir': self.dir()})
		if self.ipCheck():
			self.Write('Content-Type: text/html; charset=utf-8\n\n')
			self.Write(html)
		else:
			self.Error()
	def SavePage(self, page, text):
		pageFile = self.pageFile(page)
		text = text.replace('\r\n', '\n')
		text = text.replace('\r', '\n')
		open(pageFile, 'w').write(text)
		self.Jump('/page/'+page)
	def Jump(self, to):
		self.Write('location: '+'http://' + self.httpHost + self.scriptName + to + '\n\n')
	def Error(self):
		self.Write('Content-Type: text/html; charset=utf-8\n\n')
		self.Write('Error')

class WikiParser(object):
	Chomp = lambda self, x: (x[-1] == '\n' and x[:-1]) or x[:]
	# replace
	def _repl_http(self, word):
		url = word[1:-1]#match.group(1)
		i = url.find(':', 5)
		if i != -1:
			if url[i+1:] == 'image':
				return '<img src="'+url[:i-1]+'" alt="" />'
			elif url[i+1:] == 'page':
				return '<a href="' + url[:i-1] + '">'+ url[:i-1] + '</a>'
		else:
			if url[:7] == 'http://':
				return '<a href="' + url + '">'+ url + '</a>'
			else:
				return word
	def _repl_link(self, word):
		url = word
		return '<a href="' + url + '">'+ url + '</a>'
	def _repl_esc(self, s):
		return {'&': '&amp;',
				'<': '&lt;',
				'>': '&gt;'}[s]
	def replace(self, match):
		for type, hit in match.groupdict().items():
			if hit:
				return apply(getattr(self, '_repl' + '_' + type), (hit,))
	#
	def StrIter(self, str):
		for i in str.splitlines():
			yield i
	def ParseString(self, string):
		return self.Parse(string, self.StrIter)
	def ParseFile(self, file):
		return self.Parse(open(file, 'r'))
	def Parse(self, obj, iterFunc=iter):
		repl_re = re.compile(
			r"(?:(?P<esc>[<>&])"
			+ r"|(?P<link>(s?https?://[-_.!~*'()a-zA-Z0-9;/?:@&=+$,%#]+))"
			+ r"|(?P<http>\[(.+)\])"
			+ r")")
		patterns = (
			re.compile(r'(\*{1,3})(.+)'),	#0		見出し
			re.compile(r'>\|\|'),			#1		<pre>
			re.compile(r'\|\|<'),			#2		</pre>
			re.compile(r'----'),			#3		<hr />
			re.compile(r'<!\-\-'),			#4		<!--
			re.compile(r'\-\->'),			#5		-->
			re.compile(r'(\-+)(.+)'),		#6		li ul
			re.compile(r'>(.*)>'),			#7		<backquote>
			re.compile(r'<<'),				#8		</backquote>
			re.compile(r"(s?https?://[-_.!~*'()a-zA-Z0-9;/?:@&=+$,%#]+)"),#9	url
			re.compile(r'\[(.+)\]'),		#10		http
			re.compile(r':(.+):(.+)'),		#11		定義
			re.compile(r'\|(.+)\|'),		#12		table
			re.compile(r'(\++)(.+)')		#13		li ol
			)
		flags = {
			'pre': False,
			'desc': False,
			'list': False,
			'table': False,
			'cmnt': False,
			'ol': False
		}
		li = {
			'curLevel': 0
		}
		ol = {
			'curLevel': 0
		}
		result = []
		
		for i in iterFunc(obj):
			temp = {}
			line = i
			if len(i) > 0:
				line = self.Chomp(line).decode('utf-8', 'ignore')
			#
			#print flags
			if flags['pre']:
				if patterns[2].match(line):
					result.append('</pre>')
					flags['pre'] = not flags['pre']
				else:
					result.append(cgi.escape(line))
				continue
			elif flags['desc']:
				if not patterns[11].match(line):
					result.append('</dl>')
					flags['desc'] = not flags['desc']
			elif flags['list']:
				if not patterns[6].match(line):
					result.append(li['curLevel'] * '</ul>')
					flags['list'] = not flags['list']
			elif flags['ol']:
				if not patterns[13].match(line):
					result.append(ol['curLevel'] * '</ol>')
					flags['ol'] = not flags['ol']
			elif flags['table']:
				if not patterns[12].match(line):
					result.append('</tbody>')
					result.append('</table>')
					flags['table'] = not flags['table']
			elif flags['cmnt']:
				if patterns[5].match(line):
					flags['cmnt'] = not flags['cmnt']
				continue
			#
			# 見出し
			if patterns[0].match(line):
				temp[0] = str(len(patterns[0].match(line).group(1)))# + 2)
				temp[1] = patterns[0].match(line).group(2)
				result.append('<h'+temp[0]+'>'+re.sub(repl_re, self.replace, temp[1])+'</h'+temp[0]+'>')
			# 水平線
			elif patterns[3].match(line):
				result.append('<hr />')
			# 引用
			elif patterns[7].match(line):
				result.append('<backquote>')
			elif patterns[8].match(line):
				result.append('</backquote>')
			# pre
			elif patterns[1].match(line):
				result.append('<pre>')
				flags['pre'] = not flags['pre']
			# コメント
			elif patterns[4].match(line):
				flags['cmnt'] = not flags['cmnt']
			# 定義
			elif patterns[11].match(line):
				if not flags['desc']:
					result.append('<dl>')
					flags['desc'] = not flags['desc']
				dt = patterns[11].match(line).group(1)
				dt = '<dt>'+re.sub(repl_re, self.replace, dt)+'</dt>'
				dd = patterns[11].match(line).group(2)
				dd = '<dd>'+re.sub(repl_re, self.replace, dd)+'</dd>'
				result.append(dt)
				result.append(dd)
			# テーブル
			elif patterns[12].match(line):
				if not flags['table']:
					result.append('<table>')
					result.append('<tbody>')
					flags['table'] = not flags['table']
				temp[0] = patterns[12].match(line).group(1).split('|')
				temp[1] = []
				for i in temp[0]:
					tag = 'td'
					if i[0] == '*':
						tag = 'th'
					# replace + append
					temp[1].append('<'+tag+'>' + re.sub(repl_re, self.replace, i[1:]) + '</'+tag+'>')
				for j in temp[1]:
					result.append('<tr>'+j+'</tr>')
			# list
			elif patterns[6].match(line):
				if not flags['list']:
					flags['list'] = not flags['list']
				l = len(patterns[6].match(line).group(1))
				tag = '<ul>'
				diff = l - li['curLevel']
				li['curLevel'] = l
				if diff < 0:
					tag = '</ul>'
					diff = -diff
				for i in range(diff):
					result.append(tag)
				# replace + append
				result.append(
					'<li>'+
					re.sub(
						repl_re, self.replace, patterns[6].match(line).group(2)
					)+
					'</li>'
				)
			# ol
			elif patterns[13].match(line):
				if not flags['ol']:
					flags['ol'] = not flags['ol']
				l = len(patterns[13].match(line).group(1))
				tag = '<ol>'
				diff = l - ol['curLevel']
				ol['curLevel'] = l
				if diff < 0:
					tag = '</ol>'
					diff = -diff
				for i in range(diff):
					result.append(tag)
				# replace + append
				result.append(
					'<li>'+
					re.sub(
						repl_re, self.replace, patterns[13].match(line).group(2)
					)+
					'</li>'
				)
			# replace
			else:
				line = re.sub(repl_re, self.replace, line)
				result.append(line)#cgi.escape(
				result.append('<br />')
				
		return '\n'.join(result).encode('utf-8', 'ignore')

if __name__ == '__main__':
	Wiki()
