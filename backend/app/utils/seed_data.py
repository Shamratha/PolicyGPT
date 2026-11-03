import logging
from sqlalchemy.orm import Session
from app.database import SessionLocal, Base, engine
from app.models.user import User
from app.models.profile import Profile
from app.models.scheme import Scheme, EligibilityRule, SavedScheme, SearchHistory
from app.models.application import Application
from app.models.survey import Survey
from app.models.analytics import AnalyticsEvent
from app.services.ai_service import ai_service
from app.utils.extra_schemes import ensure_extra_schemes
import random
from datetime import datetime

logger = logging.getLogger(__name__)

# Scheme Guideline texts for ChromaDB indexing
SCHEME_GUIDELINES = {
    "karnataka_udyogini": (
        "Karnataka Udyogini Scheme Guidelines:\n"
        "The Department of Women and Child Development, Karnataka, offers the Udyogini Scheme to support women "
        "entrepreneurs in launching retail, agricultural, or cottage businesses. Financial support includes loans up to "
        "Rs. 3,00,000 with a subsidy ranging from 30% to 50% for SC/ST and special categories. Eligible candidates are "
        "females aged 18 to 55 residing in Karnataka. The family annual income must not exceed Rs. 1,500,000. "
        "Eligible activities include tailoring, grocery retail, bakeries, handicrafts, and typing institutes. "
        "Required documents for filing include Aadhaar Card, Karnataka residency/domicile certificate, "
        "family income certificate verified by the local Tahsildar, caste certificate (if applicable), and "
        "a project proposal report detailing business setup costs."
    ),
    "pmegp": (
        "Prime Minister Employment Generation Programme (PMEGP) Guidelines:\n"
        "PMEGP is a major credit-linked subsidy scheme under the Ministry of MSME, Government of India, aimed at "
        "generating self-employment opportunities through new micro-enterprises in rural and urban areas. "
        "Any individual above 18 years of age is eligible to apply. There is no income ceiling. For manufacturing "
        "units, projects up to Rs. 50 Lakhs are eligible; for service sector units, projects up to Rs. 20 Lakhs "
        "are funded. The government subsidy ranges from 15% to 35% of the project cost depending on location "
        "(rural/urban) and social category. Applications are filed online via the KVIC portal. The applicant "
        "must present a detailed project report (DPR), bank passbook, Aadhaar card, and education certificate."
    ),
    "rajiv_gandhi_scholarship": (
        "Rajiv Gandhi Scholarship for Technical Studies Guidelines:\n"
        "The Department of Higher Education, Karnataka, provides this merit-cum-means scholarship for students "
        "enrolled in engineering, medical, or management professional courses. It offers full reimbursement of "
        "college tuition fees and a monthly stipend of Rs. 2,000 during the academic year. To qualify, "
        "the student must be a resident of Karnataka, currently enrolled in a recognized university, and have a family "
        "annual income below Rs. 2,50,000. Required documents include the college admission confirmation receipt, "
        "previous academic year marksheet, domicile certificate, and income proof."
    ),
    "pm_kisan": (
        "Pradhan Mantri Kisan Samman Nidhi (PM-KISAN) Guidelines:\n"
        "PM-KISAN is a central sector scheme under the Ministry of Agriculture and Farmers Welfare, Government of India. "
        "It provides income support of Rs. 6,000 per year in three equal installments of Rs. 2,000 directly into the bank "
        "accounts of all landholding farmer families. There is no limit on land size, but institutional landholders, "
        "taxpayers, and retired government employees are excluded. Farmers must register using land records, "
        "bank passbook details, and Aadhaar card. Aadhaar-seeded bank accounts are mandatory for fund dispersion."
    )
}

def seed_database():
    db = SessionLocal()
    
    # 1. Create tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database schemas verified.")

    # 2. Check if already seeded
    if db.query(Scheme).first():
        logger.info("Database already contains seeded schemes. Skipping SQL seed.")
        try:
            ensure_extra_schemes(db)
        except Exception as e:
            logger.error(f"Could not add extra schemes: {e}")
            db.rollback()
        finally:
            db.close()
        return

    logger.info("Beginning data seeding...")

    try:
        # Create standard test users to associate survey responses
        user1 = User(email="test-karnataka-female@policygpt.ai", clerk_id="user_clerk_karnataka_female_1")
        user2 = User(email="test-farmer@policygpt.ai", clerk_id="user_clerk_farmer_2")
        user3 = User(email="test-student@policygpt.ai", clerk_id="user_clerk_student_3")
        db.add_all([user1, user2, user3])
        db.flush()

        profile1 = Profile(
            user_id=user1.id, name="Aishwarya R", age=22, gender="Female", state="Karnataka",
            education="Graduate", occupation="Unemployed", income=120000, startup_status=True, student_status=False
        )
        profile2 = Profile(
            user_id=user2.id, name="Ramesh Gowda", age=45, gender="Male", state="Karnataka",
            education="10th Pass", occupation="Farmer", income=60000, startup_status=False, student_status=False
        )
        profile3 = Profile(
            user_id=user3.id, name="Amit Kumar", age=20, gender="Male", state="Maharashtra",
            education="12th Pass", occupation="Student", income=180000, startup_status=False, student_status=True
        )
        db.add_all([profile1, profile2, profile3])
        db.flush()

        # Seed Karnataka Udyogini Scheme
        udyogini = Scheme(
            name="karnataka_udyogini",
            title="Karnataka Udyogini Scheme",
            description="Assists women entrepreneurs in launching micro-businesses by providing subsidized loans.",
            benefits="Subsidized loans up to Rs. 3,00,000. Subsidy rate ranges from 30% to 50% for SC/ST and special categories.",
            eligibility_criteria="Female candidate, age 18 to 55, resident of Karnataka, family annual income under Rs. 1.5 Lakhs.",
            required_documents="Aadhaar Card, Karnataka Domicile Certificate, Tahsildar-verified Income Certificate, caste certificate (if SC/ST), Project Proposal Report.",
            application_steps="1. Visit DWCD local office. 2. Collect and fill application form. 3. Attach required documents. 4. Submit to local committee.",
            state="Karnataka",
            category="Business",
            ministry="Department of Women and Child Development, Karnataka",
            is_for_women=True,
            is_for_students=False,
            is_for_startups=True,
            is_for_farmers=False
        )
        db.add(udyogini)
        db.flush()

        # Rules for Udyogini
        db.add_all([
            EligibilityRule(scheme_id=udyogini.id, field_name="gender", operator="==", expected_value="female"),
            EligibilityRule(scheme_id=udyogini.id, field_name="state", operator="==", expected_value="karnataka"),
            EligibilityRule(scheme_id=udyogini.id, field_name="age", operator=">=", expected_value="18"),
            EligibilityRule(scheme_id=udyogini.id, field_name="age", operator="<=", expected_value="55"),
            EligibilityRule(scheme_id=udyogini.id, field_name="income", operator="<=", expected_value="150000")
        ])

        # Seed PMEGP Scheme
        pmegp = Scheme(
            name="pmegp",
            title="Prime Minister Employment Generation Programme",
            description="Credit-linked subsidy scheme generating self-employment by supporting new micro-enterprises.",
            benefits="Subsidy of 15%-25% for urban areas and 25%-35% for rural areas. Project limits up to Rs. 50 Lakhs for manufacturing.",
            eligibility_criteria="Any individual above 18 years of age. No income limits. For project size >10 Lakhs in manufacturing, must be 8th Standard pass.",
            required_documents="Aadhaar Card, Educational Qualification Certificate, Project Report (DPR), Bank Passbook copy.",
            application_steps="1. Open PMEGP e-Portal. 2. Fill individual applicant details. 3. Upload DPR and credentials. 4. Select local bank and submit.",
            state="Central",
            category="Business",
            ministry="Ministry of Micro, Small and Medium Enterprises",
            is_for_women=False,
            is_for_students=False,
            is_for_startups=True,
            is_for_farmers=False
        )
        db.add(pmegp)
        db.flush()

        db.add(EligibilityRule(scheme_id=pmegp.id, field_name="age", operator=">=", expected_value="18"))

        # Seed Rajiv Gandhi Scholarship
        rgs = Scheme(
            name="rajiv_gandhi_scholarship",
            title="Rajiv Gandhi Scholarship for Technical Studies",
            description="Tuition reimbursement scholarship helping Karnataka students pursue engineering and medical degrees.",
            benefits="100% academic tuition fee waiver and Rs. 2,000 monthly allowance.",
            eligibility_criteria="Resident of Karnataka, currently enrolled in technical university, family annual income under Rs. 2,50,000.",
            required_documents="Admission letter, Previous academic marksheets, Domicile certificate, Income certificate.",
            application_steps="1. Go to State Scholarship Portal (SSP). 2. Register with Aadhaar. 3. Enter tuition receipt details. 4. Wait for college approval.",
            state="Karnataka",
            category="Education",
            ministry="Department of Higher Education, Karnataka",
            is_for_women=False,
            is_for_students=True,
            is_for_startups=False,
            is_for_farmers=False
        )
        db.add(rgs)
        db.flush()

        db.add_all([
            EligibilityRule(scheme_id=rgs.id, field_name="state", operator="==", expected_value="karnataka"),
            EligibilityRule(scheme_id=rgs.id, field_name="student_status", operator="==", expected_value="true"),
            EligibilityRule(scheme_id=rgs.id, field_name="income", operator="<=", expected_value="250000")
        ])

        # Seed PM-KISAN
        pmk = Scheme(
            name="pm_kisan",
            title="Pradhan Mantri Kisan Samman Nidhi",
            description="Direct income support providing Rs. 6,000 per year in three installments to farmer households.",
            benefits="Direct bank transfer of Rs. 6,000 annually (3 installments of Rs. 2,000 each).",
            eligibility_criteria="Must be a small or marginal farmer with agricultural land registry linked to their name.",
            required_documents="Land Registration records, Aadhaar Card, Bank account passbook copy.",
            application_steps="1. Go to PM-KISAN portal. 2. Select 'New Farmer Registration'. 3. Fill state, land survey number. 4. Link Aadhaar bank.",
            state="Central",
            category="Agriculture",
            ministry="Ministry of Agriculture and Farmers Welfare",
            is_for_women=False,
            is_for_students=False,
            is_for_startups=False,
            is_for_farmers=True
        )
        db.add(pmk)
        db.flush()

        db.add(EligibilityRule(scheme_id=pmk.id, field_name="occupation", operator="==", expected_value="farmer"))
        db.flush()

        # Seed Research survey feedback data (creates 20+ realistic responses for aggregations)
        schemes = [udyogini, pmegp, rgs, pmk]
        bottlenecks = [
            "Complex documentation", 
            "Online portal broken", 
            "No response from department", 
            "Opaque process flow",
            "Lack of local support centers"
        ]
        statuses = ["Approved", "Rejected", "In Progress", "Completed"]
        comments = [
            "Applying was highly complex and required many signatures.",
            "The online server was slow but got approved eventually.",
            "I could not collect all necessary documents.",
            "Process is transparent, highly helpful scheme.",
            "I spent months visiting the department offices."
        ]

        # Create randomized surveys to populate charts
        states_pool = ["Karnataka", "Maharashtra", "Tamil Nadu", "Delhi", "Gujarat"]
        genders_pool = ["Female", "Male"]
        occupations_pool = ["Farmer", "Student", "Unemployed", "Entrepreneur"]

        for i in range(25):
            # Create a mock user + profile for demographic charts
            rand_clerk = f"clerk_mock_survey_{i}"
            u = User(email=f"survey-user-{i}@policygpt.ai", clerk_id=rand_clerk)
            db.add(u)
            db.flush()

            # Random profile
            p = Profile(
                user_id=u.id,
                name=f"Survey User {i}",
                age=random.randint(19, 60),
                gender=random.choice(genders_pool),
                state=random.choice(states_pool),
                education=random.choice(["10th Pass", "12th Pass", "Graduate"]),
                occupation=random.choice(occupations_pool),
                income=random.randint(40000, 300000),
                startup_status=random.choice([True, False]),
                student_status=random.choice([True, False])
            )
            db.add(p)
            db.flush()

            sch = random.choice(schemes)
            aware = random.choice([True, True, True, False]) # 75% aware
            applied = random.choice([True, False]) if aware else False
            difficulty = random.randint(2, 5) if applied else None
            status = random.choice(statuses) if applied else "Not Applied"
            bottleneck = random.choice(bottlenecks) if (applied and difficulty and difficulty > 3) else None
            comment = random.choice(comments) if applied else "Just exploring the schemes."

            # Force specific rules for logical data patterns:
            # female only scheme has more female profiles aware
            if str(sch.name) == "karnataka_udyogini" and str(p.gender) == "Male":
                status = "Rejected"
                bottleneck = "Failed gender criteria"

            survey = Survey(
                user_id=u.id,
                scheme_id=sch.id,
                aware_of_scheme=aware,
                applied_for_scheme=applied,
                difficulty_rating=difficulty,
                application_status=status,
                bottleneck_reason=bottleneck,
                feedback_comments=comment
            )
            db.add(survey)

        db.commit()
        logger.info("Successfully seeded PostgreSQL database!")

        # 3. Seed ChromaDB Guidelines
        logger.info("Indexing guidelines documents in ChromaDB vector space...")
        for name, text in SCHEME_GUIDELINES.items():
            # Find scheme ID from database
            sch_db = db.query(Scheme).filter(Scheme.name == name).first()
            if sch_db:
                ai_service.index_scheme_text(str(sch_db.id), str(sch_db.name), text)
                
        logger.info("Successfully indexed guidelines in ChromaDB!")
        ensure_extra_schemes(db)
    except Exception as e:
        logger.error(f"Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    seed_database()
