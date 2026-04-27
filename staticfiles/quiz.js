document.addEventListener('DOMContentLoaded', () => {
    // Quiz questions data
    const quizData = [
      {
        id: 1,
        question: "What is a minimum viable product (MVP)?",
        options: [
          "A product with minimal features but can still be sold",
          "The smallest possible version of a product that can still solve the core problem",
          "A prototype that is not meant for customers",
          "A product that has passed minimum quality testing"
        ],
        correctAnswer: 1
      },
      {
        id: 2,
        question: "What does 'bootstrapping' mean in startup context?",
        options: [
          "Using advanced technology to accelerate growth",
          "Starting a business with venture capital funding",
          "Building a business without external funding",
          "Creating a business based on another successful model"
        ],
        correctAnswer: 2
      },
      {
        id: 3,
        question: "What is a pivot in startup terminology?",
        options: [
          "Moving company headquarters to a new location",
          "A significant change in business strategy",
          "Hiring a new CEO",
          "Achieving break-even point"
        ],
        correctAnswer: 1
      },
      {
        id: 4,
        question: "What is a 'unicorn' in the startup world?",
        options: [
          "A startup founded by a single person",
          "A startup with a mythical business model",
          "A privately held startup valued at over $1 billion",
          "A startup that has no competition"
        ],
        correctAnswer: 2
      },
      {
        id: 5,
        question: "What is 'burn rate' in startup finance?",
        options: [
          "The rate at which a company depletes its cash reserves",
          "How quickly a product sells out after launch",
          "The rate of employee turnover",
          "How quickly technology becomes obsolete"
        ],
        correctAnswer: 0
      },
      {
        id: 6,
        question: "What is a 'pitch deck'?",
        options: [
          "A physical space where startups present their ideas",
          "A series of outdoor presentations",
          "A presentation used to pitch to investors",
          "A collection of business cards from potential investors"
        ],
        correctAnswer: 2
      },
      {
        id: 7,
        question: "What does 'B2B' stand for?",
        options: [
          "Back to Business",
          "Business to Business",
          "Broker to Buyer",
          "Build to Budget"
        ],
        correctAnswer: 1
      },
      {
        id: 8,
        question: "What is 'customer acquisition cost' (CAC)?",
        options: [
          "The cost of retaining existing customers",
          "The cost of buying a competitor's customers",
          "The cost of a customer's first purchase",
          "The cost of acquiring a new customer"
        ],
        correctAnswer: 3
      },
      {
        id: 9,
        question: "What is a 'term sheet'?",
        options: [
          "A list of product features",
          "A non-binding agreement outlining investment terms",
          "A schedule for product development",
          "A contract between co-founders"
        ],
        correctAnswer: 1
      },
      {
        id: 10,
        question: "What is 'churn rate'?",
        options: [
          "The rate at which employees leave a company",
          "The rate of producing new products",
          "The rate at which customers stop using a product/service",
          "The rate of converting leads to customers"
        ],
        correctAnswer: 2
      },
      {
        id: 11,
        question: "What is 'market validation'?",
        options: [
          "Getting investors to validate your idea",
          "Confirming there is actual demand for your product",
          "Passing legal requirements for entering a market",
          "Receiving approval from industry regulators"
        ],
        correctAnswer: 1
      },
      {
        id: 12,
        question: "What is a 'venture capitalist'?",
        options: [
          "A wealthy individual who invests in startups",
          "A professional who manages a fund that invests in startups",
          "A government official who regulates startups",
          "A consultant who specializes in capital markets"
        ],
        correctAnswer: 1
      },
      {
        id: 13,
        question: "What is 'product-market fit'?",
        options: [
          "When a product meets the needs of a market",
          "When a product fits within market regulations",
          "When a product competes well against others in the market",
          "When a product can be manufactured at market price"
        ],
        correctAnswer: 0
      },
      {
        id: 14,
        question: "What is an 'angel investor'?",
        options: [
          "A charitable organization that funds startups",
          "A wealthy individual who personally invests in early-stage startups",
          "A foreign investor who doesn't require citizenship",
          "An investor who only funds ethical businesses"
        ],
        correctAnswer: 1
      },
      {
        id: 15,
        question: "What is 'freemium' business model?",
        options: [
          "Giving products away for free to build brand awareness",
          "Offering a basic service for free while charging for premium features",
          "Providing free trials before requiring payment",
          "Operating at a loss to gain market share"
        ],
        correctAnswer: 1
      }
    ];
    
    // Quiz state variables
    let currentQuestion = 0;
    let selectedOption = null;
    let score = 0;
    let showResult = false;
    let answers = Array(quizData.length).fill(-1);
    let revealAnswer = false;
    let quizStarted = false;
    
    // DOM Elements
    const quizContainer = document.getElementById('quiz-container');
    
    // Initialize the quiz
    initializeQuiz();
    
    function initializeQuiz() {
      renderIntroScreen();
    }
    
    function renderIntroScreen() {
      quizContainer.innerHTML = `
        <div class="quiz-card intro-screen">
          <div class="quiz-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="award-icon">
              <circle cx="12" cy="8" r="7"></circle>
              <polyline points="8.21 13.89 7 23 12 20 17 23 15.79 13.88"></polyline>
            </svg>
          </div>
          <h1>Startup Readiness Quiz</h1>
          <p>
            Assess your preparedness to start your entrepreneurial journey with this 15-question quiz
            covering key startup concepts and knowledge.
          </p>
          <div class="quiz-info">
            <div>
              <span class="info-label">Total Questions:</span>
              <span class="info-value">${quizData.length}</span>
            </div>
            <div>
              <span class="info-label">Estimated Time:</span>
              <span class="info-value">~5 minutes</span>
            </div>
          </div>
          <button id="start-quiz" class="quiz-button">
            Start Quiz
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M5 12h14"></path>
              <path d="m12 5 7 7-7 7"></path>
            </svg>
          </button>
        </div>
      `;
      
      document.getElementById('start-quiz').addEventListener('click', startQuiz);
    }
    
    function startQuiz() {
      quizStarted = true;
     
      renderQuestion();
    }
    
    function renderQuestion() {
      const question = quizData[currentQuestion];
      const progressPercentage = ((currentQuestion + 1) / quizData.length) * 100;
      
      quizContainer.innerHTML = `
        <div class="quiz-card question-screen animate-scale-in">
          <div class="quiz-header">
            <div class="quiz-progress">
              <span>Question ${currentQuestion + 1} of ${quizData.length}</span>
              <span>Score: ${score}</span>
            </div>
            <div class="progress-bar">
              <div class="progress-value" style="width: ${progressPercentage}%"></div>
            </div>
          </div>
          
          <h2>${question.question}</h2>
          
          <div class="options-container">
            ${question.options.map((option, index) => `
              <div class="quiz-option" data-index="${index}">
                <div class="option-content">
                  <div class="option-marker">${String.fromCharCode(65 + index)}</div>
                  <div>${option}</div>
                </div>
              </div>
            `).join('')}
          </div>
          
          <div class="quiz-footer">
            <button id="next-question" class="quiz-button" disabled>
              ${currentQuestion < quizData.length - 1 ? 'Next' : 'Finish'}
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="9 18 15 12 9 6"></polyline>
              </svg>
            </button>
          </div>
        </div>
      `;
      
      // Add event listeners to options
      const options = document.querySelectorAll('.quiz-option');
      options.forEach(option => {
        option.addEventListener('click', () => {
          if (revealAnswer) return;
          
          // Remove selected class from all options
          options.forEach(opt => opt.classList.remove('selected'));
          
          // Add selected class to clicked option
          option.classList.add('selected');
          
          // Update selected option
          selectedOption = parseInt(option.dataset.index);
          
          // Enable next button
          document.getElementById('next-question').removeAttribute('disabled');
        });
      });
      
      // Add event listener to next button
      document.getElementById('next-question').addEventListener('click', handleNextQuestion);
    }
    
    function handleNextQuestion() {
      // Save the answer
      answers[currentQuestion] = selectedOption;
      
      // Check if answer is correct
      if (selectedOption === quizData[currentQuestion].correctAnswer) {
        score++;
      }
      
      revealAnswer = true;
      
      // Show correct/incorrect feedback
      const options = document.querySelectorAll('.quiz-option');
      const correctIndex = quizData[currentQuestion].correctAnswer;
      
      options[correctIndex].classList.add('correct');
      if (selectedOption !== correctIndex) {
        options[selectedOption].classList.add('incorrect');
      }
      
      // Disable next button during animation
      document.getElementById('next-question').setAttribute('disabled', 'true');
      
      // Delay to next question to show the correct/incorrect animation
      setTimeout(() => {
        revealAnswer = false;
        selectedOption = null;
        
        if (currentQuestion < quizData.length - 1) {
          currentQuestion++;
          renderQuestion();
        } else {
          showResult = true;
          renderResult();
        }
      }, 1500);
    }
    
    function renderResult() {
      const percentage = calculatePercentage();
      const feedback = getFeedback(percentage);
      const scoreColor = getScoreColor(percentage);
      
      quizContainer.innerHTML = `
        <div class="quiz-card result-screen animate-scale-in">
          <div class="quiz-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="award-icon">
              <circle cx="12" cy="8" r="7"></circle>
              <polyline points="8.21 13.89 7 23 12 20 17 23 15.79 13.88"></polyline>
            </svg>
          </div>
          <h1>Quiz Results</h1>
          
          <div class="result-stats">
            <div class="score">
              <span class="current-score ${scoreColor}">${score}</span>
              <span class="total-score">/${quizData.length}</span>
            </div>
            <p class="feedback">${feedback}</p>
            <div class="score-progress">
              <div class="progress-bar">
                <div class="progress-value" style="width: ${percentage}%"></div>
              </div>
              <p class="percentage">You scored ${percentage.toFixed(0)}%</p>
            </div>
          </div>
          
          <p class="result-message">
            ${percentage >= 70 
              ? "Great job! You have a solid understanding of startup concepts."
              : "Continue learning about startups to improve your knowledge!"}
          </p>
          
          <div class="result-actions">
            <button id="restart-quiz" class="quiz-button">
              Try Again
            </button>
            <button id="back-home" class="quiz-button outline">
              Back to Home
            </button>
          </div>
        </div>
      `;
      
      document.getElementById('restart-quiz').addEventListener('click', restartQuiz);
      document.getElementById('back-home').addEventListener('click', () => {
        window.location.href = '/';
      });
    }
    
    function restartQuiz() {
      currentQuestion = 0;
      selectedOption = null;
      score = 0;
      showResult = false;
      answers = Array(quizData.length).fill(-1);
      revealAnswer = false;
      
    
      renderQuestion();
    }
    
    function calculatePercentage() {
      return (score / quizData.length) * 100;
    }
    
    function getFeedback(percentage) {
      if (percentage >= 90) return "Startup Expert!";
      if (percentage >= 75) return "Impressive Knowledge!";
      if (percentage >= 60) return "Good Understanding!";
      if (percentage >= 40) return "Getting There!";
      return "Keep Learning!";
    }
    
    function getScoreColor(percentage) {
      if (percentage >= 75) return "high-score";
      if (percentage >= 50) return "medium-score";
      return "low-score";
    }
    
    function showToast(title, message) {
      const toast = document.createElement('div');
      toast.className = 'toast animate-fade-in';
      toast.innerHTML = `
        <div class="toast-content">
          <div class="toast-title">${title}</div>
          <div class="toast-message">${message}</div>
        </div>
        <button class="toast-close">×</button>
      `;
      
      document.body.appendChild(toast);
      
      toast.querySelector('.toast-close').addEventListener('click', () => {
        toast.classList.add('animate-fade-out');
        setTimeout(() => {
          document.body.removeChild(toast);
        }, 300);
      });
      
      setTimeout(() => {
        toast.classList.add('animate-fade-out');
        setTimeout(() => {
          if (document.body.contains(toast)) {
            document.body.removeChild(toast);
          }
        }, 300);
      }, 5000);
    }
  });
  