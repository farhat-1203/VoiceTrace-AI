import React, { useState } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import MainTabNavigator from './src/navigation/MainTabNavigator';
import SignInScreen from './src/screens/SignInScreen';

export default function App() {
  const [signedIn, setSignedIn] = useState(false);

  if (!signedIn) {
    return <SignInScreen onSignIn={() => setSignedIn(true)} />;
  }

  return (
    <NavigationContainer>
      <MainTabNavigator onSignOut={() => setSignedIn(false)} />
    </NavigationContainer>
  );
}
