<html>
<body>
Server IP addresses:
<?php
$output = shell_exec('ip a|grep "inet "| grep -v "127.0.0.1"| awk \'{print $2}\'');
echo "<pre>$output</pre>";
?>

</body>
</html>
