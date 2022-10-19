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
    layout="centered", page_icon="💾", page_title="Historical data downloader"
)

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
url = "https://68o9pf66q0.execute-api.ap-south-1.amazonaws.com/"
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
    # headers = {
    #     "authority": "kite.zerodha.com",
    #     "pragma": "no-cache",
    #     "cache-control": "no-cache",
    #     "sec-ch-ua": '"Google Chrome";v="87", " Not;A Brand";v="99", "Chromium";v="87"',
    #     "accept": "application/json",
    #     "Content-Type": "application/json",
    #     "authorization": f"enctoken {token}",
    #     "sec-ch-ua-mobile": "?0",
    #     "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36",
    #     "sec-fetch-site": "same-origin",
    #     "sec-fetch-mode": "cors",
    #     "sec-fetch-dest": "empty",
    #     "referer": "https://kite.zerodha.com/chart/web/tvc/INDICES/NIFTY%2050/256265",
    #     "accept-language": "en-US,en;q=0.9",
    #     "cookie": "_ga=GA1.2.1237715775.1599025253; WZRK_G=35dc9bf39872453ca302ca61e69943d9; _hjid=a0fa20cf-2859-4186-addd-1ad51ce109c3; _fbp=fb.1.1599067875093.1182513860; mp_7b1e06d0192feeac86689b5599a4b024_mixpanel=%7B%22distinct_id%22%3A%20%225ef374f27072303def14c858%22%2C%22%24device_id%22%3A%20%221744fdf72e2277-05c84fb230310a-f7b1332-144000-1744fdf72e3148%22%2C%22%24initial_referrer%22%3A%20%22%24direct%22%2C%22%24initial_referring_domain%22%3A%20%22%24direct%22%2C%22%24user_id%22%3A%20%225ef374f27072303def14c858%22%2C%22__timers%22%3A%20%7B%7D%7D; __cfduid=d5db03e65a8d59b8756511c92cc839f141610687855; _gid=GA1.2.275777476.1611075594; kf_session=EQK5SCto80996B3JICoZQanok197GRGh; public_token=yu45f5lpkI9Oo2Ni91qJIMyzEv3GRh1N; user_id=VT5229; enctoken=x2FuRS3NQgllZxWymw/WjRNm+pxJbYsB+sPjTksKzwi+AwrBAGWZroZu5biMvrMe9BqZMLqxVn0NQ0q/sj6kBTTJb/bKxw==",
    # }

    response = requests.request("GET", url, headers=headers, data=payload)
    st.write(response.headers["content-type"])
    st.write(response.text)

    # this condition was added because Zerodha started sending html data instead of Json data when requests were made at this frequency
    if response.headers["content-type"] == "text/html; charset=UTF-8":
        return response.headers["content-type"]
    else:
        data = response.json()["data"]["candles"]
        return data


# Function to scrap data
def scrap_data(scrip_name, period):

    scrip_name = str(scrip_name)
    df = pd.DataFrame(columns=["DateTime", "Open", "High", "Low", "Close", "Volume"])

    final_start = "2015-01-01"
    start = dt.datetime.strptime(final_start, "%Y-%m-%d")
    end = start + dt.timedelta(60)

    diff = divmod((dt.datetime.today() - end).total_seconds(), 86400)[0]

    while diff >= 0:

        start_date = dt.datetime.strftime(start, "%Y-%m-%d")
        end_date = dt.datetime.strftime(end, "%Y-%m-%d")
        st.write(start_date)
        st.write(start_date)

        a = get_data(period, start_date, end_date, scrip_name)

        if a == "text/html; charset=UTF-8":
            time.sleep(5)
            continue
        else:
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
        with st.spinner("abra-ca-dabra 🎩 ... "):

            df = scrap_data(ticker, period)
            # csv = df.to_csv().encode('utf-8')
            # st.download_button("Download CSV",csv,ticker + "_" + period + ".csv", "text/csv", key='download-csv',help = ticker + ' data available to download')

            compression_opts = dict(
                method="zip", archive_name=ticker + "_" + period + ".csv"
            )
            zip = df.to_csv(
                ticker + "_" + period + ".zip", compression=compression_opts
            )

            # download button
            # with open(ticker + "_" + period + ".zip", "rb") as fp:
            #     btn = st.download_button(
            #         label="Download zip",
            #         data=fp,
            #         file_name=ticker + "_" + period + ".zip",
            #         mime="application/zip"
            #     )

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
            url_email = "https://3749e8lxlf.execute-api.ap-south-1.amazonaws.com/"
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
html_string2 = """<p align = "center">❤️ <a href="https://ctt.ac/4A0Vh" target="_blank">  Spread The Word </a></p>"""
st.markdown(html_string2, unsafe_allow_html=True)


html_string1 = """<p align = "center">☎️ <a href = "mailto: analystindie@gmail.com">Contact Us</a></p>"""
st.markdown(html_string1, unsafe_allow_html=True)
