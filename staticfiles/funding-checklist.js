// Initial checklist data
const initialChecklist = [
    { id: 1, text: "Create a business plan", completed: false },
    { id: 2, text: "Register your company", completed: false },
    { id: 3, text: "Open a business bank account", completed: false },
    { id: 4, text: "Apply for an EIN", completed: false },
    { id: 5, text: "Prepare financial projections", completed: false },
    { id: 6, text: "Research funding options", completed: false },
    { id: 7, text: "Prepare pitch deck", completed: false },
    { id: 8, text: "Network with potential investors", completed: false },
    { id: 9, text: "Attend funding events", completed: false },
    { id: 10, text: "Apply for grants", completed: false },
  ];
  
  // DOM elements
  const progressText = document.getElementById('progress-text');
  const progressValue = document.getElementById('progress-value');
  const checklistContainer = document.getElementById('checklist-container');
  const resetButton = document.getElementById('reset-button');
  const backButton = document.getElementById('back-button');
  const toast = document.getElementById('toast');
  const toastTitle = document.getElementById('toast-title');
  const toastDescription = document.getElementById('toast-description');
  
  // State variables
  let checklistItems = [];
  
  // Initialize the app
  function init() {
    loadChecklistFromStorage();
    renderChecklist();
    updateProgress();
    
    // Event listeners
    resetButton.addEventListener('click', resetChecklist);
    backButton.addEventListener('click', goBack);
  }
  
  // Load checklist data from localStorage
  function loadChecklistFromStorage() {
    const savedChecklist = localStorage.getItem('fundingChecklist');
    
    if (savedChecklist) {
      checklistItems = JSON.parse(savedChecklist);
    } else {
      checklistItems = [...initialChecklist];
    }
  }
  
  // Save checklist data to localStorage
  function saveChecklistToStorage() {
    localStorage.setItem('fundingChecklist', JSON.stringify(checklistItems));
  }
  
  // Render the checklist items
  function renderChecklist() {
    checklistContainer.innerHTML = '';
    
    checklistItems.forEach(item => {
      const checklistItem = document.createElement('div');
      checklistItem.className = `checklist-item ${item.completed ? 'completed' : ''}`;
      checklistItem.dataset.id = item.id;
      
      checklistItem.innerHTML = `
        <div class="circle-icon">
          ${item.completed ? 
            `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
              <polyline points="22 4 12 14.01 9 11.01"></polyline>
            </svg>` : 
            `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#9ca3af" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"></circle>
            </svg>`
          }
        </div>
        <div class="item-text">${item.text}</div>
      `;
      
      checklistItem.addEventListener('click', () => toggleChecklistItem(item.id));
      checklistContainer.appendChild(checklistItem);
    });
  }
  
  // Toggle an item's completed status
  function toggleChecklistItem(id) {
    checklistItems = checklistItems.map(item => {
      if (item.id === id) {
        const newCompletedState = !item.completed;
        
        if (newCompletedState) {
          showToast('Task Completed', `You've completed: ${item.text}`);
        }
        
        return { ...item, completed: newCompletedState };
      }
      return item;
    });
    
    renderChecklist();
    updateProgress();
    saveChecklistToStorage();
  }
  
  // Update the progress bar and text
  function updateProgress() {
    const completedCount = checklistItems.filter(item => item.completed).length;
    const totalCount = checklistItems.length;
    const progressPercentage = Math.round((completedCount / totalCount) * 100);
    
    progressText.textContent = `Progress: ${progressPercentage}% Complete`;
    progressValue.style.width = `${progressPercentage}%`;
  }
  
  // Reset all items to incomplete
  function resetChecklist() {
    checklistItems = checklistItems.map(item => ({ ...item, completed: false }));
    
    renderChecklist();
    updateProgress();
    saveChecklistToStorage();
    showToast('Checklist Reset', 'All items have been reset to incomplete.');
  }
  
  // Go back to the previous page
  function goBack() {
    window.history.back();
  }
  
  // Show a toast notification
  function showToast(title, description) {
    toastTitle.textContent = title;
    toastDescription.textContent = description;
    
    toast.classList.add('show');
    
    setTimeout(() => {
      toast.classList.remove('show');
    }, 3000);
  }
  
  // Initialize the app when the DOM is loaded
  document.addEventListener('DOMContentLoaded', init);