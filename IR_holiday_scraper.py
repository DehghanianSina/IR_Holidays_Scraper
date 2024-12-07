import requests
from bs4 import BeautifulSoup
import pandas as pd
import jdatetime

# تعریف سال مورد نظر
from_year = 1401
to_year = 1403 # must be same as the from_year for only single year
df_full_year = pd.DataFrame() 
df_holidays = pd.DataFrame() 

# دیکشنری تبدیل نام ماه‌ها به شماره آن‌ها
month_mapping = {
    "فروردین": "01",
    "اردیبهشت": "02",
    "خرداد": "03",
    "تیر": "04",
    "مرداد": "05",
    "شهریور": "06",
    "مهر": "07",
    "آبان": "08",
    "آذر": "09",
    "دی": "10",
    "بهمن": "11",
    "اسفند": "12"
}

# URL مورد نظر
for year in range(from_year, to_year+1): 
    for m in range(1,13):
        url = f"https://www.time.ir/fa/event/list/0/{year}/{m}"
        try:
            # ارسال درخواست به صفحه وب
            response = requests.get(url)
            response.raise_for_status()  # بررسی وضعیت پاسخ

            # پردازش محتوای HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # یافتن تمام المان‌های li با کلاس 'eventHoliday'
            event_holidays = soup.find_all('li', class_='eventHoliday')

            # استخراج داده‌های روزهای تعطیل
            holiday_data = []
            for event in event_holidays:
                date_span = event.find('span')
                date_text = date_span.text.strip() if date_span else ""
                title_text = event.text.replace(date_span.text, "").split('[')[0].strip() if date_span else event.text.strip()

                day, month_name = date_text.split()
                month_number = month_mapping.get(month_name, "")

                jalali_date = f"{year}-{month_number}-{int(day):02d}" if month_number else ""
                if jalali_date:
                    j_date = jdatetime.date(year=int(year), month=int(month_number), day=int(day))
                    miladi_date = j_date.togregorian().strftime("%Y-%m-%d")
                else:
                    miladi_date = ""

                holiday_data.append({"miladi_date": miladi_date, "jalali_date": jalali_date, "is_holiday": 1, "holiday_title": title_text})

            # df_holidays = pd.DataFrame(holiday_data)
            df_holidays = pd.concat([df_holidays, pd.DataFrame(holiday_data)], ignore_index=True)

        except requests.RequestException as e:
            print(f"Error fetching data: {e}")


    # ایجاد دیتافریم کامل سال
    full_year_data = []
    for month_name, month_number in month_mapping.items():
        for day in range(1, 32):
            try:
                jalali_date = f"{year}-{month_number}-{day:02d}"
                j_date = jdatetime.date(year=int(year), month=int(month_number), day=day)
                miladi_date = j_date.togregorian().strftime("%Y-%m-%d")
                full_year_data.append({"miladi_date": miladi_date, "jalali_date": jalali_date, "is_holiday": 0, "holiday_title": None})
            except ValueError:
                continue

    # df_full_year = pd.DataFrame(full_year_data)
    df_full_year = pd.concat([df_full_year, pd.DataFrame(full_year_data)], ignore_index=True)

# جوین دو دیتافریم
df_final = pd.merge(df_full_year, df_holidays, on="miladi_date", how="left", suffixes=("", "_y"))
df_final["holiday_title"] = df_final["holiday_title_y"].combine_first(df_final["holiday_title"])
df_final["is_holiday"] = df_final["is_holiday_y"].combine_first(df_final["is_holiday"]).fillna(0).astype(int)
df_final = df_final.drop(columns=["holiday_title_y", "is_holiday_y", "jalali_date_y"], errors="ignore")



# df_final.head()
df_final.to_csv(f"calendar_from_{from_year}_to_{to_year}.csv", index=False)