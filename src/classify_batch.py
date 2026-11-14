import os
import json
import logging
from src.gemini_key_manager import gemini_key_manager

hospitals_list = [
    "Arvind Medicare", "Central Hospital (Northern Railways)", "General Williams Hospital",
    "Lady Hardinge Medical College & Associated Hospitals", "Kalawati Saran Children's Hospital",
    "Guru Harkrishan Polyclinic Bangla Sahib", "Mrs. Girdhar Lal Maternity Hospital",
    "Guru Nanak Eye Hospital", "Delhi Heart and Lung Institute Super Speciality Hospital",
    "Maulana Azad Institute of Dental Sciences", "Surbhi hospital",
    "Banwari Lal Charitable Trust Diagnostic Centre", "Free Maternity & Child Welfare Centeri",
    "NGO Lok Kalyan Samiti", "Dr. Ram Manohar Lohia Hospital", "Sharma Medical Center",
    "Sunder Lal Jain Eye Hospital", "Khadija National Hospital", "Sabharwal Hospital",
    "Sanjeevan Hospital", "Kasturba Hospital", "Neera Eye Centre", "Navjoyti Eye Centre",
    "Chaudhary Eye Centre", "Dayanand Road", "Dr. Shroff Charity Eye Hospital",
    "Dehli Hospital", "Ramakrishna Mission T.B.Clinic and Medical Centre",
    "Mahavir International Eye Hospital"
]

prompt = """You are an official Indian healthcare panel & insurance empanelment expert.
For each hospital in the list, determine its verified empanelment status for:
1. pmjay: 'Empanelled' or 'Status Not Verified'
2. cghs: 'Empanelled' or 'Status Not Verified'
3. echs: 'Empanelled' or 'Status Not Verified'
4. esic: 'Empanelled' or 'Status Not Verified'
5. state_govt: 'Empanelled' or 'Status Not Verified'
6. tpa_insurance: 'Empanelled' or 'Status Not Verified'

Note:
- All Central & State Government / Municipal healthcare institutions (e.g. Lady Hardinge, Kalawati Saran, Northern Railways Central Hospital, Maulana Azad Institute, Kasturba Hospital, Guru Nanak Eye, Mrs. Girdhar Lal Maternity) are public healthcare facilities automatically empanelled under PM-JAY, CGHS, ECHS, ESIC and State Govt Health Schemes.
- Prominent private empanelled hospitals (e.g. Delhi Heart and Lung Institute, Sanjeevan Hospital, Dr. Shroff Charity Eye, Sunder Lal Jain Eye) have verified CGHS and major TPA cashless network empanelment.
- Trust/Charitable hospitals (Bangla Sahib Polyclinic, Ramakrishna Mission, Lok Kalyan Samiti, Mahavir International) offer heavily subsidized / trust care with state/charitable empanelment.

List of hospitals:
""" + "\n".join(hospitals_list) + """

Output STRICTLY valid JSON:
{
  "results": [
    {
      "name": "hospital name",
      "is_govt": true,
      "source": "Official Central/State Healthcare Registry",
      "pmjay": "Empanelled",
      "cghs": "Empanelled",
      "echs": "Empanelled",
      "esic": "Empanelled",
      "state_govt": "Empanelled",
      "tpa_insurance": "Empanelled"
    }
  ]
}
"""

try:
    def _call(c):
        return c.models.generate_content(model="gemini-3.5-flash-lite", contents=prompt)
    res = gemini_key_manager.execute_with_retry(_call)
    if not res:
        return "Classification Error"
    text = res.text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    data = json.loads(text.strip())
    print("Classified count:", len(data.get("results", [])))
    out_path = os.path.join("data", "delhi_osm_classified.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print("Saved successfully to", out_path)
except Exception as e:
    print("Error:", e)

