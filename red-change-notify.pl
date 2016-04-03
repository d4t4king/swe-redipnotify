#!/usr/bin/perl -w

use strict;
use warnings;
use Term::ANSIColor;
use Data::Dumper;
use MIME::Lite;

use lib "/usr/lib/smoothwall/";
use header qw( :standard );

my %redipsettings;

my ($red_iface, $old_ip, $current_ip, $new_ip);

&readhash("$swroot/mods/red-change-notify/settings", \%redipsettings);

$old_ip = $redipsettings{'old_ip'} or die colored("[!] old_ip was not set in the settings file! \n", "bold red");

# get the RED iface
open RI, "<$swroot/red/iface" or die colored("[!] Can't open SW red IP iface file: $! \n", "bold red");
$red_iface = <RI>;
chomp($red_iface);
close RI or die colored("[!] There was a problem closing the SW red IP iface file: $! \n", "bold red");
if ((!defined($redipsettings{'red_iface'})) || ($redipsettings{'red_iface'} eq "")) {
	$redipsettings{'red_iface'} = $red_iface;
}
my $ip_line = `ip addr show $red_iface | grep "inet "`;
chomp($ip_line);
#inet 70.95.130.127/20 brd 255.255.255.255 scope global eth1
if ($ip_line =~ /\s+inet\s+([0-9.]+)\/\d+\s+/) { $new_ip = $1; }
else { die colored("[!] Didn't match `ip addr` regex! \n", "bold red"); }
$redipsettings{'new_ip'} = $new_ip;

# get the "expected" IP from the config files.
open LIS, "<$swroot/red/local-ipaddress" or die colored("[!] Can't open SW red IP file: $! \n", "bold red");
$current_ip = <LIS>;
chomp($current_ip);
close LIS or die colored("[!] There was a problem closing the SW red IP file: $! \n", "bold red");
if ((!defined($redipsettings{'current_ip'})) || ($redipsettings{'current_ip'} eq "")) {
	$redipsettings{'current_ip'} = $current_ip;
}

#print Dumper(%redipsettings);

if ($old_ip ne $new_ip) {
	my $msg = MIME::Lite->new(
		'From'		=>	'swe@dataking.us',
		'To'		=>	'admin@dataking.us',
		'Subject'	=>	'RED IP Change',
		'Data'		=>	"Red IP has changed.  \nOld IP: $old_ip \nCurrent IP: $current_ip \nNew IP: $new_ip \n",
	);

	$msg->send('smtp', $redipsettings{'email_smtp_server'}, $redipsettings{'email_auth_user'}, $redipsettings{'email_auth_password'});
}

&writehash("$swroot/mods/red-change-notify/settings", \%redipsettings);

