/**
 * E-Sanjeevni — ARIA (Ambulance Response Intelligent Assistant)
 * 3D Procedural AI Virtual Assistant powered by Canvas/Three.js
 * 
 * Purely Client-Side Form Assistance Engine:
 *  - 100% Offline / Standalone (No external API or backend calls)
 *  - Dedicated Expert Guide for All Portal Forms (Registration, Clinical Triage Assessment, Hospital Search)
 *  - Interactive Hindi / English Language Selector on Initial Greeting ("Namaste! Do you want to continue in Hindi or English?")
 *  - Deep Domain Knowledge of form fields, mandatory rules, GPS geolocation, dynamic questions, and errors
 */

(function () {
    'use strict';

    /* ============================================================
       CONFIGURATION
    ============================================================ */
    const ARIA_CONFIG = {
        name: 'ARIA',
        fullName: 'Ambulance Response Intelligent Assistant',
        version: '3.0-FormExpert',
        typingDelay: { min: 30, max: 80 },
        characterThinkTime: 60
    };

    /* ============================================================
       COMPREHENSIVE FORM KNOWLEDGE BASE (HINDI & ENGLISH)
    ============================================================ */
    const FORM_KNOWLEDGE = {
        hi: {
            greeting: "नमस्ते! 🙏 मैं **ARIA (एरिया)** हूँ, आपकी E-Sanjeevni सहायक।\n\nDo you want to continue in **Hindi** or **English**?\n(क्या आप हिंदी में आगे बढ़ना चाहते हैं या English में?)",
            greetingChips: ["हिंदी (Hindi)", "English", "फॉर्म कैसे भरें?", "कौन सा फॉर्म भरें?"],
            
            whichForm: {
                title: "E-Sanjeevni पोर्टल पर मुख्य रूप से 3 फॉर्म उपलब्ध हैं:",
                body: "1. 📝 **एम्बुलेंस पंजीकरण फ़ॉर्म (Registration Form - register.html):**\n• जब किसी मरीज के लिए तत्काल सरकारी/प्राइवेट एम्बुलेंस बुलानी हो।\n• इसमें मरीज का नाम, पता, संपर्क नंबर और GPS लोकेशन भरी जाती है।\n\n2. 🩺 **क्लिनिकल असेसमेंट / ट्रायज फ़ॉर्म (Clinical Assessment - assessment.html):**\n• मरीज की स्वास्थ्य स्थिति और लक्षणों (सीने में दर्द, सांस लेने में तकलीफ, स्ट्रोक आदि) का मूल्यांकन करने के लिए।\n• इससे सिस्टम तय करता है कि ALS (Advanced Life Support) चाहिए या BLS।\n\n3. 🔍 **अस्पताल खोज फ़ॉर्म (Hospital Search - hospitals.html):**\n• नजदीकी पैनल (आयुष्मान PM-JAY, CGHS, ECHS, बीमा) और आपातकालीन बेड खोजने के लिए।\n\n👉 आपको इनमें से किस फॉर्म के बारे में जानकारी चाहिए?",
                chips: ["रजिस्ट्रेशन फॉर्म कैसे भरें?", "असेसमेंट फॉर्म कैसे भरें?", "अनिवार्य फ़ील्ड्स कौन सी हैं?", "GPS लोकेशन कैसे डालें?"]
            },
            
            registrationGuide: {
                title: "🚑 एम्बुलेंस पंजीकरण फ़ॉर्म (Registration Form) भरने की पूरी प्रक्रिया:",
                body: "**भाग 1 — मरीज की जानकारी (Patient Information):**\n• **मरीज का पूरा नाम (*):** मरीज का कानूनी नाम लिखें।\n• **उम्र (*):** मरीज की उम्र (वर्षों में) दर्ज करें (जैसे: 45)।\n• **लिंग (*):** Male (पुरुष), Female (महिला) या Other चुनें।\n\n**भाग 2 — संपर्क नंबर (Emergency Contact):**\n• **मोबाइल नंबर (*):** 10 अंकों का सक्रिय मोबाइल नंबर डालें ताकि ड्राइवर व पैरामेडिक संपर्क कर सकें।\n• **वैकल्पिक नंबर:** दूसरा फोन नंबर (यदि उपलब्ध हो)।\n\n**भाग 3 — पिकअप का पता (Pickup Location & GeoTagging):**\n• **\"Use My Current Location\"** बटन दबाएं — यह उपग्रह GPS से आपका सटीक पता और अक्षांश-देशांतर लॉक कर देगा।\n• **पूरा पता (*):** मकान नंबर, गली या इलाका लिखें।\n• **लैंडमार्क (पहचान):** पास का प्रसिद्ध स्थान (जैसे: मेट्रो पिलर 142 के पास, हनुमान मंदिर के सामने)।\n\n**भाग 4 — आवेदक का विवरण (Requestor Information):**\n• **आपका नाम (*):** जो व्यक्ति एम्बुलेंस बुला रहा है।\n• **मरीज से संबंध (*):** स्वयं (Self), परिवार (Family), पड़ोसी (Neighbour) आदि चुनें।\n\nसब भरने के बाद नीचे लाल बटन **\"Request Ambulance\"** पर क्लिक करें। आपको **NAS-XXXXXX** रेफरेंस नंबर मिलेगा!",
                chips: ["अनिवार्य फ़ील्ड्स (*)", "GPS कैसे काम करता है?", "असेसमेंट फॉर्म कैसे भरें?", "रजिस्ट्रेशन फॉर्म खोलें"]
            },
            
            assessmentGuide: {
                title: "🩺 क्लिनिकल ट्रायज असेसमेंट फ़ॉर्म (Clinical Assessment) भरने की गाइड:",
                body: "यह फॉर्म मरीज की गंभीरता का स्तर (Priority Tier) निर्धारित करता है:\n\n**1. मुख्य आपातकालीन श्रेणी (Chief Complaint Category *):**\n• Cardiac / Chest Pain (सीने में दर्द या दिल का दौरा)\n• Severe Breathing (सांस लेने में भारी तकलीफ या अस्थमा)\n• Stroke Signs / Paralysis (चेहरा लटकना, हाथ कमजोर होना)\n• Trauma / Accident (सड़क दुर्घटना, गंभीर चोट)\n• अन्य आपातकालीन विकल्प ड्रॉपडाउन से चुनें।\n\n**2. शुरुआत का समय (Onset & Duration *):**\n• यह समस्या कब शुरू हुई (15 मिनट के अंदर, 1-6 घंटे पहले आदि)।\n\n**3. संबंधित लक्षण (Associated Symptoms):**\n• पसीना आना, चक्कर आना, उल्टी, होंठ नीले पड़ना (चेकबॉक्स चुनें)।\n\n**4. चेतना का स्तर (AVPU Mental Status *):**\n• Alert (पूरी तरह होश में)\n• Voice (आवाज देने पर प्रतिक्रिया)\n• Pain (दर्द पर प्रतिक्रिया)\n• Unresponsive (बेहोश — उच्चतम प्राथमिकता RED Tier-1)।\n\n**5. वाइटल साइन्स (वैकल्पिक):**\n• यदि पल्स या बीपी नापा हुआ हो तो भरें, अन्यथा खाली छोड़ दें।\n\nसबमिट करने पर सिस्टम तुरंत उचित एम्बुलेंस और अस्पताल असाइन करता है!",
                chips: ["रजिस्ट्रेशन फॉर्म कैसे भरें?", "AVPU क्या होता है?", "हार्ट अटैक के लक्षण?", "असेसमेंट फॉर्म खोलें"]
            },
            
            mandatoryFields: {
                title: "📌 फ़ॉर्म में अनिवार्य (Mandatory *) फ़ील्ड्स की सूची:",
                body: "जिन फ़ील्ड्स के आगे लाल तारा (*) बना है, उन्हें भरना अनिवार्य है:\n\n**पंजीकरण फॉर्म में:**\n1. मरीज का पूरा नाम (Patient Full Name)\n2. मरीज की उम्र (Patient Age)\n3. मरीज का लिंग (Gender)\n4. 10 अंकों का सक्रिय मोबाइल नंबर\n5. पिकअप का पूरा पता (Complete Address)\n6. अनुरोधकर्ता का नाम व मरीज से संबंध (Relationship)\n\n*(वैकल्पिक: दूसरा फोन नंबर और लैंडमार्क)*\n\n**असेसमेंट फॉर्म में:**\n1. मुख्य आपातकाल श्रेणी (Chief Complaint)\n2. शुरुआत का समय (Onset & Duration)\n3. चेतना का स्तर (AVPU Consciousness Status)",
                chips: ["रजिस्ट्रेशन फॉर्म कैसे भरें?", "GPS लोकेशन कैसे डालें?", "फॉर्म सबमिट नहीं हो रहा"]
            },
            
            gpsHelp: {
                title: "📍 GPS ऑटो-लोकेशन का उपयोग कैसे करें:",
                body: "1. फॉर्म में **\"Use My Current Location\"** बटन पर क्लिक करें।\n2. आपका ब्राउज़र लोकेशन परमिशन मांगेगा — **\"Allow\" (अनुमति दें)** पर क्लिक करें।\n3. सिस्टम तुरंत उपग्रह GPS से सटीक अक्षांश (Latitude) व देशांतर (Longitude) लॉक करके आपका पता अपने आप भर देगा।\n\n💡 **महत्वपूर्ण टिप्स:**\n• यदि आप घर के अंदर हैं तो बालकनी या खिड़की के पास जाएं।\n• फोन या कंप्यूटर में Location / GPS ऑन रखें।\n• यदि GPS काम न करे, तो हाथ से मैन्युअल पता और लैंडमार्क टाइप कर दें।",
                chips: ["लैंडमार्क क्या लिखें?", "रजिस्ट्रेशन फॉर्म कैसे भरें?", "अनिवार्य फ़ील्ड्स"]
            },
            
            landmarkHelp: {
                title: "🏛️ लैंडमार्क (Landmark) फ़ील्ड में क्या लिखें?",
                body: "लैंडमार्क का अर्थ है आपके घर या घटना स्थल के पास की कोई प्रसिद्ध पहचान:\n\n**उदाहरण:**\n• \"मेट्रो पिलर नंबर 142 के सामने\"\n• \"एसबीआई बैंक के पास, मेन मार्केट रोड\"\n• \"हनुमान मंदिर के ठीक पीछे\"\n• \"रिलायंस फ्रेश मॉल के बगल में\"\n\nइससे एम्बुलेंस चालक को गली या कॉलोनी में बिना समय गंवाए आप तक पहुंचने में सबसे ज्यादा आसानी होती है।",
                chips: ["रजिस्ट्रेशन फॉर्म कैसे भरें?", "अनिवार्य फ़ील्ड्स"]
            },
            
            avpuHelp: {
                title: "🧠 AVPU स्केल का क्या अर्थ है?",
                body: "AVPU मरीज की मानसिक चेतना को जांचने का अंतरराष्ट्रीय पैमाना है:\n\n• **A (Alert):** मरीज पूरी तरह होश में है और सामान्य बातचीत कर रहा है।\n• **V (Voice):** मरीज आवाज देने पर आंखें खोलता है या जवाब देता है।\n• **P (Pain):** मरीज केवल चुटकी काटने या दर्द देने पर हरकत करता है।\n• **U (Unresponsive):** मरीज बिल्कुल बेहोश है और कोई हरकत नहीं कर रहा (अति गंभीर - Red Tier-1 Immediate Dispatch)।",
                chips: ["असेसमेंट फॉर्म कैसे भरें?", "रजिस्ट्रेशन फॉर्म कैसे भरें?"]
            },
            
            referenceHelp: {
                title: "🔢 NAS रेफरेंस नंबर और पावती (Acknowledgment):",
                body: "फॉर्म सफलतापूर्वक सबमिट करने के बाद आपको एक संदर्भ संख्या मिलती है:\n\n• प्रारूप: **NAS-2026-XXXXXX**\n• इसका उपयोग एम्बुलेंस की लाइव लोकेशन ट्रैक करने और आपातकालीन कॉल (102/108/112) में संदर्भ देने के लिए किया जाता है।\n• कृपया सबमिट करने के बाद स्क्रीन पर आए इस नंबर को नोट कर लें!",
                chips: ["रजिस्ट्रेशन फॉर्म कैसे भरें?", "हेल्पलाइन नंबर"]
            },
            
            formErrors: {
                title: "⚠️ यदि फ़ॉर्म सबमिट न हो रहा हो तो क्या करें?",
                body: "1. जांचें कि क्या कोई लाल तारे (*) वाली अनिवार्य फ़ील्ड खाली तो नहीं रह गई।\n2. मोबाइल नंबर पूरे 10 अंकों का होना चाहिए।\n3. उम्र 0 से 125 के बीच होनी चाहिए।\n4. यदि GPS नहीं चल रहा तो मैन्युअल पता टाइप करें।\n5. किसी भी तकनीकी समस्या की स्थिति में सीधे **102** या **108** या **112** पर कॉल करें!",
                chips: ["अनिवार्य फ़ील्ड्स", "रजिस्ट्रेशन फॉर्म कैसे भरें?", "हेल्पलाइन नंबर"]
            },
            
            resetHelp: {
                title: "🔄 फ़ॉर्म रीसेट / खाली कैसे करें?",
                body: "फॉर्म के नीचे **\"Reset Form\"** बटन दिया गया है।\nउस पर क्लिक करते ही फॉर्म की सभी फ़ील्ड्स खाली हो जाएंगी और आप नए सिरे से जानकारी भर सकते हैं।",
                chips: ["रजिस्ट्रेशन फॉर्म कैसे भरें?"]
            },
            
            helpline: {
                title: "📞 24×7 राष्ट्रीय आपातकालीन हेल्पलाइन नंबर:",
                body: "• **112** — सार्वभौमिक आपातकालीन नंबर (पुलिस, फायर, मेडिकल)\n• **102** — राष्ट्रीय एम्बुलेंस सेवा (National Ambulance Service)\n• **108** — आपातकालीन चिकित्सा व आपदा प्रतिक्रिया\n\nसभी नंबर किसी भी फोन से बिल्कुल निःशुल्क (Toll-Free) हैं।",
                chips: ["रजिस्ट्रेशन फॉर्म कैसे भरें?", "असेसमेंट फॉर्म कैसे भरें?"]
            }
        },

        en: {
            greeting: "Namaste! 🙏 I am **ARIA**, your E-Sanjeevni Virtual Assistant.\n\nDo you want to continue in **Hindi** or **English**?\n(क्या आप हिंदी में आगे बढ़ना चाहते हैं या English में?)",
            greetingChips: ["English", "हिंदी (Hindi)", "How to fill form?", "Which form to fill?"],
            
            whichForm: {
                title: "There are 3 main forms available on E-Sanjeevni:",
                body: "1. 📝 **Ambulance Registration Form (register.html):**\n• Use this when you urgently need to call or dispatch an ambulance for a patient.\n• Captures patient identity, 10-digit mobile, pickup address, and GPS coordinates.\n\n2. 🩺 **Clinical Triage Assessment Form (assessment.html):**\n• Evaluates medical urgency (cardiac chest pain, stroke FAST symptoms, trauma, respiratory arrest).\n• Categorizes urgency into RED (Immediate ALS), YELLOW, or GREEN tier.\n\n3. 🔍 **Hospital Search Form (hospitals.html):**\n• Search for empanelled hospitals under Ayushman PM-JAY, CGHS, ECHS, or private insurance.\n\n👉 Which of these forms do you need assistance with?",
                chips: ["How to fill Registration Form?", "How to fill Assessment Form?", "What fields are mandatory?", "How to use GPS?"]
            },
            
            registrationGuide: {
                title: "🚑 Step-by-Step Ambulance Registration Form Guide:",
                body: "**Section 1 — Patient Information:**\n• **Patient Full Name (*):** Enter patient's full legal name.\n• **Age (*):** Enter age in years (e.g., 45).\n• **Gender (*):** Select Male, Female, or Other.\n\n**Section 2 — Contact Numbers:**\n• **Mobile Number (*):** Active 10-digit phone number for paramedic & driver contact.\n• **Alternate Mobile:** Secondary contact number (optional).\n\n**Section 3 — Pickup Location & GeoTagging:**\n• Click **\"Use My Current Location\"** — Locks GPS coordinates & auto-fills address.\n• **Complete Address (*):** House/Flat no., street, colony or sector.\n• **Landmark (Optional):** Prominent nearby landmark (e.g., near Metro Pillar 142).\n\n**Section 4 — Requestor Information:**\n• **Requestor Name (*):** Name of person requesting the ambulance.\n• **Relationship (*):** Select Self, Family Member, Neighbour, Bystander, etc.\n\nOnce done, click **\"Request Ambulance\"**. You will receive a **NAS-XXXXXX** tracking reference number!",
                chips: ["Mandatory Fields (*)", "GPS Geolocation Help", "Assessment Form Guide", "Open Registration Form"]
            },
            
            assessmentGuide: {
                title: "🩺 Clinical Triage Assessment Form Step-by-Step Guide:",
                body: "This form determines clinical urgency and ambulance dispatch priority:\n\n**1. Chief Complaint Category (*):**\n• Cardiac / Chest Pain / Heart Condition\n• Severe Breathing Difficulty / Asthma\n• Stroke Signs / Paralysis / FAST signs\n• Road Traffic Accident / Major Trauma\n• Burns, Seizures, Pregnancy, or Other acute emergencies.\n\n**2. Onset & Duration (*):**\n• When did symptoms begin (<15 mins, 15-60 mins, 1-6 hours, days).\n\n**3. Associated Symptoms (Checkboxes):**\n• Profuse sweating, vomiting, dizziness, cold clammy skin, bluish lips.\n\n**4. Mental Status / AVPU (*):**\n• Alert (Conscious & responsive)\n• Voice (Responds to verbal stimulus)\n• Pain (Responds only to physical pain)\n• Unresponsive (Comatose / unconscious — Immediate RED Tier-1).\n\n**5. Vital Signs (Optional):**\n• Pulse, Blood Pressure, SpO2, Blood Sugar (Leave blank if not measured).\n\nSubmitting instantly routes the case to the appropriate emergency hospital!",
                chips: ["How to fill Registration Form?", "What is AVPU?", "Heart attack symptoms?", "Open Assessment Form"]
            },
            
            mandatoryFields: {
                title: "📌 Mandatory Fields (Marked with Red Asterisk *):",
                body: "Fields with a red asterisk (*) must be filled before submission:\n\n**On Registration Form:**\n1. Patient Full Name\n2. Patient Age (in years)\n3. Gender (Male / Female / Other)\n4. Active 10-digit Mobile Number\n5. Complete Pickup Address\n6. Requestor Name & Relationship to Patient\n\n*(Optional: Alternate Mobile & Landmark)*\n\n**On Clinical Assessment Form:**\n1. Chief Complaint Category\n2. Onset & Duration\n3. AVPU Consciousness Status",
                chips: ["Registration Form Guide", "How to use GPS?", "Troubleshoot Form Submission"]
            },
            
            gpsHelp: {
                title: "📍 How to Use Auto-GPS Geolocation:",
                body: "1. Click the **\"Use My Current Location\"** button on the registration form.\n2. When prompted by your browser, click **\"Allow\"** for location access.\n3. The system locks your satellite GPS coordinates and automatically populates your street address.\n\n💡 **Tips for GPS Accuracy:**\n• If indoors, move near a balcony or window.\n• Ensure location/GPS services are toggled ON in your device settings.\n• If GPS is unavailable, you can manually type your full address and nearest landmark.",
                chips: ["What is Landmark?", "Registration Form Guide", "Mandatory Fields"]
            },
            
            landmarkHelp: {
                title: "🏛️ What Should I Enter in the Landmark Field?",
                body: "A landmark is a prominent, well-known spot close to your pickup location:\n\n**Examples:**\n• \"Opposite Metro Pillar No. 142\"\n• \"Near SBI Bank ATM, Main Market\"\n• \"Behind Shiv Temple\"\n• \"Next to City Mall Gate No. 2\"\n\nThis field is optional but helps the ambulance pilot find your exact location without delay.",
                chips: ["Registration Form Guide", "Mandatory Fields"]
            },
            
            avpuHelp: {
                title: "🧠 Understanding the AVPU Consciousness Scale:",
                body: "AVPU is the international standard to measure conscious state in an emergency:\n\n• **Alert (A):** Fully awake, answers questions, oriented.\n• **Voice (V):** Responds only when spoken or shouted to.\n• **Pain (P):** Responds only to painful stimuli (pinch/sternal rub).\n• **Unresponsive (U):** Completely comatose or unconscious (triggers emergency RED Tier dispatch).",
                chips: ["Assessment Form Guide", "Registration Form Guide"]
            },
            
            referenceHelp: {
                title: "🔢 NAS Reference Tracking Number:",
                body: "Upon submitting the registration form, you receive an acknowledgment reference:\n\n• Format: **NAS-2026-XXXXXX**\n• Use this number to track your ambulance arrival or give to the 102/108 dispatcher during follow-up calls.\n• Please note or screenshot this reference number from the screen.",
                chips: ["Registration Form Guide", "Emergency Helplines"]
            },
            
            formErrors: {
                title: "⚠️ Cannot Submit Form? Troubleshooting Checklist:",
                body: "1. Check that all fields with a red asterisk (*) have valid data.\n2. Ensure the mobile number is exactly 10 digits.\n3. Ensure age is between 0 and 125.\n4. If GPS address didn't load, manually type the address.\n5. For life-threatening emergencies where you cannot type, dial **112** or **102** directly!",
                chips: ["Mandatory Fields", "Registration Form Guide", "Emergency Helplines"]
            },
            
            resetHelp: {
                title: "🔄 How to Reset or Clear the Form:",
                body: "Click the **\"Reset Form\"** button at the bottom of the page.\nThis will clear all entered input fields and allow you to restart fresh.",
                chips: ["Registration Form Guide"]
            },
            
            helpline: {
                title: "📞 24×7 National Emergency Helplines:",
                body: "• **112** — Universal National Emergency Number (Police, Fire, Medical)\n• **102** — National Ambulance Service (NAS)\n• **108** — Emergency Medical & Disaster Relief Services\n\nAll numbers are toll-free and accessible from any phone without recharge balance.",
                chips: ["Registration Form Guide", "Assessment Form Guide"]
            }
        }
    };

/* ============================================================
       THREE.JS 3D CHARACTER RENDERER
    ============================================================ */
    class ARIACharacter3D {
        constructor(canvas, options = {}) {
            this.canvas = canvas;
            this.isSmall = options.isSmall || false;
            this.state = 'idle';
            this.animTime = 0;
            this.blinkTimer = 0;
            this.blinkInterval = 3.5;
            this.headBobPhase = 0;
            this.mouthOpen = 0;
            this.eyeOpenLeft = 1;
            this.eyeOpenRight = 1;
            this.targetMouthOpen = 0;
            this.targetEyeOpen = 1;
            this.shoudlerSwayPhase = 0;
            this.frameId = null;
            this.lastTime = 0;
            this.isActive = true;
            this.init();
        }

        init() {
            const W = this.canvas.width  = this.canvas.offsetWidth  * Math.min(window.devicePixelRatio, 2);
            const H = this.canvas.height = this.canvas.offsetHeight * Math.min(window.devicePixelRatio, 2);

            this.ctx = this.canvas.getContext('2d');
            if (!this.ctx) return;

            this.W = W;
            this.H = H;
            this.cx = W / 2;
            this.cy = H / 2;

            this.startLoop();
        }

        setState(state) {
            this.state = state;
        }

        startLoop() {
            const loop = (timestamp) => {
                if (!this.isActive) return;
                const dt = Math.min((timestamp - this.lastTime) / 1000, 0.05);
                this.lastTime = timestamp;
                this.animTime += dt;
                this.update(dt);
                this.draw();
                this.frameId = requestAnimationFrame(loop);
            };
            this.frameId = requestAnimationFrame(loop);
        }

        stop() {
            this.isActive = false;
            if (this.frameId) cancelAnimationFrame(this.frameId);
        }

        update(dt) {
            this.blinkTimer += dt;
            if (this.blinkTimer >= this.blinkInterval) {
                this.blinkTimer = 0;
                this.blinkInterval = 2.5 + Math.random() * 3;
                this.targetEyeOpen = 0;
                setTimeout(() => { this.targetEyeOpen = 1; }, 120);
            }

            // Smooth eye blink
            this.eyeOpenLeft  = lerp(this.eyeOpenLeft,  this.targetEyeOpen, 18 * dt);
            this.eyeOpenRight = lerp(this.eyeOpenRight, this.targetEyeOpen, 18 * dt);

            // Head bob
            this.headBobPhase += dt * (this.state === 'idle' ? 0.8 : 1.4);

            // Shoulder sway
            this.shoudlerSwayPhase += dt * 0.6;

            // Mouth animation
            if (this.state === 'responding') {
                this.targetMouthOpen = 0.5 + 0.5 * Math.sin(this.animTime * 8.5);
            } else if (this.state === 'thinking') {
                this.targetMouthOpen = 0.1 + 0.1 * Math.sin(this.animTime * 2);
            } else {
                this.targetMouthOpen = 0.02 * Math.sin(this.animTime * 1.2);
            }
            this.mouthOpen = lerp(this.mouthOpen, this.targetMouthOpen, 12 * dt);
        }

        draw() {
            const ctx = this.ctx;
            const W = this.W, H = this.H;
            ctx.clearRect(0, 0, W, H);

            // ---- Scale to canvas size ----
            const scale = this.isSmall ? W / 76 : W / 110;
            ctx.save();
            ctx.scale(scale, scale);

            const uw = W / scale; // unit width
            const uh = H / scale; // unit height
            const cx = uw / 2;

            // Head bob offset
            const bobY = Math.sin(this.headBobPhase) * (this.state === 'idle' ? 0.5 : 1.0);
            const shoulderSway = Math.sin(this.shoudlerSwayPhase) * 1.2;

            // ---- NECK / BODY ----
            const bodyTop = uh * 0.60;

            // Body / torso — dark navy uniform
            const bodyGrad = ctx.createLinearGradient(cx - 20, bodyTop, cx + 20, uh);
            bodyGrad.addColorStop(0, '#1a3a5c');
            bodyGrad.addColorStop(0.4, '#003366');
            bodyGrad.addColorStop(1, '#00254d');
            ctx.beginPath();
            ctx.moveTo(cx - 18 + shoulderSway, bodyTop + 2);
            ctx.bezierCurveTo(cx - 24, bodyTop + 10, cx - 26, uh * 0.8, cx - 22, uh + 5);
            ctx.lineTo(cx + 22, uh + 5);
            ctx.bezierCurveTo(cx + 26, uh * 0.8, cx + 24, bodyTop + 10, cx + 18 + shoulderSway, bodyTop + 2);
            ctx.closePath();
            ctx.fillStyle = bodyGrad;
            ctx.fill();

            // Collar / white shirt peek
            ctx.beginPath();
            ctx.moveTo(cx - 7, bodyTop + 2);
            ctx.lineTo(cx, bodyTop + 10);
            ctx.lineTo(cx + 7, bodyTop + 2);
            ctx.fillStyle = '#e8ecf0';
            ctx.fill();

            // Uniform badge (small red rectangle)
            ctx.fillStyle = '#c0392b';
            ctx.beginPath();
            ctx.roundRect(cx - 12, bodyTop + 14, 12, 7, 2);
            ctx.fill();
            ctx.fillStyle = '#fff';
            ctx.font = `bold ${3.5 * (1/scale * scale)}px Inter, sans-serif`;
            ctx.textAlign = 'center';

            // Shoulder epaulettes
            ctx.fillStyle = '#c0392b';
            ctx.beginPath();
            ctx.ellipse(cx - 18, bodyTop + 4, 5, 3, -0.3, 0, Math.PI * 2);
            ctx.fill();
            ctx.beginPath();
            ctx.ellipse(cx + 18, bodyTop + 4, 5, 3, 0.3, 0, Math.PI * 2);
            ctx.fill();

            // ---- NECK ----
            const neckY = uh * 0.52 + bobY;
            const skinColor = '#c8956c';
            const skinHighlight = '#d4a07a';
            const skinShadow = '#b07d55';

            ctx.beginPath();
            ctx.moveTo(cx - 7, neckY + 10);
            ctx.lineTo(cx - 6, neckY);
            ctx.lineTo(cx + 6, neckY);
            ctx.lineTo(cx + 7, neckY + 10);
            ctx.fillStyle = skinColor;
            ctx.fill();

            // ---- HEAD ----
            const headCy = uh * 0.34 + bobY;
            const headRx = 16, headRy = 18.5;

            // Head shadow / depth
            ctx.beginPath();
            ctx.ellipse(cx + 1, headCy + 2, headRx + 1, headRy + 1, 0, 0, Math.PI * 2);
            ctx.fillStyle = 'rgba(0,0,0,0.12)';
            ctx.fill();

            // Head base
            const headGrad = ctx.createRadialGradient(cx - 4, headCy - 6, 2, cx, headCy, headRx + 4);
            headGrad.addColorStop(0, skinHighlight);
            headGrad.addColorStop(0.5, skinColor);
            headGrad.addColorStop(1, skinShadow);
            ctx.beginPath();
            ctx.ellipse(cx, headCy, headRx, headRy, 0, 0, Math.PI * 2);
            ctx.fillStyle = headGrad;
            ctx.fill();

            // Slight head tilt during thinking
            const tiltAngle = this.state === 'thinking' ? Math.sin(this.animTime * 1.5) * 0.08 : 0;
            ctx.save();
            ctx.translate(cx, headCy);
            ctx.rotate(tiltAngle);
            ctx.translate(-cx, -headCy);

            // ---- HAIR ----
            // Hair base — dark brown
            ctx.beginPath();
            ctx.ellipse(cx, headCy - 8, 16, 14, 0, Math.PI, 0);
            ctx.fillStyle = '#2c1810';
            ctx.fill();

            // Hair sides
            ctx.beginPath();
            ctx.ellipse(cx - 12, headCy - 2, 5, 10, -0.3, Math.PI * 0.8, Math.PI * 1.8);
            ctx.fillStyle = '#2c1810';
            ctx.fill();
            ctx.beginPath();
            ctx.ellipse(cx + 12, headCy - 2, 5, 10, 0.3, Math.PI * 1.2, Math.PI * 0.2);
            ctx.fillStyle = '#2c1810';
            ctx.fill();

            // Hair highlight
            ctx.beginPath();
            ctx.ellipse(cx - 3, headCy - 14, 7, 4, -0.3, 0, Math.PI * 2);
            ctx.fillStyle = 'rgba(255,255,255,0.08)';
            ctx.fill();

            // ---- EYEBROWS ----
            const browY = headCy - 6;
            const browRaise = this.state === 'thinking' ? -1.5 : 0;
            const browFurrow = this.state === 'responding' ? 0.5 : 0;

            ctx.strokeStyle = '#3d1f00';
            ctx.lineWidth = 1.5;
            ctx.lineCap = 'round';

            // Left brow
            ctx.beginPath();
            ctx.moveTo(cx - 11, browY + browRaise);
            ctx.quadraticCurveTo(cx - 7, browY - 2 + browRaise - browFurrow, cx - 4, browY + browRaise);
            ctx.stroke();

            // Right brow
            ctx.beginPath();
            ctx.moveTo(cx + 4, browY + browRaise);
            ctx.quadraticCurveTo(cx + 7, browY - 2 + browRaise - browFurrow, cx + 11, browY + browRaise);
            ctx.stroke();

            // ---- EYES ----
            const eyeY = headCy - 1;
            const eyeW = 8, eyeH = 5.5;

            // Eye whites
            ctx.fillStyle = '#fff';
            ctx.beginPath();
            ctx.ellipse(cx - 7, eyeY, eyeW / 2, eyeH / 2 * this.eyeOpenLeft, 0, 0, Math.PI * 2);
            ctx.fill();
            ctx.beginPath();
            ctx.ellipse(cx + 7, eyeY, eyeW / 2, eyeH / 2 * this.eyeOpenRight, 0, 0, Math.PI * 2);
            ctx.fill();

            if (this.eyeOpenLeft > 0.1) {
                // Iris L
                ctx.fillStyle = '#5b3c11';
                ctx.beginPath();
                ctx.ellipse(cx - 7, eyeY, 2.8, 2.8 * this.eyeOpenLeft, 0, 0, Math.PI * 2);
                ctx.fill();
                // Pupil L
                ctx.fillStyle = '#111';
                ctx.beginPath();
                ctx.ellipse(cx - 7, eyeY, 1.6, 1.6 * this.eyeOpenLeft, 0, 0, Math.PI * 2);
                ctx.fill();
                // Highlight L
                ctx.fillStyle = 'rgba(255,255,255,0.75)';
                ctx.beginPath();
                ctx.ellipse(cx - 6, eyeY - 1, 0.9, 0.9, 0, 0, Math.PI * 2);
                ctx.fill();
            }
            if (this.eyeOpenRight > 0.1) {
                // Iris R
                ctx.fillStyle = '#5b3c11';
                ctx.beginPath();
                ctx.ellipse(cx + 7, eyeY, 2.8, 2.8 * this.eyeOpenRight, 0, 0, Math.PI * 2);
                ctx.fill();
                // Pupil R
                ctx.fillStyle = '#111';
                ctx.beginPath();
                ctx.ellipse(cx + 7, eyeY, 1.6, 1.6 * this.eyeOpenRight, 0, 0, Math.PI * 2);
                ctx.fill();
                // Highlight R
                ctx.fillStyle = 'rgba(255,255,255,0.75)';
                ctx.beginPath();
                ctx.ellipse(cx + 8, eyeY - 1, 0.9, 0.9, 0, 0, Math.PI * 2);
                ctx.fill();
            }

            // Eye lashes (top)
            ctx.strokeStyle = '#2c1810';
            ctx.lineWidth = 1;
            [cx - 7, cx + 7].forEach((ex, i) => {
                const side = i === 0 ? -1 : 1;
                ctx.beginPath();
                ctx.arc(ex, eyeY, eyeW / 2, Math.PI, 0);
                ctx.stroke();
            });

            // ---- NOSE ----
            const noseY = headCy + 5;
            ctx.strokeStyle = skinShadow;
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.arc(cx, noseY, 2.5, 0.2, Math.PI - 0.2);
            ctx.stroke();
            ctx.beginPath();
            ctx.arc(cx - 3, noseY + 1, 1.5, 0, Math.PI);
            ctx.stroke();
            ctx.beginPath();
            ctx.arc(cx + 3, noseY + 1, 1.5, 0, Math.PI);
            ctx.stroke();

            // ---- MOUTH ----
            const mouthY = headCy + 11;
            const mo = this.mouthOpen;

            // Lips
            ctx.fillStyle = '#c0765a';
            // Upper lip
            ctx.beginPath();
            ctx.moveTo(cx - 7, mouthY);
            ctx.bezierCurveTo(cx - 4, mouthY - 2, cx - 1, mouthY - 2.5, cx, mouthY - 1.5);
            ctx.bezierCurveTo(cx + 1, mouthY - 2.5, cx + 4, mouthY - 2, cx + 7, mouthY);
            ctx.fill();

            // Mouth opening
            if (mo > 0.05) {
                ctx.fillStyle = '#5a2020';
                ctx.beginPath();
                ctx.ellipse(cx, mouthY + mo * 3, 5.5, mo * 4, 0, 0, Math.PI * 2);
                ctx.fill();

                // Teeth
                ctx.fillStyle = '#f5f0e8';
                ctx.beginPath();
                ctx.ellipse(cx, mouthY + 1, 4.5, mo * 2.5, 0, 0, Math.PI);
                ctx.fill();
            }

            // Lower lip
            ctx.fillStyle = '#b06050';
            ctx.beginPath();
            ctx.moveTo(cx - 7, mouthY + mo * 1);
            ctx.bezierCurveTo(cx - 3, mouthY + 3 + mo * 2, cx + 3, mouthY + 3 + mo * 2, cx + 7, mouthY + mo * 1);
            ctx.fill();

            // Smile corners
            if (this.state !== 'error') {
                ctx.strokeStyle = '#a05040';
                ctx.lineWidth = 0.8;
                ctx.beginPath();
                ctx.arc(cx - 7, mouthY + 1, 2, Math.PI * 0.8, Math.PI * 1.5);
                ctx.stroke();
                ctx.beginPath();
                ctx.arc(cx + 7, mouthY + 1, 2, Math.PI * 1.5, Math.PI * 0.2);
                ctx.stroke();
            }

            ctx.restore(); // end head tilt

            // ---- EARS ----
            const earY = headCy + 1 + bobY;
            [cx - 16, cx + 16].forEach((ex) => {
                ctx.beginPath();
                ctx.ellipse(ex, earY, 3.5, 5, 0, 0, Math.PI * 2);
                ctx.fillStyle = skinColor;
                ctx.fill();
                ctx.beginPath();
                ctx.ellipse(ex, earY, 2, 3, 0, 0, Math.PI * 2);
                ctx.fillStyle = skinShadow;
                ctx.fill();
            });

            // ---- STATE-SPECIFIC EFFECTS ----
            if (this.state === 'thinking') {
                // Thinking dots near head
                for (let i = 0; i < 3; i++) {
                    const phase = this.animTime * 3 - i * 0.6;
                    const y = headCy - 24 - Math.sin(phase) * 3;
                    const size = 2 + i * 1.5;
                    ctx.beginPath();
                    ctx.arc(cx + 20 + i * 7, y, size, 0, Math.PI * 2);
                    ctx.fillStyle = `rgba(255,255,255,${0.3 + i * 0.2})`;
                    ctx.fill();
                }
            }

            if (this.state === 'greeting') {
                // Sparkle around character
                for (let i = 0; i < 4; i++) {
                    const angle = this.animTime * 2 + i * Math.PI / 2;
                    const r = 24 + Math.sin(this.animTime * 3 + i) * 4;
                    const sx = cx + Math.cos(angle) * r;
                    const sy = headCy + Math.sin(angle) * r;
                    const alpha = 0.5 + 0.5 * Math.sin(this.animTime * 4 + i);
                    ctx.beginPath();
                    ctx.arc(sx, sy, 1.5, 0, Math.PI * 2);
                    ctx.fillStyle = `rgba(243,156,18,${alpha})`;
                    ctx.fill();
                }
            }

            ctx.restore(); // end scale
        }

        resize() {
            const W = this.canvas.width  = this.canvas.offsetWidth  * Math.min(window.devicePixelRatio, 2);
            const H = this.canvas.height = this.canvas.offsetHeight * Math.min(window.devicePixelRatio, 2);
            this.W = W; this.H = H;
        }
    }

    // Simple lerp helper
    function lerp(a, b, t) { return a + (b - a) * Math.min(t, 1); }

    // Simple lerp helper
    function lerp(a, b, t) { return a + (b - a) * Math.min(t, 1); }

    /* ============================================================
       FORM-FOCUSED CHAT ENGINE (PURE LOCAL / NO EXTERNAL APIS)
    ============================================================ */
    class ARIAChatEngine {
        constructor() {
            // Default language is unselected until user chooses, or synced from portal
            const portalLang = (window.govPortal && window.govPortal.currentLang === 'hi') ? 'hi' : null;
            this.lang = portalLang || null; // null triggers language choice prompt
        }

        getGreeting() {
            return {
                response: FORM_KNOWLEDGE.en.greeting,
                chips: ["हिंदी (Hindi)", "English", "फॉर्म कैसे भरें?", "Which form to fill?"]
            };
        }

        setLanguage(langCode) {
            this.lang = langCode === 'hi' ? 'hi' : 'en';
            if (this.lang === 'hi') {
                return {
                    response: "बहुत बढ़िया! मैं अब आपसे **हिंदी** में बात करूँगी। 😊\n\nमैं E-Sanjeevni के सभी फॉर्म भरने में आपकी पूरी सहायता कर सकती हूँ। आप पूछ सकते हैं:\n• कौन सा फॉर्म भरना है?\n• एम्बुलेंस रजिस्ट्रेशन फॉर्म कैसे भरें?\n• क्लिनिकल असेसमेंट फॉर्म कैसे भरें?\n• अनिवार्य फ़ील्ड्स कौन सी हैं?\n• GPS लोकेशन कैसे डालें?",
                    suggestions: ["कौन सा फॉर्म भरें?", "रजिस्ट्रेशन फॉर्म कैसे भरें?", "असेसमेंट फॉर्म कैसे भरें?", "अनिवार्य फ़ील्ड्स कौन सी हैं?"]
                };
            } else {
                return {
                    response: "Great! We will continue in **English**. 😊\n\nI can guide you through every form on the E-Sanjeevni portal:\n• Which form should I fill?\n• How to fill the Ambulance Registration Form?\n• How to fill the Clinical Triage Assessment Form?\n• What fields are mandatory?\n• How does the GPS location button work?",
                    suggestions: ["Which form to fill?", "How to fill Registration Form?", "How to fill Assessment Form?", "What fields are mandatory?"]
                };
            }
        }

        async processQuery(text) {
            const raw = text.trim();
            const lower = raw.toLowerCase();
            if (!lower) return null;

            // 1. Language Selection Detection
            if (lower === 'hindi' || lower.includes('हिंदी') || lower.includes('hindi me') || lower.includes('hindi mein')) {
                return this.setLanguage('hi');
            }
            if (lower === 'english' || lower.includes('इंग्लिश') || lower.includes('in english') || lower.includes('continue in english')) {
                return this.setLanguage('en');
            }

            // Detect language intent from text if not explicitly set
            if (!this.lang) {
                const hasDevanagari = /[\u0900-\u097F]/.test(raw);
                const hasHinglish = lower.includes('kaise') || lower.includes('kya') || lower.includes('kare') || lower.includes('konsa') || lower.includes('batao') || lower.includes('bhare') || lower.includes('madad');
                this.lang = (hasDevanagari || hasHinglish) ? 'hi' : 'en';
            }

            const kb = FORM_KNOWLEDGE[this.lang] || FORM_KNOWLEDGE.hi;

            // 2. Emergency Fast Path
            const isEmergency = ['heart attack', 'chest pain', 'breathing', 'stroke', 'accident', 'unconscious', 'dying', '102', '108', '112', 'आपातकाल', 'बेहोश', 'दुर्घटना', 'सांस'].some(k => lower.includes(k));
            if (isEmergency && (lower.includes('emergency') || lower.includes('urgent') || lower.includes('turant') || lower.includes('call') || lower.includes('madad') || lower.includes('helpline'))) {
                return {
                    response: this.lang === 'hi' 
                        ? "🚨 **आपातकालीन सूचना!** यदि मरीज की हालत बहुत गंभीर है, तो बिना देरी किए सीधे **112** या **102** पर कॉल करें!\n\nयदि आप ऑनलाइन एम्बुलेंस बुक करना चाहते हैं, तो कृपया **रजिस्ट्रेशन फॉर्म** भरें।"
                        : "🚨 **Emergency Alert!** If this is a critical medical emergency, immediately dial **112** or **102**!\n\nTo request an ambulance online, please fill the **Registration Form**.",
                    followUp: kb.helpline.body,
                    suggestions: this.lang === 'hi' ? ["रजिस्ट्रेशन फॉर्म कैसे भरें?", "कॉल 102", "कॉल 108", "GPS कैसे डालें?"] : ["How to fill Registration Form?", "Call 102", "Call 108", "GPS Location Help"],
                    isEmergency: true
                };
            }

            // 3. WHICH FORM TO FILL? (konsa form / which form / form types)
            if (lower.includes('konsa form') || lower.includes('kaun sa form') || lower.includes('which form') || lower.includes('what form') || lower.includes('kitne form') || lower.includes('types of form') || lower.includes('form list') || (lower.includes('form') && (lower.includes('choose') || lower.includes('batao')))) {
                return {
                    response: kb.whichForm.title,
                    followUp: kb.whichForm.body,
                    suggestions: kb.whichForm.chips
                };
            }

            // 4. REGISTRATION FORM GUIDE (kaise bhare / registration form / patient form)
            if (lower.includes('registration') || lower.includes('panjikaran') || (lower.includes('form') && (lower.includes('kaise') || lower.includes('fill') || lower.includes('guide') || lower.includes('bhar') || lower.includes('step') || lower.includes('help'))) || lower.includes('ambulance book') || lower.includes('ambulance request')) {
                // If query specifically asks about assessment
                if (!lower.includes('assessment') && !lower.includes('triage') && !lower.includes('laksan') && !lower.includes('symptom')) {
                    return {
                        response: kb.registrationGuide.title,
                        followUp: kb.registrationGuide.body,
                        suggestions: kb.registrationGuide.chips
                    };
                }
            }

            // 5. ASSESSMENT / TRIAGE FORM GUIDE
            if (lower.includes('assessment') || lower.includes('triage') || lower.includes('clincial') || lower.includes('complaint') || lower.includes('symptom') || lower.includes('lakshan') || lower.includes('tier') || lower.includes('gambhirta') || lower.includes('als') || lower.includes('bls')) {
                return {
                    response: kb.assessmentGuide.title,
                    followUp: kb.assessmentGuide.body,
                    suggestions: kb.assessmentGuide.chips
                };
            }

            // 6. MANDATORY FIELDS (anivarya / compulsory / required / star / asterisk)
            if (lower.includes('mandatory') || lower.includes('anivarya') || lower.includes('zaruri') || lower.includes('zaroori') || lower.includes('required') || lower.includes('compulsory') || lower.includes('star') || lower.includes('tara') || lower.includes('kya bharna zaruri')) {
                return {
                    response: kb.mandatoryFields.title,
                    followUp: kb.mandatoryFields.body,
                    suggestions: kb.mandatoryFields.chips
                };
            }

            // 7. GPS & LOCATION AUTO-DETECT
            if (lower.includes('gps') || lower.includes('location') || lower.includes('address') || lower.includes('pata') || lower.includes('geotag') || lower.includes('current location') || lower.includes('sthan')) {
                return {
                    response: kb.gpsHelp.title,
                    followUp: kb.gpsHelp.body,
                    suggestions: kb.gpsHelp.chips
                };
            }

            // 8. LANDMARK HELP
            if (lower.includes('landmark') || lower.includes('land mark') || lower.includes('pechan') || lower.includes('reference point')) {
                return {
                    response: kb.landmarkHelp.title,
                    followUp: kb.landmarkHelp.body,
                    suggestions: kb.landmarkHelp.chips
                };
            }

            // 9. AVPU CONSCIOUSNESS SCALE
            if (lower.includes('avpu') || lower.includes('hosh') || lower.includes('consciousness') || lower.includes('alert') || lower.includes('unresponsive') || lower.includes('behos')) {
                return {
                    response: kb.avpuHelp.title,
                    followUp: kb.avpuHelp.body,
                    suggestions: kb.avpuHelp.chips
                };
            }

            // 10. REFERENCE NUMBER / ACKNOWLEDGMENT (nas / tracking / receipt)
            if (lower.includes('reference') || lower.includes('nas') || lower.includes('tracking') || lower.includes('receipt') || lower.includes('number') || lower.includes('pawati')) {
                return {
                    response: kb.referenceHelp.title,
                    followUp: kb.referenceHelp.body,
                    suggestions: kb.referenceHelp.chips
                };
            }

            // 11. RESET / CLEAR FORM
            if (lower.includes('reset') || lower.includes('clear') || lower.includes('hatao') || lower.includes('khali') || lower.includes('cancel')) {
                return {
                    response: kb.resetHelp.title,
                    followUp: kb.resetHelp.body,
                    suggestions: kb.resetHelp.chips
                };
            }

            // 12. SUBMISSION ERRORS / TROUBLESHOOTING
            if (lower.includes('error') || lower.includes('submit nahi') || lower.includes('problem') || lower.includes('galti') || lower.includes('cannot submit') || lower.includes('not working') || lower.includes('submitting')) {
                return {
                    response: kb.formErrors.title,
                    followUp: kb.formErrors.body,
                    suggestions: kb.formErrors.chips
                };
            }

            // 13. HELPLINES
            if (lower.includes('helpline') || lower.includes('number') || lower.includes('phone') || lower.includes('call') || lower.includes('toll free')) {
                return {
                    response: kb.helpline.title,
                    followUp: kb.helpline.body,
                    suggestions: kb.helpline.chips
                };
            }

            // 14. GREETINGS (namaste, hi, hello)
            if (lower === 'hi' || lower === 'hello' || lower === 'namaste' || lower === 'hey' || lower.includes('namaskar')) {
                return {
                    response: this.lang === 'hi'
                        ? "नमस्ते! 🙏 मैं ARIA हूँ। मैं E-Sanjeevni पोर्टल पर किसी भी फॉर्म को भरने में आपकी सहायता के लिए तैयार हूँ।\n\nआप कौन सा फॉर्म भरना चाहते हैं या किस फ़ील्ड में समस्या आ रही है?"
                        : "Namaste! 🙏 I am ARIA. I am here to help you navigate and fill any form on the E-Sanjeevni portal.\n\nWhich form are you filling or what question do you have?",
                    suggestions: this.lang === 'hi'
                        ? ["कौन सा फॉर्म भरें?", "रजिस्ट्रेशन फॉर्म कैसे भरें?", "असेसमेंट फॉर्म कैसे भरें?", "अनिवार्य फ़ील्ड्स"]
                        : ["Which form to fill?", "How to fill Registration Form?", "How to fill Assessment Form?", "Mandatory Fields"]
                };
            }

            // 15. DEFAULT / COMPREHENSIVE FORM GUIDE FALLBACK
            return {
                response: this.lang === 'hi'
                    ? "मैं आपकी फॉर्म भरने में मदद करने वाली ARIA सहायक हूँ। आप मुझसे पोर्टल के फॉर्म्स के बारे में कोई भी प्रश्न पूछ सकते हैं:"
                    : "I am ARIA, your specialized form guidance assistant. You can ask me any question about filling out portal forms:",
                followUp: kb.whichForm.body,
                suggestions: this.lang === 'hi'
                    ? ["रजिस्ट्रेशन फॉर्म कैसे भरें?", "असेसमेंट फॉर्म कैसे भरें?", "अनिवार्य फ़ील्ड्स (*)", "GPS लोकेशन कैसे डालें?"]
                    : ["How to fill Registration Form?", "How to fill Assessment Form?", "What fields are mandatory?", "How to use GPS?"]
            };
        }

        formatTime() {
            const now = new Date();
            return now.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
        }
    }

    /* ============================================================
       UI BUILDER
    ============================================================ */
    class ARIAUI {
        constructor() {
            this.isOpen = false;
            this.engine = new ARIAChatEngine();
            this.mainChar = null;
            this.launcherChar = null;
            this.msgCount = 0;
            this.injectStyles();
            this.buildDOM();
            this.attachEvents();
            this.initCharsRenderers();
            setTimeout(() => this.showGreeting(), 600);
        }

        injectStyles() {
            if (!document.getElementById('aria-css-link')) {
                const link = document.createElement('link');
                link.id = 'aria-css-link';
                link.rel = 'stylesheet';
                link.href = 'assistant.css';
                document.head.appendChild(link);
            }
        }

        buildDOM() {
            /* ---- Launcher ---- */
            const launcher = document.createElement('div');
            launcher.id = 'aria-launcher';
            launcher.setAttribute('role', 'button');
            launcher.setAttribute('aria-label', 'Open ARIA Form Assistant');
            launcher.setAttribute('tabindex', '0');
            launcher.innerHTML = `
                <div id="aria-launcher-avatar">
                    <canvas id="aria-launcher-canvas" width="76" height="76"></canvas>
                </div>
                <div id="aria-launcher-label">ARIA • Form Assistant</div>
            `;
            document.body.appendChild(launcher);

            /* ---- Main Window ---- */
            const win = document.createElement('div');
            win.id = 'aria-window';
            win.setAttribute('role', 'dialog');
            win.setAttribute('aria-label', 'ARIA Form Assistant Chat');
            win.innerHTML = `
                <!-- Header -->
                <div id="aria-header">
                    <div id="aria-controls">
                        <button id="aria-btn-min" class="aria-ctrl-btn" title="Minimise" aria-label="Minimise chat">
                            <i class="fa-solid fa-minus"></i>
                        </button>
                        <button id="aria-btn-close" class="aria-ctrl-btn" title="Close" aria-label="Close chat">
                            <i class="fa-solid fa-xmark"></i>
                        </button>
                    </div>
                    <div id="aria-header-inner">
                        <div id="aria-character-stage">
                            <canvas id="aria-3d-canvas" width="110" height="160"></canvas>
                            <div id="aria-state-label">Ready</div>
                            <div id="aria-thinking-indicator">
                                <div class="aria-think-dot"></div>
                                <div class="aria-think-dot"></div>
                                <div class="aria-think-dot"></div>
                            </div>
                        </div>
                        <div id="aria-header-info">
                            <div id="aria-name">ARIA</div>
                            <div id="aria-designation">Form Assistant (फॉर्म सहायक)</div>
                            <div id="aria-status-row">
                                <div id="aria-status-dot"></div>
                                <span id="aria-status-text">Online • Form Guidance</span>
                            </div>
                            <div style="margin-top:8px; font-family:'Inter',sans-serif; font-size:9px; color:rgba(255,255,255,0.6); text-transform:uppercase; letter-spacing:0.08em;">
                                E-Sanjeevni Portal Guide
                            </div>
                        </div>
                    </div>
                    <div id="aria-quick-chips">
                        <div class="aria-chip" data-query="रजिस्ट्रेशन फॉर्म कैसे भरें?">📋 Registration Form</div>
                        <div class="aria-chip" data-query="असेसमेंट फॉर्म कैसे भरें?">🩺 Assessment Form</div>
                        <div class="aria-chip" data-query="अनिवार्य फ़ील्ड्स कौन सी हैं?">⭐ Mandatory Fields</div>
                        <div class="aria-chip" data-query="GPS लोकेशन कैसे डालें?">📍 GPS Help</div>
                    </div>
                </div>

                <!-- Messages -->
                <div id="aria-messages" role="log" aria-live="polite" aria-label="Conversation">
                    <!-- Typing indicator -->
                    <div id="aria-typing">
                        <div class="aria-msg-avatar-sm"><i class="fa-solid fa-robot" style="font-size:11px"></i></div>
                        <div class="aria-typing-bubble">
                            <div class="aria-dot"></div>
                            <div class="aria-dot"></div>
                            <div class="aria-dot"></div>
                        </div>
                    </div>
                </div>

                <!-- Input -->
                <div id="aria-input-area">
                    <input type="text" id="aria-input"
                           placeholder="Ask: 'Form kaise bhare?', 'Konsa form?', 'GPS help'..."
                           maxlength="300"
                           autocomplete="off"
                           aria-label="Type your question about forms">
                    <button id="aria-send-btn" title="Send" aria-label="Send message">
                        <i class="fa-solid fa-paper-plane"></i>
                    </button>
                </div>
                <div id="aria-footer-note">
                    E-Sanjeevni • Form Assistant &nbsp;|&nbsp; Emergency Helplines: 102 / 108 / 112
                </div>
            `;
            document.body.appendChild(win);

            this.launcher  = document.getElementById('aria-launcher');
            this.window    = document.getElementById('aria-window');
            this.messages  = document.getElementById('aria-messages');
            this.input     = document.getElementById('aria-input');
            this.sendBtn   = document.getElementById('aria-send-btn');
            this.typing    = document.getElementById('aria-typing');
            this.stateLabel= document.getElementById('aria-state-label');
            this.thinkIndicator = document.getElementById('aria-thinking-indicator');
        }

        attachEvents() {
            // Launcher open
            this.launcher.addEventListener('click', () => this.open());
            this.launcher.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') this.open(); });

            // Close / Minimise
            document.getElementById('aria-btn-close').addEventListener('click', (e) => { e.stopPropagation(); this.close(); });
            document.getElementById('aria-btn-min').addEventListener('click', (e) => { e.stopPropagation(); this.close(); });

            // Send
            this.sendBtn.addEventListener('click', () => this.handleSend());
            this.input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); this.handleSend(); }
            });

            // Quick chips in header
            document.getElementById('aria-quick-chips').querySelectorAll('.aria-chip').forEach(chip => {
                chip.addEventListener('click', () => this.handleQuery(chip.dataset.query));
            });

            // Escape key
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape' && this.isOpen) this.close();
            });
        }

        initCharsRenderers() {
            const mainCanvas = document.getElementById('aria-3d-canvas');
            if (mainCanvas) {
                this.mainChar = new ARIACharacter3D(mainCanvas, { isSmall: false });
                this.mainChar.setState('greeting');
                setTimeout(() => { if (this.mainChar) this.mainChar.setState('idle'); }, 2500);
            }

            const launcherCanvas = document.getElementById('aria-launcher-canvas');
            if (launcherCanvas) {
                this.launcherChar = new ARIACharacter3D(launcherCanvas, { isSmall: true });
                this.launcherChar.setState('idle');
            }
        }

        setCharacterState(state) {
            if (this.mainChar) this.mainChar.setState(state);
            const labels = {
                idle: 'Ready',
                greeting: 'Namaste 🙏',
                thinking: 'Thinking...',
                responding: 'Guide Active',
                error: 'Error'
            };
            if (this.stateLabel) this.stateLabel.textContent = labels[state] || '';

            if (this.thinkIndicator) {
                this.thinkIndicator.classList.toggle('visible', state === 'thinking');
            }
        }

        open() {
            if (this.isOpen) return;
            this.isOpen = true;
            this.window.classList.add('aria-open');
            this.launcher.classList.add('aria-hidden-state');
            this.input.focus();
            this.scrollBottom();

            this.setCharacterState('greeting');
            setTimeout(() => this.setCharacterState('idle'), 2000);
        }

        close() {
            if (!this.isOpen) return;
            this.isOpen = false;
            this.window.classList.remove('aria-open');
            this.launcher.classList.remove('aria-hidden-state');
        }

        scrollBottom() {
            setTimeout(() => {
                this.messages.scrollTop = this.messages.scrollHeight;
            }, 40);
        }

        showGreeting() {
            // First greeting asks: Namaste! Do you want to continue in Hindi or English?
            const greetingObj = this.engine.getGreeting();
            this.addMessage('aria', greetingObj.response);

            setTimeout(() => {
                this.addSuggestions(greetingObj.chips);
            }, 300);
        }

        addMessage(from, text, options = {}) {
            const msgId = `aria-msg-${++this.msgCount}`;
            const time = this.engine.formatTime();

            const div = document.createElement('div');
            div.className = `aria-msg from-${from}`;
            div.id = msgId;

            if (from === 'aria') {
                div.innerHTML = `
                    <div class="aria-msg-avatar-sm" aria-hidden="true">
                        <i class="fa-solid fa-robot" style="font-size:11px"></i>
                    </div>
                    <div>
                        ${options.isEmergency ? `
                        <div class="aria-emergency-alert" style="margin-bottom:6px">
                            <i class="fa-solid fa-triangle-exclamation"></i>
                            आपातकालीन स्थिति में तुरंत 112 या 102 डायल करें।
                        </div>` : ''}
                        <div class="aria-bubble">${this.formatText(text)}</div>
                        <div class="aria-msg-time">${time}</div>
                    </div>
                `;
            } else {
                div.innerHTML = `
                    <div>
                        <div class="aria-bubble">${escapeHtml(text)}</div>
                        <div class="aria-msg-time">${time}</div>
                    </div>
                `;
            }

            this.messages.insertBefore(div, this.typing);
            this.scrollBottom();
            return msgId;
        }

        addFollowUp(text) {
            const div = document.createElement('div');
            div.className = 'aria-msg from-aria';
            div.innerHTML = `
                <div class="aria-msg-avatar-sm" aria-hidden="true" style="visibility:hidden"></div>
                <div>
                    <div class="aria-bubble" style="margin-top:-4px">${this.formatText(text)}</div>
                </div>
            `;
            this.messages.insertBefore(div, this.typing);
            this.scrollBottom();
        }

        addSuggestions(chips) {
            if (!chips || chips.length === 0) return;
            const div = document.createElement('div');
            div.className = 'aria-msg from-aria';
            const inner = document.createElement('div');
            inner.style.marginLeft = '36px';

            const row = document.createElement('div');
            row.className = 'aria-suggestion-row';

            chips.forEach(label => {
                const chip = document.createElement('div');
                chip.className = 'aria-suggestion-chip';
                chip.textContent = label;
                chip.addEventListener('click', () => this.handleQuery(label));
                row.appendChild(chip);
            });

            inner.appendChild(row);
            div.appendChild(inner);
            this.messages.insertBefore(div, this.typing);
            this.scrollBottom();
        }

        showTyping() {
            this.typing.classList.add('visible');
            this.messages.appendChild(this.typing);
            this.scrollBottom();
        }

        hideTyping() {
            this.typing.classList.remove('visible');
        }

        handleSend() {
            const text = this.input.value.trim();
            if (!text) return;
            this.input.value = '';
            this.handleQuery(text);
        }

        async handleQuery(text) {
            if (!text || !text.trim()) return;

            // Add user message immediately
            this.addMessage('user', text);

            this.sendBtn.disabled = true;
            this.input.disabled = true;
            this.setCharacterState('thinking');
            this.showTyping();

            // Simulate fast natural typing (pure client-side)
            await sleep(150);

            const result = await this.engine.processQuery(text);
            this.hideTyping();
            this.setCharacterState('responding');

            if (result) {
                this.addMessage('aria', result.response, { isEmergency: result.isEmergency });
                if (result.followUp) {
                    this.addFollowUp(result.followUp);
                }
                if (result.suggestions && result.suggestions.length > 0) {
                    this.addSuggestions(result.suggestions);
                }
            }

            // Quick navigation helpers if user requests form opening
            const lower = text.toLowerCase();
            if (lower.includes('रजिस्ट्रेशन फॉर्म खोलें') || lower.includes('open registration form') || lower.includes('registration form kholo')) {
                if (!window.location.pathname.includes('register.html')) {
                    setTimeout(() => { window.location.href = 'register.html'; }, 1000);
                }
            } else if (lower.includes('असेसमेंट फॉर्म खोलें') || lower.includes('open assessment form') || lower.includes('assessment form kholo')) {
                if (!window.location.pathname.includes('assessment.html')) {
                    setTimeout(() => { window.location.href = 'assessment.html'; }, 1000);
                }
            } else if (lower.includes('कॉल 102') || lower.includes('call 102')) {
                window.open('tel:102');
            } else if (lower.includes('कॉल 108') || lower.includes('call 108')) {
                window.open('tel:108');
            }

            await sleep(1200);
            this.setCharacterState('idle');
            this.sendBtn.disabled = false;
            this.input.disabled = false;
            this.input.focus();
        }

        formatText(text) {
            if (!text) return '';
            return escapeHtml(text)
                .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
                .replace(/\n/g, '<br>')
                .replace(/• /g, '&#8226; ');
        }
    }

    /* ============================================================
       UTILITY FUNCTIONS
    ============================================================ */
    function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = String(text);
        return div.innerHTML;
    }

    /* ============================================================
       ENTRY POINT
    ============================================================ */
    function initARIA() {
        if (window.__ariaInitialized) return;
        window.__ariaInitialized = true;
        window.__ARIA = new ARIAUI();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initARIA);
    } else {
        initARIA();
    }

})();
