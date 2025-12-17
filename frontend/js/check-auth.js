// Check Auth State and Update UI with ES Modules
import { auth } from './firebase-config.js';
import { onAuthStateChanged } from 'firebase/auth';
import { getUserFromFirestore, logout } from './auth.js';

document.addEventListener('DOMContentLoaded', function() {
    // Check if user is logged in
    onAuthStateChanged(auth, user => {
        if (user) {
            console.log('✅ User is logged in:', user.email);
            
            // Get user data from Firestore
            getUserFromFirestore(user.uid).then(userData => {
                if (userData) {
                    console.log('👤 User data:', userData);
                    
                    // Update navbar/UI with user info
                    updateNavbarWithUser(userData);
                    
                    // Store user data locally
                    localStorage.setItem('currentUser', JSON.stringify(userData));
                }
            });
        } else {
            console.log('❌ User is not logged in');
            
            // Clear user data
            localStorage.removeItem('currentUser');
            
            // Update navbar to show Sign up/Sign in
            updateNavbarForGuest();
        }
    });
});

// Update navbar when user is logged in
function updateNavbarWithUser(userData) {
    const glassBtnLink = document.querySelector('.glass-btn-link');
    const glassBtn = document.querySelector('.glass-btn');
    
    if (glassBtn && userData) {
        // Change button to show user info
        glassBtn.innerHTML = `
            <div style="display: flex; align-items: center; gap: 10px;">
                <div style="text-align: right;">
                    <div style="font-size: 12px; opacity: 0.8; color: white;">Welcome</div>
                    <div style="font-size: 14px; font-weight: 600; color: white;">${userData.displayName || userData.email}</div>
                </div>
                <img id="user-avatar" src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='white'%3E%3Ccircle cx='12' cy='8' r='4'/%3E%3Cpath d='M 6 20 Q 6 14 12 14 Q 18 14 18 20'/%3E%3C/svg%3E" alt="User" style="width: 24px; height: 24px; border-radius: 50%;">
            </div>
        `;
        
        // Add click handler to navigate to user-account.html
        if (glassBtnLink) {
            glassBtnLink.addEventListener('click', (e) => {
                e.preventDefault();
                // Navigate to user account page
                window.location.href = 'pages/user-account.html';
            });
        }
    }
}

// Update navbar when user is not logged in
function updateNavbarForGuest() {
    const glassBtnLink = document.querySelector('.glass-btn-link');
    const glassBtn = document.querySelector('.glass-btn');
    
    if (glassBtn && glassBtnLink) {
        glassBtn.innerHTML = `
            <img src="assets/icons/loginicon.svg" alt="Icon" />
            <div class="button-text">Sign up/Sign in</div>
        `;
        
        // Set href to redirect to signup
        glassBtnLink.href = 'pages/signup.html';
    }
}

// Get current user from localStorage
function getCurrentUserData() {
    const userData = localStorage.getItem('currentUser');
    return userData ? JSON.parse(userData) : null;
}

// Check if user is logged in before navigating to protected pages
export function redirectIfNotAuthenticated(targetPage = 'user-account.html') {
    onAuthStateChanged(auth, user => {
        if (!user) {
            console.log('❌ User not logged in, redirecting to login...');
            window.location.href = 'login.html';
        } else {
            console.log('✅ User authenticated, access granted');
        }
    });
}

