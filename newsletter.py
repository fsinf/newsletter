#!/usr/bin/python3

"""
This program is designed to send our regular newsletter[1] to a list of
students. Its essentially a mass-mailing script with defaults that fit our
needs.

This script is written in pure python 3 and requires no additional libraries
except a sendmail implementation.

[1] http://fsinf.at/newsletter

Copyright 2009, 2010 Mathias Ertl

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import os, sys, time, subprocess
from optparse import OptionParser

parser = OptionParser()
parser.add_option( '-s', '--subject', default='Newsletter der Fachschaft Informatik',
	help="Subject of the mail [default: %default]" )
parser.add_option( '-f', '--from', dest='frm', default='Fachschaft Informatik <fsinf@fsinf.at>',
	help="From-header of the mail [default: %default]" )
parser.add_option( '-t', '--to',
	help="Set the TO: header. The addresses will receive the mail mulitiple times if the number of recipients is larger than --count." )
parser.add_option( '--recipients', default="recipients.txt", metavar="FILE",
	help="A file that lists all the recipients, one on each line [default: %default]" )
parser.add_option( '--blacklist', default="blacklist.txt", metavar="FILE",
	help="A file that lists all the recipients that no longer want to receive this newsletter - same format as the \"recipients\" parameter [default: %default]" )
parser.add_option( '--newsletter', default="newsletter.txt", metavar="FILE",
	help="A file containing the text for this newsletter [default: %default]" )
parser.add_option( '--header', default="header.txt", metavar="FILE",
	help="A file containing a header prefixed to every newsletter [default: %default]" )
parser.add_option( '--no-header', action='store_true', default=False,
	help="Do not prefix this newsletter with a header [default: %default]" )
parser.add_option( '--footer', default="footer.txt", metavar="FILE",
	help="A file containing a footer suffixed to every newsletter [default: %default]" )
parser.add_option( '--no-footer', action='store_true', default=False,
	help="Do not suffix this newsletter with a footer [default: %default]" )
parser.add_option( '--print-mail', action='store_true', default=False,
	help="Print the mail as it would be send and exit." )
parser.add_option( '--count', default=200, type='int', metavar='N',
	help="Send to N recipients at once [default: %default]" )
parser.add_option( '--sleep', default=30, type='int', metavar='SECS',
	help="Sleep SECS seconds before sending the next mail" )
parser.add_option( '--dry-run', default=False, action="store_true",
	help="Don't really send mail, only act like it" )
options, args = parser.parse_args()

bcc_count = options.count

# read initial data - it is important that we do this right away so that we 
# fail if any data is missing *before* anything is send over the wire.
recipients = open( options.recipients ).read().split()
blacklist = open( options.blacklist ).read().split()
newsletter = open( options.newsletter, 'r' ).read()
header, footer = None, None
if not options.no_header:
	header = open( options.header, 'r' ).read()
if not options.no_footer:
	footer = open( options.footer, 'r' ).read()

# filter out those in blacklist (google "list-comprehension" if you don't
# understand the code)
recipients = [ x for x in recipients if x not in blacklist ]
#recipients = list( map( get_address, recipients ) )


mail_header = """From: """ + options.frm + """
Subject: """ + options.subject + """
Content-Type: text/plain; charset=utf-8
Content-Transfer-Encoding: 8bit
"""
if options.to:
	mail_header += "To: %s\n"%(options.to)

# assemble a mail:
def assemble_mail( bcc ):
	mail = mail_header + bcc + '\n'
	if not options.no_header:
		mail += header + '\n'
	mail += newsletter + '\n'
	if not options.no_footer:
		mail += footer
	return mail

if options.print_mail:
	bcc = "Bcc: <bcc addresses>\n"
	print( assemble_mail( bcc ) )
	sys.exit(0)

offset = 0
while offset < len( recipients ):
	print( '%s...' %( len( recipients ) - offset ), end=" " )
	sys.stdout.flush()

	if not options.dry_run:
		bcc_list = recipients[offset:][:bcc_count]
		bcc = 'Bcc: ' + ', '.join( bcc_list ) + "\n"
		mail = assemble_mail( bcc )

		sendmail = [ '/usr/sbin/sendmail', '-oi', '-t' ]
		p = subprocess.Popen( sendmail, stdin=subprocess.PIPE )
		stdout, stderr = p.communicate( mail.encode('utf_8') )

	# increment counter
	offset += bcc_count
	time.sleep( options.sleep )
