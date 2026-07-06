import re

class ClinicalNER:
    def __init__(self):
        # Dictionaries of common Hindi medical terms in Devanagari script and Latin transliteration
        self.medicines = [
            "पैरासिटामोल", "paracetamol", "मेटफॉर्मिन", "metformin", "एस्पिरिन", "aspirin", 
            "इबुप्रोफेन", "ibuprofen", "अमोक्सिसिलिन", "amoxicillin", "दवा", "दवाई", "गोली", 
            "कैप्सूल", "सिरप", "इंजेक्शन", "इंसुलिन", "पैनडॉल", "पेनडॉल"
        ]
        self.diseases = [
            "मधुमेह", "डायबिटीज", "diabetes", "उच्च रक्तचाप", "हाइपरटेंशन", "hypertension", 
            "बीपी", "bp", "कैंसर", "cancer", "मलेरिया", "malaria", "टीबी", "tuberculosis", 
            "दमा", "अस्थमा", "asthma", "हार्ट अटैक", "दिल का दौरा", "गठिया", "अर्थराइटिस",
            "थायरॉयड", "थायराइड", "डेंगू", "टाइफाइड"
        ]
        self.symptoms = [
            "बुखार", "तापमान", "दर्द", "सिरदर्द", "पीठ दर्द", "पेट दर्द", "खांसी", "जुकाम", 
            "सर्दी", "उल्टी", "दस्त", "चक्कर", "घबराहट", "थकान", "कमजोरी", "सांस फूलना", 
            "सांस लेने में तकलीफ", "खुजली", "सूजन", "सिर दर्द"
        ]
        self.body_parts = [
            "सिर", "पेट", "छाती", "सीना", "हाथ", "पैर", "आंख", "कान", "गला", "दिल", "हृदय",
            "कमर", "त्वचा", "फेफड़े", "किडनी", "लिवर"
        ]
        self.procedures = [
            "एक्स-रे", "एक्सरे", "x-ray", "खून जांच", "रक्त परीक्षण", "blood test", "सर्जरी", 
            "ऑपरेशन", "operation", "ईसीजी", "ecg", "अल्ट्रासाउंड", "ultrasound", "एमआरआई", "mri",
            "टांके", "प्लास्टर"
        ]

    def extract_entities(self, text):
        entities = {
            "medicines": [],
            "diseases": [],
            "symptoms": [],
            "body_parts": [],
            "procedures": []
        }
        if not text:
            return entities

        text_lower = text.lower()
        
        # Exact and boundary word match
        for m in self.medicines:
            if m in text_lower:
                entities["medicines"].append(m)
        for d in self.diseases:
            if d in text_lower:
                entities["diseases"].append(d)
        for s in self.symptoms:
            if s in text_lower:
                entities["symptoms"].append(s)
        for b in self.body_parts:
            if b in text_lower:
                entities["body_parts"].append(b)
        for p in self.procedures:
            if p in text_lower:
                entities["procedures"].append(p)

        # Deduplicate list elements
        for k in entities:
            entities[k] = list(set(entities[k]))
            
        return entities


class MedicationExtractor:
    def __init__(self):
        self.medicine_regex = re.compile(
            r'(पैरासिटामोल|मेटफॉर्मिन|एस्पिरिन|इबुप्रोफेन|अमोक्सिसिलिन|दवा|दवाई|गोली|कैप्सूल|सिरप|इंजेक्शन|इंसुलिन|paracetamol|metformin|aspirin|ibuprofen|amoxicillin)',
            re.IGNORECASE
        )
        # Dose patterns: numbers followed by format, or common Hindi text numbers
        self.dose_regex = re.compile(
            r'(\d+\s*(गोली|कैप्सूल|चम्मच|ml|एमएल|यूनิต|mg|एमजी|ग्राम)|एक|दो|तीन|आधी|आधा|one|two|half)',
            re.IGNORECASE
        )
        # Frequencies: daily schedule timings or counters
        self.freq_regex = re.compile(
            r'(सुबह\s*शाम|दिन\s*में\s*(एक|दो|तीन|चार)\s*बार|रोजाना|हफ्ते\s*में\s*एक\s*बार|खाने\s*के\s*(पहले|बाद)|सुबह|दोपहर|शाम|रात|once|twice|thrice|daily)',
            re.IGNORECASE
        )
        # Duration: days, weeks, months
        self.duration_regex = re.compile(
            r'(\d+\s*(दिन|हफ्ते|सप्ताह|महीने|days|weeks)|एक\s*हफ्ता|दो\s*दिन|तीन\s*दिन|पांच\s*दिन|सात\s*दिन|दस\s*दिन|one week|two days|three days)',
            re.IGNORECASE
        )

    def extract_medications(self, text):
        medications = []
        if not text:
            return medications

        # Sentence level scan to isolate scope of doses/durations
        sentences = re.split(r'[।\n?.]', text)
        for sent in sentences:
            sent = sent.strip()
            med_match = self.medicine_regex.search(sent)
            if med_match:
                med_name = med_match.group(1)
                
                # Check near proximity for matches
                dose_match = self.dose_regex.search(sent)
                freq_match = self.freq_regex.search(sent)
                dur_match = self.duration_regex.search(sent)
                
                medications.append({
                    "name": med_name,
                    "dose": dose_match.group(1) if dose_match else "निर्दिष्ट नहीं",
                    "frequency": freq_match.group(1) if freq_match else "निर्देशानुसार",
                    "duration": dur_match.group(1) if dur_match else "आवश्यकतानुसार"
                })
        
        return medications


class VitalExtractor:
    def __init__(self):
        # Regexes for BP, Temp, Pulse, Oxygen, Weight
        self.bp_regex = re.compile(r'(बीपी|रक्तचाप|ब्लड\s*प्रेशर|bp)\s*(\d+/\d+|\d+\s*से\s*\d+)', re.IGNORECASE)
        self.temp_regex = re.compile(r'(तापमान|बुखार|फीवर|temperature|temp)\s*(\d+(\.\d+)?\s*(डिग्री|degree|बुखार|F|C|फारेनहाइट)?)', re.IGNORECASE)
        self.pulse_regex = re.compile(r'(पल्स|धड़कन|हार्ट\s*रेट|pulse|heart\s*rate)\s*(\d+(\s*बीपीएम|\s*bpm)?)', re.IGNORECASE)
        self.oxygen_regex = re.compile(r'(ऑक्सीजन|oxygen|sp2|spo2|सैचुरेशन)\s*(\d+(\s*प्रतिशत|\s*%)?)', re.IGNORECASE)
        self.weight_regex = re.compile(r'(वजन|भार|weight)\s*(\d+(\s*किलो|\s*kg)?)', re.IGNORECASE)

    def extract_vitals(self, text):
        vitals = {
            "blood_pressure": "सामान्य",
            "temperature": "सामान्य",
            "pulse": "सामान्य",
            "oxygen": "सामान्य",
            "weight": "सामान्य"
        }
        if not text:
            return vitals

        bp_match = self.bp_regex.search(text)
        if bp_match:
            vitals["blood_pressure"] = bp_match.group(2)
        temp_match = self.temp_regex.search(text)
        if temp_match:
            vitals["temperature"] = temp_match.group(2)
        pulse_match = self.pulse_regex.search(text)
        if pulse_match:
            vitals["pulse"] = pulse_match.group(2)
        oxygen_match = self.oxygen_regex.search(text)
        if oxygen_match:
            vitals["oxygen"] = oxygen_match.group(2)
        weight_match = self.weight_regex.search(text)
        if weight_match:
            vitals["weight"] = weight_match.group(2)

        return vitals


class TimelineBuilder:
    def __init__(self):
        # Map time triggers to English presentation equivalents
        self.time_triggers = [
            ("सुबह", "Morning"),
            ("दोपहर", "Afternoon"),
            ("शाम", "Evening"),
            ("रात", "Night"),
            ("कल", "Yesterday / Tomorrow"),
            ("आज", "Today")
        ]

    def build_timeline(self, text):
        timeline = []
        if not text:
            return timeline

        sentences = re.split(r'[।\n?.]', text)
        for sent in sentences:
            sent = sent.strip()
            for trigger, time_label in self.time_triggers:
                if trigger in sent:
                    # Clean the time trigger from event string
                    event = sent.replace(trigger, "").strip()
                    if event:
                        # Clean up punctuation
                        event = re.sub(r'[।?,.!]', '', event).strip()
                        timeline.append({
                            "time": time_label,
                            "event": event
                        })
                    break
        return timeline


class SummaryEngine:
    def __init__(self):
        pass

    def generate_summary(self, text, entities, medications, vitals, timeline):
        summary = {
            "chief_complaint": "सामान्य परामर्श (General Consultation)",
            "symptoms": "कोई लक्षण उल्लेखित नहीं (No symptoms mentioned)",
            "diagnosis": "कोई उल्लेखित नहीं (None mentioned)",
            "medicines": "कोई दवाई नहीं (No medication)",
            "advice": "डॉक्टर के निर्देशानुसार आराम करें और पानी पिएं।"
        }
        if not text:
            return summary

        # Extract Chief Complaint and Symptoms
        if entities["symptoms"]:
            summary["symptoms"] = ", ".join(entities["symptoms"])
            summary["chief_complaint"] = f"{entities['symptoms'][0]} की शिकायत"

        # Extract Diagnosis
        if entities["diseases"]:
            summary["diagnosis"] = ", ".join(entities["diseases"])

        # Extract Medicines
        if medications:
            summary["medicines"] = ", ".join([f"{m['name']} ({m['dose']})" for m in medications])

        # Advice heuristics extraction
        advice_keywords = ["सलाह", "परहेज", "आराम", "पिएं", "खाएं", "करो", "करना", "दें", "लें"]
        advice_sentences = []
        sentences = re.split(r'[।\n?.]', text)
        for sent in sentences:
            sent = sent.strip()
            if any(k in sent for k in advice_keywords):
                advice_sentences.append(sent)
        if advice_sentences:
            summary["advice"] = "। ".join(advice_sentences) + "।"

        return summary


def process_clinical_nlp(text):
    """
    Main coordinator to process text and return formatted clinical outputs.
    """
    ner = ClinicalNER()
    meds = MedicationExtractor()
    vitals = VitalExtractor()
    timeline = TimelineBuilder()
    summary = SummaryEngine()

    entities = ner.extract_entities(text)
    medications = meds.extract_medications(text)
    vitals_data = vitals.extract_vitals(text)
    timeline_data = timeline.build_timeline(text)
    summary_data = summary.generate_summary(text, entities, medications, vitals_data, timeline_data)

    return {
        "summary": summary_data,
        "medicines": medications,
        "diseases": entities["diseases"],
        "symptoms": entities["symptoms"],
        "vitals": vitals_data,
        "procedures": entities["procedures"],
        "timeline": timeline_data
    }
