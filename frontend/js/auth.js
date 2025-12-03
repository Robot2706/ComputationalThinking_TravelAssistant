// Firebase Authentication Functions with ES Modules
import { auth, db } from './firebase-config.js';
import { 
    createUserWithEmailAndPassword, 
    signInWithEmailAndPassword, 
    signOut, 
    GoogleAuthProvider, 
    signInWithPopup, 
    updateProfile,
    onAuthStateChanged 
} from 'firebase/auth';
import { collection, doc, getDoc, setDoc, updateDoc } from 'firebase/firestore';

// === LOGIN WITH EMAIL ===
export function loginWithEmail(email, password) {
    return signInWithEmailAndPassword(auth, email, password)
        .then(userCredential => {
            const user = userCredential.user;
            
            // Check if user exists in Firestore
            return getDoc(doc(db, 'users', user.uid))
                .then(docSnapshot => {
                    if (docSnapshot.exists()) {
                        // Update lastLogin
                        return updateDoc(doc(db, 'users', user.uid), {
                            lastLogin: new Date()
                        }).then(() => {
                            console.log('✅ Login successful:', user.email);
                            console.log('✅ User found in database');
                            // Redirect to home after login
                            setTimeout(() => {
                                window.location.href = '/index.html';
                            }, 1000);
                            return user;
                        });
                    } else {
                        console.warn('⚠️ User not found in database, creating new entry');
                        // User exists in Auth but not in Firestore, create entry
                        return setDoc(doc(db, 'users', user.uid), {
                            uid: user.uid,
                            email: user.email,
                            displayName: user.displayName || email.split('@')[0],
                            createdAt: new Date(),
                            lastLogin: new Date()
                        }).then(() => {
                            console.log('✅ Login successful:', user.email);
                            setTimeout(() => {
                                window.location.href = '/index.html';
                            }, 1000);
                            return user;
                        });
                    }
                });
        })
        .catch(error => {
            console.error('❌ Login error:', error.message);
            
            // Check if user doesn't exist
            if (error.code === 'auth/user-not-found') {
                showError('Email not registered. Please sign up first.');
            } else if (error.code === 'auth/wrong-password') {
                showError('Incorrect password. Please try again.');
            } else {
                showError(error.message);
            }
            throw error;
        });
}

// === LOGIN WITH GOOGLE ===
export function loginWithGoogle() {
    const provider = new GoogleAuthProvider();
    return signInWithPopup(auth, provider)
        .then(result => {
            const user = result.user;
            
            // Check if user exists in Firestore
            return getDoc(doc(db, 'users', user.uid))
                .then(docSnapshot => {
                    if (docSnapshot.exists()) {
                        // Update lastLogin
                        return updateDoc(doc(db, 'users', user.uid), {
                            lastLogin: new Date()
                        }).then(() => {
                            console.log('✅ Google login successful:', user.email);
                            // Redirect to home after login
                            setTimeout(() => {
                                window.location.href = '/index.html';
                            }, 1000);
                            return user;
                        });
                    } else {
                        // First time Google login, create new user entry
                        return setDoc(doc(db, 'users', user.uid), {
                            uid: user.uid,
                            email: user.email,
                            displayName: user.displayName,
                            photoURL: user.photoURL,
                            createdAt: new Date(),
                            lastLogin: new Date(),
                            loginMethod: 'google'
                        }).then(() => {
                            console.log('✅ Google login successful:', user.email);
                            setTimeout(() => {
                                window.location.href = '/index.html';
                            }, 1000);
                            return user;
                        });
                    }
                });
        })
        .catch(error => {
            console.error('❌ Google login error:', error.message);
            showError(error.message);
            throw error;
        });
}

// === SIGNUP ===
export function signupWithEmail(email, password, displayName = '') {
    return createUserWithEmailAndPassword(auth, email, password)
        .then(userCredential => {
            const user = userCredential.user;
            
            // Update profile with display name
            if (displayName) {
                return updateProfile(user, {
                    displayName: displayName
                }).then(() => {
                    // Save user to Firestore
                    return setDoc(doc(db, 'users', user.uid), {
                        uid: user.uid,
                        email: user.email,
                        displayName: displayName,
                        createdAt: new Date(),
                        lastLogin: new Date()
                    });
                }).then(() => {
                    console.log('✅ Signup successful:', user.email);
                    // Redirect to login page
                    setTimeout(() => {
                        window.location.href = './login.html';
                    }, 1000);
                    return user;
                });
            }
            
            // Save user to Firestore without displayName
            return setDoc(doc(db, 'users', user.uid), {
                uid: user.uid,
                email: user.email,
                displayName: email.split('@')[0], // Use email prefix as name
                createdAt: new Date(),
                lastLogin: new Date()
            }).then(() => {
                console.log('✅ Signup successful:', user.email);
                setTimeout(() => {
                    window.location.href = './login.html';
                }, 1000);
                return user;
            });
        })
        .catch(error => {
            console.error('❌ Signup error:', error.message);
            showError(error.message);
            throw error;
        });
}

// === LOGOUT ===
export function logout() {
    return signOut(auth)
        .then(() => {
            console.log('✅ Logout successful');
            window.location.href = '/index.html';
        })
        .catch(error => {
            console.error('❌ Logout error:', error.message);
            showError(error.message);
        });
}

// === GET CURRENT USER ===
export function getCurrentUser() {
    return auth.currentUser;
}

// === CHECK AUTH STATE ===
export function onAuthChange(callback) {
    return onAuthStateChanged(auth, callback);
}

// === GET USER INFO FROM FIRESTORE ===
export function getUserFromFirestore(uid) {
    return getDoc(doc(db, 'users', uid))
        .then(docSnapshot => {
            if (docSnapshot.exists()) {
                console.log('📋 User data:', docSnapshot.data());
                return docSnapshot.data();
            } else {
                console.log('❌ No user document');
                return null;
            }
        })
        .catch(error => {
            console.error('❌ Error getting user:', error.message);
            return null;
        });
}

// === SHOW ERROR ===
function showError(message) {
    const errorDiv = document.getElementById('error-message');
    if (errorDiv) {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
        setTimeout(() => {
            errorDiv.style.display = 'none';
        }, 5000);
    } else {
        alert('Error: ' + message);
    }
}

// === SHOW SUCCESS ===
function showSuccess(message) {
    const successDiv = document.getElementById('success-message');
    if (successDiv) {
        successDiv.textContent = message;
        successDiv.style.display = 'block';
        setTimeout(() => {
            successDiv.style.display = 'none';
        }, 3000);
    }
}

// === PASSWORD VISIBILITY TOGGLE ===
export function togglePasswordVisibility(passwordInput, hideBtn) {
    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        hideBtn.textContent = 'Show';
    } else {
        passwordInput.type = 'password';
        hideBtn.textContent = 'Hide';
    }
}
