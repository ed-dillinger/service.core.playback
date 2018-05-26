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

DB_TYPE = 'MySQL' if kodi.get_setting('database_type', 'service.core.playback') == '1' else 'SQLite'
if DB_TYPE == 'MySQL':
	from commoncore.database import MySQLDatabase as DATABASE_CLASS
	class DBI(DATABASE_CLASS):
		def _initialize(self):
			self.connect()
			statements = [
				"""SET autocommit=0;""",
				"""START TRANSACTION;""",
				"""CREATE TABLE IF NOT EXISTS `version` (
					`db_version` int(11) NOT NULL DEFAULT 1,
					PRIMARY KEY(`db_version`));
				""",
				""" CREATE TABLE IF NOT EXISTS `playback_states` (
					`watched_id` int(11) NOT NULL AUTO_INCREMENT,
					`media` varchar(15) DEFAULT "show",
					`trakt_id` INT(11),
					`current` VARCHAR(15) DEFAULT NULL,
					`total` VARCHAR(15) DEFAULT NULL,
					`watched` TINYINT(1) DEFAULT 0,
					`ids` LONGBLOB,
					`metadata` LONGBLOB,
					`ts` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
					PRIMARY KEY(`watched_id`),
					UNIQUE KEY `media_UNIQUE` (`media`,`trakt_id`));
				""",
				"""DELETE FROM version;""",
				"""INSERT INTO version(db_version) VALUES({});""".format(self.db_version)
			]
			for SQL in statements:
				self.execute(SQL, quiet=True)
			self.commit()
			self.disconnect()
else:
	from commoncore.database import SQLiteDatabase as DATABASE_CLASS
	class DBI(DATABASE_CLASS):
		def _initialize(self):
			self.connect()
			statements = [
				""" CREATE TABLE IF NOT EXISTS "version" (
					"db_version" INTEGER DEFAULT 1 UNIQUE,
					PRIMARY KEY(db_version));
				""",
				""" CREATE TABLE IF NOT EXISTS "playback_states" (
					"watched_id" INTEGER PRIMARY KEY AUTOINCREMENT,
					"media" TEXT,
					"trakt_id" TEXT,
					"current" varchar(45) DEFAULT NULL,
					"total" varchar(45) DEFAULT NULL,
					"watched" INTEGER DEFAULT 0,
					"ids" TEXT,
					"metadata" TEXT,
					"ts" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
					UNIQUE (media, trakt_id));
				""",
				"""DELETE FROM version;""",
				"""INSERT INTO version(db_version) VALUES({})""".format(self.db_version)
			]
			for SQL in statements:
				self.execute(SQL, quiet=True)
			self.commit()
			self.disconnect()
	
if DB_TYPE == 'MySQL':
	host = kodi.get_setting('database_mysql_host', 'service.core.playback')
	dbname = kodi.get_setting('database_mysql_name', 'service.core.playback')
	username = kodi.get_setting('database_mysql_user', 'service.core.playback')
	password = kodi.get_setting('database_mysql_pass', 'service.core.playback')
	port = kodi.get_setting('database_mysql_port', 'service.core.playback')
	DB=DBI(host, dbname, username, password, port, version=1, quiet=True, connect=True)
else:
	DB_FILE = kodi.vfs.translate_path(kodi.get_setting('database_sqlite_file', 'service.core.playback'))
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

def set_resume_point(media, trakt_id, current_time, total_time, percent, watched, metadata):
	if DB.query("SELECT 1 FROM playback_states WHERE media=? AND trakt_id=?", [media, trakt_id]):
		DB.execute("UPDATE playback_states SET current=? WHERE media=? AND trakt_id=?", [current_time, media, trakt_id])
	else:
		DB.execute("REPLACE INTO playback_states(media, trakt_id, current, total, ids, metadata) VALUES(?,?,?,?,?,?)", [media, trakt_id, current_time, total_time, kodi.json.dumps(metadata['ids']), kodi.json.dumps(metadata)])
	if watched:
		watched = 1 if percent > 94 else 0
		DB.execute("UPDATE playback_states SET watched=? WHERE media=? AND trakt_id=?", [watched, media, trakt_id])
	DB.commit()

def in_progress(media, trakt_id):
	if DB.query("SELECT 1 FROM playback_states WHERE media=? AND watched=0 AND ( current * 1.0 > 0 ) AND trakt_id=?", [media, trakt_id]):
		return True
	else:
		return False

def get_inprogress_shows():
	return DB.query("SELECT ids, metadata FROM playback_states WHERE media='episode' AND watched = 0 AND ( current * 1.0 > 0 ) ORDER BY ts DESC")

def get_inprogress_movies():
	return DB.query("SELECT ids, metadata FROM playback_states WHERE media='movie' AND watched = 0 AND ( current * 1.0 > 0 ) ORDER BY ts DESC")