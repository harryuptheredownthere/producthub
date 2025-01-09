import React from 'react';
import ProductHub from './components/ProductHub.jsx';
import AuthWrapper from './components/AuthWrapper';

function App() {
  return (
    <div className="App">
      <AuthWrapper>
        <ProductHub />
      </AuthWrapper>
    </div>
  );
}

export default App;