import React, { useState, useEffect } from 'react';

const Weather = () => {
  const [temperature, setTemperature] = useState(null);
  const [error, setError] = useState(null);

  const fetchWeather = async () => {
    console.log('Attempting to fetch weather data...'); // Debug log
    try {
      const apiKey = import.meta.env.VITE_OPENWEATHER_API_KEY;
      const url = `https://api.openweathermap.org/data/2.5/weather?lat=48.1&lon=11.6&units=metric&appid=${apiKey}`;
      console.log('Fetching from URL:', url.replace(apiKey, 'API_KEY_HIDDEN')); // Debug log (hide key)
      
      const response = await fetch(url);
      const data = await response.json();
      
      console.log('API Response:', data); // Debug log
      
      if (response.ok) {
        const roundedTemp = Math.round(data.main.temp);
        console.log('Setting temperature to:', roundedTemp); // Debug log
        setTemperature(roundedTemp);
      } else {
        console.error('API Error Response:', data); // Debug log
        setError(`Failed to fetch weather data: ${data.message}`);
      }
    } catch (err) {
      console.error('Fetch Error:', err); // Debug log
      setError(`Failed to fetch weather data: ${err.message}`);
    }
  };

  useEffect(() => {
    console.log('Weather component mounted'); // Debug log
    fetchWeather();

    const interval = setInterval(fetchWeather, 3600000);
    
    return () => {
      console.log('Cleaning up interval'); // Debug log
      clearInterval(interval);
    };
  }, []);

  // Show error message if there is one
  if (error) {
    return <div className="weather error">{error}</div>;
  }

  // Show loading state while fetching
  if (temperature === null) {
    return <div className="weather">Loading...</div>;
  }

  return (
    <div className="weather">
      {temperature}°C
    </div>
  );
};

export default Weather;