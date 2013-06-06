<?php
include("global.php");

$firstName=$_POST['firstName'];
$lastName=$_POST['lastName'];
$phone=$_POST['phone'];
$email=$_POST['email'];

$dblink = connect_db();

$query = "INSERT INTO contact (first_name,last_name,phone,email) VALUES ('$firstName','$lastName','$phone','$email')";
db_query($query);
disconnect_db($dblink);
header("Location: index.php")
?>

