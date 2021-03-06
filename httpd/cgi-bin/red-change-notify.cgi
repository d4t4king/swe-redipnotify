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

# Get CGI hash now because we need to get the token
&getcgihash(\%cgiparams);

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

$rtnToken = $cgiparams{'Token'};

# Validate the security token
if ((defined $cgiparams{'btnSave'}) and ($cgiparams{'btnSave'} eq $tr{'save'})) {
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

		&openpage($tr{'rcn page title red change notification'}, 1, '', 'about');
		&openbigbox('100%', 'LEFT');
		&alertbox($errormessage);
		print "<p style='margin:0'>&nbsp;</p>\n";
		&closebigbox;
		&closepage;

		exit;
	}
}

# Read the settings file and set defaults as needed (like if the file is empty)
&readhash("$swroot/mods/redipnotify/settings", \%redchangesettings);
if ((not defined($redchangesettings{'notify_enable'})) or ($redchangesettings{'notify_enable'} eq '')) {
	$redchangesettings{'notify_enable'} = 'off'
}
if ((not defined($redchangesettings{'email_ssl'})) or ($redchangesettings{'email_ssl'} eq '')) {
	$redchangesettings{'email_ssl'} = 'off'
}
# **** FIX ME ****
# Can't print here because we haven't sent the HTTP headers yet.  But if
# we put this output in $errormessage, it won't write to the settings config
# file.
#print "<pre>Pre-save, %redchangesettings<br />". Dumper(\%redchangesettings) ."</pre>\n";

# Take actions before processing
if ((defined($cgiparams{'btnSave'})) and ($cgiparams{'btnSave'} eq 'Save')) {
	if ((defined($cgiparams{'cbxRCNEnable'})) and ($cgiparams{'cbxRCNEnable'} eq 'on')) {
		$redchangesettings{'notify_enable'} = 'on';
		#system("sed -i -e 's/^#//' /var/smoothwall/mods/redipnotify/etc/crontab");
		system("echo \"0/30 * * * * /var/smoothwall/mods/redipnotify/red-change-notify.pl > /dev/null\" > /var/smoothwall/mods/redipnotify/etc/crontab");
	} else {
		$redchangesettings{'notify_enable'} = 'off';
		system("echo -n > /var/smoothwall/mods/redipnotify/etc/crontab");
	}
	if (defined $cgiparams{'cbxRCNSSL'} and $cgiparams{'cbxRCNSSL'} eq 'on') {
		$redchangesettings{'email_ssl'} = 'on';
	} else {
		$redchangesettings{'email_ssl'} = 'off';
	}

	$redchangesettings{'email'} = $cgiparams{'txtRCNEmailAddr'};
	$redchangesettings{'email_smtp_server'} = $cgiparams{'txtRCNEmailServer'};
	$redchangesettings{'email_smtp_port'} = $cgiparams{'txtRCNEmailPort'};
	$redchangesettings{'email_auth_user'} = $cgiparams{'txtRCNEmailAuthUser'};
	$redchangesettings{'email_auth_password'} = $cgiparams{'txtRCNEmailAuthPass'};
	unless ($errormessage) {
		&writehash("$swroot/mods/redipnotify/settings", \%redchangesettings);
	}
	# Can't print here, because we haven't set the HTTP headers yet.
	#print "<pre>In save, %redchangesettings<br />". Dumper(\%redchangesettings) ."</pre>\n";
}

# Set the 'checked' values now that the settings are correct
$checked{'cbxRCNEnable'}{'on'} = '';
$checked{'cbxRCNEnable'}{'off'} = '';
$checked{'cbxRCNEnable'}{$redchangesettings{'notify_enable'}} = 'checked="checked"';
$checked{'cbxRCNSSL'}{'on'} = '';
$checked{'cbxRCNSSL'}{'off'} = '';
$checked{'cbxRCNSSL'}{$redchangesettings{'email_ssl'}} = 'checked="checked"';
#$errormessage .= "<pre>Post chkbox assure, %checked<br />". Dumper(\%checked) ."</pre>";


# And finally render the page
&showhttpheaders();

&openpage($tr{'rcn page title red change notification'}, 1, '', 'maintenance');

&openbigbox('100%', 'LEFT');

&alertbox($errormessage);

print "<form method='post' action=\"$ENV{'SCRIPT_NAME'}\">\n";
print "  <input type='hidden' name='Token' value='$newToken'>\n";

&openbox($tr{'rcn box title red change notification'});
print <<END;
	<table width='100%' border="0">
		<tr>
			<td width='30%' class='base'>$tr{'rcnEnable'}</td>
			<td width='15%'>
				<input type="checkbox" id="cbxRCNEnable" name="cbxRCNEnable" $checked{'cbxRCNEnable'}{'on'}} />
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
							<input type="checkbox" id="cbxRCNSSL" name="cbxRCNSSL" $checked{'cbxRCNSSL'}{'on'}} />
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
				<input type="password" id="txtRCNEmailAuthPass" name="txtRCNEmailAuthPass" value="$redchangesettings{'email_auth_password'}" />
			</td>
		</tr>
		<tr>
			<td class='base' width="30%">&nbsp;</td>
			<td colspan="3" width='60%'><input type='submit' id='btnSave' name='btnSave' value='$tr{'save'}'></td>
		</tr>
	</table>
END

#&openbox($tr{'rcnDebug'});
#print "<h3>\%cgiparams</h3>\n";
#print "<pre>\n";
#print Dumper(\%cgiparams);
#print "</pre>\n";
#print "<hr />\n";
#print "<h3>\%redchangesettings</h3>\n";
#print "<pre> \n";
#print Dumper(\%redchangesettings);
#print "</pre>\n";
#print "<hr />\n";
#print "<h3>\%checked</h3>\n";
#print "<pre> \n";
#print Dumper(\%checked);
#print "</pre>\n";
#&closebox();

&closebox();

print "</form>\n";

&alertbox('add', 'add');

&closebigbox();

&closepage();
