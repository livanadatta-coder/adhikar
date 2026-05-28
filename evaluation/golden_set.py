"""
evaluation/golden_set.py — Start of your evaluation harness
10 Police/FIR scenarios with expected rights, actions, and forms.

The spec says: build a 30-scenario golden test set.
This gives you 10 for Police/FIR to start — expand it as you add domains.

You won't USE this in Week 1. Set it up now, run it in Week 3
once the agent layer is built. The spec says target >75% rights recall.
"""

GOLDEN_SET = [
    {
        "id": "pfir_001",
        "scenario": "Police arrived at my house at 11pm and want to take me to the station without showing any warrant.",
        "domain": "police_fir",
        "expected_rights": [
            "CrPC Section 41 — right not to be arrested without warrant unless conditions are met",
            "CrPC Section 41A — right to a notice of appearance instead of arrest",
            "Article 22 — right to be informed of grounds of arrest",
        ],
        "expected_actions": [
            "Ask the officer to state the specific reason for the arrest",
            "Ask whether they have a warrant — if not, ask them to issue a 41A notice",
            "Do not leave with them without a warrant or valid arrest memo",
            "Call a family member and tell them your location",
        ],
        "expected_forms": [],
        "expected_sources": ["CrPC §41", "CrPC §41A", "Article 22"],
    },
    {
        "id": "pfir_002",
        "scenario": "I was arrested and the police did not tell me why. They just put me in the van.",
        "domain": "police_fir",
        "expected_rights": [
            "CrPC Section 50 — right to be told the grounds of arrest immediately",
            "Article 22 — constitutional right to be informed of grounds of arrest",
        ],
        "expected_actions": [
            "Demand that the officer state the reason for your arrest",
            "If they refuse, note the officer's name and badge number",
            "Contact a lawyer as soon as possible",
            "File a complaint with the Superintendent of Police if rights are violated",
        ],
        "expected_forms": [],
        "expected_sources": ["CrPC §50", "Article 22"],
    },
    {
        "id": "pfir_003",
        "scenario": "The police have been holding me for 30 hours. They have not taken me to a magistrate.",
        "domain": "police_fir",
        "expected_rights": [
            "Article 22 — right to be produced before magistrate within 24 hours",
            "CrPC Section 57 — police cannot detain beyond 24 hours without magistrate order",
        ],
        "expected_actions": [
            "Demand immediately to be produced before a magistrate",
            "Ask for a lawyer — this is your constitutional right",
            "Have a family member file a habeas corpus petition in the High Court",
            "Note the names of all officers involved in the illegal detention",
        ],
        "expected_forms": [],
        "expected_sources": ["Article 22", "CrPC §57"],
    },
    {
        "id": "pfir_004",
        "scenario": "Police are refusing to register my FIR. The inspector says it is a civil matter.",
        "domain": "police_fir",
        "expected_rights": [
            "CrPC Section 154 — right to have FIR registered for cognisable offence",
            "CrPC Section 154(3) — right to send complaint to Superintendent of Police if refused",
        ],
        "expected_actions": [
            "Confirm your offence is cognisable (theft, assault, etc.)",
            "Write a complaint and send by post to the Superintendent of Police",
            "File a complaint before the nearest magistrate under Section 156(3)",
            "Approach the High Court if all else fails",
        ],
        "expected_forms": ["Complaint to Superintendent of Police (written, no standard form)"],
        "expected_sources": ["CrPC §154", "CrPC §154(3)"],
    },
    {
        "id": "pfir_005",
        "scenario": "I was arrested and the police did not allow me to call my family. They said I can call later.",
        "domain": "police_fir",
        "expected_rights": [
            "D.K. Basu guidelines — right to inform friend or family of arrest immediately",
            "Article 22 — right to consult a legal practitioner",
        ],
        "expected_actions": [
            "Invoke your D.K. Basu rights — demand to call a family member immediately",
            "Ask for the arrest memo to be signed by a family member or witness",
            "Note the name of the officer who refused",
            "File a complaint once released for violation of D.K. Basu guidelines",
        ],
        "expected_forms": [],
        "expected_sources": ["D.K. Basu guidelines", "Article 22"],
    },
    {
        "id": "pfir_006",
        "scenario": "I have been in custody for 65 days and police still haven't filed a charge sheet.",
        "domain": "police_fir",
        "expected_rights": [
            "CrPC Section 167(2) — right to default bail if charge sheet not filed in time",
        ],
        "expected_actions": [
            "Immediately apply for default bail (statutory bail) under Section 167(2)",
            "The court must grant bail if the 60/90-day limit has passed without charge sheet",
            "Engage a lawyer to file the bail application immediately",
            "Do not wait — this right expires if charge sheet is filed before you apply",
        ],
        "expected_forms": ["Bail application under CrPC Section 167(2)"],
        "expected_sources": ["CrPC §167"],
    },
    {
        "id": "pfir_007",
        "scenario": "I was arrested for stealing a mobile phone. Police say they won't give me bail.",
        "domain": "police_fir",
        "expected_rights": [
            "CrPC Section 436 — bail is a right for bailable offences",
        ],
        "expected_actions": [
            "Theft under Rs 200 is bailable — confirm the value",
            "For bailable offences, police CANNOT refuse bail",
            "Provide a surety or personal bond",
            "If police still refuse, approach the magistrate immediately",
        ],
        "expected_forms": ["Bail bond / surety form (available at court)"],
        "expected_sources": ["CrPC §436"],
    },
    {
        "id": "pfir_008",
        "scenario": "Police entered my house and searched it without showing any document.",
        "domain": "police_fir",
        "expected_rights": [
            "CrPC Section 100 — right to witness search, search must follow procedure",
            "CrPC Section 165 — police need written authorisation for search",
        ],
        "expected_actions": [
            "Ask to see the search warrant or authorisation in writing",
            "Demand that two witnesses be present during the search",
            "Note everything that is taken and ask for a receipt",
            "File a complaint with senior police officer if search was illegal",
        ],
        "expected_forms": [],
        "expected_sources": ["CrPC §100", "CrPC §165"],
    },
    {
        "id": "pfir_009",
        "scenario": "I want to complain against a police officer who beat me in custody.",
        "domain": "police_fir",
        "expected_rights": [
            "D.K. Basu guidelines — right to medical examination at time of arrest",
            "Right to file complaint with State Human Rights Commission",
        ],
        "expected_actions": [
            "Get a medical examination immediately and keep the report",
            "File a complaint with the Superintendent of Police",
            "File a complaint with the State Human Rights Commission",
            "Contact the National Human Rights Commission (NHRC) online",
        ],
        "expected_forms": ["NHRC complaint form (available at nhrc.nic.in)"],
        "expected_sources": ["D.K. Basu guidelines"],
    },
    {
        "id": "pfir_010",
        "scenario": "Police arrested me but did not prepare any arrest memo or show identification.",
        "domain": "police_fir",
        "expected_rights": [
            "D.K. Basu guidelines — arresting officer must carry visible identification",
            "D.K. Basu guidelines — arrest memo must be prepared at time of arrest",
        ],
        "expected_actions": [
            "Demand the officer show their identification badge",
            "Demand preparation of the arrest memo witnessed by a family member",
            "Note the vehicle number if being transported",
            "Have a family member file a habeas corpus if you disappear without trace",
        ],
        "expected_forms": [],
        "expected_sources": ["D.K. Basu guidelines"],
    },
]


def summary():
    print(f"Golden set: {len(GOLDEN_SET)} Police/FIR scenarios")
    print("Use this in Week 3 once the Rights Agent is built.")
    print("Target: >75% rights recall on this set before moving to multilingual.\n")
    for tc in GOLDEN_SET:
        print(f"  [{tc['id']}] {tc['scenario'][:70]}...")


if __name__ == "__main__":
    summary()
