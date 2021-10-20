import csv
import datetime
import os
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from attendance.models import AllotedLeave, LeaveType, Employee


class Command(BaseCommand):
    help = 'Import leaves from csv file, please check sample_import_leaves.csv, this command will be used at initial setup.'
    file_path = os.path.join(settings.BASE_DIR, "attendance", "management", "commands", "sample_import_leaves.csv")
    # def add_arguments(self, parser):
    #     parser.add_argument('poll_ids', nargs='+', type=int)

    def handle(self, *args, **options):
        with open(Command.file_path) as f:
            reader = csv.reader(f)
            # Extract/Pop/Remove header initialy
            header = next(reader)
            today = datetime.datetime.today().date()
            el_type = LeaveType.objects.filter(abbr='EL').first()
            sl_type = LeaveType.objects.filter(abbr='SL').first()

            for row in reader:
                empid = row[0]
                # name = row[1]
                el_count = float(row[2])
                sl_count = float(row[3])

                employee = Employee.objects.filter(empid=empid).first()
                if employee:
                    if el_type:
                        AllotedLeave.objects.allot_leaves(employee, today, el_type, el_count,
                                                          "Imported leaves from CSV")
                    if sl_type:
                        AllotedLeave.objects.allot_leaves(employee, today, sl_type, sl_count,
                                                          "Imported leaves from CSV")
