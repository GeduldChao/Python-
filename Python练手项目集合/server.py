#-*- coding:utf-8 -*-
from http.server import BaseHTTPRequestHandler, HTTPServer
import sys, os, subprocess

# 服务器异常类
class ServerException(Exception):
	'''服务器内部错误'''
	pass
class case_no_file(object):
	'''该路径不存在'''
	def test(self, handler):
		return not os.path.exists(handler.full_path)
	def act(self, handler):
		raise ServerException("'{0}' not found".format(handler.path))

class case_cgi_file(object):
	'''脚本文件处理'''
	def test(self, handler):
		return os.path.isfile(handler.full_path) and handler.full_path.endswith('.py')
	def act(self, handler):
		# 运行脚本文件
		handler.run_cgi(handler.full_path)

class case_existing_file(object):
	'''该路径是文件'''
	def test(self, handler):
		return os.path.isfile(handler.full_path)
	def act(self, handler):
		handler.handle_file(handler.full_path)

class case_directory_index_file(object):
	def index_path(self, handler):
		return os.path.join(handler.full_path, 'index.html')
	#判断目标路径是否是目录&&目录下是否有index.html
	def test(self, handler):
		return os.path.isdir(handler.full_path) and os.path.isfile(self.index_path(handler))
	#响应index.html的内容
	def act(self, handler):
		handler.handle_file(self.index_path(handler))

class case_always_fail(object):
	'''所有情况都不符合时的默认处理类'''
	def test(self, handler):
		return True
	def act(self, handler):
		raise ServerException("Unknown object '{0}'".format(handler.path))

class RequestHandler(BaseHTTPRequestHandler):
	'''处理请求并返回页面'''
	Page = '''\
<html>
<body>
<table>
<tr>  <td>Header</td>         <td>Value</td>          </tr>
<tr>  <td>Date and time</td>  <td>{date_time}</td>    </tr>
<tr>  <td>Client host</td>    <td>{client_host}</td>  </tr>
<tr>  <td>Client port</td>    <td>{client_port}</td> </tr>
<tr>  <td>Command</td>        <td>{command}</td>      </tr>
<tr>  <td>Path</td>           <td>{path}</td>         </tr>
</table>
</body>
</html>
'''
	Error_Page = '''\
<html>
	<body>
		<h1>Error accessing {path}</h1>
		<p>{msg}</p>
	</body>
</html>
'''
	print("测试字符串与字典的格式化")
	dic = {'name': 'A', 'age': 18}
	print("姓名:{name}, 年龄:{age}".format(**dic))
	print("----------测试结束----------")
	full_path = ''
	# 所有可能的情况(List中可以存放任意类型的值)
	Cases = [case_no_file(), case_cgi_file(), case_existing_file(), case_directory_index_file(), case_always_fail()]
	# 处理一个GET请求
	def do_GET(self):
		try:
			# 文件完整路径
			self.full_path += (os.getcwd() + self.path)
			self.full_path = self.full_path.replace("\\", "/")
			# 遍历所有的可能
			for case in self.Cases:
				if(case.test(self)):
					case.act(self)
					break
		# 处理异常
		except Exception as msg:
			self.handle_error(msg)

	def handle_file(self, full_path):
		try:
			with open(full_path, 'rb') as reader:
				content = reader.read()
				self.send_content(content)
		except IOError as msg:
			msg = "'{0}' cannot be read: {1}".format(self.path, msg)
			self.handle_error(msg)

	def handle_error(self, msg):
		content = self.Error_Page.format(path=self.path, msg=msg).encode('utf-8')
		self.send_content(content, 404)

	def create_page(self):
		values = {
		'date_time'   : self.date_time_string(),
		'client_host' : self.client_address[0],
		'client_port' : self.client_address[1],
		'command'     : self.command,
		'path'        : self.path
		}
		page = self.Page.format(**values)
		return page

	def send_content(self, content, status=200):
		self.send_response(status)
		self.send_header("Content-Type", "text/html")
		self.send_header("Content-Length", str(len(content)))
		self.end_headers()
		self.wfile.write(content)

	def run_cgi(self, full_path):
		data = subprocess.Popen('python '+full_path, stdout = subprocess.PIPE, shell = True).stdout.read()
		self.send_content(data)

#----------------------------------------------------------------------
if __name__ == '__main__':
	serverAddress = ('', 8080)
	server = HTTPServer(serverAddress, RequestHandler)
	server.serve_forever()