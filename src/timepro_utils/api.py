import re
from datetime import datetime, date, timedelta

from dateutil.relativedelta import relativedelta, MO, FR
from requests_html import HTMLSession

from .timesheet import Timesheet


class LoginException(Exception):
    pass


class TimesheetAPI:
    LOGIN_URL = 'https://www.timesheets.com.au/tplogin/default.asp'
    VIEW_TIMESHEET_URL = 'https://www.timesheets.com.au/tp60/ViewTimeSheet.asp'
    INPUT_TIME_URL = 'https://www.timesheets.com.au/tp60/InputTime.asp'

    def __init__(self):
        self.session = HTMLSession()
        self.user_context_id = None
        self.staff_id = None
        self.logged_in = False

    def _parse_html_login_errors(self, error_table):
        error_tds = error_table.xpath('//img[@src="images/invalid.png"]/ancestor::tr[1]/td[2]')
        return [e.text for e in error_tds]

    def _parse_html_options(self, html, option_name, selected=False):
        if selected:
            options = (
                html.xpath(f'//select[@name="{option_name}"]//option[@selected]') or
                html.xpath(f'//input[@name="{option_name}"]')
            )
        else:
            options = html.xpath(f'//select[@name="{option_name}"]//option[not(@value="")]')
        options = [(o.attrs.get('value'), o.text) for o in options]
        if selected:
            return options[0] if options else None
        return options

    def _parse_html_customer_options(self, html):
        options = self._parse_html_options(html, option_name='CustomerCode_0_0')
        customers = []
        for code, description in options:
            customers.append({
                'customer_code': code,
                'customer_description': description
            })
        return customers

    def _parse_html_project_options(self, html):
        pattern = (
            r"AddProjectEntry\("
            "'(?P<customer_code>[^']*?)',"
            "'(?P<project_code>[^']*?)',"
            "'(?P<project_psid>[^']*?)',"
            "'(?P<project_description>[^']*?)',"
            "(?P<task_count>[^']*?)"
            "\)\s"
        )
        projects = re.finditer(pattern, html.html)
        return [p.groupdict() for p in projects]

    def _parse_html_task_options(self, html):
        pattern = (
            r"AddTaskEntry\("
            "'(?P<project_code>[^']*?)',"
            "'(?P<task_id>[^']*?)',"
            "'(?P<task_description>[^']*?)'"
            "\)"
        )
        tasks = re.finditer(pattern, html.html)
        return [t.groupdict() for t in tasks]

    def login(self, username, password, customer_id):
        data = {
            'CurrentClientTime': '',
            'compact': 'off',
            'ForceInterface': 'S',
            'systemid': customer_id,
            'username': username,
            'password': password
        }
        r = self.session.post(self.LOGIN_URL, data=data)

        # Detect errors
        error_table = r.html.xpath('//a[@name="ErrorTable"]/following-sibling::table', first=True)
        if error_table:
            errors = self._parse_html_login_errors(error_table)
            raise LoginException(' '.join(errors))

        # Detect rejected logon
        rejected_login_input = r.html.find('input[name="RejectedLogon"]')
        if rejected_login_input:
            raise LoginException('Invalid login credentials.')

        # Find UserContextID (required for future session requests)
        user_context_input = r.html.find('input[name="UserContextID"]', first=True)
        if user_context_input:
            self.user_context_id = user_context_input.attrs.get('value')
        else:
            raise LoginException('UserContextID not found in login response.')

        # Load ViewTimesheet page to get StaffID
        r = self.session.post(self.VIEW_TIMESHEET_URL, data={
            'UserContextID': self.user_context_id
        })
        staff_id_input = r.html.find('input[name="StaffID"]', first=True)
        if staff_id_input:
            self.staff_id = staff_id_input.attrs.get('value')
        else:
            raise LoginException('StaffID not found in login response.')
        self.logged_in = True

    def get_timecodes(self):
        if not self.logged_in:
            raise LoginException('Not logged in.')
        today = date.today().strftime('%d-%b-%Y')
        data = {
            'UserContextID': self.user_context_id,
            'StaffID': self.staff_id,
            'Mode': 'Day',
            'StartDate': today,
            'EndDate': today
        }
        r = self.session.post(self.INPUT_TIME_URL, data=data)
        customers = self._parse_html_customer_options(r.html)
        projects = self._parse_html_project_options(r.html)
        tasks = self._parse_html_task_options(r.html)
        return customers, projects, tasks

    def get_timesheet(self, start_date=None, end_date=None):
        if start_date is None and end_date is None:
            today = date.today()
            start_date = today + relativedelta(day=1, weekday=MO)
            end_date = today + relativedelta(day=31, weekday=FR(-1))
        r = self.session.post(self.INPUT_TIME_URL, data={
            'UserContextID': self.user_context_id,
            'StaffID': self.staff_id,
            'Mode': 'Week',
            'StartDate': start_date.strftime('%d-%b-%Y'),
            'EndDate': end_date.strftime('%d-%b-%Y')
        })
        customer_options, project_options, task_options = self.get_timecodes()
        return Timesheet(
            html=r.html,
            staff_id=self.staff_id,
            user_context_id=self.user_context_id,
            customer_options=customer_options,
            project_options=project_options,
            task_options=task_options)