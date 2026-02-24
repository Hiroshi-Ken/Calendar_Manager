# Study Schedule & Deadline Manager (Telegram + Google Calendar)

A professional automation tool built with **Python** to synchronize university schedules and academic deadlines directly with **Google Calendar** via a **Telegram Bot** interface.

## Overview
This project was developed to solve the complexity of manual academic planning. It automates the creation of recurring study blocks and integrates external deadlines (exams, assignments) using CSV data, allowing real-time management through a mobile device.

## Blue Skills (Technical Stack)
* **Language:** Python 3.x
* **APIs:** Google Calendar API v3, Telegram Bot API (Telebot)
* **Data Handling:** CSV parsing and manipulation
* **Cloud Deployment:** Hosted on PythonAnywhere (24/7 availability)
* **Automation:** Logic for rescheduling unforeseen events and date-anchoring.

## Green & Soft Skills (Impact)
* **Paperless Productivity:** Replaces physical planners with a digital-first approach.
* **Process Optimization:** Reduces manual data entry time by 90% through automation.
* **Strategic Planning:** Features a specialized logic to move study blocks to weekends during unforeseen events.

## How it Works
1. **/populate [start] [end]:** Automatically generates the entire semester schedule with specific color-coding (Green for Chemistry, Blue for English, etc.).
2. **/deadlines:** Reads a `deadlines.csv` file and populates the calendar with red-colored alerts for exam dates.
3. **/reschedule [date]:** Moves a busy weekday's study blocks to the following Saturday.
4. **/revert [date]:** Moves blocks back to the original date if the schedule clears up.

## Installation & Setup
*(Note: Sensitive files like `credentials.json` and `token.json` are excluded for security.)*

1. Clone the repository.
2. Install dependencies: `pip install pyTelegramBotAPI google-api-python-client google-auth-httplib2 google-auth-oauthlib`.
3. Obtain your **Google Calendar API** credentials and **Telegram Bot Token**.
4. Run `python agenda.py`.
