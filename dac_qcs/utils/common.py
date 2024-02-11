# Copyright (c) 2024, Quark Cyber Systems and contributors
# For license information, please see license.txt

from datetime import datetime


def formatted_time(time):
    """ Function to format string to datetime """
    string_time = str(time)
    trimmed_time = string_time.split(".")[0]
    format_time = datetime.strptime(str(trimmed_time), "%H:%M:%S")
    return format_time
