// AI-Powered Project Creation Enhancement
class AIProjectCreation {
    constructor() {
        this.initializeEventListeners();
        this.currentProjectData = {};
        this.analysisResults = {};
    }

    initializeEventListeners() {
        // Real-time pitch analysis
        const pitchFields = ['projectDescription', 'projectProblem', 'projectMarket', 'projectCompetition', 'projectDetails'];
        pitchFields.forEach(field => {
            const element = document.getElementById(field);
            if (element) {
                element.addEventListener('input', (e) => this.debounce(() => this.analyzeField(field, e.target.value), 1000));
            }
        });

        // Smart template loading
        const categorySelect = document.getElementById('category');
        const stageSelect = document.getElementById('stage');
        if (categorySelect && stageSelect) {
            categorySelect.addEventListener('change', () => this.loadSmartTemplates());
            stageSelect.addEventListener('change', () => this.loadSmartTemplates());
        }

        // AI enhancement button
        const enhanceButton = document.getElementById('enhance-project-btn');
        if (enhanceButton) {
            enhanceButton.addEventListener('click', () => this.enhanceProjectCreation());
        }

        // Field suggestions
        this.setupFieldSuggestions();
    }

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    async analyzeField(fieldName, value) {
        if (!value || value.trim().length < 10) return;

        try {
            const response = await fetch('/api/analyze-pitch/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ text: value })
            });

            const data = await response.json();
            if (data.success) {
                this.displayFieldAnalysis(fieldName, data.analysis);
            }
        } catch (error) {
            console.error('Error analyzing field:', error);
        }
    }

    displayFieldAnalysis(fieldName, analysis) {
        // Create or update analysis display
        let analysisContainer = document.getElementById(`${fieldName}-analysis`);
        if (!analysisContainer) {
            analysisContainer = document.createElement('div');
            analysisContainer.id = `${fieldName}-analysis`;
            analysisContainer.className = 'field-analysis mt-2';
            
            const fieldElement = document.getElementById(fieldName);
            if (fieldElement) {
                fieldElement.parentNode.insertBefore(analysisContainer, fieldElement.nextSibling);
            }
        }

        const scoreColor = analysis.score >= 70 ? 'success' : analysis.score >= 50 ? 'warning' : 'danger';
        
        // Get field display name
        const fieldDisplayNames = {
            'projectDescription': 'Description',
            'projectProblem': 'Problem',
            'projectMarket': 'Market',
            'projectCompetition': 'Competition',
            'projectDetails': 'Details'
        };
        
        const displayName = fieldDisplayNames[fieldName] || fieldName;
        
        analysisContainer.innerHTML = `
            <div class="alert alert-${scoreColor} alert-sm">
                <div class="d-flex justify-content-between align-items-center">
                    <strong>AI Score: ${analysis.score}/100</strong>
                    <small>${analysis.word_count} words</small>
                </div>
                <div class="mt-2">
                    ${analysis.feedback.map(feedback => `<div class="small">${feedback}</div>`).join('')}
                </div>
                ${analysis.suggestions.length > 0 ? `
                    <div class="mt-2">
                        <strong>Suggestions:</strong>
                        <ul class="mb-0 mt-1">
                            ${analysis.suggestions.map(suggestion => `<li class="small">${suggestion}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
            </div>
        `;
    }

    async loadSmartTemplates() {
        const category = document.getElementById('category')?.value;
        const stage = document.getElementById('stage')?.value;

        if (!category || !stage) return;

        try {
            const response = await fetch('/api/smart-templates/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ category, stage })
            });

            const data = await response.json();
            if (data.success) {
                this.displaySmartTemplates(data.templates);
            }
        } catch (error) {
            console.error('Error loading templates:', error);
        }
    }

    displaySmartTemplates(templates) {
        let templateContainer = document.getElementById('smart-templates');
        if (!templateContainer) {
            templateContainer = document.createElement('div');
            templateContainer.id = 'smart-templates';
            templateContainer.className = 'smart-templates mb-3';
            
            const form = document.getElementById('createProjectForm');
            if (form) {
                form.insertBefore(templateContainer, form.firstChild);
            }
        }

        templateContainer.innerHTML = `
            <div class="alert alert-info">
                <h6 class="alert-heading">🤖 AI-Generated Templates</h6>
                <p class="mb-2">Based on your category and stage, here are some suggested templates:</p>
                <div class="row">
                    ${Object.entries(templates).map(([field, template]) => `
                        <div class="col-md-6 mb-2">
                            <label class="form-label small">${field.charAt(0).toUpperCase() + field.slice(1)} Template:</label>
                            <textarea class="form-control form-control-sm" rows="2" readonly>${template}</textarea>
                            <button type="button" class="btn btn-sm btn-outline-primary mt-1" 
                                    onclick="aiProjectCreation.applyTemplate('${field}', \`${template}\`)">
                                Apply Template
                            </button>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    applyTemplate(fieldName, template) {
        const field = document.getElementById(fieldName);
        if (field) {
            field.value = template;
            field.dispatchEvent(new Event('input')); // Trigger analysis
        }
    }

    async enhanceProjectCreation() {
        const projectData = this.collectProjectData();
        
        // Debug: Log the collected data
        console.log('Project data being sent:', projectData);
        
        try {
            const response = await fetch('/api/enhance-project-creation/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ project_data: projectData })
            });

            const data = await response.json();
            console.log('API response:', data);
            
            if (data.success) {
                this.displayEnhancementResults(data.enhanced_data);
            } else {
                console.error('API returned success: false');
            }
        } catch (error) {
            console.error('Error enhancing project:', error);
        }
    }

    collectProjectData() {
        const fieldMapping = {
            'projectDescription': 'description',
            'projectProblem': 'problem',
            'projectMarket': 'market',
            'projectCompetition': 'competition',
            'projectDetails': 'details'
        };
        
        const data = {};
        
        Object.entries(fieldMapping).forEach(([fieldId, fieldName]) => {
            const element = document.getElementById(fieldId);
            if (element) {
                data[fieldName] = element.value || '';
            }
        });
        
        return data;
    }

    displayEnhancementResults(enhancedData) {
        let resultsContainer = document.getElementById('enhancement-results');
        if (!resultsContainer) {
            resultsContainer = document.createElement('div');
            resultsContainer.id = 'enhancement-results';
            resultsContainer.className = 'enhancement-results mb-3';
            
            // Find the Open Positions section and insert the analysis before it
            const addPositionsBtn = document.getElementById('addPositionsBtn');
            if (addPositionsBtn) {
                const openPositionsSection = addPositionsBtn.closest('.mb-3');
                if (openPositionsSection) {
                    openPositionsSection.insertAdjacentElement('beforebegin', resultsContainer);
                } else {
                    // Fallback: append to form
                    const form = document.getElementById('createProjectForm');
                    if (form) {
                        form.appendChild(resultsContainer);
                    }
                }
            } else {
                // Fallback: append to form
                const form = document.getElementById('createProjectForm');
                if (form) {
                    form.appendChild(resultsContainer);
                }
            }
        }

        const overallScore = enhancedData.overall?.score || 0;
        const scoreColor = overallScore >= 70 ? 'success' : overallScore >= 50 ? 'warning' : 'danger';

        resultsContainer.innerHTML = `
            <div class="alert alert-${scoreColor}">
                <h6 class="alert-heading">🎯 AI Project Analysis</h6>
                <div class="row">
                    <div class="col-md-6">
                        <strong>Overall Score: ${overallScore}/100</strong>
                        <div class="progress mt-2" style="height: 20px;">
                            <div class="progress-bar bg-${scoreColor}" style="width: ${overallScore}%"></div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <strong>Word Count:</strong> ${enhancedData.overall?.word_count || 0} words
                    </div>
                </div>
                
                ${enhancedData.overall?.feedback ? `
                    <div class="mt-3">
                        <strong>Feedback:</strong>
                        <ul class="mb-0 mt-1">
                            ${enhancedData.overall.feedback.map(feedback => `<li class="small">${feedback}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
                
                ${enhancedData.overall?.suggestions ? `
                    <div class="mt-3">
                        <strong>Suggestions:</strong>
                        <ul class="mb-0 mt-1">
                            ${enhancedData.overall.suggestions.map(suggestion => `<li class="small">${suggestion}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
            </div>
        `;
    }

    setupFieldSuggestions() {
        const fields = ['projectDescription', 'projectProblem', 'projectMarket', 'projectCompetition', 'projectDetails'];
        
        fields.forEach(field => {
            const element = document.getElementById(field);
            if (element) {
                element.addEventListener('focus', () => this.showFieldSuggestions(field));
                element.addEventListener('blur', () => this.hideFieldSuggestions(field));
            }
        });
    }

    async showFieldSuggestions(fieldName) {
        const currentValue = document.getElementById(fieldName)?.value || '';
        const otherFields = this.collectProjectData();
        
        // Map field ID back to field name for API
        const fieldMapping = {
            'projectDescription': 'description',
            'projectProblem': 'problem',
            'projectMarket': 'market',
            'projectCompetition': 'competition',
            'projectDetails': 'details'
        };
        
        const apiFieldName = fieldMapping[fieldName] || fieldName;
        delete otherFields[apiFieldName];

        try {
            const response = await fetch('/api/field-suggestions/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    field: apiFieldName,
                    current_value: currentValue,
                    other_fields: otherFields
                })
            });

            const data = await response.json();
            if (data.success) {
                this.displayFieldSuggestions(fieldName, data.suggestions);
            }
        } catch (error) {
            console.error('Error getting field suggestions:', error);
        }
    }

    displayFieldSuggestions(fieldName, suggestions) {
        let suggestionsContainer = document.getElementById(`${fieldName}-suggestions`);
        if (!suggestionsContainer) {
            suggestionsContainer = document.createElement('div');
            suggestionsContainer.id = `${fieldName}-suggestions`;
            suggestionsContainer.className = 'field-suggestions mt-2';
            
            const fieldElement = document.getElementById(fieldName);
            if (fieldElement) {
                fieldElement.parentNode.insertBefore(suggestionsContainer, fieldElement.nextSibling);
            }
        }

        // Get field display name
        const fieldDisplayNames = {
            'projectDescription': 'Description',
            'projectProblem': 'Problem',
            'projectMarket': 'Market',
            'projectCompetition': 'Competition',
            'projectDetails': 'Details'
        };
        
        const displayName = fieldDisplayNames[fieldName] || fieldName;

        suggestionsContainer.innerHTML = `
            <div class="alert alert-info alert-sm">
                <strong>💡 AI Suggestions for ${displayName}:</strong>
                <ul class="mb-0 mt-1">
                    ${suggestions.suggestions.map(suggestion => `<li class="small">${suggestion}</li>`).join('')}
                </ul>
                ${suggestions.template ? `
                    <div class="mt-2">
                        <strong>Template:</strong>
                        <div class="small text-muted">${suggestions.template}</div>
                    </div>
                ` : ''}
            </div>
        `;
    }

    hideFieldSuggestions(fieldName) {
        const suggestionsContainer = document.getElementById(`${fieldName}-suggestions`);
        if (suggestionsContainer) {
            setTimeout(() => {
                suggestionsContainer.remove();
            }, 200);
        }
    }

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
               document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1] || '';
    }

    clearAnalysis() {
        const resultsContainer = document.getElementById('enhancement-results');
        if (resultsContainer) {
            resultsContainer.remove();
        }
        
        // Clear field analysis containers
        const fields = ['projectDescription', 'projectProblem', 'projectMarket', 'projectCompetition', 'projectDetails'];
        fields.forEach(field => {
            const analysisContainer = document.getElementById(`${field}-analysis`);
            if (analysisContainer) {
                analysisContainer.remove();
            }
            
            const suggestionsContainer = document.getElementById(`${field}-suggestions`);
            if (suggestionsContainer) {
                suggestionsContainer.remove();
            }
        });
        
        // Clear smart templates
        const templateContainer = document.getElementById('smart-templates');
        if (templateContainer) {
            templateContainer.remove();
        }
    }
}

// Initialize AI Project Creation
const aiProjectCreation = new AIProjectCreation();

// Export for global access
window.aiProjectCreation = aiProjectCreation;

// Clear AI analysis when modal is closed
document.addEventListener('DOMContentLoaded', function() {
    const createProjectModal = document.getElementById('createProjectModal');
    if (createProjectModal) {
        // Listen for modal hidden event
        createProjectModal.addEventListener('hidden.bs.modal', function() {
            if (window.aiProjectCreation) {
                window.aiProjectCreation.clearAnalysis();
            }
        });
        
        // Also listen for modal show event to clear any existing analysis
        createProjectModal.addEventListener('show.bs.modal', function() {
            if (window.aiProjectCreation) {
                window.aiProjectCreation.clearAnalysis();
            }
        });
    }
    
    // Also clear analysis when the page loads
    if (window.aiProjectCreation) {
        window.aiProjectCreation.clearAnalysis();
    }
}); 