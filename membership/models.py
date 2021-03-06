import csv
import json

from dateutil.parser import parse as parse_datetime
from dateutil.tz import tzoffset
from django.db import models


class Member(models.Model):
    timestamp = models.DateTimeField()
    name = models.CharField(max_length=255, blank=False)
    knights_email = models.EmailField(unique=True, blank=False)
    preferred_email = models.EmailField(unique=True, blank=False)
    paid_dues = models.BooleanField(default=False)
    shirt_size = models.CharField(max_length=3)
    shirt_gender = models.CharField(max_length=1)
    json = models.TextField()


def determine_paid_dues(data):
    return data['Payment Method'] != '' and data['Paid Dues'] == 'Y'


def update_membership(local_csv, timezone=tzoffset('EST', -1 * 5 * 60 * 60)):
    # {email: Member()}
    members = {}
    with open(local_csv, 'r', encoding='utf8') as csv_file:
        reader = csv.reader(csv_file)
        headings = next(reader)
        for row in reader:
            data = dict(zip(headings, row))
            if '' in data: del data['']
            # probably an empty row
            if not data['Timestamp']:
                continue
            timestamp = parse_datetime(data['Timestamp']).replace(
                tzinfo=timezone)
            name = '{} {}'.format(data['First Name'].capitalize(),
                                  data['Last Name'].capitalize())
            knights_email = data['UCF Student Email']
            preferred_email = data['Preferred Email Address']
            shirt_size = data['Shirt Size']
            shirt_gender = data['Shirt Gender']
            jdata = json.dumps(data)
            paid_dues = determine_paid_dues(data)

            try:
                member = Member.objects.get(knights_email=knights_email)
                member.preferred_email = preferred_email
                member.timestamp = timestamp
                member.name = name
                member.shirt_size = shirt_size
                member.shirt_gender = shirt_gender
                member.paid_dues = paid_dues
                member.json = jdata
            except Member.DoesNotExist:
                member = Member(timestamp=timestamp, name=name,
                                knights_email=knights_email,
                                preferred_email=preferred_email,
                                shirt_gender=shirt_gender,
                                shirt_size=shirt_size,
                                paid_dues=paid_dues, json=jdata)
            members[knights_email] = member

    for member in members.values():
        member.save()

    return members.values()
