CREATE TABLE IF NOT EXISTS "version" (
	"db_version" INTEGER DEFAULT 1 UNIQUE,
	PRIMARY KEY(db_version)
);

CREATE TABLE IF NOT EXISTS "playback_states" (
	"watched_id" INTEGER PRIMARY KEY AUTOINCREMENT,
	"media" TEXT,
	"trakt_id" TEXT,
	"current" varchar(45) DEFAULT NULL,
	"total" varchar(45) DEFAULT NULL,
	"watched" INTEGER DEFAULT 0,
	"ids" TEXT,
	"metadata" TEXT,
	"ts" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	UNIQUE (media, trakt_id)
);