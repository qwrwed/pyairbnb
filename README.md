# Airbnb scraper in Python

## Overview
This project is an open-source tool developed in Python for extracting product information from Airbnb. It's designed to be easy to use, making it an ideal solution for developers looking for Airbnb product data.

## Features
- Extract prices, available dates, reviews, host details and others
- Full search support
- Extracts detailed product information from Airbnb
- Implemented in Python just because it's popular
- Easy to integrate with existing Python projects
- The code is optimize to work on this format: ```https://www.airbnb.com/rooms/[room_id]```

## Legacy
- This was a project first implemented at [https://github.com/johnbalvin/pyairbnb](https://github.com/johnbalvin/pyairbnb)

## Important
- With the new airbnb changes, if you want to get the price from a room url you need to specify the date range
the date range should be on the format year-month-day, if you leave the date range empty, you will get the details but not the price


## Install

```bash
$ pip install -U git+https://github.com/qwrwed/pyairbnb.git
```
