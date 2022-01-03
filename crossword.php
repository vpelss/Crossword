<?php
// the facebook client library
include_once '../../client/facebook.php';

// this defines some of your basic setup
include_once 'config.php';

$facebook = new Facebook($api_key, $secret);
$facebook->require_frame();
$user = $facebook->require_login();

function getvar($name)
	{
    global $_GET, $_POST;
    if (isset($_GET[$name])) return $_GET[$name];
    else if (isset($_POST[$name])) return $_POST[$name];
    else return false;
	}
?>
<fb:dashboard></fb:dashboard>
<fb:tabs>  
<fb:tab-item href='?action=new' title='New Crossword'/>  
<fb:tab-item href='?action=invite' title='Invite Friends - deletes current crossword' />  
</fb:tabs>
<?
$addfriends = "
<fb:request-form action='$AppLink' method='POST' invite='true' type='$AppName'
content='Add the $AppName. After you ALLOW ACCESS for this application, a small bookmark icon will appear at the bottom of the Facebook page. <b>You must click on it to Bookmark it.</b> (This is a feature of the New Facebook)
<fb:req-choice url=\"http://www.facebook.com/apps/application.php?id=$AppIdCode\" label=\"Install\" />'>
<fb:multi-friend-selector unselected_rows='4' showborder='false' actiontext='Invite your friends to use this application.' />
<fb:request-form-submit />
</fb:request-form>
";

$runme ="<fb:iframe src='$FrameLink' width='760' height='2000'></fb:iframe>";

if (getvar("action") == 'invite')
	{
	 echo $addfriends;
	 }
else
	{
	 echo $runme;
	 }	
?>	
    
