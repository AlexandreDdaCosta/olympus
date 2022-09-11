import numpy

from dateutil import easter
from dateutil.relativedelta import MO, relativedelta
from datetime import datetime as dt
from datetime import timedelta

HALF_DAY_NAMES = ['Independence Eve','Black Friday','Christmas Eve']
HOLIDAY_NAMES = ['New Years Day','MLK Day','Presidents Day','Good Friday','Memorial Day','Juneteenth','Independence Day','Labor Day','Thanksgiving','Christmas']
QUOTE_DATE_FORMAT = "%Y-%m-%d"
OLDEST_QUOTE_DATE = '1990-01-01'

class DateVerifier(object):

    def __init__(self):
        pass

    def verify_date(self,trading_date):
        return dt.strptime(trading_date, QUOTE_DATE_FORMAT)

    def verify_date_range(self,start_date,end_date,null_start_date=False):
        now = dt.now().astimezone()
        today = "%d-%02d-%02d" % (now.year,now.month,now.day)
        if null_start_date is False and start_date is None:
            raise Exception('Parameter start_date cannot be None; set keyword null_start_date = True to override.')
        if start_date is not None:
            self.verify_date(start_date)
            if start_date < OLDEST_QUOTE_DATE:
                raise Exception('Start date cannot be less than ' + OLDEST_QUOTE_DATE)
            if start_date > today:
                raise Exception('Start date cannot be in the future.')
        if end_date is not None:
            self.verify_date(end_date)
            if start_date is not None and end_date <= start_date:
                raise Exception('End date must be greater than start date.')
        else:
            end_date = today
        return start_date, end_date

class TradingDates(DateVerifier):
    '''
    Information about the trading calendar for US equity markets
    '''

    def __init__(self,**kwargs):
        super(TradingDates,self).__init__(**kwargs)
        pass

    def holidays(self,start_date,end_date=None,**kwargs):
        # Returns a count of all trading holidays between two dates, inclusive
        # Optionally returns a list of the holidays
        # If no end date is given, will use today's date
        # If half_days keyword argument is true, will return data for shortened hour trading days instead of holidays
        half_days = kwargs.get('half_days',False)
        return_list = kwargs.get('return_list',False)
        if return_list is True:
            days_list = []
        else:
            days_count = 0
        (start_date, end_date) = self.verify_date_range(start_date,end_date)
        start_year = int(start_date[:4])
        end_year = int(end_date[:4])
        name_date = None
        if half_days is True:
            name_list = HALF_DAY_NAMES
        else:
            name_list = HOLIDAY_NAMES
        while start_year <= end_year:
            for name in name_list:
                name_date = self._calculate_name_date(name_list,name,start_year)
                if name_date is not None:
                    if name_date >= start_date and name_date <= end_date:
                        if return_list is True:
                            days_list.append(name_date)
                        else:
                            days_count = days_count + 1
            start_year = start_year + 1
        if return_list is True:
            return days_list
        return days_count

    def half_days(self,start_date,end_date=None):
        # Returns a list of all half trading days between two dates, inclusive
        # On these days, the US stock market closes at 1 PM
        # If no end date is given, will use the current date
        return self.holidays(start_date,end_date,half_days=True,return_list=True)

    def trade_days(self,start_date,end_date=None):
        # Returns a count of all dates on which the US equity markets are open
        # between two dates, inclusive.
        # If no end date is given, will use today's date
        holiday_count = self.holidays(start_date,end_date)
        if end_date is None:
            now = dt.now().astimezone()
            today = "%d-%02d-%02d" % (now.year,now.month,now.day)
            trading_days = numpy.busday_count(start_date,today,'Mon Tue Wed Thu Fri') - holiday_count
        else:
            trading_days = numpy.busday_count(start_date,end_date,'Mon Tue Wed Thu Fri') - holiday_count
        return trading_days

    def _adjust_for_weekend(self,check_date):
        weekday_no = check_date.weekday()
        if weekday_no == 5:
            return check_date - timedelta(days=1)
        elif weekday_no == 6:
            return check_date + timedelta(days=1)
        return check_date
        
    def _calculate_name_date(self,name_list,holiday,year): # New Year's Day
        '''
        Does the grunt work of calculating the date of a trading holiday or shortened hours trading day for a given year
        '''
        holiday_datetime = None
        if holiday in name_list:
            if holiday == 'New Years Day':
                holiday_datetime = self._standard_holiday(year,1,1)
            elif holiday == 'MLK Day':
                if year >= 1998:
                    holiday_datetime = self._fixed_day_of_week_holiday(year,'-01',2,'Mon')
            elif holiday == 'Presidents Day':
                holiday_datetime = self._fixed_day_of_week_holiday(year,'-02',2,'Mon')
            elif holiday == 'Good Friday':
                holiday_datetime = easter.easter(year,method=3) - timedelta(days=2)
            elif holiday == 'Memorial Day':
                holiday_datetime = dt.strptime(str(year) + '-05-01', QUOTE_DATE_FORMAT) + relativedelta(day=31, weekday=MO(-1))
            elif holiday == 'Juneteenth':
                if year >= 2022:
                    holiday_datetime = self._standard_holiday(year,6,19)
            elif holiday == 'Independence Day':
                holiday_datetime = self._standard_holiday(year,7,4)
            elif holiday == 'Independence Eve':
                holiday_datetime = self._eve_holiday(year,7,3)
            elif holiday == 'Labor Day':
                holiday_datetime = self._fixed_day_of_week_holiday(year,'-09',0,'Mon')
            elif holiday == 'Thanksgiving':
                holiday_datetime = self._fixed_day_of_week_holiday(year,'-11',3,'Thu')
            elif holiday == 'Black Friday':
                holiday_datetime = self._fixed_day_of_week_holiday(year,'-11',3,'Thu') + timedelta(days=1)
            elif holiday == 'Christmas':
                holiday_datetime = self._standard_holiday(year,12,25)
            elif holiday == 'Christmas Eve':
                holiday_datetime = self._eve_holiday(year,12,24)
        else:
            raise Exception('Unknown holiday ' + holiday + '. Valid holidays are: ' + ', ' . join(HOLIDAY_NAMES))
        if holiday_datetime is not None:
            holiday_datetime = "%d-%02d-%02d" % (holiday_datetime.year,holiday_datetime.month,holiday_datetime.day)
        return holiday_datetime

    def _eve_holiday(self,year,month,day):
        holiday_eve = dt.strptime(str(year) + '-' + str("%02d" % month) + '-' +str("%02d" % day), QUOTE_DATE_FORMAT)
        weekday_no = holiday_eve.weekday()
        if weekday_no >= 0 and weekday_no < 4: # Can't be Friday
            return holiday_eve
        return None

    def _fixed_day_of_week_holiday(self,year,month_string,ordinal,day_of_week):
        year_month = str(year) + month_string
        holiday_datetime = numpy.busday_offset(year_month, ordinal, roll='forward', weekmask=day_of_week)
        return dt.strptime(str(holiday_datetime), QUOTE_DATE_FORMAT)

    def _standard_holiday(self,year,month,day):
        holiday_datetime = dt.strptime(str(year) + '-' + str("%02d" % month) + '-' +str("%02d" % day), QUOTE_DATE_FORMAT)
        return self._adjust_for_weekend(holiday_datetime)
