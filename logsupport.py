import pygame
import webcolors

import config

wc = webcolors.name_to_rgb
import time
import os
import re
from hw import disklogging

ConsoleInfo = 0
ConsoleWarning = 1
ConsoleError = 2


# disklogging = True

class Logs(object):
	livelog = True
	livelogpos = 0
	log = []

	LogColors = ("white", "yellow", "red")

	def __init__(self, screen, dirnm):
		self.screen = screen
		if disklogging:
			cwd = os.getcwd()
			os.chdir(dirnm)
			q = [k for k in os.listdir('.') if 'Console.log' in k]
			if "Console.log." + str(config.MaxLogFiles) in q:
				os.remove('Console.log.' + str(config.MaxLogFiles))
			for i in range(config.MaxLogFiles - 1, 0, -1):
				if "Console.log." + str(i) in q:
					os.rename('Console.log.' + str(i), "Console.log." + str(i + 1))
			try:
				os.rename('Console.log', 'Console.log.1')
			except:
				pass
			self.disklogfile = open('Console.log', 'w')
			os.chmod('Console.log', 0o555)
			os.chdir(cwd)

	def Log(self, *args, **kwargs):
		"""
		:param severity:
		:param entry:
		"""
		severity = kwargs.pop('severity', ConsoleInfo)
		diskonly = kwargs.pop('diskonly', False)
		entry = "".join([unicode(i) for i in args])
		if not diskonly:
			self.log.append((severity, entry))
		if disklogging:
			self.disklogfile.write(time.strftime('%m-%d-%y %H:%M:%S')
								   + ' Sev: ' + str(severity) + " " + entry.encode('ascii',
																				   errors='backslashreplace') + '\n')
			self.disklogfile.flush()
			os.fsync(self.disklogfile.fileno())
		if self.livelog and not diskonly:
			if self.livelogpos == 0:
				config.screen.fill(wc('royalblue'))
			self.livelogpos = self.RenderLogLine(entry, self.LogColors[severity], self.livelogpos)
			if self.livelogpos > config.screenheight - config.botborder:
				time.sleep(2)
				self.livelogpos = 0
			pygame.display.update()

	def RenderLogLine(self, text, clr, pos):
		text = re.sub('\s\s+', ' ', text)
		ltext = re.split('([ :,])', text)
		ltext.append('')
		while len(ltext) > 1:
			rtext = []
			while 1:
				if config.fonts.Font(config.LogFontSize).size(''.join(ltext))[
					0] < config.screenwidth - 10:  # todo pixels literal
					break
				else:
					rtext.insert(0, ltext[-1])
					del ltext[-1]
			l = config.fonts.Font(config.LogFontSize).render(''.join(ltext), False, wc(clr))
			self.screen.blit(l, (10, pos))  # todo pixel
			ltext = rtext
			ltext.insert(0, "    ")
			pos = pos + config.fonts.Font(config.LogFontSize).get_linesize()
		pygame.display.update()
		return pos

	def RenderLog(self, backcolor, start=0):
		pos = 0
		config.screen.fill(wc(backcolor))
		for i in range(start, len(self.log)):
			pos = self.RenderLogLine(self.log[i][1], self.LogColors[self.log[i][0]], pos)
			if pos > config.screenheight - config.botborder:
				pygame.display.update()
				return (i + 1) if (i + 1) < len(self.log) else -1

		return -1
