import pygame
import webcolors
import logsupport
from pygame import gfxdraw

wc = webcolors.name_to_rgb
import config
from config import debugprint, WAITEXIT, WAITNORMALBUTTON, WAITNORMALBUTTONFAST, WAITISYCHANGE, dispratioH, dispratioW
import screen
import xmltodict
import toucharea
import utilities
from utilities import scaleW, scaleH


def trifromtop(h, v, n, size, c, invert):
	if invert:
		return h*n, v + size/2, h*n - size/2, v - size/2, h*n + size/2, v - size/2, c
	else:
		return h*n, v - size/2, h*n - size/2, v + size/2, h*n + size/2, v + size/2, c


class ThermostatScreenDesc(screen.BaseKeyScreenDesc):
	def __init__(self, screensection, screenname):
		debugprint(config.dbgscreenbuild, "New ThermostatScreenDesc ", screenname)
		screen.BaseKeyScreenDesc.__init__(self, screensection, screenname)
		utilities.LocalizeParams(self, screensection, 'KeyColor', 'KeyOffOutlineColor', 'KeyOnOutlineColor')
		self.info = {}
		self.fsize = (30, 50, 80, 160)

		if screenname in config.ISY.NodesByName:
			self.RealObj = config.ISY.NodesByName[screenname]
		else:
			self.RealObj = None
			config.Logs.Log("No Thermostat: " + screenname, severity=logsupport.ConsoleWarning)

		self.TitleRen = config.fonts.Font(self.fsize[1]).render(screen.FlatenScreenLabel(self.label), 0,
																wc(self.CharColor))
		self.TitlePos = ((config.screenwidth - self.TitleRen.get_width())/2, config.topborder)
		self.TempPos = config.topborder + self.TitleRen.get_height()
		self.StatePos = self.TempPos + config.fonts.Font(self.fsize[3]).get_linesize() - scaleH(20)
		self.SPPos = self.StatePos + scaleH(25)
		self.AdjButSurf = pygame.Surface((config.screenwidth, scaleH(40)))
		self.AdjButTops = self.SPPos + config.fonts.Font(self.fsize[2]).get_linesize() - scaleH(5)
		centerspacing = config.screenwidth/5
		self.AdjButSurf.fill(wc(self.BackgroundColor))
		arrowsize = scaleH(40)  # pixel

		for i in range(4):
			gfxdraw.filled_trigon(self.AdjButSurf, *trifromtop(centerspacing, arrowsize/2, i + 1, arrowsize,
															   wc(("red", "blue", "red", "blue")[i]), i%2 <> 0))
			self.keysbyord.append(toucharea.TouchPoint((centerspacing*(i + 1), self.AdjButTops + arrowsize/2),
													   (arrowsize*1.2, arrowsize*1.2)))
		self.ModeButPos = self.AdjButTops + scaleH(85)  # pixel

		bsize = (scaleW(100), scaleH(50))  # pixel
		self.keysbyord.append(toucharea.ManualKeyDesc("Mode", ["Mode"],
													  self.KeyColor, self.CharColor, self.CharColor,
													  center=(config.screenwidth/4, self.ModeButPos), size=bsize,
													  KOn=config.KeyOffOutlineColor))  # todo clean up
		self.keysbyord.append(toucharea.ManualKeyDesc("Fan", ["Fan"],
													  self.KeyColor, self.CharColor, self.CharColor,
													  center=(3*config.screenwidth/4, self.ModeButPos), size=bsize,
													  KOn=config.KeyOffOutlineColor))
		self.keysbyord[4].FinishKey((0,0),(0,0))
		self.keysbyord[5].FinishKey((0,0),(0,0))
		self.ModesPos = self.ModeButPos + bsize[1]/2 + scaleH(5)
		utilities.register_example("ThermostatScreenDesc", self)

	def BumpTemp(self, setpoint, degrees):

		debugprint(config.dbgscreenbuild, "Bump temp: ", setpoint, degrees)
		debugprint(config.dbgscreenbuild, "New: ", self.info[setpoint][0] + degrees)
		r = config.ISYrequestsession.get(
			config.ISYprefix + 'nodes/' + self.RealObj.address + '/set/' + setpoint + '/' + str(
				self.info[setpoint][0] + degrees))

	def BumpMode(self, mode, vals):
		debugprint(config.dbgscreenbuild, "Bump mode: ", mode, vals)
		cv = vals.index(self.info[mode][0])
		debugprint(config.dbgscreenbuild, cv, vals[cv])
		cv = (cv + 1)%len(vals)
		debugprint(config.dbgscreenbuild, "new cv: ", cv)
		r = config.ISYrequestsession.get(
			config.ISYprefix + 'nodes/' + self.RealObj.address + '/set/' + mode + '/' + str(vals[cv]))

	def ShowScreen(self):
		self.PaintBase()
		r = config.ISYrequestsession.get('http://' + config.ISYaddr + '/rest/nodes/' + self.RealObj.address,
										 verify=False)
		tstatdict = xmltodict.parse(r.text)
		props = tstatdict["nodeInfo"]["properties"]["property"]

		self.info = {}
		for item in props:
			debugprint(config.dbgscreenbuild, item["@id"], ":", item["@value"], ":", item["@formatted"])
			self.info[item["@id"]] = (int(item['@value']), item['@formatted'])
		config.screen.blit(self.TitleRen, self.TitlePos)
		r = config.fonts.Font(self.fsize[3], bold=True).render(u"{:4.1f}".format(self.info["ST"][0]/2), 0,
															   wc(self.CharColor))
		config.screen.blit(r, ((config.screenwidth - r.get_width())/2, self.TempPos))
		if isinstance(self.info["CLIHCS"][0], int):
			r = config.fonts.Font(self.fsize[0]).render(("Idle", "Heating", "Cooling")[self.info["CLIHCS"][0]], 0,
													wc(self.CharColor))
		else:
			r = config.fonts.Font(self.fsize[0]).render("n/a", 0, wc(self.CharColor))
		config.screen.blit(r, ((config.screenwidth - r.get_width())/2, self.StatePos))
		r = config.fonts.Font(self.fsize[2]).render(
			"{:2d}    {:2d}".format(self.info["CLISPH"][0]/2, self.info["CLISPC"][0]/2), 0,
			wc(self.CharColor))
		config.screen.blit(r, ((config.screenwidth - r.get_width())/2, self.SPPos))
		config.screen.blit(self.AdjButSurf, (0, self.AdjButTops))
		self.keysbyord[4].PaintKey()
		self.keysbyord[5].PaintKey()
		r1 = config.fonts.Font(self.fsize[1]).render(
			('Off', 'Heat', 'Cool', 'Auto', 'Fan', 'Prog Auto', 'Prog Heat', 'Prog Cool')[self.info["CLIMD"][0]], 0,
			wc(self.CharColor))
		r2 = config.fonts.Font(self.fsize[1]).render(('On', 'Auto')[self.info["CLIFS"][0] - 7], 0, wc(self.CharColor))
		config.screen.blit(r1, (self.keysbyord[4].Center[0] - r1.get_width()/2, self.ModesPos))
		config.screen.blit(r2, (self.keysbyord[5].Center[0] - r2.get_width()/2, self.ModesPos))

		pygame.display.update()

	def HandleScreen(self, newscr=True):

		# stop any watching for device stream
		config.toDaemon.put(["", self.RealObj.address])

		self.ShowScreen()

		while 1:
			choice = config.DS.NewWaitPress(self)
			if choice[0] == WAITEXIT:
				return choice[1]
			elif (choice[0] == WAITNORMALBUTTON) or (choice[0] == WAITNORMALBUTTONFAST):
				if choice[1] < 4:
					self.BumpTemp(('CLISPH', 'CLISPH', 'CLISPC', 'CLISPC')[choice[1]], (2, -2, 2, -2)[choice[1]])
				else:
					self.BumpMode(('CLIMD', 'CLIFS')[choice[1] - 4], (range(8), (7, 8))[choice[1] - 4])
			elif choice[0] == WAITISYCHANGE:
				debugprint(config.dbgscreenbuild, "Thermo change", choice)
				self.ShowScreen()


config.screentypes["Thermostat"] = ThermostatScreenDesc
