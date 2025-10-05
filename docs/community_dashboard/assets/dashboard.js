/**
 * StillMe AI Community Dashboard - JavaScript
 * Handles real-time voting, proposal submission, and community interaction
 */

class CommunityDashboard {
    constructor() {
        this.apiBase = '/api/community'; // Will be replaced with actual API endpoint
        this.proposals = [];
        this.contributors = [];
        this.userVotes = new Map(); // Track user votes to prevent double voting
        
        this.init();
    }

    async init() {
        console.log('🎯 Initializing StillMe Community Dashboard...');
        
        // Load initial data
        await this.loadDashboardData();
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Start real-time updates
        this.startRealTimeUpdates();
        
        console.log('✅ Dashboard initialized successfully!');
    }

    async loadDashboardData() {
        try {
            // Load statistics
            await this.loadStatistics();
            
            // Load active proposals
            await this.loadProposals();
            
            // Load contributors
            await this.loadContributors();
            
            // Load recent activity
            await this.loadRecentActivity();
            
        } catch (error) {
            console.error('❌ Error loading dashboard data:', error);
            this.showError('Failed to load dashboard data. Please refresh the page.');
        }
    }

    async loadStatistics() {
        try {
            // Mock data - replace with actual API calls
            const stats = {
                activeProposals: 12,
                totalVotes: 156,
                approvedToday: 3,
                communityMembers: 89
            };
            
            document.getElementById('active-proposals').textContent = stats.activeProposals;
            document.getElementById('total-votes').textContent = stats.totalVotes;
            document.getElementById('approved-today').textContent = stats.approvedToday;
            document.getElementById('community-members').textContent = stats.communityMembers;
            
        } catch (error) {
            console.error('Error loading statistics:', error);
        }
    }

    async loadProposals() {
        try {
            // Mock data - replace with actual API calls
            const mockProposals = [
                {
                    id: 'prop-001',
                    title: 'Learn Advanced Python Async Programming',
                    description: 'StillMe should master async/await patterns, asyncio library, and concurrent programming in Python to handle modern web applications efficiently.',
                    author: 'python_dev_2024',
                    category: 'programming',
                    upvotes: 23,
                    downvotes: 2,
                    createdAt: '2024-01-15T10:30:00Z',
                    status: 'voting',
                    learningObjectives: [
                        'Master asyncio library fundamentals',
                        'Implement async web scraping',
                        'Build concurrent API clients',
                        'Understand async database operations'
                    ]
                },
                {
                    id: 'prop-002',
                    title: 'Master Machine Learning Model Deployment',
                    description: 'Learn to deploy ML models in production using Docker, Kubernetes, and cloud platforms like AWS SageMaker and Google Cloud AI Platform.',
                    author: 'ml_engineer',
                    category: 'ai-ml',
                    upvotes: 18,
                    downvotes: 1,
                    createdAt: '2024-01-14T15:45:00Z',
                    status: 'voting',
                    learningObjectives: [
                        'Containerize ML models with Docker',
                        'Deploy on Kubernetes clusters',
                        'Implement model versioning',
                        'Set up monitoring and logging'
                    ]
                },
                {
                    id: 'prop-003',
                    title: 'Learn DevOps Best Practices',
                    description: 'Master CI/CD pipelines, infrastructure as code, monitoring, and security practices for modern software development.',
                    author: 'devops_guru',
                    category: 'devops',
                    upvotes: 31,
                    downvotes: 0,
                    createdAt: '2024-01-13T09:20:00Z',
                    status: 'voting',
                    learningObjectives: [
                        'Implement GitOps workflows',
                        'Master Terraform for IaC',
                        'Set up monitoring with Prometheus',
                        'Implement security scanning'
                    ]
                }
            ];
            
            this.proposals = mockProposals;
            this.renderProposals();
            
        } catch (error) {
            console.error('Error loading proposals:', error);
            document.getElementById('proposals-list').innerHTML = '<div class="error">Failed to load proposals. Please try again later.</div>';
        }
    }

    renderProposals() {
        const container = document.getElementById('proposals-list');
        
        if (this.proposals.length === 0) {
            container.innerHTML = '<div class="loading">No active proposals at the moment.</div>';
            return;
        }
        
        const proposalsHtml = this.proposals.map(proposal => {
            const progressPercentage = Math.min((proposal.upvotes / 50) * 100, 100);
            const userVote = this.userVotes.get(proposal.id) || 'none';
            
            return `
                <div class="proposal-card" data-proposal-id="${proposal.id}">
                    <div class="proposal-title">${proposal.title}</div>
                    <div class="proposal-meta">
                        👤 ${proposal.author} • 📅 ${this.formatDate(proposal.createdAt)} • 🏷️ ${proposal.category}
                    </div>
                    <div class="proposal-description">${proposal.description}</div>
                    
                    <div class="voting-section">
                        <div class="vote-buttons">
                            <button class="vote-btn upvote-btn ${userVote === 'up' ? 'active' : ''}" 
                                    onclick="dashboard.voteProposal('${proposal.id}', 'up')"
                                    ${userVote === 'up' ? 'disabled' : ''}>
                                👍 ${proposal.upvotes}
                            </button>
                            <button class="vote-btn downvote-btn ${userVote === 'down' ? 'active' : ''}" 
                                    onclick="dashboard.voteProposal('${proposal.id}', 'down')"
                                    ${userVote === 'down' ? 'disabled' : ''}>
                                👎 ${proposal.downvotes}
                            </button>
                        </div>
                        <div class="vote-count">
                            ${proposal.upvotes} / 50 votes needed
                        </div>
                    </div>
                    
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${progressPercentage}%"></div>
                    </div>
                </div>
            `;
        }).join('');
        
        container.innerHTML = proposalsHtml;
    }

    async loadContributors() {
        try {
            // Mock data - replace with actual API calls
            const mockContributors = [
                { rank: 1, username: 'ai_researcher', proposals: 8, votes: 156, avatar: '🤖' },
                { rank: 2, username: 'python_dev_2024', proposals: 6, votes: 134, avatar: '🐍' },
                { rank: 3, username: 'ml_engineer', proposals: 5, votes: 98, avatar: '🧠' },
                { rank: 4, username: 'devops_guru', proposals: 4, votes: 87, avatar: '⚙️' },
                { rank: 5, username: 'data_scientist', proposals: 3, votes: 76, avatar: '📊' }
            ];
            
            this.contributors = mockContributors;
            this.renderContributors();
            
        } catch (error) {
            console.error('Error loading contributors:', error);
        }
    }

    renderContributors() {
        const container = document.getElementById('contributors-list');
        
        const contributorsHtml = this.contributors.map(contributor => `
            <div class="leaderboard-item">
                <div class="leaderboard-rank">${contributor.rank}</div>
                <div class="leaderboard-info">
                    <div class="leaderboard-name">${contributor.avatar} ${contributor.username}</div>
                    <div class="leaderboard-stats">${contributor.proposals} proposals • ${contributor.votes} votes</div>
                </div>
            </div>
        `).join('');
        
        container.innerHTML = contributorsHtml;
    }

    async loadRecentActivity() {
        try {
            // Mock data - replace with actual API calls
            const mockActivity = [
                { type: 'approved', message: 'Proposal "Learn React Hooks" was approved!', time: '2 hours ago' },
                { type: 'voted', message: 'New vote on "Master Docker" proposal', time: '4 hours ago' },
                { type: 'submitted', message: 'New proposal "Learn GraphQL" submitted', time: '6 hours ago' },
                { type: 'approved', message: 'Proposal "Python Async" was approved!', time: '1 day ago' }
            ];
            
            const activityHtml = mockActivity.map(activity => `
                <div class="leaderboard-item">
                    <div class="leaderboard-info">
                        <div class="leaderboard-name">${activity.message}</div>
                        <div class="leaderboard-stats">${activity.time}</div>
                    </div>
                </div>
            `).join('');
            
            document.getElementById('recent-activity').innerHTML = activityHtml;
            
        } catch (error) {
            console.error('Error loading recent activity:', error);
        }
    }

    setupEventListeners() {
        // Proposal form submission
        document.getElementById('proposal-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.submitProposal();
        });
        
        // Real-time updates every 30 seconds
        setInterval(() => {
            this.loadDashboardData();
        }, 30000);
    }

    async submitProposal() {
        const form = document.getElementById('proposal-form');
        const formData = new FormData(form);
        
        const proposal = {
            title: document.getElementById('title').value,
            description: document.getElementById('description').value,
            objectives: document.getElementById('objectives').value.split('\n').filter(obj => obj.trim()),
            category: document.getElementById('category').value,
            author: this.getCurrentUser() || 'anonymous'
        };
        
        try {
            // Show loading state
            const submitBtn = form.querySelector('.submit-btn');
            const originalText = submitBtn.textContent;
            submitBtn.textContent = '⏳ Submitting...';
            submitBtn.disabled = true;
            
            // Mock API call - replace with actual API
            await this.mockApiCall('/api/proposals', 'POST', proposal);
            
            // Show success message
            this.showSuccess('🎉 Proposal submitted successfully! It will appear in the voting list shortly.');
            
            // Reset form
            form.reset();
            
            // Reload proposals
            await this.loadProposals();
            
        } catch (error) {
            console.error('Error submitting proposal:', error);
            this.showError('Failed to submit proposal. Please try again.');
        } finally {
            // Reset button
            const submitBtn = form.querySelector('.submit-btn');
            submitBtn.textContent = originalText;
            submitBtn.disabled = false;
        }
    }

    async voteProposal(proposalId, voteType) {
        try {
            // Check if user already voted
            if (this.userVotes.has(proposalId)) {
                this.showError('You have already voted on this proposal.');
                return;
            }
            
            // Mock API call - replace with actual API
            await this.mockApiCall(`/api/proposals/${proposalId}/vote`, 'POST', { voteType });
            
            // Update local state
            this.userVotes.set(proposalId, voteType);
            
            // Update proposal in local data
            const proposal = this.proposals.find(p => p.id === proposalId);
            if (proposal) {
                if (voteType === 'up') {
                    proposal.upvotes++;
                } else {
                    proposal.downvotes++;
                }
            }
            
            // Re-render proposals
            this.renderProposals();
            
            // Show success message
            this.showSuccess(`✅ Vote recorded! Thank you for participating.`);
            
        } catch (error) {
            console.error('Error voting on proposal:', error);
            this.showError('Failed to record vote. Please try again.');
        }
    }

    startRealTimeUpdates() {
        // In a real implementation, this would use WebSockets or Server-Sent Events
        console.log('🔄 Starting real-time updates...');
    }

    // Utility functions
    formatDate(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
        
        if (diffDays === 0) {
            return 'Today';
        } else if (diffDays === 1) {
            return 'Yesterday';
        } else {
            return `${diffDays} days ago`;
        }
    }

    getCurrentUser() {
        // In a real implementation, this would get the current user from authentication
        return 'community_member';
    }

    async mockApiCall(url, method, data) {
        // Mock API call with random delay
        await new Promise(resolve => setTimeout(resolve, Math.random() * 1000 + 500));
        
        // Simulate occasional failures
        if (Math.random() < 0.1) {
            throw new Error('Mock API error');
        }
        
        return { success: true, data };
    }

    showSuccess(message) {
        const container = document.querySelector('.main-content');
        const alert = document.createElement('div');
        alert.className = 'success';
        alert.textContent = message;
        container.insertBefore(alert, container.firstChild);
        
        setTimeout(() => {
            alert.remove();
        }, 5000);
    }

    showError(message) {
        const container = document.querySelector('.main-content');
        const alert = document.createElement('div');
        alert.className = 'error';
        alert.textContent = message;
        container.insertBefore(alert, container.firstChild);
        
        setTimeout(() => {
            alert.remove();
        }, 5000);
    }
}

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new CommunityDashboard();
});

// Add some CSS for active vote states
const style = document.createElement('style');
style.textContent = `
    .vote-btn.active {
        transform: scale(1.1);
        box-shadow: 0 0 10px rgba(102, 126, 234, 0.5);
    }
    
    .vote-btn:disabled {
        opacity: 0.6;
        cursor: not-allowed;
    }
`;
document.head.appendChild(style);
