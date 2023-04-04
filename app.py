import symbol
import time
import requests
import json
import datetime as dt
import pandas as pd
import streamlit as st
import base64
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from PIL import Image
import re

st.set_page_config(
    layout="centered", page_icon="", page_title="Historical data downloader"
)

# hide streamlit branding and hamburger menu
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)


# Get input from user
global user_id, token, TimeFrame, ticker, period

# set today's date and time
curr_time_dec = time.localtime(time.time())
date = time.strftime("%Y-%m-%d", curr_time_dec)

st.title("Tired of Scrapping Data?🤯")

st.write("➡️ Use this tool to get historical data of stock/index for **PHREEEE** !!!")

st.write("➡️ Data available from 01 Jan 2015 onwards")

st.write("➡️ FNO data available only for current expiry series")

st.write("➡️ Data sent to your inbox within 2 mins")

st.write("-------")

# get the zerodha enctoken
url = "https://4f1y5wxfde.execute-api.ap-south-1.amazonaws.com/"
payload = {}
headers = {}
response = requests.request("GET", url, headers=headers, data=payload)
token = response.text
user_id = st.secrets["User"]["user_id"]

# Function to get last 60 days of data
def get_data(period, start_date, end_date, symbol):

    scrip_ID = inst.loc[symbol]["instrument_token"]
    url = f"https://kite.zerodha.com/oms/instruments/historical/{scrip_ID}/{period}?user_id={user_id}&oi=1&from={start_date}&to={end_date}"

    payload = {}
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "authorization": f"enctoken {token}",
    }

    response = requests.request("GET", url, headers=headers, data=payload)
    # st.write(response.headers["content-type"])
    # st.write(response.text)

    # this condition was added because Zerodha started sending html data instead of Json data when requests were made at this frequency
    if (
        response.headers["content-type"] == "text/html; charset=UTF-8"
        or len(response.json()["data"]["candles"]) == 0
    ):
        return "fail"
    else:
        data = response.json()["data"]["candles"]
        return data


# Function to scrap data
def scrap_data(scrip_name, period):

    err_count = 0

    scrip_name = str(scrip_name)
    df = pd.DataFrame(columns=["DateTime", "Open", "High", "Low", "Close", "Volume"])

    final_start = "2015-01-01"
    start = dt.datetime.strptime(final_start, "%Y-%m-%d")
    end = start + dt.timedelta(60)

    diff = divmod((dt.datetime.today() - end).total_seconds(), 86400)[0]

    while diff >= 0:

        start_date = dt.datetime.strftime(start, "%Y-%m-%d")
        end_date = dt.datetime.strftime(end, "%Y-%m-%d")

        a = get_data(period, start_date, end_date, scrip_name)

        # condition if we do not receive the data from the API
        if a == "fail":

            time.sleep(1)
            err_count += 1
            # st.write(err_count)

            # if the data does not come after 5 iterations, then switch to the next date
            if err_count > 5:
                diff = divmod((dt.datetime.today() - end).total_seconds(), 86400)[0]

                if diff < 0:
                    start = end + dt.timedelta(1)
                    end = start + dt.timedelta(abs(diff))
                else:
                    start = end + dt.timedelta(1)
                    end = start + dt.timedelta(60)

            else:
                continue

        # if API gave the correct API response
        else:
            err_count = 0

            data = pd.DataFrame(
                a, columns=["DateTime", "Open", "High", "Low", "Close", "Volume", "OI"]
            )
            data.drop(columns=["OI"], inplace=True)

            df = df.append(data)

            diff = divmod((dt.datetime.today() - end).total_seconds(), 86400)[0]

            if diff < 0:
                start = end + dt.timedelta(1)
                end = start + dt.timedelta(abs(diff))
            else:
                start = end + dt.timedelta(1)
                end = start + dt.timedelta(60)

    # Transform the DataFrame
    df.insert(1, "Date", 0)
    df.insert(2, "Time", 0)
    df[["Date", "Time"]] = df["DateTime"].str.split("T", expand=True)
    df[["Time", "nan"]] = df["Time"].str.split("+", expand=True)
    df.drop(["DateTime", "nan"], axis=1, inplace=True)
    df.set_index("Date", inplace=True)
    return df


# check if the email ID is valid or not
def check(email):
    regex = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    # pass the regular expression
    # and the string into the fullmatch() method
    if re.fullmatch(regex, email):
        result = "valid"
    else:
        result = "invalid"

    return result


# lookup for segment
segment = ["NSE", "NFO"]
segment = st.selectbox(
    "Select Segment",
    segment,
    help="NSE for all Stocks & Indices data or NFO for Futures and Options Data",
)

# vlookup for instrument token
try:
    instruments = pd.read_csv("https://api.kite.trade/instruments/" + segment)
except:
    st.warning("Please Reload the page!")
    st.stop()

data = instruments[["instrument_token", "tradingsymbol"]]
inst = data.set_index("tradingsymbol")
stocks = data["tradingsymbol"].to_list()

# lookup for timeframe
TimeFrame = [
    "minute",
    "3minute",
    "5minute",
    "10minute",
    "15minute",
    "30minute",
    "60minute",
    "day",
]

ticker = st.selectbox(
    "Select the Symbol",
    stocks,
    help="The scrip name of the stock/index/futures/option instrument",
)
period = st.selectbox(
    "Select the TimeFrame",
    TimeFrame,
    help="The timeframe of the data that you are looking for",
)
email = st.text_input("Enter you Email", help="Don't worry, We will never spam you")

if st.button("Email me the data"):

    if check(email) == "valid":

        ##Download Widget
        with st.spinner("abra-ca-dabra 🎩 ..."):

            df = scrap_data(ticker, period)

            compression_opts = dict(
                method="zip", archive_name=ticker + "_" + period + ".csv"
            )
            zip = df.to_csv(
                ticker + "_" + period + ".zip", compression=compression_opts
            )

            # email the zip file
            fromaddr = "analystindie@gmail.com"
            toaddr = email
            msg = MIMEMultipart()
            msg["From"] = fromaddr
            msg["To"] = toaddr
            msg["Subject"] = "Data Available Now"
            body = "Hey there,\rPlease find the zip file in the attachement below.\r\rAlso, reply to this email if you loved using the tool or have any feedbacks :)"
            msg.attach(MIMEText(body, "plain"))
            filename = ticker + "_" + period + ".zip"
            attachment = open(ticker + "_" + period + ".zip", "rb")
            p = MIMEBase("application", "octet-stream")
            p.set_payload((attachment).read())
            encoders.encode_base64(p)
            p.add_header("Content-Disposition", "attachment; filename= %s" % filename)
            msg.attach(p)

            s = smtplib.SMTP("smtp.gmail.com", 587)
            s.starttls()
            s.login("analystindie@gmail.com", st.secrets["Smtp"]["password"])

            text = msg.as_string()
            s.sendmail(fromaddr, toaddr, text)
            s.quit()

            # store data in database
            # url_email = "https://3749e8lxlf.execute-api.ap-south-1.amazonaws.com/"
            url_email = "https://prit5qpff1.execute-api.ap-south-1.amazonaws.com/"

            payload_email = {
                "query_date": date,
                "tool_name": "tool-historical-data-downloader",
                "Segment": segment,
                "Symbol": ticker,
                "Period": period,
                "Email": email,
            }
            headers_email = {"Content-Type": "text/plain"}
            response = requests.request(
                "POST", url_email, headers=headers_email, data=json.dumps(payload_email)
            )

            # response text
            st.success("✔️ Email Sent Successfully")
            st.caption(
                "*Note: Please check your spam folder, if you did not receive the email in your inbox*"
            )

    else:
        st.error(" ❌ Please enter a valid email address")

st.write("---")
st.subheader("App Stats")

# Fetch stats data
url_email = "https://prit5qpff1.execute-api.ap-south-1.amazonaws.com/stats"

payload_email = {"tool_name": "tool-historical-data-downloader"}
headers_email = {"Content-Type": "text/plain"}
response = requests.request(
    "POST", url_email, headers=headers_email, data=json.dumps(payload_email)
)

stats_data = json.loads(response.text)

col1, col2 = st.columns(2)

# with col1:
#     st.metric("Unique User Count", f'{stats_data["total_unique_users"]} users')

with col1:
    st.metric("Usage Count", f'{stats_data["total_times_used"]} times')

with col2:
    st.metric("Time Saved", f'{stats_data["total_hrs_saved"]} hrs')

st.write("")
st.write("----")
st.write("")
st.write("")

st.markdown(
    "<h6 style='text-align: center; color: white;'>If you've found this tool valuable, kindly consider donating by buying me a book. Your contribution will fuel my learning journey and provide you with even better resources in the future 😇</h6>",
    unsafe_allow_html=True,
)

st.write("")

buy_me_a_coffee_string = """<p align = "center"> <a href="https://www.buymeacoffee.com/7paise"><img src="https://img.buymeacoffee.com/button-api/?text=Buy me a Book&emoji=📚&slug=7paise&button_colour=BD5FFF&font_colour=ffffff&font_family=Cookie&outline_colour=000000&coffee_colour=FFDD00" /></a>"""
st.markdown(buy_me_a_coffee_string, unsafe_allow_html=True)


# html_string2 = """<p align = "center">❤️ <a href="https://ctt.ac/4A0Vh" target="_blank">  Spread The Word </a></p>"""
# st.markdown(html_string2, unsafe_allow_html=True)


# html_string1 = """<p align = "center">☎️ <a href = "mailto: analystindie@gmail.com">Contact Us</a></p>"""
# st.markdown(html_string1, unsafe_allow_html=True)
