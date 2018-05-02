# -*- coding: utf-8 -*-

'''*
	This program is free software: you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation, either version 3 of the License, or
	(at your option) any later version.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with this program.  If not, see <http://www.gnu.org/licenses/>.
*'''

import xbmc
from commoncore import kodi
test = xbmc.__version__.split('.')
is_depricated = True if int(test[1]) < 19  else False

class CoreException(Exception):
	pass

class PlaybackService(xbmc.Player):
	def __init__(self, *args, **kwargs):
		self.__current_time 		= 0
		self.__total_time			= 0
		self.__percent 				= 0
		self.__tracking				= False
	
	def set_playback(self, watched=False):
		try:
				self.__percent = int(self.__current_time * 100 / self.__total_time )
		except:
			self.__percent = 0

		metadata = kodi.json.loads(kodi.get_property('core.infolabel', "service.core.playback"))
		if 'episode' in metadata:
			media = 'episode'
		else:
			media = 'movie'
			
		from commoncore.trakt import trakt as DB
		if DB.query("SELECT 1 FROM playback_states WHERE media=? AND trakt_id=?", [media, metadata[media]['trakt_id']]):
			DB.execute("UPDATE playback_states SET current=? WHERE media=? AND trakt_id=?", [self.__current_time, media, metadata[media]['trakt_id']])
		else:
			DB.execute("REPLACE INTO playback_states(media, trakt_id, current, total, ids, metadata) VALUES(?,?,?,?,?,?)", [media, metadata[media]['trakt_id'], self.__current_time, self.__total_time, kodi.json.dumps(metadata['ids']), kodi.json.dumps(metadata)])
		if watched:
			watched = 1 if self.__percent > 94 else 0
			DB.execute("UPDATE playback_states SET watched=? WHERE media=? AND trakt_id=?", [watched, media, metadata[media]['trakt_id']])
		DB.commit()
		
		del DB
		
		
	
	def clear_playback_info(self):
		kodi.set_property('core.infolabel', '', "service.core.playback")
		kodi.set_property('core.playing', "false", "service.core.playback")
	
	def monitor_playback(self):
		self.__current_time = self.getTime()
		self.__total_time = self.getTotalTime()
	
	def onPlayBackStarted(self):
		self.__tracking = kodi.get_property('core.playing', "service.core.playback")
		if self.__tracking:
			try:
				self.__total_time = self.getTotalTime()
				kodi.set_property('core.percent', "", "service.core.playback")
				kodi.set_property('core.total_time', str(self.__total_time), "service.core.playback")
			except CoreException, e:
				kodi.log(e)

	
	def onPlayBackStopped(self):
		if self.__tracking:
			self.set_playback(True)
			self.clear_playback_info()
					
	def onPlayBackEnded(self):
		self.onPlayBackStopped()
	
	def onPlayBackPaused(self):
		if self.__tracking: self.set_playback()
	
	def onPlayBackResumed(self):
		pass
	
	def onPlayBackSeek(self, time, seekOffset):
		pass
	
	def onPlayBackSeekChapter(self):
		pass
	
	def onPlayBackError(self):
		self.clear_playback_info()
	
	
	def start(self):
		class Monitor(xbmc.Monitor):
			def onSettingsChanged(self):
				pass
		monitor = Monitor()
		kodi.log("Service Starting...")

		if is_depricated:
			while not xbmc.abortRequested:
				if self.isPlaying() and self.__tracking: self.monitor_playback()
				kodi.sleep(1000)
		else:
			while not monitor.abortRequested():
				if monitor.waitForAbort(1):
					break
				if self.isPlaying() and self.__tracking: self.monitor_playback()

		self.shutdown()
	
	def shutdown(self):
		kodi.log("Service Stopping...")


if __name__ == '__main__':
	server = PlaybackService()
	server.start()

