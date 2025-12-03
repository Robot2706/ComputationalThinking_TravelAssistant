import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';
import { getFirestore } from 'firebase/firestore';

// Firebase Configuration
const firebaseConfig = {
  apiKey: "AIzaSyDF9lK914D_YpHAUNwD2lf8X5q27pH05AY",
  authDomain: "rism-24a9a.firebaseapp.com",
  projectId: "rism-24a9a",
  storageBucket: "rism-24a9a.firebasestorage.app",
  messagingSenderId: "1014525451464",
  appId: "1:1014525451464:web:facd617d7d8c86212019fd",
  measurementId: "G-LR7VE1J9XH"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Get Auth instance
export const auth = getAuth(app);

// Get Firestore instance
export const db = getFirestore(app);
