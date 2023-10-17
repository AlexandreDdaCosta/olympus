# Larry trading application

Code name and run user for a trading system currently in development.

Named in honor of **Jesse Livermore**, whose life work originally inspired
my trading interest.

## INTRODUCTION

The features of this application are as follows:

* **Securities Analyzer**.

Historically, there have been many systems that attempted to analyze past
price movements of securities to predict future prices.

Larry back tests a number of these systems and attempts to reach conclusions
about their predictive power. The theory being pursued is that some systems
will be generally more effective than others and that a carefully-chosen
combination of these systems might give better performance that any one,
especially given certain circumstances that tend to recur in financial
markets. This analysis is combined with an analysis of company fundamentals
along with a survey of informed opinions as expressed through insider
trading information made available in public sources such as
[Edgar](https://www.sec.gov/edgar/search-and-access). The goal is to
generate a probability score than is then used to execute trades. The
score also helps to decide how much capital to allocate to a trade,
combined with sound money management techniques, such as overall capital
limits allowed for any given trade and mandatory stop losses. In trading,
it's axiomatic that emotional decisions will quickly bankrupt a trader, so
Larry's overall goal is to have such decisions be based on dispassionate,
back-tested rules not subject to the vagarities of human feelings. Instinct
does have its place in trading, so one product of this analysis is a charting
system that lets a user see possible trades, along with entry/exit points and
outcomes of applying the system to past market action.

* **Trading Robot**.

This feature automates securities trading based on the output of the analyzer.

Computer trading algorithms are ubiquitous, so the competition is fierce. The
theory pursued here is that a small operator does have some advantages, such
as the ability to be *discreet* on account of the small monetary value of the
trades that such an operator will execute. Larry uses the
[TD Ameritrade API](https://developer.tdameritrade.com/) to execute trades,
although this is in the process of being integrated with Charles Schwab.

## Core trading systems

Besides the Edgar service mentioned earlier, certain trading systems show
promise when building a probability score. Among them:

* [DeMARK indicators](https://demark.com/indicators-list/)

Developed by Tom DeMark, these indicators are based on price patterns. Of the
various indicators, the TD Sequential is the most promising as it's based
on the idea that momentum will carry prices in one direction until that
momentum is exhausted, with the reversal being foreshadowed by identifiable
price action.

* [The Livermore Market Key](https://archive.org/details/howtotradeinstoc0000live)

Although Jesse Livermore published his work over eighty years ago, I believe
that his analysis remains relevant because of his use of **pivot points**, which
are simply price points where momentum has previously stalled. These pivots
thus represent key locations where price behavior needs to be watched for
indications about the underlying demand for a security. Failure at a previous
reversal point is used as evidence of confirmation that a *wall* exists due to
underlying demand and enthusiasm for a stock, while a clear movement through
a pivot suggests the start of an important continuing move in the same
direction. I feel it necessary to enhance Livermore's system by adding some
more sophisticated concepts. For example, Livermore uses fixed dollar amounts
when looking for evidence of a breakout, but a more modern understanding
incorporates the idea of *historical volatility*. The significance of a price
movement is therefore based on the underlying characteristics of a given stock.

## Other key considerations

Trading systems are often incomplete by themselves since they focus purely on
prices. A full picture requires looking at other key values:

* **Volume**. Movements of significance are reliably accompanied by a swelling
of volume. The opposite is also sometimes true: Weak volume, especially on
outsized moves, are often a sign of waning momentum.

* **Volatility**. There are many ways of measuring volatility, a simple example
being [average true range](https://www.investopedia.com/terms/a/atr.asp). It's
essential to consider volatility when analyzing the significance of a price
move, since large price moves are less significant in more volatile stocks.

Ultimately, any trading system needs to combine a number of factors, perhaps
weighing them based on back-tested analysis.
