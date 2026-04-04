"""
Generate synthetic PDF documents for AHCAM.

Creates:
- 10 CAMA contracts
- 10 invoices / collection statements
- 5 distribution agreements
- 5 interparty agreements

Usage: python doc-data/generate_docs.py
"""

import os
import sys
import random
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from fpdf import FPDF

OUT_DIR = Path(__file__).parent
random.seed(42)

PRODUCTIONS = [
    ("The Last Horizon", "Sarah Chen", "David Park", "$28M"),
    ("Midnight in Marrakech", "Jean-Luc Moreau", "Sofia Alvarez", "$12M"),
    ("Broken Strings", "Michael Torres", "Ava Williams", "$8.5M"),
    ("Wild Pacific", "Emma Nakamura", "", "$3.2M"),
    ("Neon Knights", "Robert Kim", "James Wan", "$45M"),
    ("The Baker's Daughter", "Helen Murray", "Richard Curtis", "$5.5M"),
    ("Kingdom of Dust", "Ahmed Hassan", "Denis Villeneuve", "$35M"),
    ("Code Red", "Patricia Wells", "Taylor Sheridan", "$22M"),
    ("Summer of '82", "Greta Hoffmann", "Luca Guadagnino", "$9M"),
    ("Ghost Fleet", "Nina Patel", "Jordan Peele", "$15M"),
]

DISTRIBUTORS = [
    ("Global Screen Distribution", "Munich, Germany"),
    ("Lionsgate International", "Santa Monica, CA"),
    ("Pathe Distribution", "Paris, France"),
    ("Toho International", "Tokyo, Japan"),
    ("Pacific Rim Distributors", "Sydney, Australia"),
]

FINANCIERS = [
    ("Apex Film Finance", "New York, NY"),
    ("Eagle Point Investors", "New York, NY"),
    ("Mediterranean Film Fund", "Madrid, Spain"),
]

BANKS = [
    ("JP Morgan Chase", "383 Madison Ave, New York, NY 10179"),
    ("BNP Paribas", "16 Boulevard des Italiens, 75009 Paris"),
    ("Barclays Bank", "1 Churchill Place, London E14 5HP"),
    ("Wells Fargo", "420 Montgomery St, San Francisco, CA 94104"),
]

TERRITORIES = [
    "North America", "UK & Ireland", "Germany/Austria/Switzerland",
    "France", "Italy", "Spain", "Scandinavia", "Japan",
    "Australia/New Zealand", "Latin America",
]


class StyledPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(0, 102, 204)
        self.cell(0, 8, "ASHLAND HILL MEDIA FINANCE", align="R")
        self.ln(4)
        self.set_draw_color(0, 102, 204)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Confidential | Page {self.page_no()}/{{nb}}", align="C")

    def section(self, title):
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(30, 41, 59)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)

    def field(self, label, value):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(100, 116, 139)
        self.cell(55, 6, label + ":")
        self.set_font("Helvetica", "", 9)
        self.set_text_color(30, 41, 59)
        self.cell(0, 6, str(value), new_x="LMARGIN", new_y="NEXT")

    def body_text(self, text):
        self.set_font("Helvetica", "", 9)
        self.set_text_color(30, 41, 59)
        self.multi_cell(0, 5, text)
        self.ln(2)


def gen_date(base_year=2024):
    return datetime(base_year, random.randint(1, 12), random.randint(1, 28))


def gen_ref(prefix, idx):
    return f"{prefix}-{gen_date().strftime('%Y')}-{idx:04d}"


# ---------------------------------------------------------------------------
# 1. CAMA Contracts (10)
# ---------------------------------------------------------------------------

def generate_cama(idx, prod):
    title, producer, director, budget = prod
    bank = random.choice(BANKS)
    financier = random.choice(FINANCIERS)
    date = gen_date()
    ref = gen_ref("CAMA", idx + 1)

    pdf = StyledPDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 12, "COLLECTION ACCOUNT MANAGEMENT AGREEMENT", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    pdf.section("1. PARTIES")
    pdf.field("Agreement Reference", ref)
    pdf.field("Date", date.strftime("%B %d, %Y"))
    pdf.field("Production", title)
    pdf.field("Producer", producer)
    pdf.field("Director", director or "TBD")
    pdf.field("Budget", budget)
    pdf.field("Senior Financier", f"{financier[0]}, {financier[1]}")
    pdf.field("Collection Account Manager", "Ashland Hill Media Finance LLC")
    pdf.field("Bank", f"{bank[0]}, {bank[1]}")
    pdf.ln(4)

    pdf.section("2. COLLECTION ACCOUNT")
    pdf.body_text(
        f"The Collection Account Manager shall establish and maintain a segregated collection "
        f"account (the \"Collection Account\") at {bank[0]} for the purpose of receiving all "
        f"revenues derived from the exploitation of the Production \"{title}\" in all media and "
        f"all territories worldwide."
    )
    pdf.body_text(
        "All revenues from the exploitation of the Production shall be paid directly into the "
        "Collection Account. No party shall have the right to direct payment of revenues to any "
        "account other than the Collection Account without the prior written consent of the "
        "Collection Account Manager and the Senior Financier."
    )
    pdf.ln(2)

    pdf.section("3. WATERFALL / RECOUPMENT SCHEDULE")
    pdf.body_text("The Collection Account Manager shall disburse funds from the Collection Account in the following priority order:")
    pdf.ln(2)

    rules = [
        (1, "Collection Account Manager Fee", "Fixed", "2% of gross receipts, cap $200,000"),
        (2, f"{financier[0]} -Senior Debt", "Percentage", f"100% of remaining until full recoupment of {budget}"),
        (3, "Completion Bond Fee", "Fixed", f"3% of budget = ${int(float(budget.replace('$','').replace('M','')) * 30000):,}"),
        (4, "Sales Agent Commission", "Percentage", f"{random.choice([10, 12.5, 15, 20])}% of gross receipts"),
        (5, f"{producer} -Producer Fee", "Percentage", f"{random.choice([5, 7.5, 10])}% deferred"),
        (6, "Net Profit Participants", "Residual", "All remaining net profits per Interparty Agreement"),
    ]

    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(241, 245, 249)
    pdf.cell(15, 6, "Priority", border=1, fill=True)
    pdf.cell(55, 6, "Recipient", border=1, fill=True)
    pdf.cell(30, 6, "Type", border=1, fill=True)
    pdf.cell(90, 6, "Terms", border=1, fill=True, new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 8)
    for pri, recip, rtype, terms in rules:
        pdf.cell(15, 6, str(pri), border=1)
        pdf.cell(55, 6, recip[:30], border=1)
        pdf.cell(30, 6, rtype, border=1)
        pdf.cell(90, 6, terms[:50], border=1, new_x="LMARGIN", new_y="NEXT")

    pdf.ln(4)

    pdf.section("4. REPORTING")
    pdf.body_text(
        "The Collection Account Manager shall provide quarterly collection account statements "
        "to all parties listed herein, detailing: (a) all receipts into the Collection Account; "
        "(b) all disbursements from the Collection Account; (c) the current balance; and "
        "(d) the recoupment position of each participant."
    )

    pdf.section("5. TERM AND TERMINATION")
    pdf.body_text(
        f"This Agreement shall commence on {date.strftime('%B %d, %Y')} and shall continue "
        f"for a period of fifteen (15) years or until all obligations under the waterfall "
        f"have been fully satisfied, whichever is later."
    )

    pdf.section("6. GOVERNING LAW")
    pdf.body_text(
        "This Agreement shall be governed by and construed in accordance with the laws of "
        "the State of New York, without regard to its conflict of laws principles."
    )

    pdf.add_page()
    pdf.section("7. SIGNATURES")
    for party in [producer, financier[0], "Ashland Hill Media Finance LLC"]:
        pdf.ln(8)
        pdf.line(10, pdf.get_y(), 90, pdf.get_y())
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 5, party, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(150, 150, 150)
        pdf.cell(0, 5, f"Date: {date.strftime('%B %d, %Y')}", new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(30, 41, 59)

    fname = f"CAMA_{title.replace(' ', '_')}_{ref}.pdf"
    pdf.output(str(OUT_DIR / fname))
    return fname


# ---------------------------------------------------------------------------
# 2. Invoices / Collection Statements (10)
# ---------------------------------------------------------------------------

def generate_invoice(idx, prod):
    title, producer, director, budget = prod
    dist = random.choice(DISTRIBUTORS)
    date = gen_date()
    ref = gen_ref("INV", idx + 1)
    territory = random.choice(TERRITORIES)
    amount = random.randint(50, 2000) * 1000

    pdf = StyledPDF()
    pdf.alias_nb_pages()
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 12, "COLLECTION ACCOUNT STATEMENT", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    pdf.section("STATEMENT DETAILS")
    pdf.field("Reference", ref)
    pdf.field("Statement Date", date.strftime("%B %d, %Y"))
    pdf.field("Period", f"{(date - timedelta(days=90)).strftime('%b %Y')} - {date.strftime('%b %Y')}")
    pdf.field("Production", title)
    pdf.field("Producer", producer)
    pdf.ln(2)

    pdf.section("RECEIPTS")
    num_receipts = random.randint(2, 5)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(241, 245, 249)
    pdf.cell(35, 6, "Date", border=1, fill=True)
    pdf.cell(55, 6, "Source", border=1, fill=True)
    pdf.cell(40, 6, "Territory", border=1, fill=True)
    pdf.cell(30, 6, "Reference", border=1, fill=True)
    pdf.cell(30, 6, "Amount", border=1, fill=True, new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 8)
    total = 0
    for j in range(num_receipts):
        d = random.choice(DISTRIBUTORS)
        t = random.choice(TERRITORIES)
        a = random.randint(100, 800) * 1000
        total += a
        rdate = (date - timedelta(days=random.randint(5, 85))).strftime("%Y-%m-%d")
        pdf.cell(35, 6, rdate, border=1)
        pdf.cell(55, 6, d[0][:30], border=1)
        pdf.cell(40, 6, t[:22], border=1)
        pdf.cell(30, 6, f"REC-{random.randint(1000,9999)}", border=1)
        pdf.cell(30, 6, f"${a:,.0f}", border=1, new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(160, 6, "Total Receipts:", border=1, align="R")
    pdf.cell(30, 6, f"${total:,.0f}", border=1, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    pdf.section("DISBURSEMENTS")
    pdf.body_text("No disbursements processed during this period. Funds held pending waterfall execution.")
    pdf.ln(2)

    pdf.section("ACCOUNT BALANCE")
    prev_bal = random.randint(500, 5000) * 1000
    pdf.field("Opening Balance", f"${prev_bal:,.0f}")
    pdf.field("Total Receipts", f"${total:,.0f}")
    pdf.field("Total Disbursements", "$0")
    pdf.set_font("Helvetica", "B", 10)
    pdf.field("Closing Balance", f"${prev_bal + total:,.0f}")

    pdf.ln(6)
    pdf.body_text(
        "This statement has been prepared by Ashland Hill Media Finance LLC in its capacity "
        "as Collection Account Manager. All figures are subject to final audit confirmation."
    )

    fname = f"STMT_{title.replace(' ', '_')}_{ref}.pdf"
    pdf.output(str(OUT_DIR / fname))
    return fname


# ---------------------------------------------------------------------------
# 3. Distribution Agreements (5)
# ---------------------------------------------------------------------------

def generate_distribution(idx):
    prod = PRODUCTIONS[idx]
    title, producer, director, budget = prod
    dist = DISTRIBUTORS[idx % len(DISTRIBUTORS)]
    territory = TERRITORIES[idx % len(TERRITORIES)]
    mg = random.randint(200, 3000) * 1000
    date = gen_date()
    ref = gen_ref("DIST", idx + 1)

    pdf = StyledPDF()
    pdf.alias_nb_pages()
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 12, "DISTRIBUTION AGREEMENT", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    pdf.section("1. PARTIES AND PRODUCTION")
    pdf.field("Agreement Reference", ref)
    pdf.field("Date", date.strftime("%B %d, %Y"))
    pdf.field("Licensor", producer)
    pdf.field("Distributor", f"{dist[0]}, {dist[1]}")
    pdf.field("Production", title)
    pdf.field("Director", director or "TBD")
    pdf.ln(2)

    pdf.section("2. TERRITORY AND RIGHTS")
    pdf.field("Licensed Territory", territory)
    pdf.field("Licensed Rights", "All media including theatrical, home video, VOD, SVOD, TV")
    pdf.field("License Period", f"{random.choice([10, 15, 20, 25])} years from delivery")
    pdf.ln(2)

    pdf.section("3. FINANCIAL TERMS")
    pdf.field("Minimum Guarantee (MG)", f"${mg:,.0f}")
    pdf.field("Distribution Fee", f"{random.choice([25, 30, 35])}% of gross receipts")
    pdf.field("Distribution Expenses Cap", f"${random.randint(50, 200) * 1000:,.0f}")
    pdf.field("Payment Schedule", "50% on execution, 50% on delivery")
    pdf.ln(2)

    pdf.section("4. DELIVERY")
    pdf.body_text(
        f"The Licensor shall deliver to the Distributor all delivery materials as specified "
        f"in the Delivery Schedule attached hereto as Exhibit A within thirty (30) days of "
        f"completion of the Production."
    )

    pdf.section("5. COLLECTION ACCOUNT")
    pdf.body_text(
        f"All revenues from the exploitation of the Production in the Territory shall be "
        f"paid directly into the Collection Account maintained by Ashland Hill Media Finance LLC "
        f"as Collection Account Manager, in accordance with the CAMA dated {date.strftime('%B %d, %Y')}."
    )

    fname = f"DIST_{title.replace(' ', '_')}_{territory.replace('/', '_').replace(' ', '_')}_{ref}.pdf"
    pdf.output(str(OUT_DIR / fname))
    return fname


# ---------------------------------------------------------------------------
# 4. Interparty Agreements (5)
# ---------------------------------------------------------------------------

def generate_interparty(idx):
    prod = PRODUCTIONS[idx + 5]
    title, producer, director, budget = prod
    financier = FINANCIERS[idx % len(FINANCIERS)]
    date = gen_date()
    ref = gen_ref("IPA", idx + 1)

    pdf = StyledPDF()
    pdf.alias_nb_pages()
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 12, "INTERPARTY AGREEMENT", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    pdf.section("1. PARTIES")
    pdf.field("Agreement Reference", ref)
    pdf.field("Date", date.strftime("%B %d, %Y"))
    pdf.field("Production", title)
    pdf.field("Producer", producer)
    pdf.field("Senior Financier", f"{financier[0]}, {financier[1]}")
    pdf.field("Collection Account Manager", "Ashland Hill Media Finance LLC")
    pdf.ln(2)

    pdf.section("2. PURPOSE")
    pdf.body_text(
        "This Interparty Agreement sets forth the respective rights and obligations of the "
        "parties with respect to the recoupment of their respective investments in the "
        f"Production \"{title}\" and the distribution of net profits therefrom."
    )

    pdf.section("3. RECOUPMENT ORDER")
    pdf.body_text(
        "The parties agree that all revenues from the Production shall be applied in the "
        "following order of priority, as further detailed in the Collection Account Management "
        "Agreement:"
    )
    priorities = [
        "Collection Account Manager fees and expenses",
        f"{financier[0]} -recoupment of senior financing",
        "Completion bond premium",
        "Sales agent commission",
        f"{producer} -deferred producer fee",
        "Net profit participations per individual agreements",
    ]
    for i, p in enumerate(priorities, 1):
        pdf.body_text(f"   {i}. {p}")

    pdf.section("4. NET PROFIT DEFINITION")
    pdf.body_text(
        "\"Net Profits\" shall mean all gross receipts from the exploitation of the Production "
        "in all media and territories worldwide, less: (a) all amounts disbursed under Priorities "
        "1 through 5 above; (b) any amounts required to be withheld for taxes; and (c) any "
        "reserves established by the Collection Account Manager for disputed claims."
    )

    pdf.section("5. DISPUTE RESOLUTION")
    pdf.body_text(
        "Any dispute arising under this Agreement shall be resolved by binding arbitration "
        "in New York, New York under the rules of the American Arbitration Association."
    )

    fname = f"IPA_{title.replace(' ', '_')}_{ref}.pdf"
    pdf.output(str(OUT_DIR / fname))
    return fname


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=== AHCAM Document Generator ===\n")

    files = []

    # 10 CAMA contracts
    print("Generating CAMA contracts...")
    for i, prod in enumerate(PRODUCTIONS):
        f = generate_cama(i, prod)
        files.append(("cama", f))
        print(f"  {f}")

    # 10 Collection statements
    print("\nGenerating collection statements...")
    for i, prod in enumerate(PRODUCTIONS):
        f = generate_invoice(i, prod)
        files.append(("statement", f))
        print(f"  {f}")

    # 5 Distribution agreements
    print("\nGenerating distribution agreements...")
    for i in range(5):
        f = generate_distribution(i)
        files.append(("distribution", f))
        print(f"  {f}")

    # 5 Interparty agreements
    print("\nGenerating interparty agreements...")
    for i in range(5):
        f = generate_interparty(i)
        files.append(("interparty", f))
        print(f"  {f}")

    print(f"\n{'='*50}")
    print(f"Generated {len(files)} PDF documents in {OUT_DIR}/")
    print(f"  CAMA contracts:          10")
    print(f"  Collection statements:   10")
    print(f"  Distribution agreements:  5")
    print(f"  Interparty agreements:    5")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
