"""Create the sample knowledge base for a fictional company, Nilora Electronics.

Every figure quoted in the annual reports is computed from sales_data.csv, so
questions that mix prose and data have one consistent answer.

Run:  python scripts/generate_documents.py
"""
import random
from pathlib import Path

import pandas as pd
from docx import Document
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

OUT = Path(__file__).resolve().parents[1] / "data" / "documents"
random.seed(7)

# name -> (category, 2024 price, 2025 price, base quarterly units, 2025 growth)
PRODUCTS = {
    "Lumo Phone X2": ("Smartphones", 14500, 16200, 420, 1.04),
    "Lumo Tab 11": ("Tablets", 11800, 12400, 190, 0.91),
    "Aria Buds Pro": ("Audio", 2100, 2350, 980, 1.22),
    "Vista 55 TV": ("Televisions", 18900, 19800, 160, 1.09),
    "Breeze Smart AC": ("Appliances", 22500, 24900, 130, 1.18),
}
# name -> (relative size, 2025 growth)
REGIONS = {"Cairo": (1.0, 1.0), "Alexandria": (0.62, 1.05), "Delta": (0.48, 0.97), "Gulf Export": (0.35, 1.45)}
SEASON = {"Q1": 0.88, "Q2": 1.02, "Q3": 1.06, "Q4": 1.18}
CITIES = ["Cairo", "Alexandria", "Mansoura", "Dubai"]
DEPARTMENTS = {"Engineering": (14, 38000), "Sales": (16, 24000), "Customer Support": (10, 16500),
               "Finance": (6, 29000), "Human Resources": (5, 23000), "Logistics": (9, 17500)}


def make_sales() -> pd.DataFrame:
    rows = []
    for year in (2024, 2025):
        for quarter, season in SEASON.items():
            for region, (size, region_growth) in REGIONS.items():
                for product, (category, p24, p25, base, growth) in PRODUCTS.items():
                    factor = growth * region_growth if year == 2025 else 1.0
                    units = round(base * size * season * factor * random.uniform(0.94, 1.06))
                    price = p25 if year == 2025 else p24
                    rows.append((year, quarter, region, product, category, units, price, units * price))
    return pd.DataFrame(rows, columns=["year", "quarter", "region", "product", "category",
                                       "units_sold", "unit_price_egp", "revenue_egp"])


def make_employees() -> pd.DataFrame:
    rows, number = [], 1001
    for dept, (count, base) in DEPARTMENTS.items():
        for i in range(count):
            level = "Manager" if i == 0 else random.choice(["Senior", "Mid", "Mid", "Junior"])
            mult = {"Manager": 1.9, "Senior": 1.35, "Mid": 1.0, "Junior": 0.72}[level]
            salary = int(round(base * mult * random.uniform(0.93, 1.07), -2))
            rows.append((f"E{number}", dept, level, random.choice(CITIES), random.randint(2016, 2025), salary,
                         random.randint(0, 3), round(random.uniform(2.6, 4.9), 1)))
            number += 1
    return pd.DataFrame(rows, columns=["employee_id", "department", "level", "city", "hire_year",
                                       "monthly_salary_egp", "open_leave_requests", "performance_score"])


# --- Writers -----------------------------------------------------------------
styles = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=17, spaceBefore=14, spaceAfter=8)
BODY = ParagraphStyle("B", parent=styles["BodyText"], fontSize=10, leading=14, spaceAfter=8)
TITLE = ParagraphStyle("T", parent=styles["Title"], fontSize=22)


def pdf_table(rows):
    t = Table([[str(c) for c in r] for r in rows], hAlign="LEFT")
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                           ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dbe9f6")),
                           ("FONTSIZE", (0, 0), (-1, -1), 9)]))
    return t


def write_pdf(name, title, parts):
    def frame(canvas, doc):
        canvas.setFont("Helvetica", 8)
        canvas.drawString(2 * cm, A4[1] - 1.2 * cm, f"Nilora Electronics | {title} | Internal use only")
        canvas.drawRightString(A4[0] - 2 * cm, 1.1 * cm, f"Page {doc.page}")

    flow = [Paragraph(title, TITLE)]
    for kind, value in parts:
        if kind == "h1":
            flow.append(Paragraph(value, H1))
        elif kind == "p":
            flow.append(Paragraph(value, BODY))
        elif kind == "table":
            flow += [pdf_table(value), Spacer(1, 10)]
        elif kind == "break":
            flow.append(PageBreak())
    SimpleDocTemplate(str(OUT / name), pagesize=A4, title=title, topMargin=2 * cm, bottomMargin=2 * cm,
                      invariant=1).build(flow, onFirstPage=frame, onLaterPages=frame)


def write_docx(name, title, parts):
    d = Document()
    d.add_heading(title, 0)
    for kind, value in parts:
        if kind == "h1":
            d.add_heading(value, 1)
        elif kind == "p":
            d.add_paragraph(value)
        elif kind == "table":
            t = d.add_table(rows=0, cols=len(value[0]))
            t.style = "Table Grid"
            for row in value:
                for cell, text in zip(t.add_row().cells, row):
                    cell.text = str(text)
    d.save(OUT / name)


def m(x):
    return f"{x / 1e6:,.1f}"


# --- Documents ---------------------------------------------------------------
FACTS = {
    2024: dict(opex=0.214, cogs=0.611, stores=18, staff=52, nps=41, returns=4.8, rd=3.1, cfo="Tarek Nassar"),
    2025: dict(opex=0.198, cogs=0.603, stores=22, staff=60, nps=49, returns=3.9, rd=4.2, cfo="Dina Helmy"),
}
CONTEXT = {
    2024: "The year was shaped by currency volatility, longer shipping lead times through the Red Sea and strong demand "
          "for wireless audio.",
    2025: "The year was shaped by the expansion into Gulf markets, the launch of the Nilora Care service plan in March "
          "2025 and a company-wide programme to reduce product returns.",
}
RETURNS_NOTE = {
    2024: "Management identified packaging damage as the leading cause of returns.",
    2025: "The decrease compared with the previous year was attributed to the new pre-delivery inspection process and "
          "clearer product pages.",
}
RISKS = {
    2024: "Principal risks were foreign exchange exposure on imported components, dependence on two contract "
          "manufacturers and a shortage of certified air-conditioner installers.",
    2025: "Principal risks were new e-waste regulation in the Gulf, cyber attacks on the online store and continued "
          "dependence on two contract manufacturers. The installer shortage reported in 2024 was resolved by the Nilora "
          "Academy training programme.",
}
OUTLOOK = {
    2024: "For 2025 the board set three goals: grow Gulf Export revenue by at least 30 percent, raise the Net Promoter "
          "Score to 45 or higher and bring the return rate below 4.5 percent.",
    2025: "For 2026 the board plans to open four stores in Riyadh and Jeddah, retire the Lumo Tab line if sales do not "
          "recover by the end of Q2 and reach a Net Promoter Score of 55.",
}


def annual_report(sales, year):
    f, df = FACTS[year], sales[sales.year == year]
    rev = df.revenue_egp.sum()
    region = df.groupby("region").revenue_egp.sum().sort_values(ascending=False)
    category = df.groupby("category").revenue_egp.sum().sort_values(ascending=False)
    quarter = df.groupby("quarter").revenue_egp.sum()
    cogs, opex = rev * f["cogs"], rev * f["opex"]
    write_pdf(f"annual_report_{year}.pdf", f"Annual Report {year}", [
        ("h1", "Letter from the Chief Executive"),
        ("p", f"In {year} Nilora Electronics recorded total revenue of EGP {m(rev)} million. Mariam Fouad, Chief Executive "
              f"Officer, thanked the {f['staff']} permanent employees who served customers across {f['stores']} stores "
              f"and the online channel."),
        ("p", CONTEXT[year]),
        ("h1", "Financial Highlights"),
        ("p", "All amounts are in millions of Egyptian pounds (EGP) and are derived from the audited sales ledger."),
        ("table", [["Item", f"FY{year} (EGP million)"], ["Total revenue", m(rev)], ["Cost of goods sold", m(cogs)],
                   ["Gross profit", m(rev - cogs)], ["Operating expenses", m(opex)],
                   ["Operating profit", m(rev - cogs - opex)]]),
        ("p", f"Research and development spending was {f['rd']} percent of revenue. {f['cfo']} served as Chief Financial "
              f"Officer during {year}."),
        ("h1", "Revenue by Region"),
        ("table", [["Region", "Revenue (EGP million)", "Share"]] +
         [[r, m(v), f"{v / rev:.1%}"] for r, v in region.items()]),
        ("h1", "Revenue by Category"),
        ("table", [["Category", "Revenue (EGP million)", "Share"]] +
         [[c, m(v), f"{v / rev:.1%}"] for c, v in category.items()]),
        ("break", None),
        ("h1", "Quarterly Performance"),
        ("table", [["Quarter", "Revenue (EGP million)"]] + [[q, m(v)] for q, v in quarter.items()]),
        ("p", "The fourth quarter was the strongest because of the White Friday campaign in November."),
        ("h1", "Customer Experience"),
        ("p", f"The Net Promoter Score closed the year at {f['nps']}. The product return rate was {f['returns']} percent of "
              f"units sold. {RETURNS_NOTE[year]}"),
        ("h1", "Risks"),
        ("p", RISKS[year]),
        ("break", None),
        ("h1", "Outlook"),
        ("p", OUTLOOK[year]),
    ])


def policies():
    write_pdf("hr_handbook.pdf", "Human Resources Handbook", [
        ("h1", "Working Hours"),
        ("p", "The standard working week is 40 hours, Sunday to Thursday. Core hours, when all employees must be reachable, "
              "are 10:00 to 15:00 Cairo time. Overtime must be approved in writing by the line manager and is paid at 135 "
              "percent of the hourly rate on weekdays and 200 percent on public holidays. The hourly rate is the monthly "
              "base salary divided by 173."),
        ("h1", "Annual Leave"),
        ("p", "Employees receive 21 working days of paid annual leave per year. After ten years of service the entitlement "
              "rises to 30 working days. Up to 7 unused days may be carried over and must be used before 31 March of the "
              "following year; carried-over days are never paid out in cash. Requests longer than five consecutive days "
              "need at least three weeks of notice."),
        ("h1", "Sick Leave"),
        ("p", "Employees may take up to 15 days of sick leave per year at full pay, followed by 60 days at 75 percent of base "
              "salary. A medical certificate is required for absences longer than two days."),
        ("h1", "Parental Leave"),
        ("p", "Maternity leave is 120 calendar days at full pay. Paternity leave is 10 working days at full pay and must be "
              "taken within 90 days of the birth."),
        ("break", None),
        ("h1", "Probation and Notice"),
        ("p", "New employees complete a three-month probation period. After probation the notice period is one month for "
              "Junior and Mid levels and two months for Senior and Manager levels."),
        ("h1", "Performance and Bonus"),
        ("p", "Performance is scored from 1.0 to 5.0 every December. The annual bonus depends on the score as shown below and "
              "is calculated on monthly base salary."),
        ("table", [["Performance score", "Annual bonus"], ["4.5 and above", "2.0 monthly salaries"],
                   ["3.8 to 4.4", "1.25 monthly salaries"], ["3.0 to 3.7", "0.5 monthly salary"],
                   ["Below 3.0", "No bonus; improvement plan"]]),
        ("h1", "Training Budget"),
        ("p", "Each employee has a training budget of EGP 12,000 per year. Courses above EGP 8,000 require a commitment to "
              "stay twelve months; leaving earlier means repaying the cost pro rata."),
    ])
    write_pdf("warranty_and_returns.pdf", "Warranty and Returns Policy", [
        ("h1", "Standard Warranty"),
        ("p", "The standard warranty starts on the delivery date and covers manufacturing defects."),
        ("table", [["Product", "Standard warranty", "Nilora Care extension"], ["Lumo Phone X2", "12 months", "+12 months"],
                   ["Lumo Tab 11", "12 months", "+12 months"], ["Aria Buds Pro", "6 months", "+6 months"],
                   ["Vista 55 TV", "24 months", "+24 months"],
                   ["Breeze Smart AC", "36 months (compressor 60 months)", "+24 months"]]),
        ("h1", "Nilora Care Service Plan"),
        ("p", "Nilora Care costs 8 percent of the product price, paid once at purchase. It extends the warranty as shown in "
              "the standard warranty table and includes one accidental damage repair per year with a deductible of EGP "
              "500."),
        ("h1", "Returns"),
        ("p", "Unopened products may be returned within 30 days. Opened products may be returned within 14 days and a "
              "restocking fee of 10 percent applies, except when the product is defective. Earbuds cannot be returned once "
              "the hygiene seal is broken unless they are defective."),
        ("break", None),
        ("h1", "Exclusions"),
        ("p", "The warranty does not cover liquid damage, unauthorised repair, cosmetic scratches or power surges above 250 "
              "volts. Batteries are covered for six months regardless of the product."),
        ("h1", "Repair Times"),
        ("p", "Phones, tablets and earbuds are repaired within 7 working days. Televisions and air conditioners are repaired "
              "at home within 5 working days in Cairo and Alexandria and within 10 working days elsewhere. If a repair "
              "exceeds 21 working days the customer may choose a replacement or a full refund."),
    ])
    write_docx("travel_expense_policy.docx", "Travel and Expense Policy", [
        ("h1", "Approval"),
        ("p", "Domestic trips are approved by the line manager. International trips need approval from the department "
              "director and the Chief Financial Officer at least 14 days before departure."),
        ("h1", "Flights and Trains"),
        ("p", "Economy class is the standard for all flights. Business class is allowed only for flights longer than eight "
              "hours and with CFO approval. First class train tickets are allowed inside Egypt."),
        ("h1", "Hotel and Daily Allowance Limits"),
        ("p", "The limits below are per person per night for hotels and per person per day for the meal allowance."),
        ("table", [["Destination", "Hotel limit per night", "Daily meal allowance"],
                   ["Egypt", "EGP 3,200", "EGP 650"], ["Gulf countries", "USD 180", "USD 60"],
                   ["Europe", "EUR 160", "EUR 55"], ["Other countries", "USD 150", "USD 50"]]),
        ("h1", "Reimbursement"),
        ("p", "Claims must be submitted in the finance portal within 30 days of return with original receipts. Claims "
              "submitted after 30 days are reimbursed at 50 percent, and claims after 60 days are rejected. Expenses below "
              "EGP 200 do not need a receipt."),
        ("h1", "Non-reimbursable Items"),
        ("p", "Alcohol, traffic fines, in-flight upgrades, gym access and companion travel are not reimbursed."),
    ])
    write_docx("it_security_policy.docx", "IT and Information Security Policy", [
        ("h1", "Passwords and Authentication"),
        ("p", "Passwords must contain at least 14 characters and are changed every 180 days. Multi-factor authentication is "
              "mandatory for email, the finance portal and any remote access. Hardware keys are required for "
              "administrators."),
        ("h1", "Devices"),
        ("p", "Company laptops use full-disk encryption and lock after five minutes of inactivity. A lost or stolen device "
              "must be reported to the security desk within four hours."),
        ("h1", "Data Classification"),
        ("p", "Data is classified as Public, Internal, Confidential or Restricted. Customer payment data is Restricted and "
              "may never leave the payment network. Employee records are Confidential."),
        ("h1", "Use of AI Tools"),
        ("p", "Employees may use approved AI assistants with Public and Internal data. Confidential and Restricted data must "
              "not be entered into external AI tools. Generated code must be reviewed by a second engineer."),
        ("h1", "Incident Response"),
        ("table", [["Severity", "Example", "Response time"], ["SEV1", "Online store down or data breach", "15 minutes"],
                   ["SEV2", "Payment errors in one region", "1 hour"], ["SEV3", "Single user affected", "1 business day"]]),
        ("p", "Data breaches involving personal data are reported to the regulator within 72 hours."),
    ])
    (OUT / "remote_work_policy_2023.md").write_text("""# Remote Work Policy (2023)

Status: superseded on 1 January 2026 by the Remote Work Policy 2026.

## Eligibility
Employees become eligible for remote work after completing 12 months of service. Customer Support and Logistics staff are not eligible.

## Remote Days
Eligible employees may work remotely up to 1 day per week. Remote days cannot be combined with annual leave.

## Equipment
The company provides a laptop only. Internet costs are paid by the employee.

## Working from Abroad
Working from outside Egypt is not permitted.
""", encoding="utf-8")
    (OUT / "remote_work_policy_2026.md").write_text("""# Remote Work Policy (2026)

Status: in force from 1 January 2026. Replaces the Remote Work Policy 2023.

## Eligibility
Employees become eligible for remote work after completing the three-month probation period. Logistics staff are not eligible. Customer Support staff are eligible for the evening shift only.

## Remote Days
Eligible employees may work remotely up to 3 days per week. Managers may define one fixed office day for the whole team.

## Equipment
The company provides a laptop and a one-time home office allowance of EGP 6,000. Employees also receive an internet allowance of EGP 400 per month.

## Working from Abroad
Employees may work from another country for up to 20 working days per calendar year with approval from Human Resources and the security desk. All remote access requires multi-factor authentication.
""", encoding="utf-8")
    (OUT / "company_overview.md").write_text("""# Nilora Electronics Company Overview

## Who We Are
Nilora Electronics is a consumer electronics company founded in Cairo in 2012 by Mariam Fouad and Youssef Adel. It designs smartphones, tablets, audio products, televisions and smart air conditioners and sells them through its own stores and online.

## Product Lines
- Lumo Phone X2: 6.5 inch smartphone, 256 GB storage, 5000 mAh battery.
- Lumo Tab 11: 11 inch tablet for students, 128 GB storage, stylus included.
- Aria Buds Pro: noise cancelling earbuds, 30 hours of playback with the case.
- Vista 55 TV: 55 inch 4K television with Arabic voice control.
- Breeze Smart AC: 1.5 horsepower inverter air conditioner controlled from the Nilora app.

## Leadership
- Mariam Fouad, Chief Executive Officer since 2012.
- Dina Helmy, Chief Financial Officer since January 2025. She replaced Tarek Nassar.
- Youssef Adel, Chief Technology Officer. The Engineering department reports to him.
- Salma Rady, Director of Human Resources.
- Karim Osman, Director of Sales and Gulf Expansion.

## Offices
The headquarters is in New Cairo. Regional offices are in Alexandria, Mansoura and Dubai. The Dubai office opened in September 2024 and leads Gulf Export sales.

## Suppliers
Phones and tablets are assembled by Delta Assembly Co. in 10th of Ramadan City. Televisions and air conditioners are assembled by Sunrise Manufacturing in Port Said.
""", encoding="utf-8")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    sales = make_sales()
    sales.to_csv(OUT / "sales_data.csv", index=False)
    make_employees().to_csv(OUT / "employees.csv", index=False)
    for y in (2024, 2025):
        annual_report(sales, y)
    policies()
    for p in sorted(OUT.iterdir()):
        print(f"{p.name:32} {p.stat().st_size:>8,} bytes")
