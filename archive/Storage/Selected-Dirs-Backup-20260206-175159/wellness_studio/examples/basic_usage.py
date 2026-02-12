"""
Example usage of Wellness Studio
"""

from wellness_studio import WellnessPipeline, run_pipeline

# Example 1: Quick text input
print("Example 1: Processing text input...")
result = run_pipeline(
    text="""
    Patient: Sarah, 34 years old
    Current medications: Propranolol 20mg twice daily for anxiety
    Also takes occasional ibuprofen for tension headaches
    
    Main concerns: Wants to reduce reliance on anxiety medication.
    Has tried meditation but finds it hard to stick with.
    Open to herbal supplements and lifestyle changes.
    
    Goals: Natural anxiety management, better sleep, less tension
    """,
    patient="Sarah",
    format="markdown"
)

if result.success:
    print(f"✅ Success! Report saved to: {result.report_path}")
else:
    print(f"❌ Error: {result.error_message}")

# Example 2: Full pipeline with file
print("\nExample 2: Using pipeline directly...")
pipeline = WellnessPipeline(device='auto')

# You can also process files:
# result = pipeline.process(
#     input_path="medical_report.pdf",
#     patient_name="John Doe",
#     case_type="prescription",
#     output_format="html"
# )

print("\nDone! Check the reports/ directory for outputs.")
