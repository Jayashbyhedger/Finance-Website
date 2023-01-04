# Finance-Website
The final project of CS50, a finance web-app made with Flask.

This is the final project for Harvards CS50, which is a free online bootcamp-syle course. For the final project I have to create a website where users can make an account and buy and sell stocks based on real stock prices using the IEX API. The bulk of the functionality is in app.py and the webpages are stored in templates. They're written using HTML and Jinja and for the most part they are all built off of the layout.html page. The site makes use of sessions and cookies, so once users are logged in they will remain logged in if they close and re-open their browser. The databases make use of SQLite, and the .execute() function runs SQL queries on the database. The site is made using the flask framework for Python.


For the project I was given helpers.py, layout.html, styles.css and up to line 36 on app.py, the rest was written by me.

Session data is stored in flask_session. finance.db contains two tables, the tables are as follows:

Users;
ID | username | hash (password) | cash (amount of cash that user has)

transactions;
transactionID | userID | stock | price | quantity | DateTime

In order to run this code, you will need an IEX API Key and Flask.
