<?php
    define("SQL_HOST", "localhost");
    define("SQL_DBNAME", "devassistant_table");
    define("SQL_USERNAME", "devassistant");
    define("SQL_PWD", "devassistant");

    function connect_db()
    {
        $dblink = @mysql_connect (SQL_HOST, SQL_USERNAME, SQL_PWD) or die ("Cannot connect to MySQL DB:".mysql_error());
        mysql_select_db(SQL_DBNAME) or die ("Cannot select database".mysql_error());
        return $dblink;
    }

    function db_query($sql)
    {
        $result = mysql_query($sql) or die(mysql_error());
        return $result;
    }

    function disconnect_db($dblink)
    {
        mysql_close($dblink);
    }
?>
