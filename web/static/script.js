// File: script.js (Upgraded to display images)

document.addEventListener('DOMContentLoaded', () => {
    const chatInterface = document.getElementById('chat-interface');
    const chatLog = document.getElementById('chat-log');
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const submitBtn = document.getElementById('submit-btn');
    const fengSymbol = document.getElementById('feng-symbol');
    const toggleSoundBtn = document.getElementById('toggle-sound-btn');
    const micBtn = document.getElementById('mic-btn');

    // --- 2. State Management ---
    let chatHistory = [];
    let isAudioUnlocked = false; 
    let isFengThinking = false;
    let availableVoices = [];
    let isSoundEnabled = true;

    // --- 3. การตั้งค่า Speech Recognition ---
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    let recognition;

    if (SpeechRecognition) {
        recognition = new SpeechRecognition();
        recognition.lang = 'th-TH';
        recognition.interimResults = false;
        recognition.maxAlternatives = 1;

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            userInput.value = transcript;
            handleUserSubmit(); 
        };
        recognition.onerror = (event) => {
            console.error("Speech Recognition Error:", event.error);
            userInput.placeholder = "ขออภัยครับ เกิดข้อผิดพลาดในการรับเสียง";
        };
        recognition.onend = () => {
            micBtn.classList.remove('is-listening');
            if (!isFengThinking) {
                userInput.placeholder = 'ถามคำถามของท่านที่นี่...';
            }
        };
    } else {
        console.warn("เบราว์เซอร์นี้ไม่รองรับ Speech Recognition API");
        if (micBtn) micBtn.style.display = 'none';
    }

    // --- 4. Event Listeners ---
    const loadVoices = () => {
        availableVoices = window.speechSynthesis.getVoices();
        if (availableVoices.length > 0) {
            console.log("เสียงในระบบพร้อมใช้งานแล้ว:", availableVoices.filter(v => v.lang === 'th-TH').map(v => v.name));
        }
    };
    loadVoices();
    if (speechSynthesis.onvoiceschanged !== undefined) {
        speechSynthesis.onvoiceschanged = loadVoices;
    }
    
    document.body.addEventListener('click', () => {
        if (!isAudioUnlocked) {
            isAudioUnlocked = true;
            playFengsVoice("");
            console.log("🔊 ระบบเสียงถูกปลดล็อกโดยการคลิกของผู้ใช้");
        }
    }, { once: true });

    toggleSoundBtn.addEventListener('click', () => {
        isSoundEnabled = !isSoundEnabled; 
        if (isSoundEnabled) {
            toggleSoundBtn.innerHTML = '🔊';
            toggleSoundBtn.title = 'ปิดเสียง';
        } else {
            toggleSoundBtn.innerHTML = '🔇';
            toggleSoundBtn.title = 'เปิดเสียง';
            window.speechSynthesis.cancel();
        }
    });

    chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        handleUserSubmit();
    });

    if (micBtn && recognition) {
        micBtn.addEventListener('mousedown', () => {
            if (isFengThinking) return;
            try {
                recognition.start();
                micBtn.classList.add('is-listening');
                userInput.placeholder = 'กำลังฟัง...';
            } catch (e) { console.error("ไม่สามารถเริ่มการรับเสียงได้:", e); }
        });
        micBtn.addEventListener('mouseup', () => {
            if (isFengThinking) return;
            try {
                recognition.stop();
                userInput.placeholder = 'กำลังประมวลผลเสียง...';
            } catch (e) { console.error("ไม่สามารถหยุดการรับเสียงได้:", e); }
        });
        micBtn.addEventListener('mouseleave', () => {
            if(micBtn.classList.contains('is-listening')) {
                recognition.stop();
            }
        });
    }

    // --- 5. Core Functions ---
    const handleUserSubmit = async () => {
        if (isFengThinking) return;
        const userText = userInput.value.trim();
        if (!userText) return;

        addMessageToLog(userText, 'user');
        const currentQuery = userInput.value;
        userInput.value = '';

        setThinkingState(true);
        const data = await getFengResponseFromAPI(currentQuery);

        if (data && data.answer) {
            chatHistory = data.history;
            //!! แก้ไข: ส่งทั้งข้อความและข้อมูลรูปภาพไปที่ addMessageToLog
            addMessageToLog(data.answer, 'feng', data.image); 
            playFengsVoice(data.answer);
        }
        setThinkingState(false);
    };
    
    /**
     * ฟังก์ชันสำหรับเพิ่มข้อความและรูปภาพลงใน Chat Log (อัปเกรด)
     */
    //!! แก้ไข: ฟังก์ชันนี้รับพารามิเตอร์ `imageInfo` เพิ่มเข้ามา
    const addMessageToLog = (text, sender, imageInfo = null) => {
        const messageContainer = document.createElement('div');
        messageContainer.classList.add('message', `${sender}-message`);

        // สร้างและเพิ่ม Element สำหรับข้อความ
        const messageText = document.createElement('p');
        messageText.innerText = text;
        messageContainer.appendChild(messageText);

        //!! ใหม่: ตรวจสอบและสร้าง Element สำหรับรูปภาพ
        if (sender === 'feng' && imageInfo && imageInfo.url) {
            const imageContainer = document.createElement('div');
            imageContainer.classList.add('image-container');

            const imageLink = document.createElement('a');
            imageLink.href = imageInfo.profile_url; // ลิงก์ไปที่โปรไฟล์ช่างภาพ
            imageLink.target = '_blank';
            imageLink.rel = 'noopener noreferrer';

            const imageElement = document.createElement('img');
            imageElement.src = imageInfo.url;
            imageElement.alt = imageInfo.description;
            imageElement.title = imageInfo.description; // แสดงคำอธิบายเมื่อเอาเมาส์ไปชี้
            imageLink.appendChild(imageElement);
            
            const caption = document.createElement('small');
            caption.innerHTML = `Photo by <a href="${imageInfo.profile_url}" target="_blank">${imageInfo.photographer}</a> on <a href="https://unsplash.com" target="_blank">Unsplash</a>`;
            
            imageContainer.appendChild(imageLink);
            imageContainer.appendChild(caption);
            messageContainer.appendChild(imageContainer);
        }

        chatLog.appendChild(messageContainer);
        chatLog.scrollTop = chatLog.scrollHeight;
    };

    /**
     * ฟังก์ชันสำหรับส่งคำถามไปที่ Backend (อัปเกรด)
     */
    const getFengResponseFromAPI = async (userQuery) => {
        const apiUrl = '/ask';
        
        //!! แก้ไข: ไม่จำเป็นต้องส่ง history จาก frontend อีกต่อไป
        try {
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: userQuery }) // ส่งแค่ query
            });

            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            
            return await response.json();
        } catch (error) {
            console.error('เกิดข้อผิดพลาดในการเรียก API:', error);
            const errorMessage = 'ขออภัยครับ ดูเหมือนว่าจะมีปัญหาในการเชื่อมต่อกับระบบ';
            // สร้าง history ปลอมสำหรับแสดงผลกรณี error
            const fakeHistory = [...chatHistory, { "role": "user", "parts": userQuery }];
            return { answer: errorMessage, history: fakeHistory, image: null };
        }
    };
    
    // --- (ส่วนที่เหลือเหมือนเดิม) ---
    const playFengsVoice = (textToSpeak) => {
        if (!isSoundEnabled || !isAudioUnlocked || !textToSpeak || !('speechSynthesis' in window)) return;
        try {
            const synth = window.speechSynthesis;
            synth.cancel();
            const getThaiVoice = () => {
                let bestVoice = availableVoices.find(voice => voice.lang === 'th-TH' && voice.name.includes('Kanya'));
                if (!bestVoice) bestVoice = availableVoices.find(voice => voice.lang === 'th-TH' && voice.name.includes('Google'));
                if (!bestVoice) bestVoice = availableVoices.find(voice => voice.lang === 'th-TH');
                return bestVoice;
            };
            const sentences = textToSpeak.match(/[^.!?\n]+[.!?\n]*|[^.!?\n]+/g) || [];
            sentences.forEach(sentence => {
                if (!sentence.trim()) return;
                const utterance = new SpeechSynthesisUtterance(sentence.trim());
                utterance.voice = getThaiVoice();
                utterance.lang = 'th-TH';
                utterance.rate = 0.95;
                utterance.pitch = 1.0;
                synth.speak(utterance);
            });
        } catch(error) {
            console.error("เกิดข้อผิดพลาดในการเล่นเสียง:", error);
        }
    };

    const setThinkingState = (isThinking) => {
        isFengThinking = isThinking;
        userInput.disabled = isThinking;
        submitBtn.disabled = isThinking;
        if (isThinking) {
            if(fengSymbol) fengSymbol.classList.add('thinking');
            userInput.placeholder = 'เฟิงกำลังครุ่นคิด...';
        } else {
            if(fengSymbol) fengSymbol.classList.remove('thinking');
            userInput.placeholder = 'ถามคำถามของท่านที่นี่...';
            userInput.focus();
        }
    };

    const initializeChat = () => {
        const firstMessage = "สวัสดีครับ ผมเฟิง มีสิ่งใดให้ผมช่วยชี้แนะหรือไม่?";
        addMessageToLog(firstMessage, 'feng');
        chatHistory.push({ "role": "model", "parts": firstMessage });
        userInput.focus();
    };
    
    initializeChat();
});