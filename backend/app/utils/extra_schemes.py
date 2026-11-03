"""
Additional real central and Karnataka schemes for the demo database.

Figures are summarised from official scheme guidelines as of 2025-26. Amounts and limits
change - the app always tells users to confirm details on the official portal.
`ensure_extra_schemes` is idempotent: it only inserts schemes that are missing (by name),
so it is safe to run on every start-up and on an already-seeded database.
"""
import logging
from sqlalchemy.orm import Session

from app.models.scheme import Scheme, EligibilityRule

logger = logging.getLogger(__name__)

R = lambda field, op, value: {"field_name": field, "operator": op, "expected_value": value}  # noqa: E731

EXTRA_SCHEMES = [
    # ------------------------------------------------------------------ Business / startups
    {
        "name": "pm_mudra_yojana", "title": "Pradhan Mantri Mudra Yojana (PMMY)", "category": "Business",
        "ministry": "Ministry of Finance", "state": "Central", "is_for_startups": True,
        "description": "Collateral-free loans through banks, NBFCs and MFIs for non-farm micro and small businesses in manufacturing, trading and services.",
        "benefits": "Loans in four tiers: Shishu up to Rs. 50,000; Kishore Rs. 50,000 to 5 lakh; Tarun Rs. 5 to 10 lakh; Tarun Plus Rs. 10 to 20 lakh for borrowers who repaid an earlier Tarun loan. No collateral required.",
        "eligibility_criteria": "Indian citizens aged 18+ with a business plan for a non-farm income-generating micro enterprise. No default history with any bank.",
        "required_documents": "Aadhaar card, PAN card, Business plan or quotation, Proof of business address, Bank statement for 6 months, Passport-size photographs",
        "application_steps": "1. Prepare a business plan. 2. Apply at any bank or NBFC branch or on the Udyamimitra portal. 3. Submit KYC and business documents. 4. The bank appraises and sanctions the loan.",
        "rules": [R("age", ">=", "18")],
    },
    {
        "name": "stand_up_india", "title": "Stand-Up India Scheme", "category": "Business",
        "ministry": "Department of Financial Services, Ministry of Finance", "state": "Central",
        "is_for_startups": True, "is_for_women": True,
        "description": "Bank loans for SC/ST and women entrepreneurs setting up a new (greenfield) enterprise in manufacturing, services, trading or agri-allied activities.",
        "benefits": "Composite loan between Rs. 10 lakh and Rs. 1 crore covering up to 75% of project cost, with repayment over up to 7 years and an 18-month moratorium.",
        "eligibility_criteria": "SC/ST and/or women entrepreneurs aged 18+. The enterprise must be greenfield, and for non-individual enterprises at least 51% must be held by an SC/ST or woman entrepreneur.",
        "required_documents": "Aadhaar card, PAN card, Caste certificate (for SC/ST applicants), Project report, Proof of address, Partnership deed or company documents if applicable",
        "application_steps": "1. Register on standupmitra.in. 2. Fill in the loan application and choose a bank branch. 3. Submit documents to the bank. 4. The bank appraises and sanctions the loan.",
        "rules": [R("age", ">=", "18")],
    },
    {
        "name": "startup_india_seed_fund", "title": "Startup India Seed Fund Scheme (SISFS)", "category": "Business",
        "ministry": "DPIIT, Ministry of Commerce and Industry", "state": "Central", "is_for_startups": True,
        "description": "Early-stage funding through approved incubators for proof of concept, prototype development, product trials, market entry and commercialisation.",
        "benefits": "Grant of up to Rs. 20 lakh for proof of concept or prototype, and up to Rs. 50 lakh through convertible debentures or debt for market entry and scaling.",
        "eligibility_criteria": "DPIIT-recognised startups incorporated not more than 2 years before applying, with a viable business idea using technology, and not having received more than Rs. 10 lakh from other government schemes.",
        "required_documents": "DPIIT recognition certificate, Certificate of incorporation, Pitch deck and business plan, Founders' KYC, Bank account details",
        "application_steps": "1. Get DPIIT recognition on startupindia.gov.in. 2. Apply to up to three incubators on the SISFS portal. 3. Present to the incubator's seed management committee. 4. Funds are released in milestone-based instalments.",
        "rules": [R("startup_status", "==", "true")],
    },
    {
        "name": "pm_vishwakarma", "title": "PM Vishwakarma Scheme", "category": "Employment",
        "ministry": "Ministry of MSME", "state": "Central", "is_for_startups": True,
        "description": "End-to-end support for traditional artisans and craftspeople in 18 trades such as carpenters, tailors, potters, blacksmiths, cobblers and goldsmiths.",
        "benefits": "PM Vishwakarma certificate and ID card, skill training with a Rs. 500 daily stipend, Rs. 15,000 toolkit incentive, collateral-free loans of Rs. 1 lakh and then Rs. 2 lakh at 5% interest, and digital transaction incentives.",
        "eligibility_criteria": "Artisans or craftspeople aged 18+ working in one of the 18 listed family-based trades, self-employed on an unorganised basis. Only one member per family.",
        "required_documents": "Aadhaar card, Mobile number linked to Aadhaar, Bank account details, Ration card",
        "application_steps": "1. Register at a Common Service Centre with Aadhaar-based verification. 2. Verification by the Gram Panchayat or urban local body. 3. Receive the certificate and attend skill training. 4. Apply for the toolkit incentive and loan.",
        "rules": [R("age", ">=", "18"), R("occupation", "in", "self-employed, entrepreneur, unemployed")],
    },
    # ------------------------------------------------------------------ Education
    {
        "name": "central_sector_scholarship", "title": "Central Sector Scheme of Scholarship for College and University Students",
        "category": "Education", "ministry": "Ministry of Education", "state": "Central", "is_for_students": True,
        "description": "Merit-cum-means scholarship for students who scored above the 80th percentile in Class 12 and are pursuing regular degree courses.",
        "benefits": "Rs. 12,000 per year for the first three years of graduation and Rs. 20,000 per year for post-graduation.",
        "eligibility_criteria": "Above the 80th percentile in the Class 12 board exam, enrolled in a regular college course, family income up to Rs. 4.5 lakh per year, not receiving any other scholarship.",
        "required_documents": "Aadhaar card, Class 12 mark sheet, Income certificate, College admission or fee receipt, Bank account details",
        "application_steps": "1. Register on the National Scholarship Portal (scholarships.gov.in). 2. Fill in the application and upload documents. 3. The institute verifies the application. 4. The scholarship is paid directly into the bank account.",
        "rules": [R("student_status", "==", "true"), R("income", "<=", "450000")],
    },
    {
        "name": "post_matric_scholarship_minorities", "title": "Post Matric Scholarship for Minorities",
        "category": "Education", "ministry": "Ministry of Minority Affairs", "state": "Central", "is_for_students": True,
        "description": "Scholarship for students from notified minority communities studying from Class 11 up to PhD, including technical and vocational courses.",
        "benefits": "Admission and tuition fees reimbursed up to the scheme limits, plus a monthly maintenance allowance for day scholars and hostellers.",
        "eligibility_criteria": "Students from Muslim, Christian, Sikh, Buddhist, Jain or Parsi communities with at least 50% marks in the previous exam and family income up to Rs. 2 lakh per year.",
        "required_documents": "Aadhaar card, Minority community declaration, Income certificate, Previous year mark sheet, Fee receipt, Bank account details",
        "application_steps": "1. Register on the National Scholarship Portal. 2. Choose the post-matric minority scholarship and fill in the form. 3. Upload documents. 4. Institute and state verification, then direct payment.",
        "rules": [R("student_status", "==", "true"), R("income", "<=", "200000")],
    },
    {
        "name": "karnataka_vidyasiri", "title": "Vidyasiri Scholarship (Karnataka)", "category": "Education",
        "ministry": "Backward Classes Welfare Department, Karnataka", "state": "Karnataka", "is_for_students": True,
        "description": "Food and accommodation assistance for backward-class post-matric students in Karnataka who could not get a government hostel seat.",
        "benefits": "Rs. 1,500 per month for 10 months of the academic year.",
        "eligibility_criteria": "Karnataka students from backward classes in post-matric courses, not staying in a government hostel, with family income within the department's limit (Rs. 2.5 lakh for most categories).",
        "required_documents": "Aadhaar card, Caste and income certificate, SATS student ID, College admission receipt, Bank account details",
        "application_steps": "1. Apply on the State Scholarship Portal (ssp.karnataka.gov.in). 2. Fill in the post-matric application with Aadhaar authentication. 3. Submit the printout to your college. 4. Payment through DBT.",
        "rules": [R("state", "==", "karnataka"), R("student_status", "==", "true"), R("income", "<=", "250000")],
    },
    # ------------------------------------------------------------------ Agriculture
    {
        "name": "pm_fasal_bima_yojana", "title": "Pradhan Mantri Fasal Bima Yojana (PMFBY)", "category": "Agriculture",
        "ministry": "Ministry of Agriculture and Farmers Welfare", "state": "Central", "is_for_farmers": True,
        "description": "Crop insurance that protects farmers against crop loss from natural calamities, pests and diseases, from sowing to post-harvest.",
        "benefits": "Low farmer premium: 2% of the sum insured for Kharif crops, 1.5% for Rabi crops and 5% for commercial and horticultural crops. The government pays the rest of the premium.",
        "eligibility_criteria": "All farmers, including sharecroppers and tenant farmers, growing notified crops in notified areas.",
        "required_documents": "Aadhaar card, Land records or tenancy agreement, Sowing certificate, Bank account details",
        "application_steps": "1. Apply through your bank, a Common Service Centre or the PMFBY portal (pmfby.gov.in) before the cut-off date. 2. Pay the farmer share of the premium. 3. Report crop loss within 72 hours through the Crop Insurance app or helpline.",
        "rules": [R("occupation", "==", "farmer")],
    },
    {
        "name": "kisan_credit_card", "title": "Kisan Credit Card (KCC) Scheme", "category": "Agriculture",
        "ministry": "Ministry of Agriculture and Farmers Welfare", "state": "Central", "is_for_farmers": True,
        "description": "Revolving short-term credit for crop cultivation, post-harvest expenses and allied activities such as animal husbandry and fisheries.",
        "benefits": "Crop loans at 7% interest with a 3% prompt-repayment incentive, giving an effective rate of 4% on loans up to Rs. 3 lakh. Collateral-free up to the RBI limit.",
        "eligibility_criteria": "Owner-cultivators, tenant farmers, oral lessees and sharecroppers, and self-help or joint liability groups of farmers.",
        "required_documents": "Aadhaar card, Land ownership or cultivation records, Passport-size photograph, Bank account details",
        "application_steps": "1. Visit your bank branch or apply through the PM-Kisan portal. 2. Fill in the one-page KCC form. 3. Submit land and identity documents. 4. The bank fixes the credit limit and issues the card.",
        "rules": [R("occupation", "==", "farmer"), R("age", ">=", "18")],
    },
    # ------------------------------------------------------------------ Health, housing, social security
    {
        "name": "ayushman_bharat_pmjay", "title": "Ayushman Bharat - Pradhan Mantri Jan Arogya Yojana (PM-JAY)", "category": "Healthcare",
        "ministry": "Ministry of Health and Family Welfare", "state": "Central",
        "description": "Health insurance for poor and vulnerable families covering hospitalisation at empanelled public and private hospitals.",
        "benefits": "Cashless cover of up to Rs. 5 lakh per family per year for secondary and tertiary hospitalisation, including pre- and post-hospitalisation costs.",
        "eligibility_criteria": "Families identified as deprived in the SECC 2011 database and families covered under state schemes. All senior citizens aged 70+ are also covered regardless of income.",
        "required_documents": "Aadhaar card, Ration card, Mobile number",
        "application_steps": "1. Check eligibility on beneficiary.nha.gov.in or the Ayushman app. 2. Complete e-KYC to get the Ayushman card. 3. Show the card at any empanelled hospital for cashless treatment.",
        "rules": [],
    },
    {
        "name": "pmay_urban_2", "title": "Pradhan Mantri Awas Yojana - Urban 2.0", "category": "Housing",
        "ministry": "Ministry of Housing and Urban Affairs", "state": "Central",
        "description": "Help for urban families from economically weaker sections and low and middle income groups to build, buy or rent a pucca house.",
        "benefits": "Central assistance of up to Rs. 2.5 lakh per unit for building or buying a house, or an interest subsidy on home loans for EWS, LIG and MIG families.",
        "eligibility_criteria": "Urban families without a pucca house anywhere in India, with annual income up to Rs. 3 lakh (EWS), Rs. 3 to 6 lakh (LIG) or Rs. 6 to 9 lakh (MIG).",
        "required_documents": "Aadhaar card of all family members, Income certificate, Bank account details, Land documents (for self-construction), Declaration of not owning a pucca house",
        "application_steps": "1. Apply on pmay-urban.gov.in or at a Common Service Centre. 2. Choose the scheme component. 3. Verification by the urban local body. 4. Assistance released in instalments linked to construction.",
        "rules": [R("income", "<=", "900000")],
    },
    {
        "name": "atal_pension_yojana", "title": "Atal Pension Yojana (APY)", "category": "Social Welfare",
        "ministry": "Ministry of Finance (PFRDA)", "state": "Central",
        "description": "Guaranteed pension scheme mainly for workers in the unorganised sector.",
        "benefits": "Guaranteed monthly pension of Rs. 1,000 to Rs. 5,000 from age 60, depending on contribution. The same pension goes to the spouse, and the corpus to the nominee.",
        "eligibility_criteria": "Indian citizens aged 18 to 40 with a savings bank account. People who are or have been income-tax payers cannot join.",
        "required_documents": "Aadhaar card, Savings bank account, Mobile number",
        "application_steps": "1. Visit your bank or post office, or use net banking. 2. Fill in the APY registration form and choose the pension amount. 3. Contributions are auto-debited every month, quarter or half-year.",
        "rules": [R("age", ">=", "18"), R("age", "<=", "40")],
    },
    {
        "name": "pm_ujjwala_yojana", "title": "Pradhan Mantri Ujjwala Yojana (PMUY)", "category": "Women & Child",
        "ministry": "Ministry of Petroleum and Natural Gas", "state": "Central", "is_for_women": True,
        "description": "Free LPG connections for women from poor households so families can switch to clean cooking fuel.",
        "benefits": "Deposit-free LPG connection with the first refill and stove free of cost, plus a targeted subsidy on refills.",
        "eligibility_criteria": "Adult women (18+) from poor households (SC/ST, PMAY-G, AAY, forest dwellers and similar categories) with no existing LPG connection in the household.",
        "required_documents": "Aadhaar card, Ration card, Bank account details, Proof of address",
        "application_steps": "1. Apply online at pmuy.gov.in or at the nearest LPG distributor. 2. Submit the KYC form and documents. 3. The connection is released after verification.",
        "rules": [R("gender", "==", "female"), R("age", ">=", "18")],
    },
    {
        "name": "sukanya_samriddhi_yojana", "title": "Sukanya Samriddhi Yojana", "category": "Women & Child",
        "ministry": "Ministry of Finance", "state": "Central", "is_for_women": True,
        "description": "Small savings scheme for the education and marriage expenses of a girl child.",
        "benefits": "High government-notified interest rate, tax-free returns and deductions under Section 80C. Deposits from Rs. 250 to Rs. 1.5 lakh per year.",
        "eligibility_criteria": "Parents or legal guardians can open an account for a girl child below 10 years of age, for up to two daughters.",
        "required_documents": "Girl child's birth certificate, Parent's Aadhaar and PAN card, Proof of address",
        "application_steps": "1. Visit a post office or authorised bank. 2. Fill in the account opening form. 3. Make the first deposit (minimum Rs. 250).",
        "rules": [],
    },
    {
        "name": "pmkvy_4", "title": "Pradhan Mantri Kaushal Vikas Yojana 4.0 (PMKVY)", "category": "Employment",
        "ministry": "Ministry of Skill Development and Entrepreneurship", "state": "Central",
        "description": "Free short-term skill training and certification to improve employability, including industry-relevant and new-age courses.",
        "benefits": "Free training at accredited centres, government certification, and placement support.",
        "eligibility_criteria": "Indian nationals aged 15 to 45 who are school or college dropouts or unemployed, with an Aadhaar card and bank account.",
        "required_documents": "Aadhaar card, Bank account details, Educational certificates",
        "application_steps": "1. Register on the Skill India Digital Hub (skillindiadigital.gov.in). 2. Choose a course and training centre. 3. Complete training and the assessment to get certified.",
        "rules": [R("age", ">=", "15"), R("age", "<=", "45")],
    },
    # ------------------------------------------------------------------ Karnataka guarantees
    {
        "name": "karnataka_gruha_lakshmi", "title": "Gruha Lakshmi Scheme (Karnataka)", "category": "Women & Child",
        "ministry": "Women and Child Development Department, Karnataka", "state": "Karnataka", "is_for_women": True,
        "description": "Monthly financial support for the woman head of the family in Karnataka.",
        "benefits": "Rs. 2,000 per month credited directly to the woman head of the household.",
        "eligibility_criteria": "Women heads of family listed on an APL, BPL or Antyodaya ration card in Karnataka. Not available if the woman or her husband pays income tax or GST.",
        "required_documents": "Aadhaar card, Ration card, Aadhaar-linked bank account",
        "application_steps": "1. Apply through Seva Sindhu, Grama One, Bangalore One or Karnataka One centres. 2. Complete Aadhaar authentication. 3. Payment through DBT every month.",
        "rules": [R("state", "==", "karnataka"), R("gender", "==", "female"), R("age", ">=", "18")],
    },
    {
        "name": "karnataka_yuva_nidhi", "title": "Yuva Nidhi (Karnataka)", "category": "Employment",
        "ministry": "Skill Development, Entrepreneurship and Livelihood Department, Karnataka", "state": "Karnataka",
        "description": "Unemployment allowance for young graduates and diploma holders from Karnataka who have not found a job after finishing their course.",
        "benefits": "Rs. 3,000 per month for graduates and Rs. 1,500 per month for diploma holders, for up to two years or until they find a job.",
        "eligibility_criteria": "Karnataka domicile graduates or diploma holders who completed their course in 2023 or later, have been unemployed for at least six months after the result, and are not pursuing higher studies.",
        "required_documents": "Aadhaar card, Degree or diploma certificate, Domicile proof, Self-declaration of unemployment, Bank account details",
        "application_steps": "1. Apply on the Seva Sindhu portal. 2. Submit education and domicile details. 3. Make the monthly self-declaration of unemployment to keep receiving the allowance.",
        "rules": [R("state", "==", "karnataka"), R("occupation", "==", "unemployed"), R("education", "in", "graduate, post graduate")],
    },
]


def ensure_extra_schemes(db: Session) -> int:
    """Insert any EXTRA_SCHEMES that are not yet in the database. Returns how many were added."""
    from app.services.ai_service import ai_service  # local import avoids a circular import at start-up

    added = []
    for data in EXTRA_SCHEMES:
        if db.query(Scheme).filter(Scheme.name == data["name"]).first():
            continue
        fields = {k: v for k, v in data.items() if k != "rules"}
        scheme = Scheme(**fields)
        db.add(scheme)
        db.flush()
        for rule in data["rules"]:
            db.add(EligibilityRule(scheme_id=scheme.id, **rule))
        added.append(scheme)
    if not added:
        return 0
    db.commit()
    for scheme in added:
        try:
            text = "\n".join(str(v) for v in (scheme.title, scheme.description, scheme.benefits, scheme.eligibility_criteria) if v)
            ai_service.index_scheme_text(str(scheme.id), str(scheme.name), text)
        except Exception as e:  # indexing is best-effort
            logger.warning(f"Could not index {scheme.name}: {e}")
    logger.info(f"Added {len(added)} additional schemes to the database.")
    return len(added)
