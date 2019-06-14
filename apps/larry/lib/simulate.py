import larry.market_key as market_key

from larry import *

class BacktestResult(object):

    def __init__(self,profit,thresholds,rules):
        self.profit = profit
        self.thresholds = thresholds
        self.rules = rules

class BacktestResults(object):

    def __init__(self):
        self.results = []

    def add_result(self,profit,thresholds,rules):
        new_result = BacktestResult(profit,thresholds,rules)
        self.results.extend(new_result)

class Backtest(market_key.Calculate):
    # Backtest the Livermore Market Key.

    def __init__(self,symbol=SYMBOL,**kwargs):
        super(Backtest,self).__init__(symbol,**kwargs)
        self.symbol = symbol
        self.purchase_size = kwargs.get('purchase_size',PURCHASE_SIZE)
        self.results = BacktestResults()

    def simulate(self,**kwargs):
        # ALEX steps
        # Create rotation object to change parameters for each run
        # Parameters: rules, thresholds

        # Chart signalsignals
        chart = self.chartpoints()
        last = chart.last_entry()
        signals = chart.last_buy_signal(all=True)
        signals.extend(chart.last_sell_signal(all=True))
        
        # Buy/sell based on date-ordered signals
        signals.sort(key=lambda x: x.date)
        shares = 0
        cost = 0.00
        net = 0.00
        proceeds = 0.00
        unrealized_amount = 0.00
        largest_positive_unrealized = 0.00
        largest_negative_unrealized = 0.00
        for signal in signals:
            print(signal)
            price = round(signal.price,2)
            if shares >= 0: # LONG or NO POSITION
                if signal.signal == BUY:
                    cost = cost + (self.purchase_size * price)
                    shares = shares + self.purchase_size
                else: # SELL
                    proceeds = proceeds + ( (shares + self.purchase_size) * price)
                    shares = -1 * self.purchase_size
            else: # SHORT
                if signal.signal == BUY:
                    cost = cost + ( (abs(shares) + self.purchase_size) * price)
                    shares = self.purchase_size
                else: # SELL
                    proceeds = proceeds + (self.purchase_size * price)
                    shares = -1 * self.purchase_size
            print('Shares: %d' % shares)
            print('Proceeds: %.2f' % proceeds)
            print('Cost: %.2f' % cost)
            net = proceeds - cost
            print('Net: %.2f' % net)
            unrealized_amount = shares * price
            print('Unrealized: %.2f' % unrealized_amount)
            print('Balance: %.2f' % (unrealized_amount + net) )
            if unrealized_amount < largest_negative_unrealized:
                largest_negative_unrealized = unrealized_amount
            elif unrealized_amount > largest_positive_unrealized:
                largest_positive_unrealized = unrealized_amount

        # Output
        print('STATUS: ')
        unrealized_amount = shares * last.price
        print('Shares: %d' % shares)
        print('Proceeds: %.2f' % proceeds)
        print('Cost: %.2f' % cost)
        net = proceeds - cost
        print('Net: %.2f' % net)
        print('Largest open long balance: %.2f' % largest_positive_unrealized)
        print('Largest open short balance: %.2f' % largest_negative_unrealized)
        print('Unrealized: %.2f' % unrealized_amount)
        print('Balance: %.2f' % (unrealized_amount + net) )

        # Store outcomes and associated parameters

