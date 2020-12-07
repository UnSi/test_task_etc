import calendar
import datetime
from datetime import timedelta

from flask import Flask
from notion.block import *
from notion.client import NotionClient

app = Flask(__name__)


def plus_month(day):
    return day + timedelta(days=calendar.monthrange(day.year, day.month)[1])


def calculate_due_day(row):
    freq = {
        0: r'Daily',
        1: r'3t/w',
        2: r'2t/w',
        3: r'1t/w',
        4: r'1t/2w',
        5: r'2t/m',
        6: r'1t/m',
        7: r'1t/2m',
        8: r'1t/3m',
    }

    dates = {
        "Mo": 0,
        "Tue": 1,
        "Wed": 2,
        "Thu": 3,
        "Fri": 4,
        "Sat": 5,
        "Sun": 6,
    }

    start_day = row.due_date.start

    # looking for frequency
    days = []
    period = ''

    for item in row.periodicity:
        if item in freq.values():
            period = item
        else:
            days.append(item)

    if not period:
        return

    next_day = -1
    if days:
        day_int_list = sorted([dates[i] for i in days])
        for day in day_int_list:
            if day > start_day.weekday():
                next_day = day
                break
        if next_day == -1:
            next_day = day_int_list[0]
    else:
        next_day = start_day.weekday()

    delta = next_day - start_day.weekday() if next_day > start_day.weekday() else 7 - start_day.weekday() + next_day

    if period == freq[0]:
        row.due_date = row.set_date = start_day + timedelta(days=1)
        row.status = "TO DO"
        return

    elif period.find(r'/w') != -1:
        row.due_date = start_day + timedelta(days=delta)
        row.set_date = row.due_date.start - timedelta(days=1)
        row.status = "TO DO"

    elif period == freq[4]:
        row.due_date = start_day + timedelta(days=delta+7)
        row.set_date = row.due_date.start - timedelta(days=7)
        row.status = "TO DO"

    elif period == freq[5]:
        month_days = calendar.monthrange(start_day.year, start_day.month)[1]//2
        month_days += 7 - (month_days % 7)

        row.due_date = start_day + timedelta(days=month_days-7+delta)
        row.set_date = row.due_date.start - timedelta(days=7)
        row.status = "TO DO"

    elif period == freq[6]:
        month_days = calendar.monthrange(start_day.year, start_day.month)[1]
        month_days += 7 - (month_days % 7)

        row.due_date = start_day + timedelta(days=month_days-7+delta)
        row.set_date = row.due_date.start - timedelta(days=7)
        row.status = "TO DO"

    elif period == freq[7]:
        second_month_day = plus_month(start_day)
        month_days = 0
        for day in (start_day, second_month_day):
            month_days += calendar.monthrange(day.year, day.month)[1]
        month_days += 7 - (month_days % 7)

        row.due_date = start_day + timedelta(days=month_days-7+delta)
        row.set_date = row.due_date.start - timedelta(days=14)
        row.status = "TO DO"

    elif period == freq[7]:
        second_month_day = plus_month(start_day)
        third_month_day = plus_month(second_month_day)
        month_days = 0
        for day in (start_day, second_month_day, third_month_day):
            month_days += calendar.monthrange(day.year, day.month)[1]
        month_days += 7 - (month_days % 7)

        row.due_date = start_day + timedelta(days=month_days-7+delta)
        row.set_date = row.due_date.start - timedelta(days=14)
        row.status = "TO DO"

    return


@app.route("/update_todo_desk", methods=["GET"])
def test_todo_desk():
    TOKEN = '12828fc2a49d4301f495c09c4532089219a1d48db6bcffb301b1b308d895ce70e98197c5b1d4e0da6b2bb5d497da10241140a47f959ffe484941472dfda2719c35a8804fb68e35f2b36689ae47be'
    NOTION = "https://www.notion.so/f8e9e4d17e7d4e7696595a8d56948f3b?v=d938f8f324374cf9a41ae129ebfe0301"
    today = datetime.datetime.now().date()

    client = NotionClient(TOKEN)
    cv = client.get_collection_view(NOTION)

    filter_params = {
        "filters": [
            {
                "filter": {"value": {"type": "exact", "value": "DONE"}, "operator": "enum_is"},
                "property": "Status",
            }
        ]
    }

    current_rows = cv.collection.get_rows(filter=filter_params)
    for row in current_rows:
        if row.set_date.start > today:
            continue

        if row.set_date.start < today:
            calculate_due_day(row)
        elif row.set_date.start == today:
            row.status = "TO DO"

    return 'ok'


if __name__ == "__main__":
    app.debug = True
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
