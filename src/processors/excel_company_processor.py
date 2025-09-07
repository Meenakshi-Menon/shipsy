import pandas as pd
import json
from src.agents.revenue_agent import DeepSeekRevenueAgent
from src.agents.contact_agent import run_contact_agent


class ExcelCompanyProcessor:
    def __init__(self, excel_file: str):
        self.excel_file = excel_file
        self.agent = DeepSeekRevenueAgent()

    # -----------------------------
    # PART A - Companies
    # -----------------------------
    def process_companies(self, input_sheet="Companies", output_sheet="Company Results"):
        df = pd.read_excel(self.excel_file, sheet_name=input_sheet)
        results = []

        for _, row in df.iterrows():
            company_name = row.get("Company Name", "")
            company_domain = row.get("Company Domain", "")

            analysis = self.agent.analyze_company_revenue(company_name, company_domain)

            # Assign tier (static logic)
            revenue = analysis["estimated_revenue_usd"]
            if revenue is None:
                tier = "Unknown"
            elif revenue > 1_000_000_000:
                tier = "Super Platinum"
            elif revenue >= 500_000_000:
                tier = "Platinum"
            elif revenue >= 100_000_000:
                tier = "Diamond"
            else:
                tier = "Gold"

            results.append({
                "Company Name": company_name,
                "Company Domain": company_domain,
                "Estimated Revenue (USD)": revenue,
                "Tier": tier,
                "Citation": analysis["citation"]
            })

        # Write to Excel
        results_df = pd.DataFrame(results)
        with pd.ExcelWriter(self.excel_file, mode="a", if_sheet_exists="replace") as writer:
            results_df.to_excel(writer, sheet_name=output_sheet, index=False)

        # ✅ Also save to JSON
        with open("company_results.json", "w") as f:
            json.dump(results, f, indent=4)

        print(f"✅ Companies processed. Results saved to Excel ({output_sheet}) and company_results.json")

    # -----------------------------
    # PART B - Contacts
    # -----------------------------
    def process_contacts(self, input_sheet="Contacts", output_sheet="Contact Results"):
        df = pd.read_excel(self.excel_file, sheet_name=input_sheet)
        results = []

        for _, row in df.iterrows():
            contact_name = row["Full Name"]
            company_name = row["Current Company"]
            company_domain = row.get("Company Domain", "")

            # Call contact agent
            linkedin_url, job_title, email, citation = run_contact_agent(contact_name, company_name, company_domain)

            # Fallbacks in case agent doesn’t return
            if not linkedin_url:
                linkedin_url = f"https://www.linkedin.com/in/{contact_name.lower().replace(' ', '')}"
            if not job_title:
                job_title = "Unknown (needs contact agent)"
            if not email and company_domain:
                first, last = contact_name.split(" ")[0], contact_name.split(" ")[-1]
                email = f"{first.lower()}.{last.lower()}@{company_domain}"

            results.append({
                "Contact Name": contact_name,
                "Company Name": company_name,
                "LinkedIn URL": linkedin_url,
                "Current Job Title": job_title,
                "Work Email": email,
                "Citation": citation
            })

        # Write to Excel
        results_df = pd.DataFrame(results)
        with pd.ExcelWriter(self.excel_file, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
            results_df.to_excel(writer, sheet_name=output_sheet, index=False)

        # ✅ Also save to JSON
        with open("contact_results.json", "w") as f:
            json.dump(results, f, indent=4)

        print(f"✅ Contacts processed. Results saved to Excel ({output_sheet}) and contact_results.json")



