/**
 * StillMe Community Dashboard JavaScript
 * =====================================
 * Handles all frontend interactions with StillMe API
 */

class StillMeDashboard {
    constructor() {
        this.apiUrl = 'https://your-stillme-server.com/api'; // Replace with your actual server URL
        this.userId = this.generateUserId();
        this.voteThreshold = 50;
        this.isLoading = false;
        
        this.init();
    }

    init() {
        console.log('StillMe Dashboard initialized');
        this.loadLearningProgress();
        this.loadLessons();
        this.setupEventListeners();
    }

    generateUserId() {
        // Generate a unique user ID for this session
        return 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    setupEventListeners() {
        // Chat input enter key
        const messageInput = document.getElementById('messageInput');
        if (messageInput) {
            messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
        }

        // Auto-refresh data every 30 seconds
        setInterval(() => {
            this.loadLearningProgress();
            this.loadLessons();
        }, 30000);
    }

    async loadLearningProgress() {
        try {
            const response = await fetch(`${this.apiUrl}/progress`);
            const data = await response.json();
            
            this.updateProgressDisplay(data);
        } catch (error) {
            console.error('Error loading progress:', error);
            this.showError('Failed to load learning progress');
        }
    }

    updateProgressDisplay(progress) {
        // Update progress bar
        const progressFill = document.querySelector('.progress-fill');
        if (progressFill) {
            progressFill.style.width = `${progress.progress_percentage}%`;
        }

        // Update progress text
        const progressText = document.querySelector('.learning-progress p');
        if (progressText) {
            progressText.innerHTML = `
                <strong>Currently learning:</strong> ${progress.current_lesson}<br>
                <strong>Completed:</strong> ${progress.completed_lessons} lessons<br>
                <strong>Total:</strong> ${progress.total_lessons} lessons
            `;
        }
    }

    async loadLessons() {
        try {
            const response = await fetch(`${this.apiUrl}/lessons`);
            const lessons = await response.json();
            
            this.updateLessonsDisplay(lessons);
        } catch (error) {
            console.error('Error loading lessons:', error);
            this.showError('Failed to load lessons');
        }
    }

    updateLessonsDisplay(lessons) {
        const votingSystem = document.querySelector('.voting-system');
        if (!votingSystem) return;

        // Clear existing lesson cards
        const existingCards = votingSystem.querySelectorAll('.lesson-card');
        existingCards.forEach(card => card.remove());

        // Add lesson cards
        lessons.forEach(lesson => {
            const lessonCard = this.createLessonCard(lesson);
            votingSystem.appendChild(lessonCard);
        });
    }

    createLessonCard(lesson) {
        const card = document.createElement('div');
        card.className = 'lesson-card';
        card.setAttribute('data-lesson', lesson.id);

        const isCompleted = lesson.status === 'completed';
        const isLearning = lesson.status === 'learning';
        const canVote = lesson.status === 'pending' && lesson.votes < this.voteThreshold;

        card.innerHTML = `
            <h3>${this.getLessonIcon(lesson.title)} ${lesson.title}</h3>
            <p>${lesson.description}</p>
            <div class="vote-count ${isCompleted ? 'completed' : ''}">
                ${isCompleted ? '✅ Completed' : 
                  isLearning ? '🔄 Learning...' : 
                  `Votes: ${lesson.votes}/${this.voteThreshold}`}
            </div>
            ${canVote ? 
                `<button class="vote-btn" onclick="dashboard.voteForLesson(${lesson.id})">Vote Now</button>` :
                isCompleted ? 
                `<button class="vote-btn completed" disabled>Completed</button>` :
                `<button class="vote-btn learning" disabled>Learning...</button>`
            }
        `;

        return card;
    }

    getLessonIcon(title) {
        const icons = {
            'AI Ethics': '🤖',
            'Machine Learning': '🧠',
            'Web Development': '🌐',
            'Python': '🐍',
            'JavaScript': '📜',
            'Data Science': '📊',
            'Security': '🔒',
            'DevOps': '⚙️'
        };

        for (const [keyword, icon] of Object.entries(icons)) {
            if (title.includes(keyword)) {
                return icon;
            }
        }
        return '📚';
    }

    async voteForLesson(lessonId) {
        if (this.isLoading) return;

        this.isLoading = true;
        const button = document.querySelector(`[data-lesson="${lessonId}"] .vote-btn`);
        const originalText = button.textContent;
        button.textContent = 'Voting...';
        button.disabled = true;

        try {
            const response = await fetch(`${this.apiUrl}/vote`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    lesson_id: lessonId,
                    user_id: this.userId
                })
            });

            const data = await response.json();

            if (data.status === 'learning_started') {
                this.showSuccess(data.message);
                // Reload lessons to show updated status
                setTimeout(() => this.loadLessons(), 1000);
            } else if (data.status === 'already_voted') {
                this.showWarning(data.message);
            } else {
                this.showSuccess(data.message);
                // Update vote count locally
                this.updateVoteCount(lessonId, data.votes);
            }

        } catch (error) {
            console.error('Error voting:', error);
            this.showError('Failed to vote. Please try again.');
        } finally {
            this.isLoading = false;
            button.textContent = originalText;
            button.disabled = false;
        }
    }

    updateVoteCount(lessonId, voteCount) {
        const lessonCard = document.querySelector(`[data-lesson="${lessonId}"]`);
        if (lessonCard) {
            const voteCountElement = lessonCard.querySelector('.vote-count');
            voteCountElement.textContent = `Votes: ${voteCount}/${this.voteThreshold}`;
            
            if (voteCount >= this.voteThreshold) {
                voteCountElement.style.color = '#4caf50';
                voteCountElement.textContent = '🎉 Learning Started!';
            }
        }
    }

    async sendMessage() {
        const input = document.getElementById('messageInput');
        const message = input.value.trim();
        
        if (!message || this.isLoading) return;

        this.isLoading = true;
        input.value = '';

        // Add user message to chat
        this.addMessageToChat(message, 'user');

        // Show typing indicator
        const typingId = this.addTypingIndicator();

        try {
            const response = await fetch(`${this.apiUrl}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    user_id: this.userId
                })
            });

            const data = await response.json();
            
            // Remove typing indicator
            this.removeTypingIndicator(typingId);
            
            // Add StillMe response
            this.addMessageToChat(data.response, 'stillme');
            
            // Update model info
            this.updateModelInfo(data.model, data.latency, data.timestamp);
            
        } catch (error) {
            console.error('Error chatting:', error);
            this.removeTypingIndicator(typingId);
            this.addMessageToChat('Sorry, I encountered an error. Please try again.', 'stillme');
            this.showError('Failed to send message. Please try again.');
        } finally {
            this.isLoading = false;
        }
    }

    addMessageToChat(message, sender) {
        const chatMessages = document.getElementById('chatMessages');
        if (!chatMessages) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        
        const senderName = sender === 'user' ? 'You' : 'StillMe';
        const timestamp = new Date().toLocaleTimeString();
        
        messageDiv.innerHTML = `
            <div class="message-header">
                <strong>${senderName}</strong>
                <span class="timestamp">${timestamp}</span>
            </div>
            <div class="message-content">${this.escapeHtml(message)}</div>
        `;
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    addTypingIndicator() {
        const chatMessages = document.getElementById('chatMessages');
        if (!chatMessages) return null;

        const typingDiv = document.createElement('div');
        typingDiv.className = 'message stillme typing-indicator';
        typingDiv.id = 'typing-' + Date.now();
        typingDiv.innerHTML = `
            <div class="message-header">
                <strong>StillMe</strong>
                <span class="timestamp">typing...</span>
            </div>
            <div class="message-content">
                <span class="typing-dots">
                    <span>.</span><span>.</span><span>.</span>
                </span>
            </div>
        `;
        
        chatMessages.appendChild(typingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        return typingDiv.id;
    }

    removeTypingIndicator(typingId) {
        if (typingId) {
            const typingElement = document.getElementById(typingId);
            if (typingElement) {
                typingElement.remove();
            }
        }
    }

    updateModelInfo(model, latency, timestamp) {
        const modelInfo = document.querySelector('.model-info');
        if (modelInfo) {
            const formattedTime = new Date(timestamp).toLocaleString();
            modelInfo.innerHTML = `
                <span>🤖 Model: ${model}</span>
                <span>⚡ Latency: ${latency}s</span>
                <span>🕒 Last updated: ${formattedTime}</span>
            `;
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showWarning(message) {
        this.showNotification(message, 'warning');
    }

    showNotification(message, type) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        // Add styles
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 8px;
            color: white;
            font-weight: 500;
            z-index: 1000;
            max-width: 300px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            transform: translateX(100%);
            transition: transform 0.3s ease;
        `;

        // Set background color based on type
        switch (type) {
            case 'success':
                notification.style.backgroundColor = '#4caf50';
                break;
            case 'error':
                notification.style.backgroundColor = '#f44336';
                break;
            case 'warning':
                notification.style.backgroundColor = '#ff9800';
                break;
        }

        // Add to page
        document.body.appendChild(notification);

        // Animate in
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 100);

        // Remove after 3 seconds
        setTimeout(() => {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }
}

// Global functions for HTML onclick handlers
let dashboard;

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    dashboard = new StillMeDashboard();
});

// Global functions for backward compatibility
function voteForLesson(lessonId) {
    if (dashboard) {
        dashboard.voteForLesson(lessonId);
    }
}

function sendMessage() {
    if (dashboard) {
        dashboard.sendMessage();
    }
}

function handleKeyPress(event) {
    if (event.key === 'Enter' && dashboard) {
        dashboard.sendMessage();
    }
}
