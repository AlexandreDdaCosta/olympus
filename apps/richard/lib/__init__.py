# Core application constants

USER = 'richard'

# Markets of the original turtle trading, with non-standard additions

CORE_MARKETS = [
    {
        'market' : 'cocoa',
        'etf_bull' : 'NIB',
        'close_correlation' : [],
        'loose_correlation' : []
    },
    {
        'market' : 'coffee'
        'etf_bull' : 'JO',
    },
    {
        'market' : 'corn',
        'etf_bull' : 'CORN',
        'nonstandard' : true
    },
    {
        'market' : 'cotton'
    },
    {
        'market' : 'soybean',
        'etf_bull' : 'SOYB',
        'nonstandard' : true
    },
    {
        'market' : 'sugar',
        'etf_bull' : 'CANE'
    },
    {
        'market' : 'wheat',
        'etf_bull' : 'WEAT',
        'nonstandard' : true
    },
    {
        'market' : '7-10 year treasury bond',
        'etf_bull' : 'IEF'
    },
    {
        'market' : '20+ year treasury',
        'etf_bear' : 'TBT',
        'etf_bull' : 'TLT'
    },
    {
        'market' : 'Swiss franc',
        'etf_bull' : 'FXF'
    },
    {
        'market' : 'Euro',
        'etf_bear' : 'EUO',
        'etf_bull' : 'FXE',
        'nonstandard' : true
    },
    {
        'market' : 'British pound',
        'etf_bull' : 'FXB'
    },
    {
        'market' : 'Japanese yen',
        'etf_bull' : 'FXY'
    },
    {
        'market' : 'Canadian dollar',
        'etf_bull' : 'FXC'
    },
    {
        'market' : 'Eurodollar'
    },
    {
        'market' : '90-day US treasury'
    },
    {
        'market' : 'S&P 500 index',
        'etf_bear' : 'SPDN',
        'etf_bull' : 'SPY'
    },
    {
        'market' : 'Dow Jones Industrial Average',
        'etf_bear' : 'DXD',
        'etf_bull' : 'DIA',
        'nonstandard' : true
    },
    {
        'market' : 'Nasdaq 100',
        'etf_bear' : 'SQQQ',
        'etf_bull' : 'QQQ',
        'nonstandard' : true
    },
    {
        'market' : 'Gold',
        'etf_bear' : 'UGL',
        'etf_bull' : 'GLD'
    },
    {
        'market' : 'Silver',
        'etf_bear' : 'ZSL',
        'etf_bull' : 'SLV'
    },
    {
        'market' : 'Crude oil',
        'etf_bear' : 'SCO',
        'etf_bull' : 'USO'
    },
    {
        'market' : 'Heating oil'
    },
    {
        'market' : 'Gasoline',
        'etf_bull' : 'UGA'
    },
    {
        'market' : 'Natural gas',
        'etf_bull' : 'UNG',
        'nonstandard' : true
    },
]

# Position limits

LIMIT_MARKET = 4
LIMIT_CLOSE_CORRELATION = 6
LIMIT_LOOSE_CORRELATION = 10
LIMIT_DIRECTION = 12

