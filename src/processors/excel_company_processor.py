import pandas as pd
from src.agents.revenue_agent import DeepSeekRevenueAgent
from src.agents.contact_agent import run_contact_agent


class ExcelCompanyProcessor:
    def __init__(self, excel_file: str):
        self.excel_file = excel_file
        self.agent = DeepSeekRevenueAgent()

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

        results_df = pd.DataFrame(results)
        with pd.ExcelWriter(self.excel_file, mode="a", if_sheet_exists="replace") as writer:
            results_df.to_excel(writer, sheet_name=output_sheet, index=False)

    # -----------------------------
    # NEW PART B
    # -----------------------------
    def process_contacts(self, input_sheet="Contacts", output_sheet="Contact Results"):
        df = pd.read_excel(self.excel_file, sheet_name=input_sheet)
        results = []

        for _, row in df.iterrows():
            contact_name = row["Full Name"]
            company_name = row["Current Company"]
            company_domain = row.get("Company Domain", "")

            # Call agent for LinkedIn + Job Title
              # reuse agent, but adapt for contact info later if you create a dedicated contact agent
            linkedin_url, job_title,email,citation = run_contact_agent(contact_name, company_name, company_domain)
            # Simple LinkedIn + Title mock (replace with real contact agent later)
            linkedin_url = f"https://www.linkedin.com/in/{contact_name.lower().replace(' ', '')}"
            job_title = "Unknown (needs contact agent)"  

            # Generate email
            if company_domain and "@" not in contact_name:
                first, last = contact_name.split(" ")[0], contact_name.split(" ")[-1]
                email = f"{first.lower()}.{last.lower()}@{company_domain}"
            else:
                email = ""

            results.append({
                "Contact Name": contact_name,
                "Company Name": company_name,
                "LinkedIn URL": linkedin_url,
                "Current Job Title": job_title,
                "Work Email": email,
                "Citation": citation
            })

        results_df = pd.DataFrame(results)
        with pd.ExcelWriter(self.excel_file, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
            results_df.to_excel(writer, sheet_name=output_sheet, index=False)

        print(f"✅ Contacts processed and written to {self.excel_file} (sheet: {output_sheet})")

