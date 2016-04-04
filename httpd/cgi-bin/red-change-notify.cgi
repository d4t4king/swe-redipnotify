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

my (%cgiparams,%redchangesettings);
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

$cgiparams{'ACTION_ADMIN'} = '';
$cgiparams{'ACTION_DIAL'} = '';

&getcgihash(\%cgiparams);
$rtnToken = $cgiparams{'Token'};

&readhash("$swroot/mods/redipnotify/settings", \%redchangesettings);

if ($cgiparams{'ACTION_ADMIN'} eq $tr{'save'} or $cgiparams{'ACTION_DIAL'} eq $tr{'save'})
{
	# Validate $rtnToken, then compare it with $newToken and $lastToken
	if ($rtnToken !~ /[0-9a-f]/ or ($rtnToken != $newToken and $rtnToken != $lastToken))
	{
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

		&openpage($tr{'change passwords'}, 1, '', 'maintenance');
		&openbigbox('100%', 'LEFT');
		&alertbox($errormessage);
		print "<p style='margin:0'>&nbsp;</p>\n";
		&closebigbox;
		&closepage;

		exit;
	}
}

&showhttpheaders();

if ($cgiparams{'ACTION_ADMIN'} eq $tr{'save'})
{
	my $password1 = $cgiparams{'ADMIN_PASSWORD1'};
	my $password2 = $cgiparams{'ADMIN_PASSWORD2'};
	if ($password1 eq $password2)
	{
		if ($password1 =~ m/\s|\"/)
		{
			$errormessage .= $tr{'password contains illegal characters'} ."<br />\n";
		}
		elsif (length($password1) >= 6)
		{
			system('/usr/sbin/htpasswd', '-m', '-b', "${swroot}/auth/users", 'admin', "${password1}");
			&log($tr{'admin user password has been changed'});
		}
		else
		{
			$errormessage .= $tr{'passwords must be at least 6 characters in length'} ."<br />\n";
		}
	}
	else
	{
		$errormessage = $tr{'passwords do not match'} ."<br />\n";
	}
}

if ($cgiparams{'ACTION_DIAL'} eq $tr{'save'})
{
	my $password1 = $cgiparams{'DIAL_PASSWORD1'};
	my $password2 = $cgiparams{'DIAL_PASSWORD2'};
	if ($password1 eq $password2)
	{
		if($password1 =~ m/\s|\"/)
		{
			$errormessage = $tr{'password contains illegal characters'} ."<br />\n";
		}
		elsif (length($password1) >= 6)
		{
			system('/usr/sbin/htpasswd', '-m', '-b', "${swroot}/auth/users", 'dial', "${password1}");
			&log($tr{'dial user password has been changed'});
		}
		else
		{
			$errormessage = $tr{'passwords must be at least 6 characters in length'} ."<br />\n";
		}
	}
	else
	{
		$errormessage = $tr{'passwords do not match'} ."<br />\n";
	}
}

&openpage($tr{'rcn page title: red change notification'}, 1, '', 'maintenance');

&openbigbox('100%', 'LEFT');

&alertbox($errormessage);

print "<form method='post'>\n";
print "  <input type='hidden' name='Token' value='$newToken'>\n";

&openbox($tr{'rcn box title: red change notification'});
print <<END;
	<table width='100%' border="0">
		<tr>
			<td width='30%' class='base'>$tr{'rcnEnable'}</td>
			<td width='15%'>
				<input type="checkbox" id="cbxRCNEnable" name="cbxRCNEnable" />
			</td>
			<td width='25%' class='base'>$tr{'rcnddlMethod'}</td>
			<td width='20%'>
				<select name="ddlRCNMethod" id="ddlRCNMethod" value="$redchangesettings{'notify_method'}">
					<option value="">&nbsp;</option>
END
	if ($redchangesettings{'notify_method'} eq "email") {
		print "\t\t\t\t\t<option value=\"email\" selected>Email</option>\n";
		print "\t\t\t\t\t<option value=\"ssh\">SSH</option>\n";
	} elsif ($redchangesettings{'notify_method'} eq "ssh") {
		print "\t\t\t\t\t<option value=\"email\">Email</option>\n";
		print "\t\t\t\t\t<option value=\"ssh\" selected>SSH</option>\n";
	} else {
		print "\t\t\t\t\t<option value=\"email\">Email</option>\n";
		print "\t\t\t\t\t<option value=\"ssh\">SSH</option>\n";
		$errormessage = "Unrecognized notification method!";
	}
print <<END;

				</select>
			</td>
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
							<input type="checkbox" id="cbxRCNSSL" name="cbxRCNSSL" />
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
			<td class='base'>$tr{'rcnSSHServer'}</td>
			<td>
				<input type="text" size="25" id="txtRCNSSHServer" name="txtRCNSSHServer" value="$redchangesettings{'ssh_server'}" />
			</td>
			<td class='base'>$tr{'rcnSSHPort'}</td>
			<td>
				<input type="text" size="5" id="txtRCNSSHPort" name="txtRCNSSHPort" value="$redchangesettings{'ssh_port'}" />
			</td>
		</tr>
		<tr>
			<td class='base'>$tr{'rcnSSHAuthUser'}</td>
			<td>
				<input type="text" size="25" id="txtRCNSSHAuthUser" name="txtRCNSSHAuthUser" value="$redchangesettings{'ssh_auth_user'}" />
			</td>
			<td class="base">$tr{'rcnSSHAuthKey'}</td>
			<td>
				<input type="text" id="txtRCNSSHAuthKey" name="txtRCNSSHAuthKey" value="$redchangesettings{'ssh_auth_key'}" />
			</td>
		</tr>
		<tr>
			<td class='base' width="30%">&nbsp;</td>
			<td colspan="3" width='60%'><input type='submit' name='ACTION_ADMIN' value='$tr{'save'}'></td>
		</tr>
	</table>
END

&closebox();

print "</form>\n";

&alertbox('add', 'add');

&closebigbox();

&closepage();
