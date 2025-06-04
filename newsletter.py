#!/usr/bin/env python3

"""
This program is designed to send our regular newsletter[1] to a list of
students. Its essentially a mass-mailing script with defaults that fit our
needs.

This script is written in pure python 3

[1] http://fsinf.at/newsletter

Copyright 2009, 2010 Mathias Ertl
Copyright 2021 David Kaufmann

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

import argparse
# import subprocess
import sys
import time
import smtplib
import csv
from email.message import EmailMessage
from email.policy import SMTPUTF8
from email.utils import formataddr
import jinja2

parser = argparse.ArgumentParser(
    description='Newsletter sending script.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-s', '--subject', default='Newsletter der Fachschaft Informatik',
                    help="Subject of the mail")
parser.add_argument('-f', '--from', dest='frm', default='Fachschaft Informatik <fsinf@fsinf.at>',
                    help="From header of the mail")
parser.add_argument('-t', '--to', default='noreply@fsinf.at',
                    help="To header of the mail. The addresses will receive the mail mulitiple times if the number of recipients is larger than --count.")
parser.add_argument('--recipients', default="recipients.txt", metavar="FILE",
                    help="A file that lists all the recipients, one on each line")
parser.add_argument('--blacklist', default="blacklist.txt", metavar="FILE",
                    help="A file that lists all the recipients that no longer want to receive this newsletter - same format as the \"recipients\" parameter")
parser.add_argument('--newsletter', default="newsletter.txt", metavar="FILE",
                    help="A file containing the text for this newsletter")
parser.add_argument('--header', default="header.txt", metavar="FILE",
                    help="A file containing a header prefixed to every newsletter")
parser.add_argument('--no-header', action='store_true', default=False,
                    help="Do not prefix this newsletter with a header")
parser.add_argument('--footer', default="footer.txt", metavar="FILE",
                    help="A file containing a footer suffixed to every newsletter")
parser.add_argument('--no-footer', action='store_true', default=False,
                    help="Do not suffix this newsletter with a footer")
parser.add_argument('--print-mail', action='store_true', default=False,
                    help="Print the mail as it would be send and exit.")
parser.add_argument('--count', default=100, type=int, metavar='N',
                    help="Send to N recipients at once")
parser.add_argument('--sleep', default=120, type=int, metavar='SECS',
                    help="Sleep SECS seconds before sending the next mail")
parser.add_argument('--dry-run', default=False, action="store_true",
                    help="Don't really send mail, only act like it")
parser.add_argument('--personalized', default=False, action="store_true",
                    help="Send one mail per address, allow parameter line[0..x] for message, put address in TO header, implies count=1")
args = parser.parse_args()

# read files
with open(args.recipients, encoding="utf-8", newline='') as f:
    reader = csv.reader(f, delimiter=',', quotechar='"')
    recipients = list(reader)

with open(args.blacklist, encoding="utf-8") as f:
    blacklist = f.read().splitlines()

environment = jinja2.Environment()
with open(args.newsletter, 'r', encoding="utf-8") as f:
    template = environment.from_string(f.read())

header, footer = "", ""
if not args.no_header:
    with open(args.header, 'r', encoding="utf-8") as f:
        header = f.read()
if not args.no_footer:
    with open(args.footer, 'r', encoding="utf-8") as f:
        footer = f.read()

if args.personalized:
    args.count = 1

# remove email addresses contained in blacklist
for entry in blacklist:
    recipients = [r for r in recipients if entry not in r]

offset = 0
while offset < len(recipients):
    # print number of addresses still to handle and clear line
    print(f"Mails to send: {len(recipients) - offset}\u001b[0K", end="\r")
    sys.stdout.flush()

    mail = EmailMessage(policy=SMTPUTF8)

    mail.add_header("From", args.frm)

    if args.personalized:
        newsletter = template.render(line=recipients[offset])
        cur = recipients[offset]
        mail.add_header("To", formataddr((f"{cur[2]} {cur[1]}", cur[3])))
        print(mail["To"])
    else:
        newsletter = template.render()
        mail.add_header("To", args.to)

        # add recipients to bcc (first field contains email address)
        bcc_list = recipients[offset:][:args.count][0]
        mail.add_header("Bcc", ', '.join(bcc_list))

    mail.add_header("Subject", args.subject)
    mail.add_header("MIME-Version", "1.0")

    # quoted-printable is still more common, but we have upstream autoconvert, so stick to utf8
    mail.set_content(f"{header}{newsletter}{footer}", charset="utf-8", cte="8bit")

    if args.print_mail:
        print(mail)
        sys.exit()

    if not args.dry_run:
        smtp = smtplib.SMTP("localhost")
        smtp.send_message(mail)

    # increment counter
    offset += args.count
    time.sleep(args.sleep)

# print "Done" and clear line
print("Done.\u001b[0K")
