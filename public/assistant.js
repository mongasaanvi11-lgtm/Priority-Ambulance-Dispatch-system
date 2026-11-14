/**
 * AmbuPriority — ARIA (Ambulance Response Intelligent Assistant)
 * 3D AI Virtual Assistant powered by Three.js
 * 
 * Architecture:
 *  - Three.js WebGL scene with procedurally animated 3D character
 *  - State machine: idle → greeting → thinking → responding → error
 *  - Domain-specific AmbuPriority knowledge base
 *  - Bilingual support (EN/HI) synced with govPortal language state
 *  - Fully self-contained, no server required
 */

(function () {
    'use strict';

    /* ============================================================
       CONFIGURATION
    ============================================================ */
    const ARIA_CONFIG = {
        name: 'ARIA',
        fullName: 'Ambulance Response Intelligent Assistant',
        version: '2.0',
        typingDelay: { min: 50, max: 150 },   // Instant real-time response
        characterThinkTime: 100,
        apiBase: '',        // Backend API base URL
    };

    /* ============================================================
       KNOWLEDGE BASE — AmbuPriority Domain
    ============================================================ */
    const KB = {
        en: {
            greetings: [
                "Namaste! I'm ARIA, your AmbuPriority assistant. I can help you request an ambulance, understand our emergency services, or navigate the portal. How can I assist you today?",
                "Welcome to AmbuPriority! I'm ARIA. Whether you need an ambulance, information about our dispatch system, or portal guidance — I'm here to help. What can I do for you?"
            ],
            intents: [
                {
                    // HINDI FORM HELP
                    phrases: ['form kaise bhare', 'form bharne me madad', 'form bharna', 'form kaise bharna hai', 'form samjh nahi aa raha', 'form me kya bhare', 'kaise bhare'],
                    patterns: ['form', 'मदद', 'सहायता', 'भरें', 'फॉर्म'],
                    response: "एम्बुलेंस पंजीकरण फ़ॉर्म (Registration Form) भरने की चरणबद्ध गाइड:",
                    followUp: "1. **मरीज का नाम:** मरीज का पूरा कानूनी नाम दर्ज करें।\n2. **उम्र व लिंग:** उम्र (वर्षों में) दर्ज करें और Male/Female/Other चुनें।\n3. **मोबाइल नंबर:** 10 अंकों का सक्रिय मोबाइल नंबर दर्ज करें ताकि पैरामेडिक सीधे संपर्क कर सकें।\n4. **पिकअप का पता:** पता टाइप करें या **\"Use My Current Location\"** बटन दबाएं (जीपीएस से पता अपने आप भर जाएगा)।\n5. **लैंडमार्क (ऐच्छिक):** कोई नजदीकी प्रसिद्ध जगह लिखें (जैसे: मेट्रो पिलर 142 के पास, सिटी मॉल के सामने)।\n6. **आवेदक का नाम व संबंध:** अपना नाम लिखें और मरीज से संबंध (स्वयं, माता/पिता, भाई आदि) चुनें।\n\nसब भरने के बाद नीचे **\"Request Ambulance\"** बटन दबाएं!",
                    suggestions: ['अनिवार्य फ़ील्ड कौन सी हैं?', 'जीपीएस का उपयोग कैसे करें?', 'लैंडमार्क क्या लिखें?'],
                    priority: 11
                },
                {
                    // HINDI MANDATORY FIELDS
                    phrases: ['anivarya field', 'zaruri field', 'kya bharna zaruri hai', 'konsi field zaruri hai'],
                    patterns: ['जरूरी', 'अनिवार्य'],
                    response: "फॉर्म में लाल तारे (*) वाली ये फ़ील्ड भरना अनिवार्य है:",
                    followUp: "• **मरीज का नाम**\n• **उम्र**\n• **लिंग (Gender)**\n• **मोबाइल नंबर**\n• **पिकअप का पूरा पता**\n• **अनुरोधकर्ता का नाम व मरीज से संबंध**\n\n(वैकल्पिक: वैकल्पिक मोबाइल नंबर और लैंडमार्क)",
                    suggestions: ['फॉर्म कैसे भरें?', 'जीपीएस का उपयोग कैसे करें?'],
                    priority: 11
                },
                {
                    // HINDI GPS HELP
                    phrases: ['gps kaise use kare', 'location kaise daale', 'location nahi aa rahi', 'gps kaam nahi kar raha'],
                    patterns: ['लोकेशन', 'जीपीएस'],
                    response: "अपने वर्तमान स्थान (GPS) का उपयोग करने का तरीका:",
                    followUp: "1. फॉर्म में **\"Use My Current Location\"** बटन पर क्लिक करें।\n2. आपका ब्राउज़र लोकेशन परमिशन मांगेगा — **\"Allow\"** या **\"अनुमति दें\"** पर क्लिक करें।\n3. सिस्टम उपग्रह जीपीएस से सटीक अक्षांश-देशांतर लॉक करके आपका पता अपने आप फ़ील्ड में भर देगा।\n\n**टिप:** यदि आप कमरे के अंदर हैं तो बालकनी या खिड़की के पास से जीपीएस बेहतर काम करता है।",
                    suggestions: ['फॉर्म कैसे भरें?', 'लैंडमार्क क्या लिखें?'],
                    priority: 11
                },
                {
                    // HINDI LANDMARK HELP
                    phrases: ['landmark kya likhe', 'landmark me kya aayega', 'landmark ka matlab'],
                    patterns: ['लैंडमार्क'],
                    response: "लैंडमार्क (Landmark) का मतलब है आपके घर के पास की प्रसिद्ध पहचान:",
                    followUp: "जैसे:\n• \"मेट्रो पिलर नंबर 142 के सामने\"\n• \"एसबीआई बैंक के पास, मेन रोड\"\n• \"हनुमान मंदिर के पीछे\"\n• \"रिलायंस फ्रेश के बगल में\"\n\nइससे एम्बुलेंस ड्राइवर को बिना समय गंवाए आप तक पहुंचने में बहुत आसानी होती है।",
                    suggestions: ['फॉर्म कैसे भरें?'],
                    priority: 11
                },
                {
                    // GENERAL HELP — catches generic "help", "assist" etc. before ambulance
                    phrases: ['help me', 'what can you do', 'how to use', 'i need help', 'please help', 'help please', 'how does this work'],
                    patterns: ['help', 'assist', 'guide', 'options', 'menu'],
                    response: "I can help you with the following:",
                    followUp: "1. 🚑 **Ambulance Request** — How to call or register for an ambulance\n2. 📋 **Form Filling Guide** — Step-by-step help filling the registration form\n3. 📍 **GPS Location** — Auto-detect your address using GPS\n4. 📞 **Emergency Helplines** — Dial 102 / 108 / 112 (toll-free)\n5. ℹ️ **About AmbuPriority** — System features and documentation\n\nJust ask about any of these topics!",
                    suggestions: ['Form Filling Help', 'Request Ambulance', 'Emergency Numbers', 'GPS Location Help'],
                    priority: 0 // lowest — only wins if nothing more specific matches
                },
                {
                    // FORM FILLING — must win for "help in form filling", "how to fill", etc.
                    phrases: ['form filling', 'fill form', 'help fill', 'help in form', 'how to fill', 'form help', 'fill the form', 'filling form', 'help me fill', 'form guide', 'step by step', 'how do i register', 'how to register', 'registration help', 'help with registration', 'what to enter', 'what should i fill', 'guide me'],
                    patterns: ['register', 'registration', 'patient', 'form', 'fill', 'filling', 'step', 'instructions', 'field', 'submit'],
                    response: "Here's how to fill the Patient Registration Form:",
                    followUp: "**Step 1 — Patient Details:**\n• **Full Name** — Enter patient's full name\n• **Age** — Enter age in years\n• **Gender** — Select from dropdown\n\n**Step 2 — Contact Information:**\n• **Mobile Number** — 10-digit number (required)\n• **Alternate Number** — Optional backup contact\n\n**Step 3 — Pickup Address:**\n• Type your address OR click **\"Use My Current Location\"** for GPS\n• **Landmark** — Nearby landmark (optional but helpful)\n\n**Step 4 — Requestor Details:**\n• **Your Name** — Person requesting the ambulance\n• **Relationship** — Your relationship to the patient\n\nClick **Submit Emergency Registration** when done. You'll receive a reference number (NAS-XXXX).",
                    suggestions: ['What Fields are Mandatory?', 'GPS Location Help', 'What is Landmark?'],
                    priority: 10
                },
                {
                    // MANDATORY FIELDS
                    phrases: ['mandatory fields', 'required fields', 'which fields', 'compulsory', 'what is required', 'fields are required'],
                    patterns: ['mandatory', 'required', 'compulsory', 'star', 'asterisk'],
                    response: "The following fields are mandatory (marked with *):",
                    followUp: "• **Patient Name** — Full name of the patient\n• **Age** — Age in years\n• **Gender** — Select Male / Female / Other\n• **Mobile Number** — 10-digit contact number\n• **Complete Address** — Pickup location\n• **Requesting Person** — Who is making the request\n• **Relationship** — Relation to patient\n\nOptional fields: Alternate Mobile, Landmark",
                    suggestions: ['Form Filling Help', 'GPS Location Help'],
                    priority: 10
                },
                {
                    // LANDMARK
                    phrases: ['what is landmark', 'landmark field', 'landmark meaning', 'what to write in landmark', 'nearby landmark'],
                    patterns: ['landmark'],
                    response: "The Landmark field helps the ambulance driver find you faster:",
                    followUp: "Enter a well-known nearby reference point, for example:\n• \"Near Metro Pillar 142\"\n• \"Opposite SBI Bank, Main Road\"\n• \"Behind Shiv Mandir\"\n• \"Next to Reliance Mall\"\n\nThis field is **optional** but highly recommended — it helps the driver reach you quickly.",
                    suggestions: ['Form Filling Help'],
                    priority: 10
                },
                {
                    // RELATIONSHIP FIELD
                    phrases: ['what is relationship', 'relationship field', 'relationship dropdown', 'who is requesting'],
                    patterns: ['relationship', 'requestor', 'requesting person', 'who is calling'],
                    response: "The Relationship field identifies who is requesting the ambulance:",
                    followUp: "Select your relationship to the patient:\n• **Self** — You are the patient\n• **Family Member** — Parent, sibling, spouse, child\n• **Friend / Neighbour** — Known to the patient\n• **Bystander** — Witness / passerby helping\n• **Other** — Any other relationship\n\nThis helps the dispatch team verify and coordinate.",
                    suggestions: ['Form Filling Help'],
                    priority: 10
                },
                {
                    // REFERENCE / NAS NUMBER
                    phrases: ['reference number', 'nas number', 'tracking number', 'acknowledgment', 'registration id', 'what is nas'],
                    patterns: ['reference', 'nas', 'tracking', 'acknowledgment', 'ack'],
                    response: "After submitting the form, you receive a Reference Number:",
                    followUp: "Format: **NAS-YEAR-XXXXXX** (e.g., NAS-2026-483921)\n\nThis number can be used to:\n• Track your ambulance request status\n• Communicate with the dispatch centre\n• Reference in follow-up calls to 102/108\n\nPlease save this number — it appears on screen after successful submission.",
                    suggestions: ['Form Filling Help', 'Emergency Numbers'],
                    priority: 10
                },
                {
                    // RESET FORM
                    phrases: ['reset form', 'clear form', 'start over', 'cancel registration', 'cancel form'],
                    patterns: ['reset', 'clear', 'cancel', 'start over'],
                    response: "To reset or clear the registration form:",
                    followUp: "Click the **Reset Form** button at the bottom of the registration page. This will:\n• Clear all entered data\n• Remove the acknowledgment card\n• Scroll back to the top\n\nNote: If you've already submitted, your previous registration is saved. Resetting only clears the current form.",
                    suggestions: ['Form Filling Help'],
                    priority: 5
                },
                {
                    // AMBULANCE REQUEST — requires more specific phrases now
                    phrases: ['call ambulance', 'book ambulance', 'need ambulance', 'request ambulance', 'send ambulance', 'want ambulance', 'ambulance chahiye', 'emergency ambulance', 'urgent ambulance'],
                    patterns: ['ambulance'],
                    response: "To request an ambulance immediately:",
                    followUp: "1. Click **Call for Ambulance** at the top of this page, OR\n2. Dial **102** (National Ambulance) or **108** (State EMS) or **112** (Universal Emergency)\n\nPlease provide the patient's name, address, and contact number. Our GPS dispatch system will assign the nearest unit.",
                    suggestions: ['Register Patient', 'Call 102', 'Call 108'],
                    isEmergency: true,
                    priority: 8
                },
                {
                    // EMERGENCY — only for true emergency keywords
                    phrases: ['i have an emergency', 'someone is dying', 'accident happened', 'medical emergency', 'heart attack', 'bleeding', 'unconscious', 'serious injury'],
                    patterns: ['emergency', 'dying', 'accident', 'attack', 'unconscious', 'bleeding', 'critical', 'serious'],
                    response: "🚨 This sounds like a medical emergency!",
                    followUp: "**CALL IMMEDIATELY:**\n📞 **112** — Universal Emergency Number\n📞 **102** — National Ambulance Service\n📞 **108** — Emergency Medical Services\n\nAll numbers are toll-free, 24×7, from any phone.\n\nWhile waiting:\n• Keep the patient still and calm\n• Do not move them if there's a spinal injury\n• Apply pressure to any bleeding wounds\n• Note the exact location for the dispatcher",
                    suggestions: ['Call 102', 'Call 108'],
                    isEmergency: true,
                    priority: 9
                },
                {
                    phrases: ['gps location', 'use my location', 'current location', 'detect location', 'auto detect address', 'use gps', 'location button', 'how to use gps', 'gps help', 'location help', 'how to use location'],
                    patterns: ['gps', 'location', 'detect', 'current location', 'where am i', 'address'],
                    response: "Our smart location system can automatically detect your address:",
                    followUp: "On the registration form, click **\"Use My Current Location\"**. Your browser will request GPS permission — allow it, and your address will be filled automatically.\n\nThis uses the browser's built-in GPS sensor. No special app is required.\n\n**Tip:** For best accuracy, use the GPS feature outdoors or near a window.",
                    suggestions: ['Open Registration Form'],
                    priority: 5
                },
                {
                    phrases: ['emergency numbers', 'helpline numbers', 'phone numbers', 'which number to call', 'ambulance number'],
                    patterns: ['helpline', 'number', 'phone', 'hotline', '102', '108', '112'],
                    response: "National Emergency Helplines (Toll-Free, 24×7):",
                    followUp: "📞 **102** — National Ambulance Service (NAS)\n📞 **108** — Emergency Medical Services (EMS)\n📞 **112** — Universal Emergency (Police/Fire/Medical)\n\nAll numbers are free from any phone, any network, anytime.",
                    suggestions: ['Request Ambulance Online', 'Registration Form'],
                    priority: 5
                },
                {
                    phrases: ['how long', 'arrival time', 'response time', 'how fast', 'how many minutes', 'when will ambulance come'],
                    patterns: ['time', 'arrival', 'long', 'wait', 'eta', 'fast', 'quick', 'minutes'],
                    response: "AmbuPriority's average response time:",
                    followUp: "⏱ **Average: 6.8 minutes** in covered metropolitan areas\n\nOur system uses:\n• Real-time GPS routing to the nearest idle unit\n• Traffic signal preemption (green corridors)\n• Pre-alert to destination hospital ICU\n\nResponse times vary based on location and traffic conditions.",
                    suggestions: ['How it Works', 'Request Ambulance'],
                    priority: 5
                },
                {
                    phrases: ['hospital integration', 'which hospitals', 'hospital list', 'icu bed'],
                    patterns: ['hospital', 'icu', 'bed', 'trauma', 'facility'],
                    response: "AmbuPriority integrates with 48+ hospitals across India:",
                    followUp: "Our system automatically:\n• Pre-alerts destination trauma centres\n• Transmits patient vitals via FHIR-compliant API\n• Reserves ICU/emergency bay before arrival\n\nThis eliminates critical delays at the emergency entrance.",
                    suggestions: ['View Documentation', 'Request Ambulance'],
                    priority: 5
                },
                {
                    phrases: ['green corridor', 'signal preemption', 'traffic signals', 'smart signal'],
                    patterns: ['signal', 'traffic', 'green', 'corridor', 'preemption'],
                    response: "Smart Signal Preemption — a core AmbuPriority feature:",
                    followUp: "When an ambulance is dispatched, our RF signal system turns traffic signals GREEN on the route — up to 500m ahead of the vehicle.\n\nThis system is operational at **120+ major junctions** across covered cities.",
                    suggestions: ['View Documentation'],
                    priority: 5
                },
                {
                    phrases: ['dark mode', 'light mode', 'switch theme', 'change theme', 'night mode'],
                    patterns: ['dark', 'theme', 'mode', 'color'],
                    response: "To switch between Light and Dark mode:",
                    followUp: "Click the **🌙 Dark Mode** button in the top utility bar (blue bar at the very top of the page). Your preference is saved automatically.",
                    suggestions: [],
                    priority: 3
                },
                {
                    phrases: ['switch to hindi', 'hindi me', 'change language', 'bhasha'],
                    patterns: ['hindi', 'हिंदी', 'language', 'भाषा', 'translate'],
                    response: "AmbuPriority supports Hindi and English:",
                    followUp: "Click the **हिंदी** button in the top utility bar to switch the entire portal to Hindi. Click again to return to English.",
                    suggestions: [],
                    priority: 3
                },
                {
                    phrases: ['ais 125', 'compliance', 'certification', 'standards'],
                    patterns: ['ais', '125', 'standard', 'compliant', 'certification', 'iso'],
                    response: "AmbuPriority complies with multiple national standards:",
                    followUp: "• **AIS-125** — Ambulance construction & equipment\n• **GIGW 3.0** — Government web portal standards\n• **HL7 FHIR R4** — Health data exchange\n• **DPDPA 2023** — Data privacy\n• **ISO 9001:2015** — Quality management\n\nSee the Documentation page for full details.",
                    suggestions: ['View Documentation'],
                    priority: 5
                },
                {
                    phrases: ['is my data safe', 'data security', 'privacy policy', 'personal data'],
                    patterns: ['safe', 'secure', 'privacy', 'data', 'personal'],
                    response: "Your data is protected under India's digital framework:",
                    followUp: "• All data protected under **DPDPA 2023**\n• TLS 1.3 encrypted transmission\n• No login required for emergency registration\n• Data processed on government (NIC) infrastructure\n• Registration data used solely for dispatch",
                    suggestions: [],
                    priority: 5
                },
                {
                    phrases: ['what is ambupriority', 'about this portal', 'about ambupriority', 'what does this do', 'tell me about'],
                    patterns: ['about', 'ambupriority', 'explain', 'system', 'portal'],
                    response: "AmbuPriority is India's National Emergency Ambulance Priority System:",
                    followUp: "It connects three systems in real-time:\n1. **GPS Ambulances** — nearest unit dispatch\n2. **Smart Traffic Signals** — green corridor creation\n3. **Hospital ICU dashboards** — pre-arrival alerts\n\nOperated by the National Health Authority under the Ministry of Health & Family Welfare.",
                    suggestions: ['Request Ambulance', 'View Documentation', 'Emergency Numbers'],
                    priority: 3
                },
                {
                    // GREETINGS
                    phrases: ['hi', 'hello', 'hey', 'namaste', 'good morning', 'good evening', 'good afternoon', 'hii', 'hiii'],
                    patterns: ['hi', 'hello', 'hey', 'namaste'],
                    response: "Namaste! 🙏 Welcome to AmbuPriority.",
                    followUp: "I'm ARIA, your emergency services assistant. I can help you with:\n\n🚑 Request an ambulance\n📋 Guide you through form filling\n📍 Help with GPS location\n📞 Share emergency helplines\n\nWhat would you like help with?",
                    suggestions: ['Request Ambulance', 'Form Filling Help', 'Emergency Numbers', 'GPS Location Help'],
                    priority: 2
                },
                {
                    // THANKS
                    phrases: ['thank you', 'thanks', 'dhanyavaad', 'shukriya', 'thank u'],
                    patterns: ['thank', 'thanks', 'dhanyavaad', 'shukriya'],
                    response: "You're welcome! 🙏",
                    followUp: "I'm always here to help. If you need anything else — ambulance request, form guidance, or emergency helplines — just ask.\n\nStay safe!",
                    suggestions: ['Request Ambulance', 'Emergency Numbers'],
                    priority: 2
                }
            ],
            fallback: [
                "I'm designed to assist with AmbuPriority emergency services. Could you rephrase your question? You can ask about requesting an ambulance, our system features, emergency helplines, or portal navigation.",
                "I didn't quite catch that. I can help with ambulance registration, emergency helplines (102/108/112), our dispatch system, or portal guidance. What would you like to know?"
            ],
            hiName: 'ARIA (एरिया)',
        },
        hi: {
            greetings: [
                "नमस्ते! मैं ARIA हूं, आपकी AmbuPriority सहायक। मैं आपको एम्बुलेंस बुलाने, हमारी सेवाओं के बारे में जानकारी देने या पोर्टल में मदद करने के लिए यहाँ हूं। आज मैं आपकी कैसे सहायता कर सकती हूं?",
            ],
            fallback: [
                "मैं AmbuPriority की आपातकालीन सेवाओं के बारे में सहायता के लिए यहाँ हूं। कृपया एम्बुलेंस अनुरोध, हेल्पलाइन नंबर, या सिस्टम के बारे में पूछें।"
            ]
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

    /* ============================================================
       CHAT ENGINE — Augmented with Hospital Panel & Insurance AI
    ============================================================ */
    class ARIAChatEngine {
        constructor() {
            this.isHindi = false;
            // Conversation Memory for Panel & Insurance
            this.sessionPanel = {
                schemeCode: null,    // 'pmjay', 'cghs', 'echs', 'esic', 'state_govt', 'tpa_insurance'
                schemeName: null,    // 'Ayushman Bharat PM-JAY', 'CGHS', etc.
                insurerOrPlan: null, // 'Star Health', 'HDFC ERGO', etc.
                searchLocation: null // 'Delhi', 'Jaipur', etc.
            };
            // AI conversation history (sent to backend for context)
            this.conversationHistory = [];
        }

        getGreeting() {
            const greets = KB.en.greetings;
            return greets[Math.floor(Math.random() * greets.length)];
        }

        // Helper to query the ARIA AI backend (/api/chat via Gemini Flash)
        async askAI(userMessage) {
            try {
                // Get patient location from page if available
                let lat = null, lon = null, address = '';
                try {
                    if (window.patientLat && window.patientLon) {
                        lat = window.patientLat;
                        lon = window.patientLon;
                    }
                    if (window.patientAddress) address = window.patientAddress;
                } catch (_) {}

                const payload = {
                    message: userMessage,
                    session: this.conversationHistory.slice(-10), // Last 10 turns
                    lat: lat,
                    lon: lon,
                    address: address
                };

                const resp = await fetch(`${ARIA_CONFIG.apiBase}/api/chat`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload),
                    signal: AbortSignal.timeout(18000) // 18 second timeout
                });

                if (!resp.ok) return null;
                const data = await resp.json();

                // If backend encountered an AI error, let frontend fall back to verified local panel logic
                if (data.source === 'error' || data.model === 'all_failed') {
                    return null;
                }

                if (data.reply) {
                    // Update conversation history
                    this.conversationHistory.push({ role: 'user', content: userMessage });
                    this.conversationHistory.push({ role: 'assistant', content: data.reply });
                    // Keep last 20 entries (10 turns)
                    if (this.conversationHistory.length > 20) {
                        this.conversationHistory = this.conversationHistory.slice(-20);
                    }
                    return data.reply;
                }
                return null;
            } catch (err) {
                console.warn('ARIA AI backend unavailable:', err.message);
                return null;
            }
        }

        // Helper to query backend hospital discovery and panel data
        async fetchHospitalsForPanel(locationQuery, panelCode) {
            try {
                // If specific location mentioned, use search endpoint; otherwise nearby
                let url;
                let postBody = null;
                if (locationQuery && locationQuery.trim()) {
                    url = `/api/hospitals/search?q=${encodeURIComponent(locationQuery)}&lat=28.5672&lon=77.2100`;
                    const resp = await fetch(url);
                    if (resp.ok) {
                        const data = await resp.json();
                        return data.hospitals || [];
                    }
                } else {
                    url = '/api/hospitals/nearby';
                    postBody = {
                        request_id: 'ARIA-PANEL-LOOKUP',
                        address: 'AIIMS Delhi',
                        latitude: 28.5672,
                        longitude: 77.2100,
                        radius_km: 15.0
                    };
                    const resp = await fetch(url, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(postBody)
                    });
                    if (resp.ok) {
                        const data = await resp.json();
                        return data.hospitals || [];
                    }
                }
            } catch (e) {
                console.warn('ARIA panel fetch error:', e);
            }
            return [];
        }

        async processPanelQuery(lower, rawText) {
            // Check if user specifically asked in Devanagari Hindi or Hinglish
            const isDevanagari = /[\u0900-\u097F]/.test(rawText);
            const isHinglish = lower.includes('mere paas') || lower.includes('hai') || lower.includes('kya') || lower.includes('kaise') || lower.includes('batao') || lower.includes('kahan');
            const isEn = !isDevanagari && !isHinglish;

            // 1. Detect City / Location in user message
            const cities = ['jaipur', 'mumbai', 'delhi', 'chennai', 'kolkata', 'bengaluru', 'bangalore', 'pune', 'hyderabad', 'lucknow', 'chandigarh', 'ahmedabad', 'gurgaon', 'gurugram', 'noida'];
            for (const c of cities) {
                if (lower.includes(c)) {
                    this.sessionPanel.searchLocation = c.charAt(0).toUpperCase() + c.slice(1);
                    break;
                }
            }

            // 2. Identify Health Scheme / Insurance Provider
            let matchedScheme = null;
            let schemeDisplayName = null;
            let insurerName = null;

            if (lower.includes('ayushman') || lower.includes('pmjay') || lower.includes('pm-jay') || lower.includes('pm jay') || lower.includes('golden card') || lower.includes('ayushman card')) {
                matchedScheme = 'pmjay';
                schemeDisplayName = 'Ayushman Bharat – PM-JAY';
            } else if (lower.includes('cghs') || lower.includes('central govt') || lower.includes('central government health')) {
                matchedScheme = 'cghs';
                schemeDisplayName = 'CGHS (Central Government Health Scheme)';
            } else if (lower.includes('echs') || lower.includes('ex-servicemen') || lower.includes('fauji') || lower.includes('defence') || lower.includes('army card')) {
                matchedScheme = 'echs';
                schemeDisplayName = 'ECHS (Ex-Servicemen Contributory Health Scheme)';
            } else if (lower.includes('esic') || lower.includes('esi card') || lower.includes('esi hospital') || lower.includes('peon') || lower.includes('factory insurance')) {
                matchedScheme = 'esic';
                schemeDisplayName = 'ESIC (Employees State Insurance Corporation)';
            } else if (lower.includes('rghs') || lower.includes('mjpjay') || lower.includes('aarogyasri') || lower.includes('swasthya sathi') || lower.includes('state govt') || lower.includes('state scheme')) {
                matchedScheme = 'state_govt';
                schemeDisplayName = 'State Government Health Scheme';
            } else if (lower.includes('star health') || lower.includes('star health insurance')) {
                matchedScheme = 'tpa_insurance';
                schemeDisplayName = 'Star Health Insurance Network';
                insurerName = 'Star Health';
            } else if (lower.includes('hdfc ergo') || lower.includes('hdfc')) {
                matchedScheme = 'tpa_insurance';
                schemeDisplayName = 'HDFC ERGO Health Insurance';
                insurerName = 'HDFC ERGO';
            } else if (lower.includes('icici lombard') || lower.includes('icici')) {
                matchedScheme = 'tpa_insurance';
                schemeDisplayName = 'ICICI Lombard Health Network';
                insurerName = 'ICICI Lombard';
            } else if (lower.includes('care health') || lower.includes('religare') || lower.includes('max bupa') || lower.includes('niva bupa') || lower.includes('tata aig') || lower.includes('bajaj allianz')) {
                matchedScheme = 'tpa_insurance';
                schemeDisplayName = 'Private Health Insurance Network';
                insurerName = 'Private Insurer';
            } else if (lower.includes('company') || lower.includes('corporate') || lower.includes('office') || lower.includes('group insurance')) {
                matchedScheme = 'tpa_insurance';
                schemeDisplayName = 'Corporate / Employer Group Health Insurance';
                insurerName = 'Corporate TPA';
            } else if (lower.includes('insurance') || lower.includes('tpa') || lower.includes('cashless') || lower.includes('panel')) {
                matchedScheme = this.sessionPanel.schemeCode || 'tpa_insurance';
                schemeDisplayName = this.sessionPanel.schemeName || 'Health Insurance / TPA Panel';
            }

            // Update session memory
            if (matchedScheme) {
                this.sessionPanel.schemeCode = matchedScheme;
                this.sessionPanel.schemeName = schemeDisplayName;
                if (insurerName) this.sessionPanel.insurerOrPlan = insurerName;
            }

            // 3. User says they don't know their panel or plan ("nahi pata", "don't know", etc.)
            if ((lower.includes('nahi pata') || lower.includes('pata nahi') || lower.includes("don't know") || lower.includes('not sure') || lower.includes('malum nahi')) && !matchedScheme) {
                if (isEn) {
                    return {
                        response: "No problem at all! Let's help identify your healthcare panel.",
                        followUp: "Please check your health card or policy document for:\n• **Government Scheme:** Ayushman Bharat (PM-JAY), CGHS, ECHS, or ESIC\n• **Insurer Name:** Star Health, HDFC ERGO, Niva Bupa, Care Health, ICICI Lombard\n• **TPA Name:** Medi Assist, Vidal Health, MDIndia, Paramount TPA\n\n*(Note: Never share sensitive numbers, passwords, OTPs, or full policy IDs — just share the insurer or scheme name!)*",
                        suggestions: ['I have Ayushman Card', 'I have CGHS Card', 'Star Health Policy', 'Corporate Company Policy']
                    };
                } else if (isHinglish) {
                    return {
                        response: "Koi baat nahi! Main aapka panel identify karne me madad karti hun.",
                        followUp: "Kripya apna health card ya policy document check karein:\n• Kya us par **Ayushman Bharat (PM-JAY)**, **CGHS**, **ECHS**, ya **ESIC** likha hai?\n• Ya kisi private company ka naam (jaise: Star Health, HDFC ERGO, Care, ICICI Lombard)?\n• Ya TPA ka naam (jaise: Medi Assist, Vidal, Paramount)?\n\n*(Kripya password, OTP ya full policy number share na karein — sirf company ya scheme ka naam batayein!)*",
                        suggestions: ['Mere paas Ayushman Card hai', 'Mere paas CGHS Card hai', 'Star Health Insurance', 'Company Insurance hai']
                    };
                } else {
                    return {
                        response: "कोई बात नहीं! मैं आपका पैनल पहचानने में मदद करती हूँ।",
                        followUp: "कृपया अपने बीमा कार्ड या पॉलिसी दस्तावेज़ की जाँच करें:\n• क्या उस पर **आयुष्मान भारत (PM-JAY)**, **CGHS**, **ECHS**, या **ESIC** लिखा है?\n• या किसी निजी कंपनी का नाम (जैसे: Star Health, HDFC ERGO, Care, ICICI Lombard)?\n• या TPA का नाम (जैसे: Medi Assist, Vidal, Paramount)?\n\n*(कृपया पासवर्ड, ओटीपी या पूरा पॉलिसी नंबर कभी साझा न करें — केवल योजना या कंपनी का नाम बताएं!)*",
                        suggestions: ['मेरे पास आयुष्मान कार्ड है', 'मेरे पास CGHS कार्ड है', 'Star Health Insurance', 'कंपनी का बीमा है']
                    };
                }
            }

            // If no panel detected in this or past turn, let normal intents handle it
            if (!this.sessionPanel.schemeCode) {
                return null;
            }

            const activeScheme = this.sessionPanel.schemeCode;
            const activeTitle = this.sessionPanel.schemeName || 'Health Scheme';
            const loc = this.sessionPanel.searchLocation || (isEn ? 'your selected location' : (isHinglish ? 'aapke chune huye location' : 'आपके चयनित स्थान'));

            // 4. Fetch actual matching hospitals from backend
            const hospitals = await this.fetchHospitalsForPanel(this.sessionPanel.searchLocation, activeScheme);

            let empanelledHospitals = [];
            let unverifiedHospitals = [];

            hospitals.forEach(h => {
                const pInfo = h.panel_info || {};
                const p = (pInfo.panels || {})[activeScheme];
                if (p && (p.status === 'Empanelled' || p.badge === 'empanelled')) {
                    empanelledHospitals.push({
                        name: h.name,
                        address: h.address,
                        distance: h.distance_km,
                        source: pInfo.source || 'Official Central Registry',
                        lastVerified: pInfo.last_verified || 'Recent',
                        details: p.details || 'Empanelled'
                    });
                } else {
                    unverifiedHospitals.push(h.name);
                }
            });

            // Format conversational response with verified hospital cards strictly matching language
            let respHeader = "";
            let followUpText = "";

            if (isEn) {
                respHeader = `Understood! Checking verified hospital empanelment for **${activeTitle}** in ${loc}:`;
                if (empanelledHospitals.length > 0) {
                    const topHospitals = empanelledHospitals.slice(0, 3);
                    followUpText = topHospitals.map((h, idx) => {
                        return `🏥 **${idx + 1}. ${h.name}**\n` +
                               `📍 ${h.address} (Distance: ~${h.distance} km)\n` +
                               `✅ **Status:** Empanelled (${activeTitle})\n` +
                               `📋 **Coverage:** ${h.details}\n` +
                               `🏛️ **Verification Source:** ${h.source} (Verified: ${h.lastVerified})`;
                    }).join('\n\n');
                    followUpText += `\n\n💡 **Important Note:** Cashless treatment depends on active policy status and pre-authorization at hospital TPA desk. Emergency ambulance service will not be delayed for insurance.`;
                } else {
                    followUpText = `No directly confirmed **Empanelled** facility was found for this specific area in the central registry. For other facilities: **Empanelment status could not be verified**.\n\nYou can also search for a major city (e.g. 'Delhi' or 'Jaipur') to view regional empanelled hubs.`;
                }
            } else if (isHinglish) {
                respHeader = `Samajh gayi! Main **${activeTitle}** ke tehat ${loc} mein empanelled hospitals check kar rahi hun:`;
                if (empanelledHospitals.length > 0) {
                    const topHospitals = empanelledHospitals.slice(0, 3);
                    followUpText = topHospitals.map((h, idx) => {
                        return `🏥 **${idx + 1}. ${h.name}**\n` +
                               `📍 ${h.address} (Doori: ~${h.distance} km)\n` +
                               `✅ **Status:** Empanelled (${activeTitle})\n` +
                               `📋 **Suvidha:** ${h.details}\n` +
                               `🏛️ **Verification Source:** ${h.source}`;
                    }).join('\n\n');
                    followUpText += `\n\n💡 **Zaroori Jankari:** Cashless suvidha hospital ke TPA desk par pre-authorization par depend karti hai. Emergency ambulance me bima ke karan koi deri nahi hogi.`;
                } else {
                    followUpText = `Is location par abhi koi direct **Empanelled** record nahi mila. Baaki hospitals ka status: **Status Not Verified** hai.\n\nAap kisi bade shehar (jaise 'Delhi' ya 'Jaipur') ka naam likhkar bhi khoj sakte hain!`;
                }
            } else {
                respHeader = `समझ गई! मैं **${activeTitle}** के तहत ${loc} में सूचीबद्ध अस्पतालों की जाँच कर रही हूँ:`;
                if (empanelledHospitals.length > 0) {
                    const topHospitals = empanelledHospitals.slice(0, 3);
                    followUpText = topHospitals.map((h, idx) => {
                        return `🏥 **${idx + 1}. ${h.name}**\n` +
                               `📍 ${h.address} (दूरी: ~${h.distance} km)\n` +
                               `✅ **स्थिति:** Empanelled (${activeTitle})\n` +
                               `📋 **सुविधा:** ${h.details}\n` +
                               `🏛️ **सत्यापन स्रोत:** ${h.source} (सत्यापित: ${h.lastVerified})`;
                    }).join('\n\n');
                    followUpText += `\n\n💡 **महत्वपूर्ण सूचना:** NABH मान्यता व कैशलेस सुविधा भर्ती समय कार्ड व टीपीए प्री-ऑथराइजेशन पर निर्भर करती है। आपातकालीन एम्बुलेंस सहायता में बीमा के कारण कोई देरी नहीं की जाएगी।`;
                } else {
                    followUpText = `इस विशिष्ट स्थान पर अभी कोई सीधा प्रमाणित **Empanelled** रिकॉर्ड नहीं मिला। बाकी सुविधाओं की स्थिति: **Empanelment status could not be verified**।\n\nआप किसी बड़े शहर (जैसे 'Jaipur' या 'Delhi') का नाम लिखकर भी खोज सकते हैं!`;
                }
            }

            const chips = isEn
                ? ['Check CGHS Hospitals', 'Check PM-JAY Hospitals', 'Hospitals in Delhi', 'Hospitals in Jaipur']
                : (isHinglish ? ['CGHS Hospitals Dekho', 'Ayushman PM-JAY Hospitals', 'Delhi Hospitals', 'Jaipur Hospitals'] : ['CGHS अस्पताल देखें', 'आयुष्मान PM-JAY अस्पताल', 'Delhi में अस्पताल', 'Jaipur में अस्पताल']);

            return {
                response: respHeader,
                followUp: followUpText,
                suggestions: chips
            };
        }

        async processQuery(text) {
            const lower = text.toLowerCase().trim();
            if (!lower) return null;

            // ----------------------------------------------------------------
            // STEP 1: EMERGENCY FAST-PATH — always check first
            // ----------------------------------------------------------------
            const emergencyKeywords = ['heart attack', 'chest pain', 'breathing problem', 'unconscious', 'accident', 'bleeding', 'stroke', 'faint', 'ambulance chahiye', 'emergency hai', '102', '108', '112'];
            const isEmergencyQuery = emergencyKeywords.some(kw => lower.includes(kw));
            if (isEmergencyQuery) {
                // Show emergency warning immediately, then also query AI in background
                const isHi = (window.govPortal && window.govPortal.currentLang === 'hi') || lower.includes('chahiye') || lower.includes('hai');
                const emergencyResponse = {
                    response: isHi 
                        ? "⚠️ **Emergency Alert!** TURANT **112, 102, ya 108** par call karein!\n\nAmbuPriority dispatch team ko alert bheja ja sakta hai."
                        : "⚠️ **Emergency Alert!** Please dial **112, 102, or 108** immediately for urgent emergency assistance!",
                    suggestions: isHi ? ['Call 102', 'Call 108', 'Call 112', 'Ambulance Request'] : ['Call 102', 'Call 108', 'Call 112', 'Request Ambulance'],
                    isEmergency: true
                };
                this.askAI(text).catch(() => {});
                return emergencyResponse;
            }

            // ----------------------------------------------------------------
            // STEP 2: AI BACKEND FIRST — Powered by Gemini API
            // Delivers intelligent, natural responses matching user language
            // ----------------------------------------------------------------
            try {
                const aiReply = await this.askAI(text);
                if (aiReply) {
                    return {
                        response: aiReply,
                        suggestions: this._suggestionsFromReply(aiReply, lower)
                    };
                }
            } catch (err) {
                console.warn('AI query error, falling back to local engine:', err);
            }

            // ----------------------------------------------------------------
            // STEP 3: FALLBACK LOCAL ENGINE (Only if AI backend is unavailable)
            // ----------------------------------------------------------------

            // Check panel & insurance queries
            const panelKeywords = [
                'ayushman', 'pmjay', 'pm-jay', 'cghs', 'echs', 'esic', 'rghs', 'mjpjay', 
                'insurance', 'bima', 'card', 'star health', 'hdfc ergo', 'icici lombard', 
                'tpa', 'cashless', 'panel', 'empanelled', 'empanelment', 'mere paas'
            ];
            const hasPanelIntent = panelKeywords.some(kw => lower.includes(kw));
            if (hasPanelIntent) {
                const panelResult = await this.processPanelQuery(lower, text);
                if (panelResult) return panelResult;
            }

            // Check known portal help intents (Form help, mandatory fields, etc.)
            const intents = KB.en.intents;
            let best = null, bestScore = -1;
            for (const intent of intents) {
                let score = 0;
                const priority = intent.priority || 5;
                if (intent.phrases) {
                    for (const phrase of intent.phrases) {
                        if (lower.includes(phrase.toLowerCase())) score += phrase.length * 3;
                    }
                }
                if (intent.patterns) {
                    for (const pattern of intent.patterns) {
                        if (lower.includes(pattern.toLowerCase())) score += pattern.length;
                    }
                }
                if (score > 0) score = score + (priority * 2);
                if (score > bestScore || (score === bestScore && best && priority > (best.priority || 5))) {
                    bestScore = score;
                    best = intent;
                }
            }
            if (best && bestScore >= 4) {
                return {
                    response: best.response,
                    followUp: best.followUp,
                    suggestions: best.suggestions || [],
                    isEmergency: best.isEmergency || false
                };
            }

            // Offline fallback message matching user language
            const isHinglishQuery = lower.includes('kya') || lower.includes('kaise') || lower.includes('hai') || lower.includes('mujhe') || lower.includes('batao') || lower.includes('paas') || lower.includes('kare');
            if (isHinglishQuery) {
                return {
                    response: "Main ARIA hun, aapki AmbuPriority sahayak. Main aapko hospital panels, cashless insurance claims, ya form bharne me madad kar sakti hun. Kripya apna sawal thoda vistaar se batayein!",
                    suggestions: ['Hospital Panels (Ayushman/CGHS)', 'Star Health / Private Insurance', 'Form Kaise Bhare?', 'Emergency Helplines']
                };
            }

            return { 
                response: "I am ARIA, your AmbuPriority assistant. I can guide you regarding hospital empanelment, cashless insurance claims, or help you fill out the registration form. Please let me know how I can help!",
                suggestions: ['Hospital Panels (Ayushman/CGHS)', 'Health Insurance & Cashless Help', 'Form Filling Help', 'Emergency Numbers (102/108)'] 
            };
        }

        // Generate contextual suggestion chips from AI reply
        _suggestionsFromReply(reply, lower) {
            const chips = [];
            if (reply.includes('CGHS') || lower.includes('cghs')) chips.push('Check CGHS Hospitals');
            if (reply.includes('PM-JAY') || reply.includes('Ayushman') || lower.includes('ayushman')) chips.push('Check PM-JAY Hospitals');
            if (reply.includes('ECHS') || lower.includes('echs')) chips.push('Check ECHS Hospitals');
            if (reply.includes('ESIC') || lower.includes('esic')) chips.push('Check ESIC Hospitals');
            if (reply.includes('insurance') || reply.includes('TPA') || lower.includes('insurance')) chips.push('TPA Network Hospitals');
            if (chips.length === 0) {
                chips.push('Hospital Panels (Ayushman/CGHS)', 'Form Filling Help', 'Emergency Helplines');
            }
            return chips.slice(0, 4);
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
            setTimeout(() => this.showGreeting(), 800);
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
            launcher.setAttribute('aria-label', 'Open ARIA Emergency Assistant');
            launcher.setAttribute('tabindex', '0');
            launcher.innerHTML = `
                <div id="aria-launcher-avatar">
                    <canvas id="aria-launcher-canvas" width="76" height="76"></canvas>
                </div>
                <div id="aria-launcher-label">ARIA • Emergency Assistant</div>
            `;
            document.body.appendChild(launcher);

            /* ---- Main Window ---- */
            const win = document.createElement('div');
            win.id = 'aria-window';
            win.setAttribute('role', 'dialog');
            win.setAttribute('aria-label', 'ARIA Emergency Assistant Chat');
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
                            <div id="aria-designation">Emergency Response Assistant</div>
                            <div id="aria-status-row">
                                <div id="aria-status-dot"></div>
                                <span id="aria-status-text">Online • 24×7 Active</span>
                            </div>
                            <div style="margin-top:8px; font-family:'Inter',sans-serif; font-size:9px; color:rgba(255,255,255,0.5); text-transform:uppercase; letter-spacing:0.08em;">
                                AmbuPriority National Portal
                            </div>
                        </div>
                    </div>
                    <div id="aria-quick-chips">
                        <div class="aria-chip" data-query="request ambulance">🚑 Request Ambulance</div>
                        <div class="aria-chip" data-query="emergency helpline numbers">📞 Helplines</div>
                        <div class="aria-chip" data-query="about ambupriority system">ℹ️ About</div>
                        <div class="aria-chip" data-query="gps location address">📍 GPS Help</div>
                    </div>
                </div>

                <!-- Messages -->
                <div id="aria-messages" role="log" aria-live="polite" aria-label="Conversation">
                    <!-- Typing indicator (always rendered, shown/hidden) -->
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
                           placeholder="Ask about ambulance, helplines, portal..."
                           maxlength="300"
                           autocomplete="off"
                           aria-label="Type your question">
                    <button id="aria-send-btn" title="Send" aria-label="Send message">
                        <i class="fa-solid fa-paper-plane"></i>
                    </button>
                </div>
                <div id="aria-footer-note">
                    AmbuPriority • National Health Authority &nbsp;|&nbsp; Emergency: 102 / 108 / 112
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

            // Close on outside click
            document.addEventListener('click', (e) => {
                if (this.isOpen && !this.window.contains(e.target) && !this.launcher.contains(e.target)) {
                    // Don't auto-close — user must explicitly close
                }
            });

            // Escape key
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape' && this.isOpen) this.close();
            });
        }

        initCharsRenderers() {
            // Main character (in chat header)
            const mainCanvas = document.getElementById('aria-3d-canvas');
            if (mainCanvas) {
                this.mainChar = new ARIACharacter3D(mainCanvas, { isSmall: false });
                this.mainChar.setState('greeting');
                setTimeout(() => { if (this.mainChar) this.mainChar.setState('idle'); }, 3000);
            }

            // Launcher avatar
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
                greeting: 'Greeting',
                thinking: 'Thinking...',
                responding: 'Responding',
                error: 'Error'
            };
            if (this.stateLabel) this.stateLabel.textContent = labels[state] || '';

            // Show/hide thinking indicator
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

            // Greeting state
            this.setCharacterState('greeting');
            setTimeout(() => this.setCharacterState('idle'), 2500);
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
            }, 50);
        }

        showGreeting() {
            const onRegister = window.location.pathname.includes('register.html');
            const onAssessment = window.location.pathname.includes('assessment.html');
            const onHospitals = window.location.pathname.includes('hospitals.html');
            const isHindi = (window.govPortal && window.govPortal.currentLang === 'hi');

            let greeting = this.engine.getGreeting();
            let suggestions = ['Request Ambulance', 'Emergency Helplines', 'GPS Location Help', 'About AmbuPriority'];

            if (onHospitals) {
                if (isHindi) {
                    greeting = "नमस्ते! मैं ARIA हूँ। क्या आपके पास आयुष्मान भारत, CGHS, ECHS, ESIC या कोई निजी स्वास्थ्य बीमा है? मुझे बताएं — मैं प्रमाणित पैनल अस्पतालों की सूची दिखा सकती हूँ!";
                    suggestions = ['मेरे पास आयुष्मान कार्ड है', 'मेरे पास CGHS कार्ड है', 'Star Health Insurance', 'कंपनी का बीमा है'];
                } else {
                    greeting = "Namaste! I'm ARIA. Do you hold Ayushman Bharat, CGHS, ECHS, ESIC, or private health insurance? Tell me, and I will check verified empanelled hospitals for you!";
                    suggestions = ['I have Ayushman Card', 'I have CGHS Card', 'Star Health Policy', 'Corporate Company Policy'];
                }
            } else if (onRegister) {
                if (isHindi) {
                    greeting = "नमस्ते! मैं ARIA हूं। क्या आपको एम्बुलेंस रजिस्ट्रेशन फ़ॉर्म भरने में कोई सहायता चाहिए? आप मुझसे किसी भी फ़ील्ड, जीपीएस लोकेशन, या आपातकालीन नंबर के बारे में पूछ सकते हैं।";
                    suggestions = ['फ़ॉर्म कैसे भरें?', 'अनिवार्य फ़ील्ड कौन सी हैं?', 'जीपीएस का उपयोग कैसे करें?', 'लैंडमार्क क्या लिखें?'];
                } else {
                    greeting = "Namaste! I'm ARIA. Do you need help filling out this Ambulance Registration form? Feel free to ask about any field, GPS location, mandatory details, or emergency numbers!";
                    suggestions = ['How to fill form?', 'Mandatory fields?', 'How to use GPS?', 'What is Landmark?'];
                }
            } else if (onAssessment) {
                if (isHindi) {
                    greeting = "नमस्ते! मैं क्लिनिकल ट्रायज में आपकी मदद के लिए यहाँ हूँ। मुख्य आपातकाल (हृदय, सांस, दुर्घटना आदि) चुनने में कोई संशय हो तो बेझिझक पूछें।";
                    suggestions = ['सीने का दर्द / हार्ट अटैक', 'स्ट्रोक के लक्षण (FAST)', 'सांस की तकलीफ'];
                } else {
                    greeting = "Namaste! I'm ARIA, here to guide you through the Clinical Triage Assessment. If you are unsure which primary complaint or symptom to select, just ask me!";
                    suggestions = ['Chest Pain guidance', 'Stroke FAST signs', 'Breathing emergency'];
                }
            }

            this.addMessage('aria', greeting);

            setTimeout(() => {
                this.addSuggestions(suggestions);
            }, 400);
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
                            If this is a life-threatening emergency, dial 112 immediately.
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

            // Insert before typing indicator
            this.messages.insertBefore(div, this.typing);
            this.scrollBottom();
            return msgId;
        }

        addFollowUp(text) {
            const time = this.engine.formatTime();
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
                chip.addEventListener('click', () => this.handleQuery(label.toLowerCase()));
                row.appendChild(chip);
            });

            inner.appendChild(row);
            div.appendChild(inner);
            this.messages.insertBefore(div, this.typing);
            this.scrollBottom();
        }

        showTyping() {
            this.typing.classList.add('visible');
            this.messages.appendChild(this.typing); // move to end
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

            // Start thinking state & show typing instantly
            this.sendBtn.disabled = true;
            this.input.disabled = true;
            this.setCharacterState('thinking');
            this.showTyping();

            // Process query directly without artificial pre-delay
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

            // Handle action chips (Only redirect if NOT already on register.html)
            const onRegisterPage = window.location.pathname.includes('register.html');
            if (!onRegisterPage && (text.toLowerCase().includes('open registration') || text.toLowerCase().includes('registration form'))) {
                setTimeout(() => { window.location.href = 'register.html'; }, 1500);
            }
            if (text.toLowerCase().includes('view documentation') || text.toLowerCase().includes('documentation')) {
                setTimeout(() => {
                    this.addFollowUp('Opening documentation page...');
                    setTimeout(() => { window.location.href = 'detail.html'; }, 1000);
                }, 500);
            }
            if (text.toLowerCase().includes('call 102')) {
                window.open('tel:102');
            }
            if (text.toLowerCase().includes('call 108')) {
                window.open('tel:108');
            }

            // Return to idle
            await sleep(2000);
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
        // Prevent double init
        if (window.__ariaInitialized) return;
        window.__ariaInitialized = true;

        // Don't load on register.html to avoid UX conflicts during emergency forms
        // But still provide a minimal launcher
        window.__ARIA = new ARIAUI();
    }

    // Wait for DOM + FA icons
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initARIA);
    } else {
        initARIA();
    }

})();

