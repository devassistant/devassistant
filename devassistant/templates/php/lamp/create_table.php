<?php
$database="devassistant_table";
mysql_connect('localhost', 'devassistant', 'devassistant');
@mysql_select_db($database) or die ("Unable to select database\n");
$query = "CREATE TABLE contact (id int(6) NOT NULL auto_increment, first_name varchar(255) NOT NULL, last_name varchar(255) NOT NULL, phone varchar(20) NOT NULL, email varchar(255), PRIMARY KEY (id), UNIQUE id (id))";
mysql_query($query) or die ("Unable to create table in database\n".mysql_error()."\n");
mysql_close();
?>
