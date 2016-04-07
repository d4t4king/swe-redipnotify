#!/usr/bin/perl
#
# SmoothWall CGIs
#
# This code is distributed under the terms of the GPL
#
# (c) The SmoothWall Team

use lib "/usr/lib/smoothwall";
use Digest::SHA qw(sha1_hex);
use header qw( :standard );
use smoothtype qw( :standard );
use strict;
use warnings;
use Data::Dumper;

my (%cgiparams,%redchangesettings,%checked);
my $errormessage = "";
my ($lastToken, $newToken, $rtnToken);
my $tmp = "";

# Generate a new token and the previous token on each entry.
foreach my $token ("1","2","3")
{
  if (open TKN,"</usr/etc/token${token}.sum")
  {
    $tmp .= <TKN>;
    close TKN;
  }
  else
  {
    $errormessage .= "Can't read token${token}.<br />";
  }
}

my $time = time;
my $life = 30;   # seconds
my $toSum = $tmp . int($time/$life) ."\n";
$newToken = sha1_hex $toSum;
$toSum = $tmp . int($time/$life - 1) ."\n";
$lastToken = sha1_hex $toSum;

# Clear these, just in case
undef $time;
undef $toSum;
undef $tmp;

&getcgihash(\%cgiparams);
$rtnToken = $cgiparams{'Token'};

if ($cgiparams{'btnSave'} eq $tr{'save'}) {
	# Validate $rtnToken, then compare it with $newToken and $lastToken
	if (($rtnToken !~ /[0-9a-f]/) or (($rtnToken ne $newToken) and ($rtnToken ne $lastToken))) {
		$errormessage = "
Incorrect security token; returning to home page!<br /><br />
This happens when you wait too long to click an action button (Reboot/Shutdown/Save)<br />
to shut down or reboot the system or to change passwords.<br />
";
		print <<END;
Refresh: 6; url=/cgi-bin/index.cgi\r
Content-type: text/html\r
\r
END

		&openpage($tr{'rcn page title: red change notification'}, 1, '', 'about');
		&openbigbox('100%', 'LEFT');
		&alertbox($errormessage);
		print "<p style='margin:0'>&nbsp;</p>\n";
		&closebigbox;
		&closepage;

		exit;
	}
}

&readhash("$swroot/mods/redipnotify/settings", \%redchangesettings);

$checked{'cbxRCNEnable'}{'on'} = '';
$checked{'cbxRCNEnable'}{'off'} = '';
$checked{'cbxRCNEnable'}{$redchangesettings{'notify_enable'}} = 'checked';
$checked{'cbxRCNSSL'}{'on'} = '';
$checked{'cbxRCNSSL'}{'off'} = '';
$checked{'cbxRCNSSL'}{$redchangesettings{'email_ssl'}} = 'checked';

if ($cgiparams{'btnSave'} eq 'Save') {
	if ($cgiparams{'cbxRCNEnable'} eq 'on') {
		$redchangesettings{'notify_enable'} = 'on';
		system("sed -i -e 's/^#//' /var/smoothwall/mods/redipnotify/etc/crontab");
	} else {
		$redchangesettings{'notify_enable'} = 'off';
		system("sed -i -e 's/\(.*\)/#\1/' /var/smoothwall/mods/redipnotify/etc/crontab");
	}

	$redchangesettings{'email'} = $cgiparams{'txtRCNEmailAddr'};
	$redchangesettings{'email_smtp_server'} = $cgiparams{'txtRCNEmailServer'};
	$redchangesettings{'email_smtp_port'} = $cgiparams{'txtRCNEmailPort'};
	$redchangesettings{'email_auth_user'} = $cgiparams{'txtRCNEmailAuthUser'};
	$redchangesettings{'email_auth_password'} = $cgiparams{'txtRCNEmailAuthPass'};
	$redchangesettings{'email_ssl'} = $checked{'cbxRCNSSL'}{$cgiparams{'cbxRCNSSL'}};
	unless ($errormessage) {
		&writehash("$swroot/mods/redipnotify/settings", \%redchangesettings);
	}
}

&showhttpheaders();


&openpage($tr{'rcn page title: red change notification'}, 1, '', 'maintenance');

&openbigbox('100%', 'LEFT');

&alertbox($errormessage);

print "<form method='post' action=\"$ENV{'SCRIPT_NAME'}\">\n";
print "  <input type='hidden' name='Token' value='$newToken'>\n";

&openbox($tr{'rcn box title: red change notification'});
print <<END;
	<table width='100%' border="0">
		<tr>
			<td width='30%' class='base'>$tr{'rcnEnable'}</td>
			<td width='15%'>
				<input type="checkbox" id="cbxRCNEnable" name="cbxRCNEnable" $checked{'cbxRCNEnable'}{$redchangesettings{'notify_enable'}} />
			</td>
			<td width='45%' class='base' colspan='2'>&nbsp;</td>
		</tr>
		<tr>
			<td class='base'>$tr{'rcnEmailAddr'}</td>
			<td colspan='3'>
				<input type="text" size="45" id="txtRCNEmailAddr" name="txtRCNEmailAddr" value="$redchangesettings{'email'}" />
			</td>
		</tr>
		<tr>
			<td class='base'>$tr{'rcnEmailServer'}</td>
			<td>
				<input type="text" size="25" id="txtRCNEmailServer" name="txtRCNEmailServer" value="$redchangesettings{'email_smtp_server'}" />
			</td>
			<td colspan='2'>
				<table width="100%" border="0">
					<tr>
						<td class='base'>$tr{'rcnEmailPort'}</td>
						<td>
							<input type="text" size="5" id="txtRCNEmailPort" name="txtRCNEmailPort" value="$redchangesettings{'email_smtp_port'}" />
						</td>
						<td class='base' width="12.5%">$tr{'rcnEmailSSL'}</td>
						<td width="7%">
							<input type="checkbox" id="cbxRCNSSL" name="cbxRCNSSL" $checked{'cbxRCNSSL'}{$redchangesettings{'email_ssl'}} />
						</td>
					</tr>
				</table>
			</td>
		</tr>
		<tr>
			<td class='base'>$tr{'rcnEmailAuthUser'}</td>
			<td>
				<input type="text" size="25" id="txtRCNEmailAuthUser" name="txtRCNEmailAuthUser" value="$redchangesettings{'email_auth_user'}" />
			</td>
			<td class="base">$tr{'rcnEmailAuthPass'}</td>
			<td>
				<input type="text" id="txtRCNEmailAuthPass" name="txtRCNEmailAuthPass" value="$redchangesettings{'email_auth_password'}" />
			</td>
		</tr>
		<tr>
			<td class='base' width="30%">&nbsp;</td>
			<td colspan="3" width='60%'><input type='submit' id='btnSave' name='btnSave' value='$tr{'save'}'></td>
		</tr>
	</table>
END

&openbox($tr{'rcnDebug'});
print "<h3>\%cgiparams</h3>\n";
print "<pre>\n";
print Dumper(\%cgiparams);
print "</pre>\n";
print "<hr />\n";
print "<h3>\%redchangesettings</h3>\n";
print "<pre> \n";
print Dumper(\%redchangesettings);
print "</pre>\n";
&closebox();

&closebox();

print "</form>\n";

&alertbox('add', 'add');

&closebigbox();

&closepage();
