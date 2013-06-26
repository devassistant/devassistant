<html>
<?php
    include("global.php");
    error_reporting(E_ALL);
?>
    <body>
        <?php
            $dblink = connect_db();
            $result = db_query("SELECT * FROM contact");
            $num=mysql_numrows($result);
            disconnect_db($dblink);
            if ($num>0)
            {
                echo "<b><center>List of contacts:</center></b><br>";
                echo "<table border=\"1\"><th>First name</th><th>Surname</th><th>Phone</th><th>Email</th>";

                $i=0;
                while ($i < $num)
                {
                    $firstName=mysql_result($result,$i,"first_name");
                    if ($firstName == "")
                    {
                        $i++;
                        continue;
                    }
                    echo "<tr>";
                    $lastName=mysql_result($result,$i,"last_name");
                    $phone=mysql_result($result,$i,"phone");
                    $email=mysql_result($result,$i,"email");
                    echo "<td><b>";
                    echo $firstName;
                    echo "</b></td>";
                    echo "<td><b>";
                    echo "$lastName";
                    echo "</b></td>";
                    echo "<td>".$phone."</td>";
                    echo "<td>".$email."</td>";
                    $i++;
                    echo "</tr>";

                };
                echo "</table>";
                echo "<hr>";
            }

        ?>
<form action="insert.php" method="post">
First Name: <input type="text" name="firstName"><br>
Last Name: <input type="text" name="lastName"><br>
Phone: <input type="text" name="phone"><br>
E-mail: <input type="text" name="email"><br>
<input type="submit">
</form>
</body>
</html>
