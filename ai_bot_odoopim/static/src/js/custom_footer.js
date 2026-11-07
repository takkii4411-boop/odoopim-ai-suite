document.addEventListener('DOMContentLoaded', function() {
    setTimeout(function() {
        const botImage = document.getElementById('botImage');
        if (botImage) {
            botImage.classList.add('show-icon');
        }
    }, 2000);

    // Placeholder animation
    const placeholders = ["Type your message...", "Ask about Odoo PIM...", "Search for Product..."];
    const inputField = document.getElementById("userMessage");
    let placeholderIndex = 0;
    let charIndex = 0;

    function typePlaceholder() {
        const currentPlaceholder = placeholders[placeholderIndex];
        if (charIndex < currentPlaceholder.length) {
            inputField.placeholder = currentPlaceholder.substring(0, charIndex + 1);
            charIndex++;
            setTimeout(typePlaceholder, 100);
        } else {
            charIndex = 0;
            placeholderIndex = (placeholderIndex + 1) % placeholders.length;
            setTimeout(typePlaceholder, 1000);
        }
    }

    typePlaceholder();

    document.querySelector('.custom-footer').removeAttribute('style');

    document.addEventListener('click', function(event) {
        const botChat = document.getElementById('botChat');
        const botImage = document.getElementById('botImage');

        if (botChat && botImage && !botChat.contains(event.target) && !botImage.contains(event.target)) {
            botChat.classList.remove('show');
        }
    });

    const botImage = document.getElementById('botImage');
    const botChat = document.getElementById('botChat');
    const closeChat = document.getElementById('closeChat');
    const sendButton = document.querySelector('.send-button');
    const clearChatButton = document.getElementById('clearChat');
    const cancelDeleteButton = document.getElementById('cancelDelete');
    const confirmDeleteButton = document.getElementById('confirmDelete');
    const closeClearButton = document.getElementById('closeClear');
    const confirmationPopup = document.getElementById('confirmationPopup');
    const chatInput = document.querySelector('.chat-input');
    const chatBody = document.querySelector('.chat-body');
    const switchButton = document.getElementById('switchButton');
    const toggleScrape = document.getElementById('toggleScrape');
    const botElements = document.querySelectorAll('.bot-info, #botImage, #botChat, .chat-header, .chat-body, .chat-footer');
    let pageContent = '';
    let initialMessageSent = false;
    let abortController;

    function closeChatbot() {
        setTimeout(function() {
            botChat.classList.remove('show');
        }, 4000);
    }

    function hideBotElements() {
        botElements.forEach(element => {
            element.style.visibility = 'hidden';
        });
    }

    function showBotElements() {
        botElements.forEach(element => {
            element.style.visibility = '';
        });
    }

    function handleChatVisibility() {
        if (botChat.classList.contains('show') && !initialMessageSent) {
            initialMessageSent = true;
            sendInitialBotMessage();
        }
    }

    if (botImage) {
        botImage.addEventListener('click', function() {
            botChat.classList.toggle('show');
            handleChatVisibility();
        });
    }

    function sendInitialBotMessage() {
        if (chatBody) {
            const initialMessage = 'Hey! How can I assist you with Odoo today?';
            addMessage('bot', initialMessage);
        }
    }

    if (closeChat) {
        closeChat.addEventListener('click', function() {
            botChat.classList.remove('show');
        });
    }
        // --- NEW: MAXIMIZE BUTTON LOGIC ---
    if (maximizeChat) {
        maximizeChat.addEventListener('click', function() {
            botChat.classList.toggle('maximized');
            if (botChat.classList.contains('maximized')) {
                maximizeChat.innerHTML = '&#9472;'; // Minimize icon (Dash)
                maximizeChat.title = "Minimize";
            } else {
                maximizeChat.innerHTML = '&#9633;'; // Maximize icon (Square)
                maximizeChat.title = "Maximize";
            }
        });
    }
    // --- END MAXIMIZE LOGIC ---

    if (sendButton) {
        sendButton.addEventListener('click', function() {
            sendMessage();
        });
    }

    if (chatInput) {
        chatInput.addEventListener('keypress', function(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        });
    }

    if (switchButton) {
        switchButton.addEventListener('change', function() {
            const switchState = switchButton.checked;
            console.log('Switch state:', switchState);
        });
    }

    if (toggleScrape) {
        toggleScrape.addEventListener('click', function() {
            scrapePageData();
            var elements = document.getElementsByClassName("o_content");
            var innerTexts = [];
            for (var i = 0; i < elements.length; i++) {
                innerTexts.push(elements[i].innerText);
                pageContent = innerTexts;
            }
            console.log('Page Content:', pageContent);
        });
    }

    if (clearChatButton) {
        clearChatButton.addEventListener('click', function() {
            if (confirmationPopup) {
                if (confirmationPopup.parentNode) {
                    confirmationPopup.parentNode.removeChild(confirmationPopup);
                }
                document.getElementById('botChat').appendChild(confirmationPopup);
                confirmationPopup.style.display = 'block';
            }
        });
    }

    if (cancelDeleteButton) {
        cancelDeleteButton.addEventListener('click', function() {
            if (confirmationPopup) {
                confirmationPopup.style.display = 'none';
            }
        });
    }

    if (confirmDeleteButton) {
        confirmDeleteButton.addEventListener('click', function() {
            console.log('Chat memory cleared successfully');
            if (chatBody) {
                const chatMessages = chatBody.querySelectorAll(':scope > :not(.bot-info)');
                chatMessages.forEach(message => message.remove());
                chatInput.style.display = 'block';
            }

            if (confirmationPopup) {
                confirmationPopup.style.display = 'none';
                botChat.classList.remove('show');
            }
        });
    }

    if (closeClearButton) {
        closeClearButton.addEventListener('click', function() {
            if (chatInput) {
                chatInput.value = '';
            }

            const apiCheckSetting = document.getElementById('APICheckSetting');
            if (apiCheckSetting) {
                apiCheckSetting.style.display = 'none';
                botChat.classList.remove('show');
            }
        });
    }

    const stopButton = document.querySelector('.stop-button');
    stopButton.addEventListener('click', function() {
        if (abortController) {
            abortController.abort();
            console.log("Ongoing bot process aborted.");

            fetch('/groq_api/stop', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ stop: true })
            })
            .then(response => response.json())
            .then(data => {
                console.log("Backend response:", data.message);
            })
            .catch(error => {
                console.error('Error:', error);
            });

            const loadingElement = document.querySelector('.loader-wrapper');
            if (loadingElement) {
                loadingElement.parentNode.parentNode.remove();
            }
        }
    });

    function sendMessage() {
        if (chatInput) {
            const message = chatInput.value;
            console.log('Sending message:', message);
            if (message.trim() !== '') {
                fetch('/get_api_key')
                    .then(response => response.json())
                    .then(data => {
                        const apiKey = data.api_key;
                        const model = data.model;
                        if (!apiKey || !model) {
                            const apiCheckSetting = document.getElementById('APICheckSetting');
                            if (apiCheckSetting) {
                                apiCheckSetting.style.display = 'block';
                            }
                            return;
                        }
                        addMessage('user', message);
                        chatInput.value = '';
                        if(toggleScrape.checked){
                            const pagedata = scrapePageData();
                            forpagecontent(pagedata , message);
                        }
                        else{
                            fetchResponse(message);
                        }
                    });
            } else {
                console.warn('Empty message cannot be sent.');
            }
        } else {
            console.error('Chat input element not found.');
        }
    }

    function formatTime(date) {
        let hours = date.getHours();
        const minutes = date.getMinutes().toString().padStart(2, '0');
        const ampm = hours >= 12 ? 'PM' : 'AM';

        hours = hours % 12;
        hours = hours ? hours : 12;
        hours = hours.toString().padStart(2, '0');

        return `${hours}:${minutes}:${ampm}`;
    }

    function addMessage(sender, message, isLoading = false) {
        if (typeof message !== 'string') {
            return;
        }
        console.log("user messageeeeeeeeee",message)
        if (chatBody) {
            const md = window.markdownit().use(window.markdownitMultimdTable);
            const formattedResponse = md.render(message);

            const loadingElement = document.querySelector('.loader-wrapper');
            if (loadingElement) {
                loadingElement.parentNode.parentNode.remove();
            }

            const messageElement = document.createElement('div');
            messageElement.classList.add('chat-message', `${sender}-message`);
            const innerHTMLContent = isLoading ? `
                <div class="chat-title ${sender}-title">
                    <img src="/ai_bot_odoopim/static/src/img/${sender}_icon.png" alt="${sender} Icon" class="chat-icon"/> ${sender.charAt(0).toUpperCase() + sender.slice(1)}
                </div>
                <div class="chat-bubble ${sender}-bubble">
                    <div class="loader-wrapper">
                        <div class="loader"></div>
                    </div>
                </div>
            ` : `
                <div class="chat-title ${sender}-title">
                    <img src="/ai_bot_odoopim/static/src/img/${sender}_icon.png" alt="${sender} Icon" class="chat-icon"/> ${sender.charAt(0).toUpperCase() + sender.slice(1)}
                </div>
                <div class="chat-bubble ${sender}-bubble">
                    ${formattedResponse}
                </div>
                <div class="message-time-${sender}">
                    ${formatTime(new Date())}
                    <img src="/ai_bot_odoopim/static/src/img/copy1.svg" class="copy-icon"/>
                </div>
            `;
            messageElement.innerHTML = innerHTMLContent;

            chatBody.appendChild(messageElement);
            chatBody.scrollTop = chatBody.scrollHeight;
        } else {
            console.error('Chat body element not found.');
        }
    }

    function fetchResponse(userMessage) {
        const casualPatterns = [
            /good morning/i, /morning/i, /afternoon/i, /evening/i, /good afternoon/i, /hello buddy/i, /buddy/i, /good evening/i, /good night/i, /hi/i, /hello/i, /hey/i, /bye/i, /what's up/i,
            /how are you/i, /what happened/i, /anything new/i, /who are you/i, /howdy/i, /welcome/i, /nice to meet you/i, /what’s going on/i, /long time no see/i,
            /what’s up with you/i, /what’s happening/i, /hey there/i, /yo/i, /how’s it going/i, /how’s everything/i, /sup/i, /what’s new/i,
            /hey y’all/i, /hi there/i, /hello there/i, /greetings/i, /what’s the latest/i, /what’s the news/i, /how’s your day/i, /hey friend/i,
            /how’s life/i, /good to see you/i, /glad to see you/i, /hey everyone/i, /what’s up with you/i, /what are you up to/i, /how’s it going today/i,
            /hey there friend/i, /hello again/i, /how’s your day been/i, /what’s new with you/i, /how’s it going/i, /how are things/i, /what’s the buzz/i,
            /what’s up today/i, /hey there buddy/i, /hello friend/i, /what’s new/i, /what’s up man/i, /what’s up girl/i, /hey there pal/i
        ];

        const personalInfoPatterns = [
            /my name is/i, /i am/i, /i live/i, /i work/i, /i am from/i, /i come from/i, /my location is/i, /i’m currently/i, /i have/i,
            /i’m known as/i, /my occupation is/i, /i am employed as/i, /my job is/i, /i am a/i, /i am currently/i, /i reside in/i, /i am based in/i,
            /i come from/i, /my hometown is/i, /i’m a/i, /i’m an/i, /i work as/i, /i’m working as/i, /my role is/i, /i am a resident of/i,
            /my job title is/i, /i am currently living/i, /i am from/i, /i am residing/i, /i’m situated in/i, /i am located in/i, /my city is/i,
            /i am a native of/i, /i have lived in/i, /i’m currently based in/i, /my place of origin is/i, /i’m originally from/i, /my current location is/i,
            /i’m from/i, /i’m working at/i, /i am currently residing/i, /i am currently located/i, /i’m living in/i, /i am a resident of/i, /i’m based in/i,
            /my hometown is/i, /i am employed at/i, /i work in/i, /i’m affiliated with/i, /i am a/i, /i am situated in/i, /i am currently at/i
        ];

        const odooKeywords = [
            'odoopim','sku' , 'product'
        ];

        const casualResponses = [
            'Good day! How can I assist you with Odoopim today?',
            'Hello! What can I help you with regarding Odoopim?',
            'Hi there! If you have any questions about Odoopim, feel free to ask!',
            'Hello! For Odoopim-related inquiries, I’m here to help!',
            'Greetings! Let me know if you have any Odoopim-related questions.',
            'Hi! What’s on your mind today? If it’s Odoopim-related, I’m here to help!',
            'Hello there! How can I assist you with your Odoopim needs today?',
            'Hey! If you need assistance with Odoopim, just let me know!',
            'Welcome! If you have questions about Odoopim, feel free to ask.',
            'Hello! How can I support your Odoopim experience today?',
            'Hi! Ready to help with your Odoopim inquiries. What’s up?',
            'Hey there! Let me know how I can make your Odoopim experience smoother.',
            'Hello! I’m here for any questions you have about Odoopim. Just ask!',
            'Hi! Need any help with Odoopim? I’m here for you.',
            'Hey! Curious about something in Odoopim? I’m here to assist.',
            'Greetings! I’m here to answer any Odoopim-related queries you might have.',
            'Hello! If you’re looking for Odoopim assistance, you’ve come to the right place!',
            'Hi there! Ready to tackle any Odoopim questions you have.',
            'Hello! I’m eager to help with your Odoopim-related needs. Just let me know!'
        ];

        const personalInfoResponses = [
            'It’s nice to meet you! How can I assist with Odoopim today?',
            'Hello! Feel free to ask any Odoopim-related questions.',
            'Hi there! How can I support you with Odoopim today?',
            'Greetings! Let me know how I can assist you with Odoopim.',
            'Hello! I’m available for any questions you have about Odoopim.',
            'Nice to meet you! I’m here to support your Odoopim experience.',
            'Hi! If you have any Odoopim-related questions or need support, just ask.',
            'Hey! Let me know how I can assist you with Odoopim today.',
            'Hello! I’m ready to help with your Odoopim needs and queries.',
            'Hi there! How can I support you with Odoopim today?'
        ];

        const redirectResponses = [
            'I specialize in assisting with Odoopim-related inquiries. For questions about Odoopim or its features, please feel free to ask.',
            'I’m focused on helping with Odoopim inquiries. For questions about Odoo or its capabilities, I’m here to assist.'
        ];

        const exitKeywords = [
            'bye'
        ];

        const goodbyeResponses = [
            'Goodbye! If you need any more help, just let me know. Have a wonderful day!',
        ];

        if (exitKeywords.some(keyword => userMessage.toLowerCase().includes(keyword))) {
            const randomGoodbyeResponse = goodbyeResponses[Math.floor(Math.random() * goodbyeResponses.length)];
            addMessage('bot', randomGoodbyeResponse);
            closeChatbot();
            return;
        }

        const userMessageLower = userMessage.toLowerCase();
        const isOdooRelated = odooKeywords.some(keyword => userMessageLower.includes(keyword));
        const isCasual = casualPatterns.some(pattern => pattern.test(userMessage));
        const isPersonalInfo = personalInfoPatterns.some(pattern => pattern.test(userMessage));

        function generateCasualResponse() {
            addMessage('bot', '', true);

            setTimeout(() => {
                const responses = casualResponses.filter(response => typeof response === 'string');
                const response = responses[Math.floor(Math.random() * responses.length)];
                if (typeof response === 'string') {
                    addMessage('bot', response);
                } else {
                    console.error('Response is not a string:', response);
                }
            }, 1000);
        }

        function generatePersonalInfoResponse() {
            addMessage('bot', '', true);
            setTimeout(() => {
                const responses = personalInfoResponses.filter(response => typeof response === 'string');
                const response = responses[Math.floor(Math.random() * responses.length)];
                if (typeof response === 'string') {
                    addMessage('bot', response);
                } else {
                    console.error('Response is not a string:', response);
                }
            }, 1000);
        }

        function RedirectResponses() {
            addMessage('bot', '', true);

            setTimeout(() => {
                const responses = redirectResponses.filter(response => typeof response === 'string');
                const response = responses[Math.floor(Math.random() * responses.length)];
                if (typeof response === 'string') {
                    addMessage('bot', response);
                } else {
                    console.error('Response is not a string:', response);
                }
            }, 1000);
        }

        function generateOdooResponse(userMessage) {
            addMessage('bot', '', true);
            const promptText = `You are a highly intelligent AI model similar to ChatGPT. Provide a detailed, accurate, and concise answer to the following question: "${userMessage} in Odoo"`;

            console.log('Prompt text:', promptText);

            const requestBody = {
                question: promptText,
            };

            console.log('Request body:', JSON.stringify(requestBody));

            abortController = new AbortController();
            const signal = abortController.signal;

            return fetch('/groq_api', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody),
                signal: signal
            })
            .then(response => {
                console.log('HTTP response status:', response.status);
                console.log('HTTP response headers:', response.headers);

                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                console.log('API response data:', data);
                let responseMessage = data.message || 'I’m sorry, I couldn’t find an answer to your question. Please ask something related to Odoo for better assistance.';
                return responseMessage;
            })
            .catch(error => {
                if (error.name === 'AbortError') {
                    console.log("Fetch request aborted");
                    return 'The request was stopped by the user.';
                } else {
                    console.error('Error:', error);
                    return 'An error occurred while processing your request. Please try again later.';
                }
            });
        }

        if (isOdooRelated) {
            generateOdooResponse(userMessage).then(response => {
                const loadingElement = document.querySelector('.loader-wrapper');
                if (loadingElement) {
                    loadingElement.parentNode.parentNode.remove();
                }
                addMessage('bot', response);
            });
        } else if (isCasual) {
            const loadingElement = document.querySelector('.loader-wrapper');
            if (loadingElement) {
                loadingElement.parentNode.parentNode.remove();
            }
            addMessage('bot', generateCasualResponse());
        } else if (isPersonalInfo) {
            const loadingElement = document.querySelector('.loader-wrapper');
            if (loadingElement) {
                loadingElement.parentNode.parentNode.remove();
            }
            addMessage('bot', generatePersonalInfoResponse());
        } else {
            const loadingElement = document.querySelector('.loader-wrapper');
            if (loadingElement) {
                loadingElement.parentNode.parentNode.remove();
            }
            addMessage('bot', RedirectResponses());
        }
    }

    function forpagecontent(pageContent, message){
        const exitKeywords = [
            'bye'
        ];
        const goodbyeResponses = [
            'Goodbye! If you need any more help, just let me know. Have a wonderful day!',
        ];

        if (exitKeywords.some(keyword => message.toLowerCase().includes(keyword))) {
            const randomGoodbyeResponse = goodbyeResponses[Math.floor(Math.random() * goodbyeResponses.length)];
            addMessage('bot', randomGoodbyeResponse);
            closeChatbot();
            return;
        }

        const promptText = `You are a highly intelligent AI model similar to ChatGPT. Based on the provided page data: "${pageContent}", give a detailed, accurate, and concise answer to the following user message: "${message}" in Odoo. Ensure the response includes relevant details, is well-structured, and professional.`;
        console.log('Sending message:', message);
        addMessage('bot', '', true);
        const requestBody = {
            question: promptText,
        };

        return fetch('/page_content_data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log('page data output:', data);
            if (data && data.message) {
                const loadingElement = document.querySelector('.loader-wrapper');
                if (loadingElement) {
                    loadingElement.parentNode.parentNode.remove();
                }
                addMessage('bot', data.message);
                return data.message;
            } else {
                const errorMessage = 'I’m sorry, I couldn’t find an answer to your question. Please ask something related to Odoo for better assistance.';
                addMessage('bot', errorMessage);
                return errorMessage;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            const errorMessage = 'An error occurred while processing your request. Please try again later.';
            addMessage('bot', errorMessage);
            return errorMessage;
        });
    }

    chatBody.addEventListener('click', function(event) {
        if (event.target.classList.contains('copy-icon')) {
            const messageContent = event.target.parentElement.previousElementSibling.textContent.trim();
            copyToClipboard(messageContent);

            const originalSrc = event.target.src;
            event.target.src = "/ai_bot_odoopim/static/src/img/copied.svg";

            setTimeout(() => {
                event.target.src = originalSrc;
            }, 2000);
        }
    });

    function typeEffect(element, text, callback) {
        const typingSpeed = 20;
        let index = 0;
        const interval = setInterval(() => {
            if (index < text.length) {
                element.innerHTML += text.charAt(index);
                index++;
                chatBody.scrollTop = chatBody.scrollHeight;
            } else {
                clearInterval(interval);
                if (callback) callback();
            }
        }, typingSpeed);
    }

    function copyToClipboard(text) {
        const textarea = document.createElement('textarea');
        textarea.value = text;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
    }

    function scrapePageData() {
        if (toggleScrape && toggleScrape.checked) {
            hideBotElements();
            var elements = document.getElementsByClassName("o_content");
            var innerTexts = [];
            for (var i = 0; i < elements.length; i++) {
                innerTexts.push(elements[i].innerText);
                pageContent = innerTexts;
            }
            console.log('Updated Page Content:', pageContent);

            showBotElements();
            return pageContent;
        }
    }

    showBotElements();
    scrapePageData();
});