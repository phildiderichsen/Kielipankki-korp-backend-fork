
CREATE TABLE IF NOT EXISTS `corpus_info` (
   `corpus` varchar(64) NOT NULL DEFAULT '',
   `key` varchar(32) NOT NULL DEFAULT '',
   `value` varchar(1024) DEFAULT NULL,
 INDEX `corpus_key` (`corpus`, `key`))  DEFAULT CHARSET = `utf8` ;
