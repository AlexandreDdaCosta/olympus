import numpy

from dateutil import easter, tz
from dateutil.relativedelta import MO, relativedelta
from datetime import datetime as dt
from datetime import timedelta

from olympus import DATE_STRING_FORMAT as QUOTE_DATE_FORMAT
from olympus.securities.equities.data import TIMEZONE

HALF_DAY_NAMES = ['Independence Eve', 'Black Friday', 'Christmas Eve']
HOLIDAY_NAMES = ['New Years Day', 'MLK Day', 'Presidents Day', 'Good Friday',
                 'Memorial Day', 'Juneteenth', 'Independence Day', 'Labor Day',
                 'Thanksgiving', 'Christmas']
OLDEST_QUOTE_DATE = (dt.strptime('1990-01-01',
                                 QUOTE_DATE_FORMAT)
                     .replace(tzinfo=tz.gettz(TIMEZONE)))


class DateVerifier(object):

    def verify_date(self, trading_date):
        trading_date.strftime('%s')

    def verify_date_range(self, start_date, end_date, **kwargs):
        allow_future_end_date = kwargs.get('allow_future_end_date', True)
        null_start_date = kwargs.get('null_start_date', False)
        keep_null_end_date = kwargs.get('keep_null_end_date', False)
        today = dt.now().astimezone()
        if null_start_date is False and start_date is None:
            raise Exception('Parameter start_date cannot be None; set ' +
                            'keyword null_start_date = True to override.')
        if start_date is not None:
            self.verify_date(start_date)
            if start_date < OLDEST_QUOTE_DATE:
                raise Exception('Start date cannot be less than ' +
                                OLDEST_QUOTE_DATE)
            if start_date > today:
                raise Exception('Start date cannot be in the future.')
            start_date = dt(start_date.year,
                            start_date.month,
                            start_date.day,
                            0,
                            0,
                            0).replace(tzinfo=tz.gettz(TIMEZONE))
        if end_date is not None:
            self.verify_date(end_date)
            if start_date is not None and end_date <= start_date:
                raise Exception('End date must be greater than start date.')
            if end_date < OLDEST_QUOTE_DATE:
                raise Exception('End date cannot be less than ' +
                                OLDEST_QUOTE_DATE)
            if allow_future_end_date is False and end_date > today:
                raise Exception('End date cannot be in the future.')
            end_date = dt(end_date.year,
                          end_date.month,
                          end_date.day,
                          0,
                          0,
                          0).replace(tzinfo=tz.gettz(TIMEZONE))
        elif keep_null_end_date is False:
            end_date = today
        return start_date, end_date


class TradingDates(DateVerifier):
    '''
    Information about the trading calendar for US equity markets
    '''

    def __init__(self, **kwargs):
        super(TradingDates, self).__init__(**kwargs)

    def holidays(self, start_date, end_date=None, **kwargs):
        # Returns a count of all trading holidays between two dates, inclusive
        # Optionally returns a list of the holidays
        # If no end date is given, will use today's date
        # If half_days keyword argument is true, will return data
        # for shortened hour trading days instead of holidays
        half_days = kwargs.get('half_days', False)
        return_list = kwargs.get('return_list', False)
        if return_list is True:
            days_list = []
        else:
            days_count = 0
        (start_date, end_date) = self.verify_date_range(start_date, end_date)
        start_year = start_date.year
        end_year = end_date.year
        name_date = None
        if half_days is True:
            name_list = HALF_DAY_NAMES
        else:
            name_list = HOLIDAY_NAMES
        while start_year <= end_year:
            for name in name_list:
                name_date = self._calculate_name_date(name_list,
                                                      name,
                                                      start_year)
                if name_date is not None:
                    if name_date >= start_date and name_date <= end_date:
                        if return_list is True:
                            days_list.append(name_date)
                        else:
                            days_count = days_count + 1
            start_year = start_year + 1
        if return_list is True:
            if days_list:
                return days_list
            return None
        return days_count

    def half_days(self, start_date, end_date=None):
        # Returns a list of all half trading days between two dates, inclusive
        # On these days, the US stock market closes at 1 PM
        # If no end date is given, will use the current date
        return self.holidays(start_date,
                             end_date,
                             half_days=True,
                             return_list=True)

    def trade_days(self, start_date, end_date=None):
        # Returns a count of all dates on which the US equity markets are open
        # between two dates, inclusive.
        # If no end date is given, will use today's date
        holiday_count = self.holidays(start_date, end_date)
        start_date = "%d-%02d-%02d" % (start_date.year,
                                       start_date.month,
                                       start_date.day)
        if end_date is None:
            now = dt.now().astimezone()
            today = "%d-%02d-%02d" % (now.year, now.month, now.day)
            trading_days = (numpy.busday_count(start_date,
                                               today,
                                               'Mon Tue Wed Thu Fri')
                            - holiday_count)
        else:
            end_date = "%d-%02d-%02d" % (end_date.year,
                                         end_date.month,
                                         end_date.day)
            trading_days = (numpy.busday_count(start_date,
                                               end_date,
                                               'Mon Tue Wed Thu Fri')
                            - holiday_count)
        return trading_days

    def _adjust_for_weekend(self, check_date):
        weekday_no = check_date.weekday()
        if weekday_no == 5:
            return check_date - timedelta(days=1)
        elif weekday_no == 6:
            return check_date + timedelta(days=1)
        return check_date

    def _calculate_name_date(self, name_list, holiday, year):  # noqa: F403
        '''
        Does the grunt work of calculating the date of a trading holiday or
        shortened hours trading day for a given year
        '''
        holiday_datetime = None
        if holiday in name_list:
            if holiday == 'New Years Day':
                holiday_datetime = self._standard_holiday(year, 1, 1)
            elif holiday == 'MLK Day':
                if year >= 1998:
                    holiday_datetime = \
                        self._fixed_day_of_week_holiday(year, '-01', 2, 'Mon')
            elif holiday == 'Presidents Day':
                holiday_datetime = \
                    self._fixed_day_of_week_holiday(year, '-02', 2, 'Mon')
            elif holiday == 'Good Friday':
                holiday_datetime = \
                    easter.easter(year, method=3) - timedelta(days=2)
            elif holiday == 'Memorial Day':
                holiday_datetime = \
                    (dt.strptime(str(year) + '-05-01', QUOTE_DATE_FORMAT) +
                     relativedelta(day=31, weekday=MO(-1)))
            elif holiday == 'Juneteenth':
                if year >= 2022:
                    holiday_datetime = self._standard_holiday(year, 6, 19)
            elif holiday == 'Independence Day':
                holiday_datetime = self._standard_holiday(year, 7, 4)
            elif holiday == 'Independence Eve':
                holiday_datetime = self._eve_holiday(year, 7, 3)
            elif holiday == 'Labor Day':
                holiday_datetime = \
                    self._fixed_day_of_week_holiday(year, '-09', 0, 'Mon')
            elif holiday == 'Thanksgiving':
                holiday_datetime = \
                    self._fixed_day_of_week_holiday(year, '-11', 3, 'Thu')
            elif holiday == 'Black Friday':
                holiday_datetime = \
                    (self._fixed_day_of_week_holiday(year, '-11', 3, 'Thu')
                     + timedelta(days=1))
            elif holiday == 'Christmas':
                holiday_datetime = self._standard_holiday(year, 12, 25)
            elif holiday == 'Christmas Eve':
                holiday_datetime = self._eve_holiday(year, 12, 24)
        else:
            raise Exception('Unknown holiday ' +
                            holiday +
                            '. Valid holidays are: ' +
                            ', ' . join(HOLIDAY_NAMES))
        if holiday_datetime is not None:
            holiday_datetime = \
                holiday_datetime.replace(tzinfo=tz.gettz(TIMEZONE))
        return holiday_datetime

    def _eve_holiday(self, year, month, day):
        holiday_eve = (dt.strptime(str(year) +
                       '-' + str("%02d" % month) +
                       '-' + str("%02d" % day),
                       QUOTE_DATE_FORMAT))
        weekday_no = holiday_eve.weekday()
        if weekday_no >= 0 and weekday_no < 4:  # Can't be Friday
            return holiday_eve
        return None

    def _fixed_day_of_week_holiday(self,
                                   year,
                                   month_string,
                                   ordinal,
                                   day_of_week):
        year_month = str(year) + month_string
        holiday_datetime = numpy.busday_offset(year_month,
                                               ordinal,
                                               roll='forward',
                                               weekmask=day_of_week)
        return dt.strptime(str(holiday_datetime), QUOTE_DATE_FORMAT)

    def _standard_holiday(self, year, month, day):
        holiday_datetime = (dt.strptime(str(year) +
                            '-' + str("%02d" % month) +
                            '-' + str("%02d" % day),
                            QUOTE_DATE_FORMAT))
        return self._adjust_for_weekend(holiday_datetime)
