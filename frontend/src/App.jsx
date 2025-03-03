import React, { useState } from 'react';

function App() {
  const [message, setMessage] = useState('');
  const apiEndpoint = 'https://v97zpgbtk5.execute-api.us-east-1.amazonaws.com/Prod/refresh';

  const callApi = async (action) => {
    try {
      const response = await fetch(apiEndpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action })
      });
      const data = await response.json();
      setMessage(JSON.stringify(data, null, 2));
    } catch (error) {
      console.error('Error calling API:', error);
      setMessage('Error calling API');
    }
  };

  return (
    <div style={{ padding: '20px' }}>
      <h1>ECFR Analyzer</h1>
      <div>
        <button onClick={() => callApi('refresh')}>Refresh Agencies</button>
        <button onClick={() => callApi('full_refresh')}>Full Refresh (Multiple Endpoints)</button>
        <button onClick={() => callApi('detailed')}>Detailed Analysis</button>
      </div>
      {message && <pre>{message}</pre>}
    </div>
  );
}

export default App;