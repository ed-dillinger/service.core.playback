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

from commoncore import kodi
from commoncore.database import SQLiteDatabase

DB_TYPE = 'sqlite'
DB_FILE = kodi.vfs.join("special://profile", 'addon_data/service.core.playback/API_CACHE/cached.db')
class DBI(SQLiteDatabase):
	def _initialize(self):
		pass

DB = DBI(DB_FILE, quiet=True, connect=True, version=1)

def check_resume_point(media, trakt_id):
	from commoncore.core import format_time
	test = DB.query("SELECT current FROM playback_states WHERE watched=0 AND media=? AND trakt_id=? LIMIT 1", [media, trakt_id], force_double_array=False)
	if test:
		seconds = float(test[0])
		if seconds < 60: return False
		ok = kodi.dialog_confirm("Resume Playback?", "Resume playback from %s" % format_time(seconds), yes='Start from beginning', no='Resume') == 0
		if ok:
			return int(seconds)
	return False

def in_progress(media, trakt_id):
	if DB.query("SELECT 1 FROM playback_states WHERE media=? AND watched=0 AND ( current * 1.0 > 0 ) AND trakt_id=?", [media, trakt_id]):
		return True
	else:
		return False

def get_inprogress_shows():
	return DB.query("SELECT ids, metadata FROM playback_states WHERE media='episode' AND watched = 0 AND ( current * 1.0 > 0 ) ORDER BY ts DESC")

def get_inprogress_movies():
	return DB.query("SELECT ids, metadata FROM playback_states WHERE media='movie' AND watched = 0 AND ( current * 1.0 > 0 ) ORDER BY ts DESC")