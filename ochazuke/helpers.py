#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Some helpers for the data processing section."""

import datetime
import json

from ochazuke import logging
from ochazuke.models import IssuesCount
from ochazuke.models import WeeklyTotal


def get_days(from_date, to_date):
    """Create the list of dates spanning two dates.

    A date is a string 'YYYY-MM-DD'
    A date is considered to be starting at 00:00:00.
    An invalid date format should be ignored and return None.
    The same from_date and to_date should return from_date.
    """
    date_format = "%Y-%m-%d"
    try:
        start = datetime.datetime.strptime(from_date, date_format)
        end = datetime.datetime.strptime(to_date, date_format)
        # we assume that the person is requesting one day
        if start == end:
            return [from_date]
    except Exception:
        return None
    else:
        dates = []
        delta = end - start
        days = delta.days
        if days < 0:
            end = start
            days = abs(days)
        for n in range(0, days + 1):
            new_date = end - datetime.timedelta(days=n)
            dates.append(new_date.strftime(date_format))
    return dates


def get_timeline_slice(timeline, dates_list):
    """Return a partial timeline including only a predefined list of dates."""
    sliced_data = [
        dated_data
        for dated_data in timeline
        if dated_data["timestamp"][:10] in dates_list
    ]
    return sliced_data


def get_json_slice(timeline, from_date, to_date):
    """Return a partial JSON timeline."""
    dates = get_days(from_date, to_date)
    full_data = json.loads(timeline)
    partial_data = get_timeline_slice(full_data["timeline"], dates)
    full_data["timeline"] = partial_data
    return json.dumps(full_data)


def is_valid_args(args):
    """Check if the arguments we receive are valid."""
    if args:
        try:
            from_date = args["from"]
            to_date = args["to"]
        except Exception:
            return False
        try:
            date_format = "%Y-%m-%d"
            datetime.datetime.strptime(from_date, date_format)
            datetime.datetime.strptime(to_date, date_format)
        except Exception:
            return False
        else:
            return True
    return False


def is_valid_category(category):
    """Check if the category is acceptable."""
    VALID_CATEGORY = [
        "needsdiagnosis",
        "needstriage",
        "needscontact",
        "contactready",
        "sitewait",
    ]
    if category in VALID_CATEGORY:
        return True
    return False


def normalize_date_range(from_date, to_date):
    """Add a day to the to_date so dates are inclusive in a database query.

    A date is a string 'YYYY-MM-DD'
    A date is considered to be starting at 00:00:00.
    An invalid date format should be ignored and return None.
    The same from_date and to_date should return from_date.
    """
    date_format = "%Y-%m-%d"
    try:
        start = datetime.datetime.strptime(from_date, date_format)
        end = datetime.datetime.strptime(to_date, date_format)
    except Exception:
        return None
    else:
        end = end + datetime.timedelta(days=1)
        end_date = end.strftime(date_format)
        start_date = start.strftime(date_format)
    return start_date, end_date


def get_timeline_data(category, start, end):
    """Query the data in the DB for a defined category."""
    # Extract the list of issues
    date_range = IssuesCount.timestamp.between(start, end)
    logging.info("DATE_RANGE {}".format(date_range))
    category_issues = IssuesCount.query.filter_by(milestone=category)
    logging.info("CATEGORY {}".format(category_issues))
    issues_list = (
        category_issues.filter(date_range).order_by(IssuesCount.timestamp.asc()).all()
    )
    logging.info("ISSUES {}".format(issues_list))
    timeline = [
        {"count": issue.count, "timestamp": issue.timestamp.isoformat() + "Z"}
        for issue in issues_list
    ]
    return timeline


def get_weekly_data(start, end):
    """Query the data in the DB for weekly bug counts."""
    # Extract the list of issues
    date_range = WeeklyTotal.monday.between(start, end)
    msg = (
        "DATE_RANGE {dr}, where timestamp_1 = {t1}" " and timestamp_2 = {t2}"
    ).format(dr=date_range, t1=start, t2=end)
    logging.info(msg)
    reports_list = (
        WeeklyTotal.query.filter(date_range).order_by(WeeklyTotal.monday.asc()).all()
    )
    logging.info("REPORTS {}".format(reports_list))
    timeline = [
        {"count": report.count, "timestamp": report.monday.isoformat() + "Z"}
        for report in reports_list
    ]
    return timeline
