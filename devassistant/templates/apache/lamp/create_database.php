#!/usr/bin/php
<?php
if ($argc > 2){
?>
    Usage:
        Only one parameter is allowed
<?php
}
else
{
    if  ($argc == 1) {
        @mysql_connect('localhost', 'root', '') or die ("Cannot connect to MySQL DB:" . mysql_error());
    }
    else
    {
        $root_password = $argv[1];
        @mysql_connect('localhost', 'root', $root_password) or die ("Cannot connect to MySQL DB:" . mysql_error());
    }
    mysql_query("CREATE DATABASE devassistant_table;");
    mysql_query("CREATE USER 'devassistant'@'localhost' IDENTIFIED BY 'devassistant';");
    mysql_query("GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, INDEX, ALTER ON devassistant_table.* TO 'devassistant'@'localhost' IDENTIFIED BY 'devassistant';");
    mysql_query("FLUSH PRIVILEGES;");
    mysql_close();
}
?>
