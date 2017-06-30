# USERS TABLE

CREATE TABLE `users` (
  `user` varchar(45) NOT NULL,
  `picurl` varchar(1000) DEFAULT NULL,
  `passhash` varchar(255) DEFAULT NULL,
  `jointime` datetime DEFAULT NULL,
  `showplace` tinyint(4) DEFAULT NULL,
  PRIMARY KEY (`user`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


# users relation to groups
CREATE TABLE `user_groups` (
  `user` varchar(45) NOT NULL,
  `group` varchar(45) NOT NULL,
  `admin` tinyint(4) DEFAULT NULL,
  `approved` tinyint(4) DEFAULT NULL,
  `jointime` datetime DEFAULT NULL,
  PRIMARY KEY (`user`,`group`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

# messeges inside groups
CREATE TABLE `messages` (
  `user` varchar(45) NOT NULL,
  `group` varchar(45) NOT NULL,
  `time` datetime NOT NULL,
  `text` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`user`,`group`,`time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


#user locations
CREATE TABLE `locations` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user` varchar(45) DEFAULT NULL,
  `lat` double DEFAULT NULL,
  `lon` double DEFAULT NULL,
  `time` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `time` (`time`),
  KEY `name` (`user`)
) ENGINE=InnoDB AUTO_INCREMENT=455 DEFAULT CHARSET=utf8;


# query the recent location 
CREATE VIEW `recent_loc` AS 
select `l1`.`user` AS `user`,
`l1`.`lat` AS `lat`,`l1`.`lon` AS `lon`,
cast(`l1`.`time` as date) AS `date`,
cast(`l1`.`time` as time) AS `time`,
`u`.`picurl` AS `picurl`,`g`.`group` AS `group` 
from ((`locations` `l1` join `user_groups` `g` on((`l1`.`user` = `g`.`user`))) 
join `users` `u` on((`l1`.`user` = `u`.`user`))) 
where ((`u`.`showplace` = 1) and 
		(`l1`.`time` = (select max(`l2`.`time`) 
		from `locations` `l2` where (`l1`.`user` = `l2`.`user`))));



