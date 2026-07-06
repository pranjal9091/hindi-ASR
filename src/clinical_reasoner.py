import re

class DiagnosisEngine:
    def __init__(self):
        # Maps clinical keyword combinations to possible diagnoses
        self.rules = [
            {
                "keywords": ["बुखार", "तापमान", "ठंड", "fever", "temp"],
                "diagnosis": "संभावित वायरल संक्रमण (Possible Viral Infection)",
                "confidence": 0.85
            },
            {
                "keywords": ["खांसी", "सांस", "गला", "cough", "breath"],
                "diagnosis": "श्वसन तंत्र संक्रमण (Respiratory Tract Infection)",
                "confidence": 0.80
            },
            {
                "keywords": ["सीने में दर्द", "छाती", "दर्द दिल", "हार्ट", "chest pain"],
                "diagnosis": "कार्डियक स्पस्म / सीने का दर्द (Cardiac Spasm / Chest Pain)",
                "confidence": 0.90
            },
            {
                "keywords": ["मधुमेह", "डायबिटीज", "शुगर", "sugar", "diabetes"],
                "diagnosis": "मधुमेह असंतुलन (Hyperglycemia / Diabetes)",
                "confidence": 0.85
            },
            {
                "keywords": ["चक्कर", "बीपी", "रक्तचाप", "bp", "blood pressure"],
                "diagnosis": "रक्तचाप असंतुलन (Blood Pressure Fluctuation)",
                "confidence": 0.80
            },
            {
                "keywords": ["उल्टी", "दस्त", "पेट दर्द", "पेट", "vomit", "stomach"],
                "diagnosis": "गैस्ट्रोएंटेराइटिस / पेट में संक्रमण (Gastroenteritis / Stomach Infection)",
                "confidence": 0.75
            }
        ]

    def infer_diagnoses(self, text, symptoms):
        diagnoses = []
        if not text:
            return diagnoses

        text_lower = text.lower()
        combined_symptoms = [s.lower() for s in symptoms]

        # Scan rules
        for rule in self.rules:
            # Check if any keyword matches
            matches = 0
            for kw in rule["keywords"]:
                if kw in text_lower or any(kw in sym for sym in combined_symptoms):
                    matches += 1
            if matches > 0:
                # Scale confidence based on matches count
                adjusted_conf = min(0.95, rule["confidence"] + (matches - 1) * 0.05)
                diagnoses.append({
                    "name": rule["diagnosis"],
                    "confidence": adjusted_conf
                })

        # Fallback diagnosis
        if not diagnoses:
            diagnoses.append({
                "name": "अनिर्धारित लक्षण (Undetermined Clinical Presentation)",
                "confidence": 0.50
            })

        # Sort by confidence descending
        diagnoses.sort(key=lambda x: x["confidence"], reverse=True)
        return diagnoses


class RiskAnalyzer:
    def __init__(self):
        # Keyword triggers for specific clinical risk flags
        self.emergency_triggers = ["आपातकालीन", "इमरजेंसी", "गंभीर", "emergency", "severe"]
        self.stroke_triggers = ["लकवा", "पैरालिसिस", "लड़खड़ाना", " paralysis", "stroke"]
        self.heart_attack_triggers = ["सीने में तेज दर्द", "छाती में दर्द", "दिल का दौरा", "हार्ट अटैक", "heart attack"]
        self.respiratory_triggers = ["सांस फूलना", "सांस लेने में तकलीफ", "दम घटना", "dyspnea", "breathing issue"]
        self.fall_triggers = ["चक्कर खाकर गिरना", "गिर गया", "फिसल गया", "fall", "injury"]
        self.compliance_triggers = ["दवा नहीं ली", "भूल गया", "दवाई छोड़ दी", "skip medicine", "non compliant"]

    def analyze_risks(self, text):
        flags = {
            "emergency_risk": False,
            "stroke_risk": False,
            "heart_attack_risk": False,
            "respiratory_risk": False,
            "fall_risk": False,
            "medication_non_compliance": False
        }
        if not text:
            return flags

        text_lower = text.lower()

        if any(t in text_lower for t in self.emergency_triggers):
            flags["emergency_risk"] = True
        if any(t in text_lower for t in self.stroke_triggers):
            flags["stroke_risk"] = True
        if any(t in text_lower for t in self.heart_attack_triggers):
            flags["heart_attack_risk"] = True
        if any(t in text_lower for t in self.respiratory_triggers):
            flags["respiratory_risk"] = True
        if any(t in text_lower for t in self.fall_triggers):
            flags["fall_risk"] = True
        if any(t in text_lower for t in self.compliance_triggers):
            flags["medication_non_compliance"] = True

        return flags


class QuestionGenerator:
    def __init__(self):
        pass

    def generate_questions(self, symptoms, diagnoses):
        questions = []
        
        # Primary check on symptom trigger list
        has_fever = any("बुखार" in s or "तापमान" in s for s in symptoms)
        has_chest_pain = any("सीने" in s or "दर्द" in s and "छाती" in s for s in symptoms)
        has_breathing = any("सांस" in s or "दम" in s for s in symptoms)
        has_sugar = any("शुगर" in s or "डायबिटीज" in s or "मधुमेह" in s for s in symptoms)

        if has_chest_pain:
            questions.extend([
                "क्या दर्द बाएं कंधे, गर्दन या जबड़े की तरफ फैल रहा है?",
                "क्या दर्द के साथ सांस लेने में तकलीफ या बहुत पसीना आ रहा है?",
                "यह दर्द कब से है और क्या यह लगातार बना हुआ है या रुक-रुक कर हो रहा है?"
            ])
        elif has_breathing:
            questions.extend([
                "क्या आपको पहले से दमा (अस्थमा) या फेफड़ों की कोई बीमारी है?",
                "क्या लेटने पर सांस लेने की तकलीफ बढ़ जाती है?",
                "क्या आपको सूखी खांसी आ रही है या बलगम भी है?"
            ])
        elif has_fever:
            questions.extend([
                "क्या बुखार के साथ कंपकंपी (ठंड) लग रही है या पसीना आ रहा है?",
                "घर पर थर्मामीटर से कितना तापमान मापा गया है?",
                "क्या आपको उल्टी, सिरदर्द या शरीर में अत्यधिक दर्द की भी शिकायत है?"
            ])
        elif has_sugar:
            questions.extend([
                "क्या आपको हाल ही में अधिक प्यास लगना या बार-बार पेशाब आने की समस्या हो रही है?",
                "आज सुबह खाली पेट (Fasting) शुगर का स्तर कितना था?",
                "क्या हाथ-पैरों में झनझनाहट या घाव ठीक होने में समय लग रहा है?"
            ])

        # Standard clinical questions fallback
        while len(questions) < 4:
            fallbacks = [
                "यह समस्या पहली बार हुई है या पहले भी कभी हो चुकी है?",
                "क्या आप वर्तमान में किसी अन्य बीमारी के लिए नियमित रूप से दवाएं ले रहे हैं?",
                "क्या परिवार में किसी को रक्तचाप (BP) या हृदय रोग की समस्या है?",
                "लक्षणों की गंभीरता दिन के किस समय अधिक महसूस होती है?"
            ]
            for f in fallbacks:
                if f not in questions:
                    questions.append(f)
                    break
                    
        return questions[:5]


class SOAPGenerator:
    def __init__(self):
        pass

    def build_soap_note(self, text, entities, vitals, diagnoses, medications, summary):
        # Subjective (S): Patient history, symptoms, and timelines
        symptoms_str = ", ".join(entities["symptoms"]) if entities["symptoms"] else "कोई विशिष्ट लक्षण उल्लेखित नहीं"
        subjective = (
            f"मरीज की मुख्य शिकायत (Chief Complaint): {summary['chief_complaint']}\n"
            f"लक्षण (Symptoms): {symptoms_str}। मरीज के कथनानुसार ये तकलीफें महसूस हो रही हैं।"
        )

        # Objective (O): Vitals measurements
        bp = vitals.get("blood_pressure", "सामान्य / मापा नहीं गया")
        temp = vitals.get("temperature", "सामान्य / मापा नहीं गया")
        pulse = vitals.get("pulse", "सामान्य / मापा नहीं गया")
        oxy = vitals.get("oxygen", "सामान्य / मापा नहीं गया")
        wt = vitals.get("weight", "सामान्य / मापा नहीं गया")
        
        objective = (
            f"रक्तचाप (Blood Pressure): {bp}\n"
            f"शारीरिक तापमान (Temp): {temp}\n"
            f"पल्स रेट (Pulse): {pulse}\n"
            f"ऑक्सीजन स्तर (SpO2): {oxy}\n"
            f"वजन (Weight): {wt}"
        )

        # Assessment (A): Clinical diagnostic hypotheses
        diag_list = [f"{d['name']} (विश्वास स्तर: {int(d['confidence']*100)}%)" for d in diagnoses]
        assessment = "नैदानिक विश्लेषण (Clinical Assessment):\n" + "\n".join(diag_list)

        # Plan (P): Actions, prescriptions, and follow-ups
        med_list = [f"- {m['name']} (खुराक: {m['dose']}, आवृत्ति: {m['frequency']}, अवधि: {m['duration']})" for m in medications]
        meds_section = "\n".join(med_list) if med_list else "- कोई तात्कालिक दवा निर्धारित नहीं की गई।"
        
        plan = (
            f"अनुशंसित दवाएं (Medications):\n{meds_section}\n\n"
            f"चिकित्सीय सलाह (Advice): {summary['advice']}\n"
            f"फॉलो-अप निर्देश: आवश्यक होने पर डॉक्टर से संपर्क करें।"
        )

        return {
            "subjective": subjective,
            "objective": objective,
            "assessment": assessment,
            "plan": plan
        }


class ClinicalReasoner:
    def __init__(self):
        self.diag_engine = DiagnosisEngine()
        self.risk_analyzer = RiskAnalyzer()
        self.question_gen = QuestionGenerator()
        self.soap_gen = SOAPGenerator()

    def reason(self, text, base_clinical):
        """
        Main runner combining all intelligence submodules.
        """
        symptoms = base_clinical.get("symptoms", [])
        medicines = base_clinical.get("medicines", [])
        vitals = base_clinical.get("vitals", {})
        summary = base_clinical.get("summary", {})
        procedures = base_clinical.get("procedures", [])
        timeline = base_clinical.get("timeline", [])

        # 1. Infer Possible Diagnoses
        diagnoses = self.diag_engine.infer_diagnoses(text, symptoms)

        # 2. Risk Flags Detection
        risks = self.risk_analyzer.analyze_risks(text)

        # 3. Follow-up Questions Formulator
        questions = self.question_gen.generate_questions(symptoms, diagnoses)

        # 4. Generate structured SOAP note
        entities = {
            "symptoms": symptoms,
            "diseases": base_clinical.get("diseases", []),
            "procedures": procedures
        }
        soap = self.soap_gen.build_soap_note(text, entities, vitals, diagnoses, medicines, summary)

        # 5. Formulate Clinical Confidence Scores
        # Static baseline confidence mapped on rule-based triggers
        confidences = {
            "ner_confidence": 0.94,
            "diagnosis_confidence": round(diagnoses[0]["confidence"], 2) if diagnoses else 0.50,
            "timeline_confidence": 0.90 if timeline else 0.60,
            "summary_confidence": 0.92
        }

        # Override Chief Complaint in summary if specific detail detected
        # e.g. "मुझे दो दिन से बुखार है" -> "Fever for 2 days"
        # Search duration patterns in text
        dur_match = re.search(r'(\d+|एक|दो|तीन|चार|पांच|छह|सात)\s*(दिन|सप्ताह|हफ्ते|महीने|साल)', text)
        if dur_match and symptoms:
            summary["chief_complaint"] = f"{symptoms[0]} for {dur_match.group(0)}"

        return {
            "possible_diagnosis": diagnoses,
            "risk_flags": risks,
            "follow_up_questions": questions,
            "soap_note": soap,
            "confidence_scores": confidences,
            "summary": summary  # updated summary compliant
        }


def reason_clinical_nlp(text, base_clinical):
    """
    Helper function invoked by app.py
    """
    reasoner = ClinicalReasoner()
    result = reasoner.reason(text, base_clinical)
    
    # Merge result keys back into the base clinical output
    base_clinical.update(result)
    return base_clinical
