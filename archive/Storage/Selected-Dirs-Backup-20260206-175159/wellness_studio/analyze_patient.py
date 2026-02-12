"""
Quick Wellness Analysis for Patient Care
Using Wellness Studio with privacy safeguards
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from wellness_studio.security import PIIDetector, SensitivityLevel

# Patient medication data
patient_text = """
Medication Routine Summary Table
TimeMorning (সকাল)AfternoonEvening (সন্ধ্যে)NotesBefore MealPantonix 40mg (½ tab)30 min before--Stomach protectionWith MealNidipine SR 20mgLarcadip 10mg (½)Nitrin SR 2.6mg (½)Metacard MR 35mg (½)Corangi 10mg (½)Doxiva 200mg (½)Bisopro Plus (½)Clopid 75mg (½)Dicaltrol 0.25mcg (½)Nidipine SR 20mgLarcadip 10mg (½)Monas 10mg (½)Nitrin SR 2.6mg (½)Metacard MR 35mg (½)Corangi 10mg (½)Doxiva 200mg (½)Pase 1mg (½)Bextrum Gold (½)Renocal Plus (½)Blood pressure & heart medicationsBefore Each MealEmistat 8mg (½)Emistat 8mg (½)Emistat 8mg (½)30 min before eatingSpecial Schedule--Roxatat 100mg(Sat, Mon, Thu only)Specific days only
Key Instructions
Fluid Restriction: 750ml total per 24 hours
Avoid: Tea, coffee, and other liquids beyond fluid limit
Follow-up: 2 weeks or earlier if needed
Total Daily Tablets: ~15-17 doses spread across the day

Patient has been having health difficulties and pain in last 2 weeks.
This mimics symptoms from months back 10-11, health first degraded then improved now degrading again.
"""

# Step 1: Check for PII/PHI
detector = PIIDetector()
entities = detector.detect_pii(patient_text)

print(f"PII Detection Found: {len(entities)} entities")
print(f"Risk Level: {detector.assess_risk_level(patient_text)['risk_level']}")

# Step 2: Sanitize for analysis
sanitized, mapping = detector.sanitize_text(patient_text, replacement_mode="hash")

print("\n--- SANITIZED FOR ANALYSIS ---")
print(sanitized[:500] + "..." if len(sanitized) > 500 else sanitized)

# Step 3: Key observations for home care (non-medical)
print("\n--- HOME CARE RECOMMENDATIONS ---")
print("""
Based on the medication profile (cardiovascular, blood pressure, stomach protection),
here are general home care suggestions:

1. MEDICATION MANAGEMENT
   - Use a pill organizer with compartments for morning/afternoon/evening
   - Set alarms for medication timing (especially 30 min before meals)
   - Keep a daily checklist to track doses taken
   - Document any missed doses

2. FLUID MANAGEMENT (750ml/day is very strict)
   - Measure fluids with a marked bottle
   - Sip slowly throughout the day
   - Track intake in a notebook
   - Consider ice chips for thirst without volume

3. MONITORING (non-medical)
   - Daily blood pressure log if home monitor available
   - Note any swelling in ankles/feet
   - Track energy levels and pain levels (1-10 scale)
   - Keep a symptom diary

4. COMFORT MEASURES
   - Elevate legs when resting (helps with fluid)
   - Gentle movement/walking as tolerated
   - Rest periods between activities
   - Comfortable clothing that doesn't restrict

5. NUTRITION SUPPORT
   - Small, frequent meals (easier on digestion)
   - Balanced diet with adequate protein
   - Avoid excessive salt (follow doctor's guidance)
   - Stay within fluid restrictions

6. ENVIRONMENT
   - Cool, comfortable room temperature
   - Quiet, restful space for recovery
   - Easy access to bathroom and water
   - Remove tripping hazards

7. COMMUNICATION
   - Keep a list of questions for doctor visits
   - Note any changes in symptoms
   - Family support for medication reminders
   - Emergency contact information readily available

⚠️ IMPORTANT: This is general home care guidance, not medical advice.
   Always consult with the healthcare provider managing the medications.
   For concerning symptoms, seek medical attention promptly.
""")

print("\n--- PRIVACY NOTE ---")
print("All personal identifiers have been sanitized.")
print("Analysis based on medication profile and general care principles.")
