# Market Data Vendor Contact Questionnaire

> [!IMPORTANT]
> **Purpose**: Standardized, copy-ready questionnaire for evaluating market data vendors against platform research specifications.
> **Use Case Context**: Internal quantitative research and historical market-data analysis only. No commercial redistribution.

## Section 1: Intraday Index Data Questions (NIFTY 50 & NIFTY BANK)

Please provide explicit, binding answers to the following 20 questions regarding historical intraday index data:

1. Do you provide historical NIFTY 50 1-minute data?
2. Do you provide historical NIFTY BANK 1-minute data?
3. Do you provide historical NIFTY 50 5-minute data?
4. Do you provide historical NIFTY BANK 5-minute data?
5. What is the exact historical date range available (start date to end date)?
6. How many verified trading sessions are available in your historical archive?
7. Is the historical archive 100% complete bar-by-bar, or are there sampled/interpolated intervals?
8. Are timestamps official exchange matching-engine timestamps or vendor-normalized reception times?
9. What exact timezone and timestamp standard is used (e.g. Asia/Kolkata UTC+05:30, ISO-8601)?
10. What is your system's handling and policy for missing bars (e.g. zero-tick intervals during trading hours)?
11. Are post-session trade corrections, tick revisions, and official exchange settlement adjustments reflected in historical bars?
12. Is bulk historical download available (e.g., S3 bucket, SFTP, direct HTTP archive download)?
13. Is REST/WebSocket API access available for programmatically querying historical bars?
14. What are the specific rate limits, concurrent connection limits, and bandwidth throttles on the historical API?
15. What file and data serialization formats are supported (e.g., CSV, Parquet, JSON, binary)?
16. What is the exact price for historical NIFTY 50 and NIFTY BANK 1m and 5m data?
17. Is the pricing structured as a one-time historical purchase, a monthly subscription, or an annual license?
18. Is Indian Goods and Services Tax (GST, 18%) included in the quoted price or billed separately?
19. Are official exchange data licensing fees or royalty fees separate from vendor platform fees?
20. What specific research, non-display, and internal quantitative use license is included?

## Section 2: Historical Options Microstructure Questions (NIFTY & BANKNIFTY Options)

Please provide explicit, binding answers to the following 30 questions regarding historical options quote archives:

1. Do you provide historical NIFTY options Bid/Ask quote archives?
2. Do you provide historical BANKNIFTY options Bid/Ask quote archives?
3. What exact historical date range is available for options quote data?
4. Are expired options contracts completely retained, queryable, and identifiable post-expiry?
5. Are all historical strike prices (ITM, ATM, OTM) included without truncation?
6. Are all historical expiries (weekly, monthly, quarterly) included where applicable?
7. Are weekly and monthly contracts properly distinguished and indexed in historical metadata?
8. Are timestamps exchange matching-engine event-time timestamps, and at what precision (microsecond, millisecond, second)?
9. What is the recorded quote frequency (tick-by-tick, 1-second snapshot, periodic snapshot)?
10. Are Best Bid and Best Ask paired synchronously at the exact same timestamp?
11. Across regular market hours (09:15-15:30 IST), what empirical percentage of market time has continuous paired Bid/Ask coverage?
12. Is the quoted options surface continuous throughout the day or sparse/sporadic?
13. Are crossed or inverted quotes (Bid > Ask) filtered, flagged, or delivered raw?
14. Are stale or non-refreshing quotes identifiable via sequence numbers or quote update flags?
15. Is order book depth available historically beyond the top-of-book (Level 1)?
16. If depth is available, how many levels are provided (e.g. 5-depth snapshot)?
17. Is full order-book reconstruction possible from the delivered data (Level 3 / Level 4)?
18. Are discrete order messages (add, modify, cancel) and trade execution messages available?
19. Are contract identifiers stable and authoritative across the lifetime of the contract?
20. Is historical Open Interest (OI) provided at intraday intervals or EOD only?
21. Is historical contract trading volume provided bar-by-bar or tick-by-tick?
22. Are exchange trade cancellation and erroneous trade corrections incorporated?
23. What is the exact data schema and file/API format for options archives?
24. Is bulk archive delivery available (e.g. cloud storage delivery or physical drive)?
25. What is the exact price for historical NIFTY and BANKNIFTY options quote archives?
26. Is the pricing structured as a one-time archive purchase, monthly fee, or annual license?
27. Are exchange data licensing fees billed separately?
28. Does the commercial license explicitly authorize internal quantitative research and model simulation?
29. Can derived models, backtest logs, and research conclusions be permanently retained internally without ongoing fees?
30. What specific redistribution, third-party disclosure, or display restrictions apply?
