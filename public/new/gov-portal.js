// Bilingual Dictionary & Core Government Portal Controller (GIGW 3.0 Standard)
const translations = {
    en: {
        // Top Accessibility Bar
        "gov_authority": "Government of National Health Authority | Official Emergency Portal",
        "gov_india": "Government of India",
        "skip_content": "Skip to Main Content",
        "screen_reader": "Screen Reader Access",
        "text_size": "Text Size",
        "theme_light": "Light Mode",
        "theme_dark": "Dark Mode",
        "lang_switch_label": "हिंदी",
        "lang_current": "English",
        
        // Brand & Header
        "portal_name": "AmbuPriority",
        "portal_subtitle": "National Ambulance Priority Routing & Dispatch System",
        "ministry_name": "Ministry of Health and Family Welfare",
        "nav_home": "Home",
        "nav_features": "System Features",
        "nav_emergency": "Emergency Help",
        "nav_docs": "Portal Documentation",
        "nav_dashboard": "National Dashboard",
        "btn_emergency_102": "Emergency: Dial 102 / 108",

        // Ticker
        "ticker_latest": "LATEST DISPATCH UPDATE",
        "ticker_news": "AmbuPriority green-corridor priority integrated across 48 major metropolitan hospitals. | Real-time traffic signal preemption operational at 120 key junctions. | Multilingual emergency hotline 102 & 108 operating 24x7 nationwide.",

        // Hero Section
        "hero_tag": "NATIONAL HEALTH EMERGENCY CORRIDOR",
        "hero_heading": "Seconds Save Lives. Priority Ensures Reaching.",
        "hero_desc": "Centrally integrated automated emergency response system connecting GPS ambulances, automated traffic signal corridors, and hospital ICU dashboards in real-time across the country.",
        "hero_cta_stats": "View National Statistics",
        "hero_cta_help": "Call for Ambulance",
        "hero_badge_247": "24/7 Command Active",
        "hero_badge_avg": "Average Arrival: 6.8 Mins",

        // Features Section
        "features_badge": "System Architecture",
        "features_heading": "Core Emergency Dispatch Architecture",
        "features_subheading": "Standardized under National Ambulance Services (NAS) and AIS-125 Code of Practice",
        "f1_title": "Real-time GPS Tracking",
        "f1_desc": "Continuous geofencing monitors every ambulance's location, velocity, and priority status to predict traffic preemption requirements at next junctions.",
        "f2_title": "Smart Signal Preemption",
        "f2_desc": "Automated radio-frequency & sensor integration switches upcoming traffic signals to green when emergency vehicles are detected within 500 meters.",
        "f3_title": "Hospital ICU Bed Sync",
        "f3_desc": "Direct telemetric feed to designated trauma centers to transmit patient vital telemetry and prepare emergency bays before the vehicle arrives.",
        "learn_more": "Learn More",

        // Citizen Resource Center
        "crc_badge": "Citizen Services",
        "crc_heading": "Citizen Resource & Emergency Command Center",
        "crc_desc": "Direct citizen access to emergency protocols, first responder instructions, and real-time helpline networks.",
        "crc_card1_title": "First Aid Medical Guide",
        "crc_card1_desc": "Official Standard Operating Procedures (SOP) for roadside trauma and acute cardiac arrest.",
        "crc_card2_title": "Nearby Trauma Hubs",
        "crc_card2_desc": "Live network map of recognized emergency trauma centers and government tertiary hospitals.",
        "crc_helpline_title": "Toll-Free National Helpline",
        "crc_gallery_title": "National Fleet & Command Gallery",
        "gallery_next": "Next Photo",

        // Footer
        "footer_title": "AmbuPriority National Portal",
        "footer_dept": "National Health Authority • Ministry of Health and Family Welfare, Government of India",
        "footer_disclaimer": "Official Central Citizen Emergency Health Corridor System. All ambulances are monitored under Real-Time Priority Routing Protocol (AIS-125 Compliant).",
        "footer_links_home": "Home",
        "footer_links_docs": "Documentation",
        "footer_links_privacy": "Privacy Policy",
        "footer_links_terms": "Terms of Service",
        "footer_links_guidelines": "GIGW Compliance",
        "footer_links_contact": "Contact Directorate",
        "footer_copyright": "© 2026 National Health Authority, Government of India. All Rights Reserved. Emergency Helpline: 102 / 108 / 112",
        "footer_last_updated": "Last Reviewed & Updated: 07 Nov 2026",

        // Register Page Specific
        "reg_title": "CALL FOR AMBULANCE",
        "reg_subtitle": "Official citizen registry for rapid emergency dispatch. Please enter verified patient and caller coordinates below.",
        "reg_badge_live": "LIVE EMERGENCY DISPATCH",
        "reg_badge_form": "FORM NAS-108-IN",
        "reg_trust_1": "No Login Required",
        "reg_trust_2": "GPS Smart Geotagging",
        "reg_trust_3": "Encrypted Gov Transmission",
        "reg_card_title": "Patient & Caller Registration Form",
        "reg_card_sub": "National Ambulance Service Protocol • Complete All Mandatory Details",
        "reg_mandatory_note": "Fields with red star (*) are mandatory",
        "sec1_num": "01",
        "sec1_title": "Patient Information",
        "sec1_sub": "Identity of the individual requiring immediate medical response",
        "field1_label": "1. Patient Full Name",
        "field1_ph": "Enter patient's full legal name",
        "field1_hint": "Full legal name or known name of the patient",
        "field2_label": "2. Patient Age",
        "field2_ph": "e.g. 45",
        "field2_hint": "In completed years (0 for newborn)",
        "field3_label": "3. Gender",
        "field3_select": "Select Gender",
        "gender_male": "Male",
        "gender_female": "Female",
        "gender_trans": "Transgender",
        "gender_other": "Other / Prefer not to say",
        "field3_hint": "For medical team & triage allocation",
        "sec2_num": "02",
        "sec2_title": "Emergency Contact Numbers",
        "sec2_sub": "Active mobile numbers for driver and paramedic dispatch coordination",
        "field4_label": "4. Mobile Number",
        "field4_ph": "10-digit mobile number",
        "field4_hint": "The driver and paramedic team will call this primary number",
        "field5_label": "5. Alternate Mobile Number",
        "field5_opt": "(optional)",
        "field5_ph": "Secondary contact number",
        "field5_hint": "Backup contact in case primary number is busy or unreachable",
        "sec3_num": "03",
        "sec3_title": "Pickup Location & Geotagging",
        "sec3_sub": "Provide exact address or tap current location to ensure nearest fleet dispatch",
        "gps_box_title": "Instant High-Precision Location Detection",
        "gps_box_sub": "Detect GPS sensor coordinates and autofill verified address automatically.",
        "btn_gps": "USE MY CURRENT LOCATION",
        "btn_gps_loading": "DETECTING GPS LOCATION...",
        "field6_label": "6. Complete Address",
        "field6_sub": "Address Search & Location Suggestions",
        "field6_ph": "Type address, building, or area (e.g. Delhi Cantt, AIIMS, Connaught Place)",
        "field6_hint": "Include House/Flat No., Building Name, Street, Locality, City and PIN Code.",
        "field7_label": "7. Landmark",
        "field7_opt": "(optional)",
        "field7_ph": "e.g. Near Metro Pillar 142, Opposite City Mall, Beside SBI ATM",
        "field7_hint": "Crucial for ambulance driver navigation during urgent moments",
        "sec4_num": "04",
        "sec4_title": "Requestor / Caller Information",
        "sec4_sub": "Details of the individual initiating this emergency registry request",
        "field8_label": "8. Person Requesting Ambulance",
        "field8_ph": "Enter caller / applicant's full name",
        "field8_hint": "Name of the caller requesting medical dispatch",
        "field9_label": "9. Relationship with Patient",
        "field9_select": "Select Relationship",
        "rel_self": "Self (I am the patient)",
        "rel_spouse": "Spouse / Partner",
        "rel_parent": "Parent (Father / Mother)",
        "rel_child": "Child (Son / Daughter)",
        "rel_sibling": "Sibling (Brother / Sister)",
        "rel_relative": "Other Family Relative",
        "rel_friend": "Friend / Colleague",
        "rel_bystander": "Good Samaritan / Road Bystander",
        "rel_staff": "Hospital / Clinic Attendant",
        "rel_other": "Other",
        "field9_hint": "Relationship to the individual in need of care",
        "btn_reset": "Reset Form",
        "btn_submit": "Register Patient Information",
        "dpdpa_notice": "Protected under Digital Personal Data Protection Act (DPDPA 2023)",
        "success_title": "Patient Registration Recorded Successfully",
        "success_badge": "MoHFW Acknowledged",
        "success_msg": "Patient identification and pickup coordinates have been recorded in the central emergency dispatch queue. The dispatch control center has flagged this request for nearest vehicle assignment.",
        "ack_lbl_patient": "Patient:",
        "ack_lbl_contact": "Contact:",
        "ack_lbl_requestor": "Requestor:",
        "ack_lbl_status": "Status:",
        "ack_val_status": "DISPATCH QUEUED",

        // Documentation Page Specific
        "docs_badge": "NATIONAL HEALTH SERVICES DOCUMENTATION",
        "docs_heading": "Official System Documentation & Standards",
        "docs_sub": "Guidelines, Technical Architecture & Operational Protocols under Ministry of Health and Family Welfare",
        "docs_tab1": "System Overview",
        "docs_tab2": "AIS-125 Standards",
        "docs_tab3": "Dispatch Protocol",
        "docs_tab4": "Hospital Integration",
        "docs_back": "Return to Main Portal"
    },
    hi: {
        // Top Accessibility Bar
        "gov_authority": "राष्ट्रीय स्वास्थ्य प्राधिकरण सरकार | आधिकारिक आपातकालीन पोर्टल",
        "gov_india": "भारत सरकार",
        "skip_content": "मुख्य सामग्री पर जाएं",
        "screen_reader": "स्क्रीन रीडर एक्सेस",
        "text_size": "टेक्स्ट आकार",
        "theme_light": "लाइट मोड",
        "theme_dark": "डार्क मोड",
        "lang_switch_label": "English",
        "lang_current": "हिंदी (Hindi)",
        
        // Brand & Header
        "portal_name": "एम्बुप्राथमिकता",
        "portal_subtitle": "राष्ट्रीय एम्बुलेंस प्राथमिकता रूटिंग एवं प्रेषण प्रणाली",
        "ministry_name": "स्वास्थ्य एवं परिवार कल्याण मंत्रालय",
        "nav_home": "होम",
        "nav_features": "प्रणाली विशेषताएं",
        "nav_emergency": "आपातकालीन सहायता",
        "nav_docs": "पोर्टल दस्तावेज़",
        "nav_dashboard": "राष्ट्रीय डैशबोर्ड",
        "btn_emergency_102": "आपातकाल: 102 / 108 डायल करें",

        // Ticker
        "ticker_latest": "ताज़ा प्रेषण सूचना",
        "ticker_news": "एम्बुप्राथमिकता ग्रीन-कॉरिडोर देश के 48 बड़े महानगर अस्पतालों से एकीकृत। | 120 प्रमुख चौराहों पर रीयल-टाइम ट्रैफिक सिग्नल प्राथमिकता चालू। | चौबीसों घंटे बहुभाषी आपातकालीन हेल्पलाइन 102 एवं 108 सक्रिय।",

        // Hero Section
        "hero_tag": "राष्ट्रीय स्वास्थ्य आपातकालीन गलियारा",
        "hero_heading": "सेकंड्स बचाते हैं जान। प्राथमिकता सुनिश्चित करती है पहुंच।",
        "hero_desc": "देश भर में वास्तविक समय में जीपीएस एम्बुलेंस, स्वचालित ट्रैफिक सिग्नल कॉरिडोर और अस्पताल आईसीयू डैशबोर्ड को जोड़ने वाली केंद्रीय रूप से एकीकृत आपातकालीन प्रतिक्रिया प्रणाली।",
        "hero_cta_stats": "राष्ट्रीय आंकड़े देखें",
        "hero_cta_help": "एम्बुलेंस बुलाएं",
        "hero_badge_247": "24/7 कमांड सक्रिय",
        "hero_badge_avg": "औसत आगमन: 6.8 मिनट",

        // Features Section
        "features_badge": "प्रणाली संरचना",
        "features_heading": "मूल आपातकालीन प्रेषण वास्तुकला",
        "features_subheading": "राष्ट्रीय एम्बुलेंस सेवा (NAS) एवं AIS-125 अभ्यास संहिता के तहत मानकीकृत",
        "f1_title": "वास्तविक समय जीपीएस ट्रैकिंग",
        "f1_desc": "निरंतर जियोफेंसिंग प्रत्येक एम्बुलेंस की स्थिति, गति और प्राथमिकता का विश्लेषण करती है ताकि अगले जंक्शन पर ट्रैफिक प्रबंधन सुनिश्चित हो सके।",
        "f2_title": "स्मार्ट सिग्नल प्राथमिकता",
        "f2_desc": "स्वचालित रेडियो फ्रीक्वेंसी एवं सेंसर तकनीक से 500 मीटर के दायरे में आपातकालीन वाहन आते ही आगामी ट्रैफिक सिग्नल हरा हो जाता है।",
        "f3_title": "अस्पताल आईसीयू बेड सिंक",
        "f3_desc": "नामित ट्रॉमा सेंटरों को सीधा टेलीमेट्रिक डेटा ताकि एम्बुलेंस पहुंचने से पहले ही मरीज के महत्वपूर्ण संकेतों के आधार पर आपातकालीन बे तैयार हो सके।",
        "learn_more": "और जानें",

        // Citizen Resource Center
        "crc_badge": "नागरिक सेवाएं",
        "crc_heading": "नागरिक संसाधन एवं आपातकालीन नियंत्रण केंद्र",
        "crc_desc": "आपातकालीन प्रोटोकॉल, प्राथमिक चिकित्सा गाइड और चौबीसों घंटे हेल्पलाइन नेटवर्क तक नागरिकों की सीधी पहुंच।",
        "crc_card1_title": "प्राथमिक चिकित्सा गाइड",
        "crc_card1_desc": "सड़क दुर्घटना एवं आकस्मिक हृदयघात के लिए आधिकारिक मानक संचालन प्रक्रिया (एसओपी)।",
        "crc_card2_title": "निकटवर्ती ट्रॉमा हब",
        "crc_card2_desc": "मान्यता प्राप्त आपातकालीन ट्रॉमा केंद्रों और तृतीयक सरकारी अस्पतालों का लाइव नेटवर्क मानचित्र।",
        "crc_helpline_title": "टोल-फ्री राष्ट्रीय हेल्पलाइन",
        "crc_gallery_title": "राष्ट्रीय फ्लीट एवं कमांड गैलरी",
        "gallery_next": "अगली तस्वीर",

        // Footer
        "footer_title": "एम्बुप्राथमिकता राष्ट्रीय पोर्टल",
        "footer_dept": "राष्ट्रीय स्वास्थ्य प्राधिकरण • स्वास्थ्य एवं परिवार कल्याण मंत्रालय, भारत सरकार",
        "footer_disclaimer": "आधिकारिक केंद्रीय नागरिक आपातकालीन स्वास्थ्य कॉरिडोर प्रणाली। सभी एम्बुलेंस रीयल-टाइम प्राथमिकता रूटिंग प्रोटोकॉल (AIS-125 अनुपालन) के तहत ट्रैक की जाती हैं।",
        "footer_links_home": "होम",
        "footer_links_docs": "दस्तावेज़",
        "footer_links_privacy": "गोपनीयता नीति",
        "footer_links_terms": "सेवा की शर्तें",
        "footer_links_guidelines": "जीआईजीडब्ल्यू अनुपालन",
        "footer_links_contact": "निदेशालय संपर्क",
        "footer_copyright": "© 2026 राष्ट्रीय स्वास्थ्य प्राधिकरण, भारत सरकार। सर्वाधिकार सुरक्षित। आपातकालीन हेल्पलाइन: 102 / 108 / 112",
        "footer_last_updated": "अंतिम समीक्षा एवं अद्यतन: 07 नवम्बर 2026",

        // Register Page Specific
        "reg_title": "एम्बुलेंस के लिए कॉल करें",
        "reg_subtitle": "त्वरित आपातकालीन प्रेषण हेतु आधिकारिक नागरिक पंजीकरण। कृपया नीचे सत्यापित मरीज और कॉलर का विवरण भरें।",
        "reg_badge_live": "लाइव आपातकालीन प्रेषण",
        "reg_badge_form": "प्रपत्र संख्या NAS-108-IN",
        "reg_trust_1": "लॉगिन की आवश्यकता नहीं",
        "reg_trust_2": "जीपीएस स्मार्ट जियोटैगिंग",
        "reg_trust_3": "एन्क्रिप्टेड सरकारी संचरण",
        "reg_card_title": "मरीज एवं कॉलर पंजीकरण प्रपत्र",
        "reg_card_sub": "राष्ट्रीय एम्बुलेंस सेवा प्रोटोकॉल • सभी अनिवार्य विवरण पूर्ण करें",
        "reg_mandatory_note": "लाल तारे (*) वाले फ़ील्ड अनिवार्य हैं",
        "sec1_num": "01",
        "sec1_title": "मरीज की जानकारी",
        "sec1_sub": "त्वरित चिकित्सा प्रतिक्रिया की आवश्यकता वाले व्यक्ति की पहचान",
        "field1_label": "1. मरीज का पूरा नाम",
        "field1_ph": "मरीज का पूरा कानूनी नाम दर्ज करें",
        "field1_hint": "सरकारी पहचान पत्र या परिचारक के अनुसार नाम",
        "field2_label": "2. मरीज की उम्र",
        "field2_ph": "उदा. 45",
        "field2_hint": "पूर्ण वर्षों में (नवजात शिशु के लिए 0)",
        "field3_label": "3. लिंग",
        "field3_select": "लिंग चुनें",
        "gender_male": "पुरुष",
        "gender_female": "महिला",
        "gender_trans": "ट्रांसजेंडर",
        "gender_other": "अन्य / नहीं बताना चाहते",
        "field3_hint": "चिकित्सा टीम एवं ट्राइएज आवंटन हेतु",
        "sec2_num": "02",
        "sec2_title": "आपातकालीन संपर्क नंबर",
        "sec2_sub": "चालक एवं पैरामेडिक समन्वय हेतु सक्रिय मोबाइल नंबर",
        "field4_label": "4. मोबाइल नंबर",
        "field4_ph": "10-अंकों का मोबाइल नंबर",
        "field4_hint": "चालक और पैरामेडिक इस प्राथमिक नंबर पर संपर्क करेंगे",
        "field5_label": "5. वैकल्पिक मोबाइल नंबर",
        "field5_opt": "(वैकल्पिक)",
        "field5_ph": "द्वितीयक संपर्क नंबर",
        "field5_hint": "प्राथमिक नंबर व्यस्त या नेटवर्क बाहर होने की स्थिति में बैकअप",
        "sec3_num": "03",
        "sec3_title": "पिकअप स्थान एवं जियोटैगिंग",
        "sec3_sub": "सटीक पता दर्ज करें या निकटतम वाहन प्रेषण हेतु वर्तमान स्थान टैप करें",
        "gps_box_title": "त्वरित उच्च-सटीकता स्थान पहचान",
        "gps_box_sub": "डिवाइस सेंसर से जीपीएस निर्देशांक प्राप्त करें और सत्यापित पता स्वतः भरें।",
        "btn_gps": "मेरे वर्तमान स्थान का उपयोग करें",
        "btn_gps_loading": "जीपीएस स्थान का पता लगाया जा रहा है...",
        "field6_label": "6. पूरा पता",
        "field6_sub": "पता खोजें और स्थान सुझाव",
        "field6_ph": "पता, भवन, या क्षेत्र टाइप करें (उदा. दिल्ली कैंट, एम्स, कनॉॉट प्लेस)",
        "field6_hint": "मकान/फ्लैट नं., भवन का नाम, सड़क, इलाका, शहर और पिन कोड शामिल करें।",
        "field7_label": "7. प्रमुख लैंडमार्क",
        "field7_opt": "(वैकल्पिक)",
        "field7_ph": "उदा. मेट्रो पिलर 142 के पास, सिटी मॉल के सामने, एसबीआई एटीएम के बगल में",
        "field7_hint": "तत्काल समय में एम्बुलेंस चालक के आसान नेविगेशन हेतु महत्वपूर्ण",
        "sec4_num": "04",
        "sec4_title": "आवेदक / कॉलर की जानकारी",
        "sec4_sub": "इस आपातकालीन पंजीकरण अनुरोध को प्रारंभ करने वाले व्यक्ति का विवरण",
        "field8_label": "8. एम्बुलेंस अनुरोधकर्ता का नाम",
        "field8_ph": "कॉलर / आवेदक का पूरा नाम दर्ज करें",
        "field8_hint": "चिकित्सा प्रेषण का अनुरोध करने वाले कॉलर का नाम",
        "field9_label": "9. मरीज के साथ संबंध",
        "field9_select": "संबंध चुनें",
        "rel_self": "स्वयं (मैं मरीज हूं)",
        "rel_spouse": "पति / पत्नी",
        "rel_parent": "माता / पिता",
        "rel_child": "बेटा / बेटी",
        "rel_sibling": "भाई / बहन",
        "rel_relative": "अन्य पारिवारिक रिश्तेदार",
        "rel_friend": "मित्र / सहकर्मी",
        "rel_bystander": "सड़क प्रत्यक्षदर्शी / मददगार नागरिक",
        "rel_staff": "अस्पताल / क्लिनिक परिचारक",
        "rel_other": "अन्य",
        "field9_hint": "देखभाल की आवश्यकता वाले मरीज से कानूनी संबंध",
        "btn_reset": "फ़ॉर्म रीसेट करें",
        "btn_submit": "मरीज की जानकारी पंजीकृत करें",
        "dpdpa_notice": "डिजिटल व्यक्तिगत डेटा संरक्षण अधिनियम (DPDPA 2023) के तहत संरक्षित",
        "success_title": "मरीज पंजीकरण सफलतापूर्वक दर्ज किया गया",
        "success_badge": "स्वास्थ्य मंत्रालय द्वारा अभिस्वीकृत",
        "success_msg": "मरीज की पहचान और पिकअप निर्देशांक केंद्रीय आपातकालीन प्रेषण कतार में दर्ज हो गए हैं। नियंत्रण कक्ष ने निकटतम वाहन आवंटन हेतु अनुरोध चिह्नित कर दिया है।",
        "ack_lbl_patient": "मरीज:",
        "ack_lbl_contact": "संपर्क:",
        "ack_lbl_requestor": "अनुरोधकर्ता:",
        "ack_lbl_status": "स्थिति:",
        "ack_val_status": "प्रेषण कतार में",

        // Documentation Page Specific
        "docs_badge": "राष्ट्रीय स्वास्थ्य सेवा दस्तावेज़ीकरण",
        "docs_heading": "आधिकारिक प्रणाली दस्तावेज़ एवं मानक",
        "docs_sub": "स्वास्थ्य एवं परिवार कल्याण मंत्रालय के तहत दिशानिर्देश, तकनीकी वास्तुकला एवं संचालन प्रोटोकॉल",
        "docs_tab1": "प्रणाली अवलोकन",
        "docs_tab2": "AIS-125 मानक",
        "docs_tab3": "प्रेषण प्रोटोकॉल",
        "docs_tab4": "अस्पताल एकीकरण",
        "docs_back": "मुख्य पोर्टल पर वापस जाएं"
    }
};

// State Manager
class GovPortalManager {
    constructor() {
        this.currentLang = localStorage.getItem('gov_lang') || 'en';
        this.currentTheme = localStorage.getItem('gov_theme') || 'light';
        this.init();
    }

    init() {
        // Apply initial theme
        this.applyTheme(this.currentTheme);
        // Apply initial language
        this.applyLanguage(this.currentLang);
    }

    applyTheme(theme) {
        this.currentTheme = theme;
        localStorage.setItem('gov_theme', theme);
        if (theme === 'dark') {
            document.documentElement.classList.add('dark');
        } else {
            document.documentElement.classList.remove('dark');
        }
        this.updateThemeButtonUI();
    }

    toggleTheme() {
        const nextTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
        this.applyTheme(nextTheme);
    }

    updateThemeButtonUI() {
        const themeBtnText = document.getElementById('themeToggleText');
        const themeBtnIcon = document.getElementById('themeToggleIcon');
        if (!themeBtnText) return;

        const isDark = this.currentTheme === 'dark';
        if (isDark) {
            themeBtnIcon.className = 'fa-solid fa-sun text-yellow-400';
            themeBtnText.textContent = this.currentLang === 'hi' ? 'लाइट मोड' : 'Light Mode';
        } else {
            themeBtnIcon.className = 'fa-solid fa-moon text-blue-200';
            themeBtnText.textContent = this.currentLang === 'hi' ? 'डार्क मोड' : 'Dark Mode';
        }
    }

    applyLanguage(lang) {
        if (!translations[lang]) lang = 'en';
        this.currentLang = lang;
        localStorage.setItem('gov_lang', lang);
        document.documentElement.setAttribute('lang', lang);

        const dict = translations[lang];

        // Replace all elements with data-i18n attribute
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            if (dict[key]) {
                el.textContent = dict[key];
            }
        });

        // Replace all elements with data-i18n-ph (placeholder) attribute
        document.querySelectorAll('[data-i18n-ph]').forEach(el => {
            const key = el.getAttribute('data-i18n-ph');
            if (dict[key]) {
                el.setAttribute('placeholder', dict[key]);
            }
        });

        // Update language switcher UI button
        const langToggleText = document.getElementById('langToggleText');
        if (langToggleText) {
            langToggleText.textContent = lang === 'en' ? 'हिंदी (Hindi)' : 'English';
        }

        this.updateThemeButtonUI();
    }

    toggleLanguage() {
        const nextLang = this.currentLang === 'en' ? 'hi' : 'en';
        this.applyLanguage(nextLang);
    }

    getText(key) {
        const dict = translations[this.currentLang] || translations.en;
        return dict[key] || key;
    }
}

// Global instance
window.govPortal = new GovPortalManager();

// Global zoom controller for GIGW standard
let portalZoomLevel = 1;
function adjustPortalZoom(dir) {
    if (dir === 0) portalZoomLevel = 1;
    else if (dir === 1 && portalZoomLevel < 1.15) portalZoomLevel += 0.05;
    else if (dir === -1 && portalZoomLevel > 0.9) portalZoomLevel -= 0.05;
    document.body.style.zoom = portalZoomLevel;
}

