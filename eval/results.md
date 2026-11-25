# Evaluation

## Retrieval (one raw query, no agent)

| Mode | Recall of needed documents, top 4 |
|---|---|
| hybrid | 15/16 (94%) |
| semantic | 15/16 (94%) |
| keyword | 12/16 (75%) |

## Answers

| System | Correct | Average tokens | Average seconds |
|---|---|---|---|
| Standard | 8/13 | 524 | 0.5 |
| Agentic | 13/13 | 6,943 | 14.1 |

| Question | Type | Standard | Agentic | Tool calls |
|---|---|---|---|---|
| fact-1 | single fact | yes | yes | 1 |
| fact-2 | single fact | yes | yes | 1 |
| fact-3 | single fact | yes | yes | 1 |
| arabic-1 | arabic | yes | yes | 1 |
| arabic-2 | arabic | yes | yes | 1 |
| compare-1 | comparison | no | yes | 3 |
| compare-2 | comparison | yes | yes | 3 |
| multi-1 | multi-hop | no | yes | 6 |
| multi-2 | multi-hop | no | yes | 2 |
| multi-3 | multi-hop | yes | yes | 1 |
| data-1 | data analysis | no | yes | 1 |
| data-2 | data analysis | no | yes | 1 |
| missing-1 | not in documents | yes | yes | 6 |

## All answers

### fact-1 - Standard (correct)

**Q:** How many days of annual leave does an employee with 12 years of service get?

Ein Mitarbeiter mit 12 Jahren Betriebszugehörigkeit hat Anspruch auf 30 Arbeitstage Jahresurlaub pro Jahr. [1]

Sources: hr_handbook.pdf - Annual Leave, p.1

### fact-1 - Agentic (correct)

**Q:** How many days of annual leave does an employee with 12 years of service get?

The employee is entitled to **30 working days of paid annual leave** per year. The HR handbook states that after ten years of service the leave entitlement rises to 30 days, so a staff member with 12 years of service receives this amount[1].

Sources: hr_handbook.pdf - Annual Leave, p.1

### fact-2 - Standard (correct)

**Q:** What is the hotel limit per night in the Gulf countries?

The hotel limit per night in the Gulf countries is USD 180 [1].

Sources: travel_expense_policy.docx - Hotel and Daily Allowance Limits

### fact-2 - Agentic (correct)

**Q:** What is the hotel limit per night in the Gulf countries?

The hotel limit per night in Gulf countries is **USD 180** per person [1].

Sources: travel_expense_policy.docx - Hotel and Daily Allowance Limits

### fact-3 - Standard (correct)

**Q:** Who assembles the Vista 55 TV?

Vista 55 TV is assembled by Sunrise Manufacturing in Port Said. [2]

Sources: company_overview.md - Suppliers

### fact-3 - Agentic (correct)

**Q:** Who assembles the Vista 55 TV?

The Vista 55 TV is assembled by Sunrise Manufacturing in Port Said[2].

Sources: company_overview.md - Suppliers

### arabic-1 - Standard (correct)

**Q:** كم عدد أيام إجازة الأبوة؟

إجازة الأبوة تبلغ 10 أيام عمل [1].

Sources: hr_handbook.pdf - Parental Leave, p.1

### arabic-1 - Agentic (correct)

**Q:** كم عدد أيام إجازة الأبوة؟

إجازة الأبوة هي 10 أيام عمل مدفوعة الأجر. تم استخراج هذه المعلومة من دليل الموارد البشرية حيث يذكر أن إجازة الأبوة تُمنح لمدة 10 أيام عمل [1]

Sources: hr_handbook.pdf - Parental Leave, p.1

### arabic-2 - Standard (correct)

**Q:** ما هي مدة الرد على حوادث SEV1؟

مدة الرد على حوادث SEV1 هي 15 دقيقة. [1]

Sources: it_security_policy.docx - Incident Response

### arabic-2 - Agentic (correct)

**Q:** ما هي مدة الرد على حوادث SEV1؟

مدة الرد على حوادث SEV1 هي **15 دقيقة**[1].

Sources: it_security_policy.docx - Incident Response

### compare-1 - Standard (wrong)

**Q:** How did the number of remote days per week and the eligibility period change between the 2023 and 2026 remote work policies?

The provided passages do not contain information about the number of remote days per week or the eligibility period in the 2026 Remote Work Policy, so the changes between the 2023 and 2026 policies cannot be determined from the given data.

Sources: none

### compare-1 - Agentic (correct)

**Q:** How did the number of remote days per week and the eligibility period change between the 2023 and 2026 remote work policies?

- 2023 policy: employees could work remotely **up to 1 day per week** and became eligible after **12 months of service**[1][3].  
- 2026 policy: employees may work remotely **up to 3 days per week** and become eligible after **the three‑month probation period**[5][9].  

Thus, the allowed remote days increased from 1 to 3 per week, and the eligibility period shortened from 12 months to three months.

Sources: remote_work_policy_2023.md - Remote Days; remote_work_policy_2023.md - Eligibility; remote_work_policy_2026.md - Remote Days; remote_work_policy_2026.md - Eligibility

### compare-2 - Standard (correct)

**Q:** Which risk from the 2024 annual report was resolved in 2025, and how?

The 2024 report listed a “shortage of certified air‑conditioner installers” as a principal risk [1]. In the 2025 report it is noted that this installer shortage was resolved through the Nilora Academy training programme [2].

Sources: annual_report_2024.pdf - Risks, p.2; annual_report_2025.pdf - Risks, p.2

### compare-2 - Agentic (correct)

**Q:** Which risk from the 2024 annual report was resolved in 2025, and how?

The risk that was resolved is the **shortage of certified air-conditioner installers**.

- In the 2024 annual report, the principal risks were: foreign exchange exposure on imported components, dependence on two contract manufacturers, and a shortage of certified air-conditioner installers [1].
- In the 2025 annual report, the principal risks were: new e-waste regulation in the Gulf, cyber attacks on the online store, and continued dependence on two contract manufacturers. The installer shortage reported in 2024 was resolved by the **Nilora Academy training programme** [5].

So the installer shortage was resolved through the Nilora Academy training programme, which trained and certified installers.

Sources: annual_report_2024.pdf - Risks, p.2; annual_report_2025.pdf - Risks, p.2

### multi-1 - Standard (wrong)

**Q:** Did Nilora meet all three goals the board set for 2025? Give the actual figure for each goal.

The passages do not provide the actual 2025 results for the three board‑set goals, so it cannot be determined whether Nilora met all of them.

Sources: none

### multi-1 - Agentic (correct)

**Q:** Did Nilora meet all three goals the board set for 2025? Give the actual figure for each goal.

Yes. Nilora met all three board goals for 2025.

- **Gulf Export revenue**: EGP 40.5 million [14] (up from 23.5 million in 2024, a ≈ 73 % increase, exceeding the 30 % target).  
- **Net Promoter Score (NPS)**: 49 [12] (above the 45‑point target).  
- **Return rate**: 3.9 % of units sold [12] (below the 4.5 % target).  

The figures were taken directly from the 2025 annual report and the 2024 outlook, confirming that each goal was achieved.

Sources: annual_report_2025.pdf - Customer Experience, p.2; annual_report_2025.pdf - Revenue by Region, p.1

### multi-2 - Standard (wrong)

**Q:** What does Nilora Care cost for a Breeze Smart AC at the 2025 price, and what is the total warranty length with it?

The provided passages do not contain the price of the Breeze Smart AC in 2025, so the cost of Nilora Care for that product cannot be determined from the given information.

Sources: none

### multi-2 - Agentic (correct)

**Q:** What does Nilora Care cost for a Breeze Smart AC at the 2025 price, and what is the total warranty length with it?

Nilora Care for a Breeze Smart AC costs **EGP 1,992** (8 % of the 2025 price of EGP 24,900) and extends the warranty to a total of **60 months** (the standard 36‑month warranty plus the 24‑month Nilora Care extension)[1][2][3].

Sources: sales_data.csv - SQL result; warranty_and_returns.pdf - Standard Warranty, p.1; warranty_and_returns.pdf - Nilora Care Service Plan, p.1

### multi-3 - Standard (correct)

**Q:** A manager earns EGP 45,000 per month and scored 4.6. What is the annual bonus, and what is the notice period?

The manager’s annual bonus is 2 × EGP 45,000 = EGP 90,000 [3].  
The notice period for a Manager after probation is two months [4].

Sources: hr_handbook.pdf - Performance and Bonus, p.2; hr_handbook.pdf - Probation and Notice, p.2

### multi-3 - Agentic (correct)

**Q:** A manager earns EGP 45,000 per month and scored 4.6. What is the annual bonus, and what is the notice period?

The manager’s annual bonus is **EGP 90,000** (2 × monthly salary of 45,000 EGP) because a performance score of 4.6 falls in the “4.5 and above” bracket that awards a bonus equal to two monthly salaries[1].  

The notice period for a manager is **two months** after the probation period[2].

Sources: hr_handbook.pdf - Performance and Bonus, p.2; hr_handbook.pdf - Probation and Notice, p.2

### data-1 - Standard (wrong)

**Q:** Which product sold the most units in the Gulf Export region in 2025, and how many?

The provided passages do not contain the specific sales figures needed to determine which product sold the most units in the Gulf Export region in 2025, nor the number of units sold.

Sources: none

### data-1 - Agentic (correct)

**Q:** Which product sold the most units in the Gulf Export region in 2025, and how many?

Aria Buds Pro sold the most units in the Gulf Export region in 2025, with a total of **2,490 units** sold[1].

Sources: sales_data.csv - SQL result

### data-2 - Standard (wrong)

**Q:** What is the average monthly salary in Engineering?

The provided passages describe the structure of the employee data but do not include the actual salary figures for the Engineering department, so the average monthly salary in Engineering cannot be determined from the given information.

Sources: none

### data-2 - Agentic (correct)

**Q:** What is the average monthly salary in Engineering?

The average monthly salary for employees in the Engineering department is **≈ 42,779 EGP**[1].

Sources: employees.csv - SQL result

### missing-1 - Standard (correct)

**Q:** What is the dental insurance coverage limit for employees?

The provided passages do not contain any information about a dental insurance coverage limit for employees.

Sources: none

### missing-1 - Agentic (correct)

**Q:** What is the dental insurance coverage limit for employees?

I couldn’t find any information in the company’s documents about a dental‑insurance coverage limit for employees. The available policy documents (HR handbook, travel expense policy, remote work policy, annual reports, etc.) do not mention dental benefits. If you need this detail, please check the employee benefits or insurance policy documents that are not included in the current knowledge base.

Sources: none
